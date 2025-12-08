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

def _parse_date(s: Optional[str]):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        return None

@tool("select_fixture_id_by_team_vs", description="通过双方队名或包含'VS'的对阵字符串查询比赛ID")
def select_fixture_id_by_team_vs(team_vs_query: str) -> str:
    tz = ZoneInfo("Asia/Shanghai")
    today = datetime.now(tz).date()
    start = today
    end = today + timedelta(days=2)
    sql = 'SELECT fixture_id, league_name, teams_vs, fixture_date FROM api_football_fixtures WHERE 1=1'
    params: list[Any] = []
    sql += ' AND fixture_date::date BETWEEN %s AND %s'
    params.extend([start, end])
    sql += ' AND teams_vs ILIKE %s'
    params.append(f"%{team_vs_query}%")
    sql += ' ORDER BY similarity(teams_vs, %s) DESC NULLS LAST, fixture_date ASC LIMIT 100'
    params.append(team_vs_query)
    res = _run_query(sql, params)
    return _json_dumps(res)

@tool("select_fixture_id_by_date_range", description="按日期范围查询比赛ID")
def select_fixture_id_by_date_range(query_start_date: Optional[str] = None, query_end_date: Optional[str] = None) -> str:
    tz = ZoneInfo("Asia/Shanghai")
    today = datetime.now(tz).date()
    start = _parse_date(query_start_date) or today
    end = _parse_date(query_end_date) or (today + timedelta(days=2))
    sql = 'SELECT fixture_id, league_name, teams_vs, fixture_date FROM api_football_fixtures WHERE fixture_date::date BETWEEN %s AND %s ORDER BY fixture_date ASC LIMIT 100'
    params: list[Any] = [start, end]
    res = _run_query(sql, params)
    return _json_dumps(res)

@tool("select_fixture_id_by_league", description="按联赛名称查询比赛ID")
def select_fixture_id_by_league(league_name: str) -> str:
    tz = ZoneInfo("Asia/Shanghai")
    today = datetime.now(tz).date()
    start = today
    end = today + timedelta(days=2)
    sql = 'SELECT fixture_id, league_name, teams_vs, fixture_date FROM api_football_fixtures WHERE 1=1'
    params: list[Any] = []
    sql += ' AND fixture_date::date BETWEEN %s AND %s'
    params.extend([start, end])
    sql += ' AND league_name ILIKE %s'
    params.append(f"%{league_name}%")
    sql += ' ORDER BY similarity(league_name, %s) DESC NULLS LAST, fixture_date ASC LIMIT 100'
    params.append(league_name)
    res = _run_query(sql, params)
    return _json_dumps(res)

prompt = """
你是一个专业的足球比赛查询助手，能够根据用户的查询条件翻译成英文查询条件比如"homeA vs homeB", "league_name", "fixture_date"并返回相关的比赛信息。
你可以使用的工具：
1. select_fixture_id_by_team_vs：根据双方队名或包含“VS”的对阵字符串查询比赛ID
2. select_fixture_id_by_date_range：根据日期范围查询比赛ID（默认今起三天）
3. select_fixture_id_by_league：根据联赛名称查询比赛ID
输出规范：
- 若查询包含双方队名或包含“VS”，优先调用select_fixture_id_by_team_vs。
- 工具会返回按相似度排序的比赛列表。请选择列表中的第一条（最相似的一条）作为目标比赛。
- 必须在回复的首行明确输出：fixture_id: <数字>
- 然后在后续行中列出该比赛的详情（日期、联赛、对阵双方）供用户确认。
"""


query_agent = create_react_agent(
    llm,
    [select_fixture_id_by_team_vs, select_fixture_id_by_date_range, select_fixture_id_by_league],
    prompt=prompt,
    name="query_agent",
)
