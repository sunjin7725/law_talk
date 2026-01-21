from typing import List, Annotated, TypedDict, Literal
from pydantic import BaseModel, Field

from langgraph.graph import START, StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage, RemoveMessage, ToolMessage

from chat.chat_utils import load_chat_model
from agents.law_agent import law_agent
from utils import graph_to_png


class MainState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    contents: Annotated[List, "Added contents for user`s chat"]
    summary: Annotated[str, "chat history summary"]


class Router(BaseModel):
    """Route a user query to the appropriate agent."""

    datasource: Literal[
        "",
        "law_talk",
    ] = Field(
        ...,
        description="""
        Decide whether the user's question should be handled by a specialized
        Korean tax law agent or by general conversation.

        Choose one of the following options:
        - law_talk: Use this if the question is about Korean tax laws, tax regulations,
          legal definitions, articles, interpretations, or procedures.
        - "" (empty string): Use this if the question is general conversation,
          casual chat, or does not require legal or tax-specific knowledge.

        Select exactly one option based on the user's intent.
        """,
    )

model = load_chat_model(stream=True)
routing_model = load_chat_model(temperature=0)
routing_model = routing_model.with_structured_output(Router)

chat_prompt = """
You are a helpful and friendly assistant designed for engaging conversations with users. 
Your primary mission is to answer questions using the following contents and chat history. 
If the contents or chat history is not provided, feel free to engage the user in a friendly manner and ask how you can assist them. 
You should aim to provide concise and relevant answers while maintaining a natural flow of dialogue.

If you do not have the necessary context or chat history to answer the user's question, you can still provide a general response based on your knowledge. 
However, remember that special knowledge may be required for certain questions, and you should acknowledge that if applicable.

If the contents includes source information, please include the source in your response.

Always respond in the same language as the user's question.

contents:
    {contents}

chat_history:
    {chat_history}
"""
chat_template = ChatPromptTemplate([("system", chat_prompt), ("human", "{question}")])
chat_chain = chat_template | model | StrOutputParser()


routing_prompt = """
You are an expert at routing a user question to ["", "law_talk"].
"""
routing_prompt_template = ChatPromptTemplate([("system", routing_prompt), ("human", "{question}")])
routing_chain = routing_prompt_template | routing_model


def chat(state: MainState):
    summary = state.get("summary", "")
    contents = state.get("contents", "")
    response = chat_chain.invoke(
        {
            "question": state["messages"],
            "chat_history": summary,
            "contents": contents,
        }
    )
    return {"messages": AIMessage(response)}

def summarize_history(state: MainState):
    summary = state.get("summary", "")
    if summary:
        summary_message = (
            f"This is summary of the conversation to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above in Korean:"
        )
    else:
        summary_message = "Create a summary of the conversation above in Korean:"

    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = model.invoke(messages)
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages}

def need_summarize_history(state: MainState):
    if len(state["messages"]) > 10:
        return "summarize_history"
    return END

def law_talk(state: MainState):
    agent = law_agent()
    return agent.invoke({"messages": state["messages"]})

def routing_question(state: MainState):
    question = state["messages"][-1].content
    source = routing_chain.invoke({"question": question})

    if source.datasource == "law_talk":
        return "law_talk"
    else:
        return "chat"

workflow = StateGraph(MainState)
workflow.add_node("chat", chat)
workflow.add_node("law_talk", law_talk)
workflow.add_node("summarize_history", summarize_history)

workflow.add_conditional_edges(
    START,
    routing_question,
    {"chat": "chat", "law_talk": "law_talk"},
)

# workflow.add_edge("law_talk", "chat")
# workflow.add_edge(START, "chat")
workflow.add_conditional_edges("chat", need_summarize_history, {"summarize_history": "summarize_history", END: END})
workflow.add_edge("summarize_history", END)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

graph_to_png(app, "main_graph.png", xray=True)
