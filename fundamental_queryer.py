import json
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from api_football_tools import get_fixture_head2head, get_home_last_10, get_away_last_10, get_injuries, get_fixture_basic_info, get_standing_home_info, get_standing_away_info

llm = ChatOpenAI(model="gpt-5", temperature=0)
tools = [
            get_fixture_head2head,
            get_home_last_10,
            get_away_last_10,
            get_injuries,
            get_fixture_basic_info,
            get_standing_home_info,
            get_standing_away_info,
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
            get_fixture_odds,.\n"

"你是足球资讯助手，能够根据用户提出的与足球相关的问题，调用工具获取实时数据，并用中文或英文（依据用户提问语言）给出准确、简洁、易懂的回答。"
+ "回答时先直接回应用户关切，再按需补充背景或细节；如用户仅询问比分、赛程、伤停等单点信息，优先给出核心结果，无需冗长报告。"
+ "若用户希望深入了解某场比赛或球队，可主动提供基本面简述（实力、近况、伤停、战意）并附上关键数据。"
+ "请使用以下可用工具: "
+ "get_fixture_head2head: 获取主队和客队的最近比赛记录."
+ "get_home_last_10: 获取主队最近10场比赛记录."
+ "get_away_last_10: 获取客队最近10场比赛记录."
+ "get_injuries: 获取球队伤停信息."
+ "get_fixture_basic_info: 获取比赛基本信息."
+ "get_standing_home_info: 获取主队积分榜信息."
+ "get_standing_away_info: 获取客队积分榜信息."
+ "get_fixture_odds: 获取比赛赔率信息."
"""

fundamental_query_agent = create_react_agent(llm, tools, prompt=prompt, name="fundamental_query_agent")
