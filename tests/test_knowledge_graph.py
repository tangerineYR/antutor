import csv
import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest
from services.concept_normalization import normalize_concept
from services import knowledge_graph as kg

@pytest.mark.parametrize('term,canonical',[(' CPI ','consumer price index'),('기회비용','opportunity cost'),
    ('Interest_Rate','interest rate'),('환율','exchange rate'),('INFLATION','inflation')])
def test_aliases(term,canonical):
    assert normalize_concept(term)==canonical

async def test_graph_lookup_normalizes_and_uses_database(monkeypatch):
    session=AsyncMock(); driver=MagicMock()
    driver.session.return_value.__aenter__=AsyncMock(return_value=session)
    driver.session.return_value.__aexit__=AsyncMock(return_value=None)
    transaction=AsyncMock(); result=AsyncMock()
    result.data.return_value=[{'Subject':'inflation','Action':'RELATED_TO','Object':'consumer price index','Reason':'measure'}]
    transaction.run.return_value=result
    async def read(fn): return await fn(transaction)
    session.execute_read.side_effect=read
    monkeypatch.setattr(kg,'get_neo4j_driver',AsyncMock(return_value=driver))
    facts=await kg.get_economic_facts('인플레이션')
    assert 'consumer price index' in facts
    assert transaction.run.call_args.kwargs['keyword']=='inflation'
    assert driver.session.call_args.kwargs['database']==kg.NEO4J_DATABASE

def test_seed_deduplicates_aliases(tmp_path):
    spec=importlib.util.spec_from_file_location('seed',Path(__file__).parents[1]/'scripts/seed_neo4j.py')
    seed=importlib.util.module_from_spec(spec); spec.loader.exec_module(seed)
    path=tmp_path/'relations.csv'
    path.write_text('source,target,relationship,reason\n인플레이션,CPI,RELATED_TO,measure\nconsumer price index,inflation,RELATED_TO,measure\n')
    assert len(seed.load_relations(path))==1
    bundled=Path(__file__).parents[1]/'neo4j/seed/relation_data.csv'
    with bundled.open() as stream: count=len(list(csv.DictReader(stream)))
    assert len(seed.load_relations(bundled))==count
