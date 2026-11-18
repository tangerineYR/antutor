"""Quiz checks using synthetic fixtures in a disposable local PostgreSQL stack."""
import copy
import os
import uuid
from urllib.parse import quote

import httpx
from supabase import create_client

from local_test_environment import require_disposable_environment


def main():
    base, database_url = require_disposable_environment()
    service = create_client(database_url, os.environ["SUPABASE_KEY"])
    suffix = uuid.uuid4().hex[:16]
    password = "Local quiz integration! 2026"

    def insert_one(table, values):
        response = service.table(table).insert(values).execute()
        assert response.data, f"Fixture insert failed: {table}"
        return response.data[0]

    with httpx.Client(base_url=base, timeout=15) as client:
        username = "quiz" + suffix
        other_username = "other" + suffix
        for name in (username, other_username):
            response = client.post("/register", json={"username": name, "password": password})
            assert response.status_code == 200
        login = client.post("/token", data={"username": username, "password": password})
        assert login.status_code == 200
        client.headers["Authorization"] = "Bearer " + login.json()["access_token"]

        def find_user(name):
            rows = service.table("users").select("user_id").eq("username", name).execute().data
            assert len(rows) == 1
            return rows[0]["user_id"]

        user_id = find_user(username)
        other_user_id = find_user(other_username)
        concepts = [insert_one("concepts", {
            "name": f"quiz test {label} {suffix}",
            "definition": f"Synthetic test concept {label}.",
        }) for label in ("a", "b", "empty")]
        concept_a, concept_b, concept_empty = concepts

        def create_question(concept, label):
            return insert_one("questions", {
                "concept_id": concept["concept_id"],
                "question_text": "Synthetic question " + label,
                "option_1": "A", "option_2": "B", "option_3": "C",
                "option_4": "D", "option_5": "E",
                "correct_option": 1, "commentary": "Synthetic explanation.",
            })

        question_a = create_question(concept_a, "A")
        question_b = create_question(concept_b, "B")
        fixture_question_ids = [question_a["question_id"], question_b["question_id"]]

        def create_session(owner, concept):
            return insert_one("sessions", {"user_id": owner, "concept_id": concept["concept_id"]})

        session_a = create_session(user_id, concept_a)
        session_b = create_session(user_id, concept_b)
        foreign_session = create_session(other_user_id, concept_a)

        def get_questions(concept):
            return client.get("/quiz/" + quote(concept, safe=""))

        for concept, question in ((concept_a, question_a), (concept_b, question_b)):
            response = get_questions(concept["name"])
            assert response.status_code == 200
            rows = response.json()
            assert [row["id"] for row in rows] == [question["question_id"]]
            assert all(row["concept"] == concept["name"] for row in rows)
            assert all("correct_option" not in row and "commentary" not in row for row in rows)

        empty = get_questions(concept_empty["name"])
        assert empty.status_code == 200 and empty.json() == []
        assert get_questions("unknown quiz " + suffix).status_code == 404
        english, korean = get_questions("inflation"), get_questions("인플레이션")
        assert english.status_code == korean.status_code == 200
        assert english.json() == korean.json()

        payload = {
            "session_id": str(session_a["session_id"]),
            "user_id": "ignored-client-id", "concept": concept_a["name"],
            "is_pre_test": True,
            "answers": [{"question_id": question_a["question_id"],
                         "selected_choice": 6, "confidence_level": 0}],
        }

        def assert_no_quiz_records():
            assert service.table("quiz_attempts").select("attempt_id").eq("user_id", user_id).execute().data == []
            assert service.table("quiz_answers").select("answer_id").in_("question_id", fixture_question_ids).execute().data == []

        def assert_rejected(candidate, expected_status):
            response = client.post("/quiz/submit", json=candidate)
            assert response.status_code == expected_status, (response.status_code, response.text)
            # Validation precedes writes. This is not a transaction rollback test.
            assert_no_quiz_records()

        assert_no_quiz_records()
        candidate = copy.deepcopy(payload)
        candidate["answers"] = []
        assert_rejected(candidate, 422)
        for duplicate_id in (question_a["question_id"], str(question_a["question_id"])):
            candidate = copy.deepcopy(payload)
            duplicate = dict(candidate["answers"][0], question_id=duplicate_id)
            candidate["answers"].append(duplicate)
            assert_rejected(candidate, 422)
        for invalid_id in (question_b["question_id"], 9223372036854775807):
            candidate = copy.deepcopy(payload)
            candidate["answers"][0]["question_id"] = invalid_id
            assert_rejected(candidate, 422)
        for wrong_session in (session_b, foreign_session):
            candidate = copy.deepcopy(payload)
            candidate["session_id"] = str(wrong_session["session_id"])
            assert_rejected(candidate, 404)

        response = client.post("/quiz/submit", json=payload)
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["score"] == 0 and result["max_score"] == 3
        assert result.get("details") is None
        attempts = service.table("quiz_attempts").select("attempt_id,user_id,total_score").eq("session_id", session_a["session_id"]).execute().data
        assert len(attempts) == 1 and attempts[0]["user_id"] == user_id
        assert attempts[0]["total_score"] == 0
        answers = service.table("quiz_answers").select(
            "question_id,selected_option,confidence_level,is_correct,earned_score"
        ).eq("attempt_id", attempts[0]["attempt_id"]).execute().data
        assert answers == [{"question_id": question_a["question_id"],
                            "selected_option": 6, "confidence_level": 0,
                            "is_correct": False, "earned_score": 0}]

        # POST covers the actual PRE lookup and hakes_gain UPDATE path too.
        post = copy.deepcopy(payload)
        post["is_pre_test"] = False
        post["answers"] = [{"question_id": str(question_a["question_id"]),
                            "selected_choice": 1, "confidence_level": 3}]
        response = client.post("/quiz/submit", json=post)
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["score"] == 3 and result["pre_test_score"] == 0
        assert result["skill_improvement"] == 1.0
        assert result["details"][0]["correct_option"] == 1
        stored = service.table("sessions").select("hakes_gain").eq("session_id", session_a["session_id"]).execute().data
        assert stored[0]["hakes_gain"] == 1.0

    print("Quiz integration passed: filtering, validation, ownership, persistence and PRE/POST gain")


if __name__ == "__main__":
    main()
