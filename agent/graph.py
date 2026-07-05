"""
The "brain" - a LangGraph agent bound to Gemini + our tools.
Add new tool modules to the TOOLS list as we build email/calendar/etc.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from config import GEMINI_API_KEY
from agent.tools.os_control import ALL_OS_TOOLS

SYSTEM_PROMPT = """You are Aria, a helpful voice assistant running on the user's Windows PC.
You control the OS and (soon) email/calendar via tools. Keep spoken replies SHORT (1-2 sentences) -
they will be read aloud through text-to-speech, so no markdown, no lists, no long explanations.
If a command is ambiguous, make a reasonable assumption and act rather than asking for clarification,
unless it's something risky like shutting down or closing something important."""

TOOLS = [*ALL_OS_TOOLS]  # email_tool / calendar_tool get appended here in later phases

_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    google_api_key=GEMINI_API_KEY,
    temperature=0.3,
)

agent_executor = create_react_agent(_llm, TOOLS, prompt=SYSTEM_PROMPT)


def run_command(user_text: str) -> str:
    """Sends the transcribed command to the agent and returns its final spoken reply."""
    result = agent_executor.invoke({"messages": [("user", user_text)]})
    final_message = result["messages"][-1]
    content = final_message.content

    # Gemini sometimes returns content as a list of blocks (text + metadata/signature)
    # instead of a plain string - extract just the text parts.
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif isinstance(block, str):
                text_parts.append(block)
        return " ".join(text_parts).strip()

    return content