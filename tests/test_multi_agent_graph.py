from unittest.mock import AsyncMock
import pytest
from multi_agent import graph

@pytest.mark.parametrize('retry',[True,False])
async def test_compiled_graph_routes_and_preserves_scope(monkeypatch,retry):
    seen=[]
    async def draft(state):
        seen.append(state['cache_scope'])
        return {'draft_reviews':{'The Academic Auditor':{'retry_needed':retry}}}
    retry_node=AsyncMock(return_value={'final_synthesis':'retry'})
    cross=AsyncMock(return_value={'rebuttal_results':[]})
    synthesis=AsyncMock(return_value={'final_synthesis':'synthesized'})
    monkeypatch.setattr(graph,'drafting_node',draft)
    monkeypatch.setattr(graph,'retry_node',retry_node)
    monkeypatch.setattr(graph,'cross_review_node',cross)
    monkeypatch.setattr(graph,'synthesis_node',synthesis)
    scope={'learner_id':'learner','session_id':'1','concept_id':'2'}
    result=await graph.build_graph().ainvoke({'concept':'inflation','user_answer':'answer','cache_scope':scope})
    assert seen==[scope]
    if retry:
        assert result['final_synthesis']=='retry'
        retry_node.assert_awaited_once(); cross.assert_not_awaited(); synthesis.assert_not_awaited()
    else:
        assert result['final_synthesis']=='synthesized'
        cross.assert_awaited_once(); synthesis.assert_awaited_once(); retry_node.assert_not_awaited()
    assert result['cache_scope']==scope
