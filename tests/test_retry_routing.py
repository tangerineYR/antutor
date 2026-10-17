import pytest
from multi_agent.nodes import retry_router, moderator_check_node
from multi_agent.graph import debate_router

@pytest.mark.parametrize('flag,route', [(True,'retry_node'),('true','retry_node'),(False,'cross_review_node'),('false','cross_review_node')])
def test_retry_routing(flag,route):
    assert retry_router({'draft_reviews':{'The Academic Auditor':{'retry_needed':flag}}})==route

async def test_debate_is_bounded():
    state=await moderator_check_node({'debate_count':0})
    assert state['debate_count']==1
    assert debate_router(state)=='synthesis_node'
