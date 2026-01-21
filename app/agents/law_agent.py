from langchain.agents import create_agent

from chat.chat_utils import load_chat_model
from rag.law_tools import filter_search, query_search


def law_agent():
    tools = [filter_search, query_search]
    prompt = (
        "You have access to a tool that retrieves context from a korean law.\n"
        "Use the tool to help answer user queries.\n"
        "If you have enough information from the tool results, provide the final answer immediately.\n"
        "If the any information is not found after a search, do not repeat the same search; inform the user instead.\n"
        "만약, 특정 조문을 설명할 때는 항상 법령의 이름과 조항호목을 알려줘야돼.\n"
        "또한, 특정 조문이 포함되어 있는 법령의 link를 제공해줘."
    )
    model = load_chat_model(temperature=0)
    agent = create_agent(model, tools, system_prompt=prompt)
    return agent


# if __name__ == "__main__":
#     agent = law_agent()
#     print(agent.invoke({"messages": [{"role": "user", "content": "내가 절세를 좀 해보고 싶은데 정보 좀 알려줄래?"}]}))
