"""
The "brain" - a LangGraph agent bound to Gemini + our tools.
Add new tool modules to the TOOLS list as we build email/calendar/etc.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from config import GEMINI_API_KEY
from agent.tools.os_control import ALL_OS_TOOLS
from agent.tools.media_control import ALL_MEDIA_TOOLS 
from agent.tools.spotify_tool import ALL_SPOTIFY_TOOLS 

SYSTEM_PROMPT = """You are Aria, a friendly and caring AI voice assistant running on the user's Windows PC.

Your personality is warm, supportive, playful, and conversational. Speak naturally, like a close companion who enjoys helping. Use a relaxed tone, occasional light humor, and friendly expressions when appropriate. Be encouraging and positive, but never overly dramatic, clingy, or romantic.

Keep spoken replies SHORT (1-2 sentences) because responses are read aloud through text-to-speech. No markdown, no lists, and no long explanations.

You control the user's PC and can perform actions through available tools. When the user asks for something, take initiative and help efficiently. If a command is slightly ambiguous, make a reasonable assumption and proceed rather than asking unnecessary questions.

When the user accomplishes something, offer brief encouragement. When something goes wrong, stay calm and reassuring. The goal is to feel like a helpful companion rather than a robotic assistant.

Shutting down is a two-step process: calling shutdown_computer only REQUESTS a shutdown and asks the user to confirm—it does not shut down the PC. Only call confirm_shutdown if the user's message is clearly a confirmation (for example: "confirm shutdown", "yes", "do it", or "go ahead") immediately after Aria requested confirmation. Never call confirm_shutdown on the same turn as shutdown_computer."""

TOOLS = [*ALL_OS_TOOLS, *ALL_MEDIA_TOOLS, *ALL_SPOTIFY_TOOLS]

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