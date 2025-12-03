import json
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Any, Optional
from api_football_tools import get_fixture_head2head, get_home_last_10, get_away_last_10, get_injuries, get_fixture_basic_info, get_standing_home_info, get_standing_away_info

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

llm = ChatOpenAI(model="gpt-5", temperature=0)
tools = [
            get_fixture_head2head,
            get_home_last_10,
            get_away_last_10,
            get_injuries,
            get_fixture_basic_info,
            get_standing_home_info,
            get_standing_away_info,
            query_fixture_id_by_league,
            query_fixture_id_by_date,
            query_fixture_id_by_team_name,
        ]

prompt = """
"你是一个有帮助的AI助手，正在与其他助手协作。"
" 请使用提供的工具逐步回答问题。"
" 如果无法完全回答也没关系，其他拥有不同工具的助手会接续你的工作。请尽你所能推进进度。"
" 如果你或任何其他助手已有最终交易建议：下注/观望或者可交付成果，"
" 请在回复前加上'最终交易建议：下注/观望'，以便团队停止后续操作。"
" 你可使用以下工具：get_fixture_head2head,
            get_home_last_10,
            get_away_last_10,
            get_injuries,
            get_fixture_basic_info,
            get_standing_home_info,
            get_standing_away_info,
            query_fixture_id_by_league,
            query_fixture_id_by_date,
            query_fixture_id_by_team_name,
.\n"

"你是足球资讯助手，能够根据用户提出的与足球相关的问题，调用工具获取实时数据，并用中文或英文（依据用户提问语言）给出准确、简洁、易懂的回答。"
+ "回答时先直接回应用户关切，再按需补充背景或细节；如用户仅询问比分、赛程、伤停等单点信息，优先给出核心结果，无需冗长报告。"
+ "若用户希望深入了解某场比赛或球队，可根据用户对比赛的联赛或者队伍的描述查询fixture_id, 通过fixture_id获取数据并为用户提供资讯。"
+ "请使用以下可用工具: "
+ "get_fixture_head2head: 获取主队和客队的最近比赛记录."
+ "get_home_last_10: 获取主队最近10场比赛记录."
+ "get_away_last_10: 获取客队最近10场比赛记录."
+ "get_injuries: 获取球队伤停信息."
+ "get_fixture_basic_info: 获取比赛基本信息."
+ "get_standing_home_info: 获取主队积分榜信息."
+ "get_standing_away_info: 获取客队积分榜信息."
+ "get_fixture_odds: 获取比赛赔率信息."
+ "query_fixture_id_by_league: 根据联赛名称查询比赛ID."
+ "query_fixture_id_by_date: 根据日期查询比赛ID."
+ "query_fixture_id_by_team_name: 根据队伍名称查询比赛ID."
"""

fundamental_query_agent = create_react_agent(llm, tools, prompt=prompt, name="fundamental_query_agent")
