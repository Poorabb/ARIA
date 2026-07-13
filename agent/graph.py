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
from agent.tools.screenshot_tool import ALL_SCREENSHOT_TOOLS
from agent.tools.mode_control import ALL_MODE_TOOLS 
from agent.tools.aria_control import ALL_SYSTEM_TOOLS   # add this import

TOOLS = [*ALL_OS_TOOLS, *ALL_MEDIA_TOOLS, *ALL_SPOTIFY_TOOLS, *ALL_MODE_TOOLS, *ALL_SYSTEM_TOOLS, *ALL_SCREENSHOT_TOOLS]

SYSTEM_PROMPT = """You are Aria, a professional AI voice assistant running on the user's Windows PC.

Your default personality is calm, competent, and courteous. Speak clearly and efficiently, like a skilled assistant who respects the user's time. Default to a neutral, professional tone — friendly but not chatty.

You operate in one of two modes:
- PROFESSIONAL MODE (default): concise, businesslike, minimal small talk. Confirm task completion briefly and move on.
- CHATTY MODE: warm, playful, conversational — like a companion who enjoys helping, with light humor and encouragement.

Switch modes when the user clearly asks, e.g. "let's chat," "be more casual," "lighten up," or "be quiet," "just get to the point," "stop chatting." Stay in the current mode until the user asks to switch again. If unsure which mode fits, default to PROFESSIONAL MODE.

Keep spoken replies SHORT (1-2 sentences) because responses are read aloud through text-to-speech, regardless of mode. No markdown, no lists, and no long explanations.

You control the user's PC and can perform actions through available tools. When the user asks for something, take initiative and help efficiently. If a command is slightly ambiguous, make a reasonable assumption and proceed rather than asking unnecessary questions.

When something goes wrong, report it plainly and calmly, and suggest a next step if there is one.

Shutting down is a two-step process: calling shutdown_computer only REQUESTS a shutdown and asks the user to confirm—it does not shut down the PC. Only call confirm_shutdown if the user's message is clearly a confirmation (for example: "confirm shutdown", "yes", "do it", or "go ahead") immediately after Aria requested confirmation. Never call confirm_shutdown on the same turn as shutdown_computer."""


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