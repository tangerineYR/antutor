from unittest.mock import MagicMock
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from fastapi import HTTPException
from schemas import QuizAnswerSubmit, QuizSubmission
from services.quiz_service import QuizService

@pytest.mark.parametrize('choice,confidence', [(6,0),(1,1),(2,2),(5,3)])
def test_valid_answer(choice,confidence):
    QuizAnswerSubmit(question_id=1,selected_choice=choice,confidence_level=confidence)

@pytest.mark.parametrize('choice,confidence', [(6,3),(6,1),(1,0),(0,1),(7,1),(1,4),(1,-1),(True,1),('6',0)])
def test_invalid_answer(choice,confidence):
    with pytest.raises(ValidationError):
        QuizAnswerSubmit(question_id=1,selected_choice=choice,confidence_level=confidence)

@pytest.mark.parametrize('correct,confidence,score', [(True,1,1),(True,2,2),(True,3,3),(False,1,0),(False,2,-2),(False,3,-6)])
def test_cbm(correct,confidence,score):
    assert QuizService._calculate_cbm_score(correct,confidence)==score

def submission(*, question_id=1, pre=True, session_id="1", choice=6, confidence=0):
    return QuizSubmission(
        session_id=session_id, user_id="user", concept="inflation",
        is_pre_test=pre,
        answers=[QuizAnswerSubmit(
            question_id=question_id, selected_choice=choice,
            confidence_level=confidence,
        )],
    )


@pytest.fixture
def quiz_db(monkeypatch):
    import services.quiz_service as service
    import routers.quiz as router

    def query(data):
        mock = MagicMock()
        for method in ("eq", "in_", "order", "limit"):
            getattr(mock, method).return_value = mock
        mock.execute.return_value = SimpleNamespace(data=data)
        return mock

    rows = {
        "concepts": [{"concept_id": 2, "name": "inflation"}],
        "questions": [{
            "question_id": 1, "correct_option": 3, "commentary": "Explanation",
            "question_text": "Question?",
            **{f"option_{i}": str(i) for i in range(1, 6)},
        }],
        "sessions": [{"session_id": 1}],
        "quiz_attempts": [{"attempt_id": 10, "total_score": 0}],
        "quiz_answers": [{"question_id": 1, "earned_score": 0}],
    }
    tables = {}
    for name, data in rows.items():
        table = MagicMock()
        table.select.return_value = query(data)
        table.insert.return_value = query([{"attempt_id": 11}])
        table.update.return_value = query([{"session_id": 1}])
        tables[name] = table
    client = MagicMock()
    client.table.side_effect = tables.__getitem__
    monkeypatch.setattr(service, "supabase", client)
    monkeypatch.setattr(router, "supabase", client)
    return tables


def assert_no_inserts(db):
    db["quiz_attempts"].insert.assert_not_called()
    db["quiz_answers"].insert.assert_not_called()


@pytest.mark.parametrize("question_id", [None, True, [], {}, "", "  "])
def test_invalid_question_id(question_id):
    with pytest.raises(ValidationError):
        submission(question_id=question_id)


@pytest.mark.parametrize("ids", [[], [1, 1], [1, "1"]])
def test_empty_or_duplicate_submission(ids):
    with pytest.raises(ValidationError):
        QuizSubmission(
            user_id="user", concept="inflation", is_pre_test=True,
            answers=[{
                "question_id": question_id, "selected_choice": 6,
                "confidence_level": 0,
            } for question_id in ids],
        )


def test_uncertainty_is_persisted_as_zero(quiz_db):
    result = QuizService.evaluate_submission(submission(), concept_id=2)
    assert result.score == 0 and result.max_score == 3
    assert result.details is None
    quiz_db["questions"].select.return_value.eq.assert_called_once_with("concept_id", 2)
    answers = quiz_db["quiz_answers"].insert.call_args.args[0]
    assert answers == [{
        "attempt_id": 11, "question_id": 1, "selected_option": 6,
        "confidence_level": 0, "is_correct": False, "earned_score": 0,
    }]


@pytest.mark.parametrize("question_id", [1, "1"])
def test_question_id_representations_score_identically(quiz_db, question_id):
    result = QuizService.evaluate_submission(
        submission(question_id=question_id, choice=3, confidence=3), concept_id=2,
    )
    assert result.score == 3
    assert quiz_db["quiz_answers"].insert.call_args.args[0][0]["question_id"] == 1


