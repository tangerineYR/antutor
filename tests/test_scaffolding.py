import pytest
from routers.chat import get_recovery_prompt
from multi_agent.prompts import RECOVERY_NUDGE_PROMPT, RECOVERY_CONCEPT_PROMPT, RECOVERY_FILL_BLANK_PROMPT, RECOVERY_REVEAL_PROMPT

@pytest.mark.parametrize('level,template',[(1,RECOVERY_NUDGE_PROMPT),(2,RECOVERY_CONCEPT_PROMPT),(3,RECOVERY_FILL_BLANK_PROMPT),(4,RECOVERY_REVEAL_PROMPT),(5,RECOVERY_REVEAL_PROMPT)])
def test_recovery_levels_keep_learner_context(level,template):
    values=dict(concept_name='inflation',definition='prices rise',acceptable_extensions='sustained',
        last_question='Why?',kg_context='prices',student_answer='not sure',session_context='earlier answer')
    result=get_recovery_prompt(**values,idk_count=level)
    assert result=='/no_think\n'+template.format(**values)
    assert 'inflation' in result
