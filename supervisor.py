from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor
from fundamental_analyst import report_agent
from fundamental_queryer import fundamental_query_agent
from query_fixture_id import query_agent

model = ChatOpenAI(model="gpt-5", temperature=0)

SUPERVISOR_PROMPT = """
你是一个智能任务调度系统，负责判断用户意图并将任务分配给最合适的Agent。

可选Agent及适用场景：
1. report_agent：根据fixture_id可以撰写英文的全面比赛基本面报告，含实力、近况、伤停、战意与Markdown表格。
2. fundamental_query_agent：根据fixture_id可以用中英回答足球资讯类问答，聚焦即时数据与简明结果。
3. query_agent：按联赛名、今天/明天日期、队名进行比赛信息以及fixture_id查询（PostgreSQL，支持模糊与相似度）。

决策规则：
1. 依据问题类型选择最匹配的Agent；一次仅选择一个。
2. 当用户输入包含双方队名或出现“VS”时：首先路由到query_agent，并让其选取最匹配的一场（优先使用select_fixture_id_by_team_vs），在交接消息首行明确写出：fixture_id: <数字>。
3. 若成功得到fixture_id，则立即路由到report_agent生成详尽英文基本面报告；如用户只需简要资讯回答，路由到fundamental_query_agent。
4. 若无法获得fixture_id，返回简短说明并继续尝试其他可行检索（如联赛或日期）；实在无法定位时再选择FINISH。

结束规则（避免循环）：
1. 最近一次调用是report_agent且已输出报告，立即选择FINISH，不再调用其他Agent。
2. 最近一次调用是fundamental_query_agent且已直接回答用户关切，选择FINISH。
3. 最近一次调用是query_agent且已明确提供fixture_id，但用户未提出更深入分析需求时，选择FINISH。
4. 最多交接2次：query_agent → report_agent 或 query_agent → fundamental_query_agent；超过则选择FINISH。
5. 内容充分时严禁再次调用任何Agent。

从以下选项中选择一个：['report_agent','fundamental_query_agent','query_agent','FINISH']
"""

supervisor = create_supervisor(
    model=model,
    agents=[report_agent, fundamental_query_agent, query_agent],
    prompt=SUPERVISOR_PROMPT,
    add_handoff_back_messages=True
).compile()
