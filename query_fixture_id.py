import json
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
try:
    import psycopg
except Exception:
    psycopg = None
try:
    import psycopg2
except Exception:
    psycopg2 = None

llm = ChatOpenAI(model="gpt-5", temperature=0)

def _get_conn():
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    db = os.getenv("POSTGRES_DB")
    if psycopg is not None:
        return psycopg.connect(f"host={host} port={port} dbname={db} user={user} password={password}")
    if psycopg2 is not None:
        return psycopg2.connect(host=host, port=port, dbname=db, user=user, password=password)
    raise RuntimeError("PostgreSQL driver not available")

def _run_query(sql, params):
    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, r)) for r in rows]
    except Exception as e:
        return {"error": str(e)}

def _json_dumps(data):
    def _default(o):
        if isinstance(o, datetime):
            return o.isoformat()
        return str(o)
    return json.dumps(data, ensure_ascii=False, default=_default)

@tool("query_fixture_id_by_league", description="查询比赛ID")
def query_fixture_id_by_league(query: str) -> str:
    sql = 'SELECT fixture_id, league_name, teams_vs, fixture_date FROM api_football_fixtures WHERE league_name ILIKE %s ORDER BY similarity(league_name, %s) DESC NULLS LAST LIMIT 50'
    res = _run_query(sql, [f"%{query}%", query])
    return _json_dumps(res)
    
@tool("query_fixture_id_by_date", description="查询比赛ID")
def query_fixture_id_by_date(query: str) -> str:
    tz = ZoneInfo("Asia/Shanghai")
    today = datetime.now(tz).date()
    tomorrow = today + timedelta(days=1)
    sql = 'SELECT fixture_id, league_name, teams_vs, fixture_date FROM api_football_fixtures WHERE fixture_date::date IN (%s, %s) ORDER BY fixture_date ASC LIMIT 100'
    res = _run_query(sql, [today, tomorrow])
    return _json_dumps(res)

@tool("query_fixture_id_by_team_name", description="查询比赛ID")
def query_fixture_id_by_team_name(query: str) -> str:
    sql = 'SELECT fixture_id, league_name, teams_vs, fixture_date FROM api_football_fixtures WHERE teams_vs ILIKE %s ORDER BY similarity(teams_vs, %s) DESC NULLS LAST LIMIT 50'
    res = _run_query(sql, [f"%{query}%", query])
    return _json_dumps(res)

prompt = """
你是一个专业的足球比赛查询助手，能够根据用户的查询条件翻译成英文并返回相关的比赛信息。
你可以使用的工具：
1. query_fixture_id_by_league：根据联赛名称查询比赛ID
2. query_fixture_id_by_date：根据日期查询比赛ID
3. query_fixture_id_by_team_name：根据队伍名称查询比赛ID
输出规范：
- 若查询包含双方队名或包含“VS”，请优先选择相似度最高的一场比赛，并在首行明确输出：fixture_id: <数字>
- 若有多条候选，仅返回最匹配的一条；同时给出简要信息：联赛、对阵、时间。
"""

@tool("select_fixture_id_by_team_vs", description="根据队名对阵选择最匹配的一场比赛并返回ID")
def select_fixture_id_by_team_vs(query: str) -> str:
    sql = 'SELECT fixture_id, league_name, teams_vs, fixture_date, similarity(teams_vs, %s) AS sim FROM api_football_fixtures WHERE teams_vs ILIKE %s ORDER BY similarity(teams_vs, %s) DESC NULLS LAST LIMIT 1'
    res = _run_query(sql, [query, f"%{query}%", query])
    if isinstance(res, list) and res:
        return _json_dumps(res[0])
    return _json_dumps({})

query_agent = create_react_agent(llm, [query_fixture_id_by_league, query_fixture_id_by_date, query_fixture_id_by_team_name, select_fixture_id_by_team_vs], prompt=prompt, name="query_agent")
