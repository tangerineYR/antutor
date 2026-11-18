from schemas import QuizQuestionOut, QuizSubmission, QuizResultOut, QuizAnswerDetailOut
from typing import List
from database import supabase
from fastapi import HTTPException
from services.concept_normalization import normalize_concept

class QuizService:
    @staticmethod
    def get_concept(concept: str) -> dict:
        try:
            response = (
                supabase.table("concepts")
                .select("concept_id, name")
                .eq("name", normalize_concept(concept))
                .limit(1)
                .execute()
            )
            if response.data is None:
                raise RuntimeError("Missing database response")
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail="개념 정보를 불러오지 못했습니다.",
            ) from exc

        if not response.data:
            raise HTTPException(status_code=404, detail="Concept not found")

        return response.data[0]

    @staticmethod
    def get_questions(concept: str) -> List[QuizQuestionOut]:
        resolved = QuizService.get_concept(concept)

        try:
            response = (
                supabase.table("questions")
                .select(
                    "question_id, question_text, "
                    "option_1, option_2, option_3, option_4, option_5"
                )
                .eq("concept_id", resolved["concept_id"])
                .order("question_id")
                .limit(5)
                .execute()
            )
            if response.data is None:
                raise RuntimeError("Missing database response")

            return [
                QuizQuestionOut(
                    id=question["question_id"],
                    concept=resolved["name"],
                    question=question["question_text"],
                    choices=[
                        question[f"option_{index}"]
                        for index in range(1, 6)
                    ],
                )
                for question in response.data
            ]
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail="퀴즈 문항을 불러오지 못했습니다.",
            ) from exc

    @staticmethod
    def _calculate_cbm_score(is_correct: bool, confidence_level: int) -> int:
        if confidence_level not in [1, 2, 3]:
            return 0
        
        if is_correct:
            if confidence_level == 1: return 1
            if confidence_level == 2: return 2
            if confidence_level == 3: return 3
        else:
            if confidence_level == 1: return 0
            if confidence_level == 2: return -2
            if confidence_level == 3: return -6
        return 0

    @staticmethod
    def _calculate_hakes_gain(pre_score: float, post_score: float, perfect_score: float) -> float:
        # 만점인 경우 공식의 분모가 0이 되어 계산이 불가능하므로, 향상 여지가 없었다고 가정하고 0.0을 반환
        if perfect_score == pre_score:
            return 0.0
        return (post_score - pre_score) / (perfect_score - pre_score)

    @staticmethod
    def evaluate_submission(submission: QuizSubmission, *, concept_id) -> QuizResultOut:
        question_ids = [answer.question_id for answer in submission.answers]
        requested_ids = {str(question_id) for question_id in question_ids}
        if not question_ids or len(requested_ids) != len(question_ids):
            raise HTTPException(status_code=422, detail="유효하지 않은 퀴즈 답안입니다.")

        try:
            questions_res = (
                supabase.table("questions")
                .select("question_id, correct_option, commentary")
                .eq("concept_id", concept_id)
                .in_("question_id", question_ids)
                .execute()
            )
            if questions_res.data is None:
                raise RuntimeError("Missing database response")
            questions_map = {
                str(question["question_id"]): question
                for question in questions_res.data
            }
        except Exception as exc:
            raise HTTPException(
                status_code=503, detail="퀴즈 채점 정보를 불러오지 못했습니다."
            ) from exc

        # Reject missing or cross-concept questions before either INSERT.
        if requested_ids != set(questions_map):
            raise HTTPException(
                status_code=422,
                detail="존재하지 않거나 해당 개념에 속하지 않는 문제입니다.",
            )

        evaluated_answers = []
        for answer in submission.answers:
            question = questions_map[str(answer.question_id)]
            is_correct = answer.selected_choice == question["correct_option"]
            earned_score = (
                0 if answer.selected_choice == 6
                else QuizService._calculate_cbm_score(is_correct, answer.confidence_level)
            )
            evaluated_answers.append({
                # Persist the database's ID representation, not the client's spelling.
                "question_id": question["question_id"],
                "selected_option": answer.selected_choice,
                "confidence_level": answer.confidence_level,
                "is_correct": is_correct,
                "earned_score": earned_score,
            })

        total_score = sum(answer["earned_score"] for answer in evaluated_answers)
        max_possible_score = len(evaluated_answers) * 3
        session_id = submission.session_id
        user_id = submission.user_id
        quiz_type = "PRE" if submission.is_pre_test else "POST"

        # Separate HTTP writes are not atomic. A 503 can follow a committed write.
        try:
            attempt_res = supabase.table("quiz_attempts").insert({
                "session_id": session_id,
                "user_id": user_id,
                "quiz_type": quiz_type,
                "total_score": total_score,
            }).execute()
            if not attempt_res.data or attempt_res.data[0].get("attempt_id") is None:
                raise RuntimeError("Missing attempt ID")
            attempt_id = attempt_res.data[0]["attempt_id"]
        except Exception as exc:
            raise HTTPException(
                status_code=503, detail="퀴즈 결과 저장을 완료하지 못했습니다."
            ) from exc

        try:
            answers_res = supabase.table("quiz_answers").insert([
                {"attempt_id": attempt_id, **answer}
                for answer in evaluated_answers
            ]).execute()
            if answers_res.data is None or len(answers_res.data) != len(evaluated_answers):
                raise RuntimeError("Missing saved answers")
        except Exception as exc:
            raise HTTPException(
                status_code=503, detail="퀴즈 답안 저장을 완료하지 못했습니다."
            ) from exc

        skill_improvement = None
        details = None
        pre_test_score_out = None
        pre_test_details_out = None

        if quiz_type == "POST":
            details = [
                QuizAnswerDetailOut(
                    question_id=answer["question_id"],
                    correct_option=questions_map[str(answer["question_id"])]["correct_option"],
                    commentary=questions_map[str(answer["question_id"])].get("commentary", ""),
                    earned_score=answer["earned_score"],
                )
                for answer in evaluated_answers
            ]

            # A sessionless POST has feedback but no comparable session history.
            if session_id is not None:
                try:
                    pre_res = (
                        supabase.table("quiz_attempts")
                        .select("total_score, attempt_id")
                        .eq("session_id", session_id)
                        .eq("user_id", user_id)
                        .eq("quiz_type", "PRE")
                        .order("created_at", desc=True)
                        .order("attempt_id", desc=True)
                        .limit(1)
                        .execute()
                    )
                    if pre_res.data is None:
                        raise RuntimeError("Missing PRE query response")
                except Exception as exc:
                    raise HTTPException(
                        status_code=503, detail="사전 퀴즈 결과를 불러오지 못했습니다."
                    ) from exc

                if pre_res.data:
                    try:
                        pre_attempt = pre_res.data[0]
                        pre_answers_res = (
                            supabase.table("quiz_answers")
                            .select("question_id, earned_score")
                            .eq("attempt_id", pre_attempt["attempt_id"])
                            .execute()
                        )
                        if pre_answers_res.data is None:
                            raise RuntimeError("Missing PRE answers response")
                        pre_answers = pre_answers_res.data
                        pre_ids = {str(answer["question_id"]) for answer in pre_answers}

                        # Orphan attempts and different question sets are not comparable.
                        if pre_ids == requested_ids and len(pre_answers) == len(question_ids):
                            pre_test_score_out = int(pre_attempt["total_score"])
                            skill_improvement = QuizService._calculate_hakes_gain(
                                pre_score=float(pre_test_score_out),
                                post_score=float(total_score),
                                perfect_score=float(max_possible_score),
                            )
                            pre_scores = {
                                str(answer["question_id"]): answer["earned_score"]
                                for answer in pre_answers
                            }
                            pre_test_details_out = [
                                QuizAnswerDetailOut(
                                    question_id=answer["question_id"],
                                    correct_option=questions_map[str(answer["question_id"])]["correct_option"],
                                    commentary=questions_map[str(answer["question_id"])].get("commentary", ""),
                                    earned_score=pre_scores[str(answer["question_id"])],
                                )
                                for answer in evaluated_answers
                            ]
                    except Exception as exc:
                        raise HTTPException(
                            status_code=503, detail="사전 퀴즈 답안을 불러오지 못했습니다."
                        ) from exc

                try:
                    updated = (
                        supabase.table("sessions")
                        .update({"hakes_gain": skill_improvement})
                        .eq("session_id", session_id)
                        .eq("user_id", user_id)
                        .eq("concept_id", concept_id)
                        .execute()
                    )
                    if not updated.data:
                        raise RuntimeError("Session update was not confirmed")
                except Exception as exc:
                    raise HTTPException(
                        status_code=503, detail="학습 향상도 저장을 완료하지 못했습니다."
                    ) from exc

        return QuizResultOut(
            session_id=session_id,
            score=total_score,
            max_score=max_possible_score,
            skill_improvement=skill_improvement,
            details=details,
            pre_test_score=pre_test_score_out,
            pre_test_details=pre_test_details_out,
        )
