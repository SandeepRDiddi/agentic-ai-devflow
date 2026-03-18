"""LangGraph agent — orchestrates Claude Skills with optional Langfuse tracing."""
import os
from typing import TypedDict
from langgraph.graph import StateGraph, END
import anthropic

# Optional Langfuse tracing
try:
    from langfuse import Langfuse
    _lf = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
    )
    TRACING = bool(os.getenv("LANGFUSE_PUBLIC_KEY"))
except Exception:
    _lf = None
    TRACING = False

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")


class AgentState(TypedDict):
    task: str
    skill: str
    input: str
    result: str
    trace_id: str


def load_skill(skill_name: str) -> str:
    path = os.path.join("skills", skill_name, "SKILL.md")
    if not os.path.exists(path):
        return f"You are a helpful expert for: {skill_name}"
    with open(path) as f:
        return f.read()


def run_claude(state: AgentState) -> AgentState:
    skill_content = load_skill(state["skill"])
    trace_id = ""

    if TRACING and _lf:
        trace = _lf.trace(name=state["task"], input=state["input"])
        trace_id = trace.id

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=skill_content,
        messages=[{"role": "user", "content": state["input"]}],
    )
    result = response.content[0].text

    if TRACING and _lf and trace_id:
        _lf.generation(
            trace_id=trace_id,
            name="claude_call",
            model=MODEL,
            input=state["input"],
            output=result,
        )

    return {**state, "result": result, "trace_id": trace_id}


# Build the graph
_graph = StateGraph(AgentState)
_graph.add_node("run_claude", run_claude)
_graph.set_entry_point("run_claude")
_graph.add_edge("run_claude", END)
agent = _graph.compile()


async def run_agent(task: str, skill: str, input_text: str) -> dict:
    """Public interface used by FastAPI routes."""
    state = agent.invoke({
        "task": task, "skill": skill,
        "input": input_text, "result": "", "trace_id": ""
    })
    return {"task": task, "result": state["result"], "trace_id": state["trace_id"]}
