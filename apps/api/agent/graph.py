from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent.tool_router import build_langchain_tools
from agent.tools import ToolContext
from config import get_settings
from memory.checkpoint import get_redis_checkpointer, graph_config
from services.prompt_service import prompt_service
from telemetry.langfuse_tracing import (
    build_langfuse_callbacks,
    flush_langfuse_callbacks,
)


def build_chat_model() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key or "missing",
        temperature=0.2,
    )


async def build_react_agent(ctx: ToolContext):
    tools = await build_langchain_tools(ctx)
    llm = build_chat_model()
    checkpointer = await get_redis_checkpointer()
    return create_react_agent(llm, tools, checkpointer=checkpointer)


async def invoke_agent(
    query: str, ctx: ToolContext, *, thread_id: str | None = None
) -> dict[str, Any]:
    settings = get_settings()
    agent = await build_react_agent(ctx)
    roles = ",".join(sorted(role.value for role in ctx.roles))
    compiled = prompt_service.compile_system(user_roles=roles)
    callbacks = build_langfuse_callbacks(
        settings,
        session_id=thread_id or ctx.session_id,
        user_id=ctx.user_sub,
        request_id=ctx.request_id,
        prompt_name=compiled.name,
        prompt_version=compiled.version,
        roles=roles,
    )
    config = graph_config(
        thread_id=thread_id or ctx.session_id,
        callbacks=callbacks,
        metadata={
            "request_id": ctx.request_id,
            "prompt_name": compiled.name,
            "prompt_version": compiled.version,
            "user_roles": roles,
            "langfuse_session_id": thread_id or ctx.session_id,
            "langfuse_user_id": ctx.user_sub,
        },
        tags=["relay", "react", *roles.split(",")[:3]],
        run_name="relay-agent",
    )
    try:
        result = await agent.ainvoke(
            {
                "messages": [
                    SystemMessage(content=compiled.text),
                    HumanMessage(content=query),
                ]
            },
            config=config,
        )
    finally:
        flush_langfuse_callbacks(callbacks)

    messages = result.get("messages") or []
    answer = ""
    tools_used: list[str] = []
    for message in messages:
        name = getattr(message, "name", None)
        if name:
            tools_used.append(str(name))
        tool_calls = getattr(message, "tool_calls", None) or []
        for call in tool_calls:
            if isinstance(call, dict) and call.get("name"):
                tools_used.append(str(call["name"]))
        if message.__class__.__name__ == "AIMessage" and getattr(
            message, "content", None
        ):
            content = message.content
            if isinstance(content, str):
                answer = content
    return {
        "answer": answer,
        "tools_used": list(dict.fromkeys(tools_used)),
        "pending_approvals": list(ctx.pending_approvals),
        "prompt_name": compiled.name,
        "prompt_version": compiled.version,
        "messages": messages,
        "tool_calls": list(ctx.tool_calls_log),
    }
