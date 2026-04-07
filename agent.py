from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from tools import calculate_budget, search_flights, search_hotels

load_dotenv()

SYSTEM_PROMPT = Path(__file__).with_name("system_prompt.txt").read_text(encoding="utf-8")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


TOOLS = [search_flights, search_hotels, calculate_budget]
LLM = ChatOpenAI(model=MODEL_NAME, temperature=0)
LLM_WITH_TOOLS = LLM.bind_tools(TOOLS)

CITY_ALIASES = {
    "Hà Nội": ["ha noi", "hanoi", "hn"],
    "Đà Nẵng": ["da nang", "danang", "dn"],
    "Phú Quốc": ["phu quoc", "pq"],
    "Hồ Chí Minh": [
        "ho chi minh",
        "thanh pho ho chi minh",
        "tp ho chi minh",
        "tphcm",
        "tp hcm",
        "hcm",
        "hcmc",
        "sai gon",
        "saigon",
    ],
}

HOTEL_KEYWORDS = ("khach san", "dat khach san", "dat phong", "phong", "noi o", "luu tru")
FLIGHT_KEYWORDS = ("chuyen bay", "ve may bay", "ve may", "bay tu", "di may bay")
TRIP_KEYWORDS = ("muon di", "du lich", "tu van", "budget", "ngan sach", "ke hoach")


def _render_message_content(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content

    rendered_parts: list[str] = []
    for part in content:
        if isinstance(part, dict):
            text = part.get("text")
            if text:
                rendered_parts.append(str(text))
        else:
            rendered_parts.append(str(part))
    return "\n".join(rendered_parts).strip()


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return without_marks.replace("đ", "d").replace("Đ", "D")


def _normalize_text(text: str) -> str:
    cleaned = " ".join(text.lower().split())
    cleaned = cleaned.replace("thành phố", "thanh pho")
    return _strip_accents(cleaned)


def _extract_cities(text: str) -> list[str]:
    normalized_text = _normalize_text(text)
    city_hits: list[tuple[int, str]] = []

    for city, aliases in CITY_ALIASES.items():
        earliest_hit = None
        for alias in aliases:
            pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"
            match = re.search(pattern, normalized_text)
            if match and (earliest_hit is None or match.start() < earliest_hit):
                earliest_hit = match.start()
        if earliest_hit is not None:
            city_hits.append((earliest_hit, city))

    city_hits.sort(key=lambda item: item[0])

    ordered_cities: list[str] = []
    for _, city in city_hits:
        if city not in ordered_cities:
            ordered_cities.append(city)
    return ordered_cities


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _build_tool_call_message(tool_name: str, args: dict[str, object]) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": tool_name,
                "args": args,
                "id": f"{tool_name}_{uuid4().hex[:8]}",
                "type": "tool_call",
            }
        ],
    )


def _rule_based_response(messages: list[BaseMessage]) -> AIMessage | None:
    if not messages or not isinstance(messages[-1], HumanMessage):
        return None

    user_text = _render_message_content(messages[-1])
    normalized_text = _normalize_text(user_text)
    cities = _extract_cities(user_text)

    hotel_request = _contains_any(normalized_text, HOTEL_KEYWORDS)
    flight_request = _contains_any(normalized_text, FLIGHT_KEYWORDS)
    trip_request = _contains_any(normalized_text, TRIP_KEYWORDS)

    if hotel_request and not cities:
        return AIMessage(
            content=(
                "Bạn muốn đặt khách sạn ở thành phố nào? "
                "Bạn dự định ở bao nhiêu đêm và tổng ngân sách khoảng bao nhiêu để mình gợi ý phù hợp hơn?"
            )
        )

    if hotel_request and len(cities) == 1 and not re.search(r"\b\d+\s*dem\b", normalized_text):
        return AIMessage(
            content=(
                f"Bạn muốn ở {cities[0]} bao nhiêu đêm và ngân sách khoảng bao nhiêu "
                "để mình gợi ý khách sạn phù hợp?"
            )
        )

    if len(cities) >= 2 and (flight_request or trip_request):
        return _build_tool_call_message(
            "search_flights",
            {"origin": cities[0], "destination": cities[1]},
        )

    return None


def agent_node(state: AgentState) -> AgentState:
    rule_based = _rule_based_response(state["messages"])
    if rule_based is not None:
        response = rule_based
    else:
        model_messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        response = LLM_WITH_TOOLS.invoke(model_messages)

    if response.tool_calls:
        for tool_call in response.tool_calls:
            print(f"Gọi tool: {tool_call['name']}({tool_call['args']})", flush=True)
    else:
        print("Trả lời trực tiếp", flush=True)

    return {"messages": [response]}


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    return builder.compile()


GRAPH = build_graph()


def chat_loop() -> None:
    print("=" * 60)
    print("TravelBuddy - Trợ lý Du lịch Thông minh")
    print(f"Model: {MODEL_NAME}")
    print("Gõ 'quit', 'exit' hoặc 'q' để thoát")
    print("=" * 60)

    conversation: list[BaseMessage] = []

    while True:
        user_input = input("\nBạn: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "q"}:
            break

        conversation.append(HumanMessage(content=user_input))
        print("\nTravelBuddy đang suy nghĩ...", flush=True)

        try:
            result = GRAPH.invoke({"messages": conversation})
        except Exception as exc:
            conversation.pop()
            print(f"\nTravelBuddy: Không thể xử lý yêu cầu lúc này. Chi tiết lỗi: {exc}")
            continue

        conversation = result["messages"]
        final_message = conversation[-1]
        print(f"\nTravelBuddy: {_render_message_content(final_message)}")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Thiếu OPENAI_API_KEY trong file .env hoặc environment variables.")
    chat_loop()
