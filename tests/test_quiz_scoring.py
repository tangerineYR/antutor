from unittest.mock import MagicMock
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
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

def test_uncertainty_is_persisted_as_zero(monkeypatch):
    import services.quiz_service as service
    db=MagicMock(); monkeypatch.setattr(service,'supabase',db)
    questions=db.table.return_value.select.return_value.in_.return_value
    questions.execute.return_value=SimpleNamespace(data=[{'question_id':1,'correct_option':3}])
    db.table.return_value.insert.return_value.execute.return_value=SimpleNamespace(data=[{'attempt_id':1}])
    result=QuizService.evaluate_submission(QuizSubmission(session_id='1',user_id='user',concept='inflation',
        is_pre_test=True,answers=[QuizAnswerSubmit(question_id=1,selected_choice=6,confidence_level=0)]))
    assert result.score==0
    answers=db.table.return_value.insert.call_args.args[0]
    assert answers[0]['is_correct'] is False and answers[0]['earned_score']==0

def test_quiz_rejects_another_learners_session(monkeypatch):
    import routers.quiz as router
    from fastapi import HTTPException
    db=MagicMock();monkeypatch.setattr(router,'supabase',db)
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data=[]
    submission=QuizSubmission(session_id='12',user_id='forged',concept='inflation',is_pre_test=True,answers=[])
    with pytest.raises(HTTPException) as error:
        router.submit_quiz(submission,{'user_id':'real-user'})
    assert error.value.status_code==404
    assert db.table.return_value.select.return_value.eq.return_value.eq.call_args.args==('user_id','real-user')
