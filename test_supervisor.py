from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor
from fundamental_queryer import fundamental_query_agent
from query_fixture_id import query_agent

model = ChatOpenAI(model="gpt-5", temperature=0)

SUPERVISOR_PROMPT = """
你是一个智能任务调度系统，总的目标是根据用户给的讯息去找到比赛的fixture_id, 再根据fixture_id去提供用户想要的讯息比如实力、近况、伤停、战意等.
你需要任务分配给最合适的Agent。

可选Agent及适用场景：
1. fundamental_query_agent：根据fixture_id可以用中英回答足球资讯类问答，聚焦即时数据与简明结果。
2. query_agent：按联赛名、查询日期范围(开始日期, 查询结束日期(默认为今明后三天))、队名进行比赛信息等查询获取fixture_id（PostgreSQL，支持模糊与相似度）。

决策规则：
1. 依据问题类型选择最匹配的Agent；一次仅选择一个。
2. 当用户输入包含双方队名或出现“VS”时：首先路由到query_agent，并让其选取最匹配的一场（优先使用select_fixture_id_by_team_vs），在交接消息首行明确写出：fixture_id: <数字>。
3. 若成功得到fixture_id（即历史消息中包含 "fixture_id: <数字>"），则路由到fundamental_query_agent，让其利用该ID回答用户关于比赛详情（实力、近况、伤停、战意等）的提问。

从以下选项中选择一个：['fundamental_query_agent','query_agent','FINISH']
"""

supervisor = create_supervisor(
    model=model,
    agents=[fundamental_query_agent, query_agent],
    prompt=SUPERVISOR_PROMPT,
    add_handoff_back_messages=True
).compile()