@pytest.mark.parametrize("available", [[], [{"question_id": 2, "correct_option": 3}]])
def test_missing_or_wrong_concept_question_rejected_before_writes(quiz_db, available):
    quiz_db["questions"].select.return_value.execute.return_value.data = available
    with pytest.raises(HTTPException) as error:
        QuizService.evaluate_submission(submission(), concept_id=2)
    assert error.value.status_code == 422
    assert_no_inserts(quiz_db)


def test_partially_resolved_question_set_rejected(quiz_db):
    request = submission()
    request.answers.append(QuizAnswerSubmit(
        question_id=2, selected_choice=6, confidence_level=0,
    ))
    with pytest.raises(HTTPException) as error:
        QuizService.evaluate_submission(request, concept_id=2)
    assert error.value.status_code == 422
    assert_no_inserts(quiz_db)


@pytest.mark.parametrize("phase", ["questions", "attempt", "answers"])
def test_database_failures_are_not_success(quiz_db, phase):
    query = {
        "questions": quiz_db["questions"].select.return_value,
        "attempt": quiz_db["quiz_attempts"].insert.return_value,
        "answers": quiz_db["quiz_answers"].insert.return_value,
    }[phase]
    query.execute.side_effect = RuntimeError("private database error")
    with pytest.raises(HTTPException) as error:
        QuizService.evaluate_submission(submission(), concept_id=2)
    assert error.value.status_code == 503
    assert "private" not in error.value.detail
    if phase == "questions":
        assert_no_inserts(quiz_db)
    elif phase == "attempt":
        quiz_db["quiz_answers"].insert.assert_not_called()
    else:
        # The first write already ran; this test makes no rollback claim.
        quiz_db["quiz_attempts"].insert.assert_called_once()
    quiz_db["quiz_attempts"].delete.assert_not_called()


@pytest.mark.parametrize("data", [None, [], [{}], [{"attempt_id": None}]])
def test_missing_attempt_id_stops_answer_write(quiz_db, data):
    quiz_db["quiz_attempts"].insert.return_value.execute.return_value.data = data
    with pytest.raises(HTTPException) as error:
        QuizService.evaluate_submission(submission(), concept_id=2)
    assert error.value.status_code == 503
    quiz_db["quiz_answers"].insert.assert_not_called()


@pytest.mark.parametrize("data", [None, []])
def test_unconfirmed_answer_write_is_error(quiz_db, data):
    quiz_db["quiz_answers"].insert.return_value.execute.return_value.data = data
    with pytest.raises(HTTPException) as error:
        QuizService.evaluate_submission(submission(), concept_id=2)
    assert error.value.status_code == 503


def test_post_feedback_and_comparable_pre_gain(quiz_db):
    result = QuizService.evaluate_submission(
        submission(pre=False, question_id="1", choice=3, confidence=3), concept_id=2,
    )
    assert result.score == 3 and result.skill_improvement == 1.0
    assert result.pre_test_score == 0
    assert result.details[0].correct_option == 3
    assert result.pre_test_details[0].correct_option == 3
    quiz_db["quiz_attempts"].select.return_value.eq.assert_any_call("user_id", "user")
    quiz_db["sessions"].update.assert_called_once_with({"hakes_gain": 1.0})
    quiz_db["sessions"].update.return_value.eq.assert_any_call("user_id", "user")
    quiz_db["sessions"].update.return_value.eq.assert_any_call("concept_id", 2)


@pytest.mark.parametrize("phase", ["pre", "pre_answers", "update"])
@pytest.mark.parametrize("missing_response", [False, True])
def test_post_processing_failures_are_errors(quiz_db, phase, missing_response):
    query = {
        "pre": quiz_db["quiz_attempts"].select.return_value,
        "pre_answers": quiz_db["quiz_answers"].select.return_value,
        "update": quiz_db["sessions"].update.return_value,
    }[phase]
    if missing_response:
        query.execute.return_value.data = None
    else:
        query.execute.side_effect = RuntimeError("private database error")
    with pytest.raises(HTTPException) as error:
        QuizService.evaluate_submission(submission(pre=False), concept_id=2)
    assert error.value.status_code == 503
    assert "private" not in error.value.detail
    quiz_db["quiz_answers"].insert.assert_called_once()


@pytest.mark.parametrize("pre_answers", [[], [{"question_id": 2, "earned_score": 0}]])
def test_incomplete_or_different_pre_has_no_gain(quiz_db, pre_answers):
    quiz_db["quiz_answers"].select.return_value.execute.return_value.data = pre_answers
    result = QuizService.evaluate_submission(submission(pre=False), concept_id=2)
    assert result.skill_improvement is None
    assert result.pre_test_score is None and result.pre_test_details is None
    quiz_db["sessions"].update.assert_called_once_with({"hakes_gain": None})


def test_missing_pre_is_normal_but_clears_stale_gain(quiz_db):
    quiz_db["quiz_attempts"].select.return_value.execute.return_value.data = []
    result = QuizService.evaluate_submission(submission(pre=False), concept_id=2)
    assert result.skill_improvement is None
    quiz_db["quiz_answers"].select.assert_not_called()
    quiz_db["sessions"].update.assert_called_once_with({"hakes_gain": None})


def test_sessionless_post_does_not_query_history(quiz_db):
    result = QuizService.evaluate_submission(submission(pre=False, session_id=None), concept_id=2)
    assert result.details and result.skill_improvement is None
    quiz_db["quiz_attempts"].select.assert_not_called()
    quiz_db["sessions"].update.assert_not_called()


def test_quiz_rejects_another_learners_session(quiz_db):
    import routers.quiz as router
    query = quiz_db["sessions"].select.return_value
    query.execute.return_value.data = []
    with pytest.raises(HTTPException) as error:
        router.submit_quiz(submission(), {"user_id": "real-user"})
    assert error.value.status_code == 404
    query.eq.assert_any_call("session_id", "1")
    query.eq.assert_any_call("user_id", "real-user")
    query.eq.assert_any_call("concept_id", 2)
    assert_no_inserts(quiz_db)


def test_session_lookup_failure_does_not_write(quiz_db):
    import routers.quiz as router
    quiz_db["sessions"].select.return_value.execute.side_effect = RuntimeError("private error")
    with pytest.raises(HTTPException) as error:
        router.submit_quiz(submission(), {"user_id": "real-user"})
    assert error.value.status_code == 503
    assert_no_inserts(quiz_db)


def test_token_identity_overrides_client_identity(quiz_db):
    import routers.quiz as router
    router.submit_quiz(submission(), {"user_id": "real-user"})
    assert quiz_db["quiz_attempts"].insert.call_args.args[0]["user_id"] == "real-user"


def test_missing_authenticated_identity_does_not_query_database(quiz_db):
    import routers.quiz as router
    with pytest.raises(HTTPException) as error:
        router.submit_quiz(submission(), {})
    assert error.value.status_code == 401
    quiz_db["concepts"].select.assert_not_called()
    assert_no_inserts(quiz_db)


def test_lookup_normalizes_alias_and_filters_concept(quiz_db):
    questions = QuizService.get_questions("인플레이션")
    quiz_db["concepts"].select.return_value.eq.assert_called_once_with("name", "inflation")
    quiz_db["questions"].select.return_value.eq.assert_called_once_with("concept_id", 2)
    assert questions[0].concept == "inflation"
    assert "correct_option" not in questions[0].model_dump()
    assert "commentary" not in questions[0].model_dump()


def test_known_concept_with_no_questions_is_empty(quiz_db):
    quiz_db["questions"].select.return_value.execute.return_value.data = []
    assert QuizService.get_questions("inflation") == []


def test_unknown_concept_is_404(quiz_db):
    quiz_db["concepts"].select.return_value.execute.return_value.data = []
    with pytest.raises(HTTPException) as error:
        QuizService.get_questions("unknown")
    assert error.value.status_code == 404
    quiz_db["questions"].select.assert_not_called()


@pytest.mark.parametrize("table", ["concepts", "questions"])
def test_lookup_failure_is_503(quiz_db, table):
    quiz_db[table].select.return_value.execute.side_effect = RuntimeError("private error")
    with pytest.raises(HTTPException) as error:
        QuizService.get_questions("inflation")
    assert error.value.status_code == 503


@pytest.mark.parametrize("answers", [[], [1, 1], [1, "1"]])
@pytest.mark.asyncio
async def test_http_validation_rejects_before_database_access(quiz_db, answers):
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient
    import routers.quiz as router

    app = FastAPI()
    app.include_router(router.router)
    async def current_user():
        return {"user_id": "user"}

    app.dependency_overrides[router.get_current_user] = current_user
    payload = submission().model_dump()
    payload["answers"] = [{
        "question_id": question_id, "selected_choice": 6, "confidence_level": 0,
    } for question_id in answers]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.post("/quiz/submit", json=payload)).status_code == 422
    quiz_db["concepts"].select.assert_not_called()
    assert_no_inserts(quiz_db)
