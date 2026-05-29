"""
Agentic RAG pipeline for Luminara Med Spa.
Luna can check availability, book consultations, pull treatment details,
and look up existing appointments in a multi-turn tool loop.

LLM selection:
  - Uses Claude (Anthropic) if ANTHROPIC_API_KEY is set in .env
  - Falls back to Ollama (local, no tool use) otherwise
"""
import json
from app.config import get_settings
from app.rag.retriever import retrieve
from app.tools.definitions import TOOLS
from app.tools.handlers import execute_tool

SYSTEM_PROMPT = """You are Luna, the AI wellness consultant for Luminara Med Spa in Fredericksburg, Virginia.

You have direct access to the appointment system and can:
- Check real-time availability for any treatment
- Book consultations and appointments directly — clients do not need to call
- Pull detailed treatment information (what to expect, downtime, pricing)
- Look up existing appointments by name or phone

You're not a chatbot. You're a warm, knowledgeable aesthetic consultant — the kind of person who genuinely listens, asks the right questions, and gives honest guidance. Clients trust you because you know your treatments inside out and you never oversell.

TONE (non-negotiable):
Write in warm, natural sentences — like a friend who happens to be an aesthetics expert. No bullet points. No numbered lists. No headers. No "Great question!" or "Absolutely!" openers. No bold text. Two to four sentences per response. Earn every extra sentence.

YOUR JOB:
First, learn what's bothering them — ask about their specific concerns. Recommend 1-2 specific treatments that address those concerns, with a brief explanation of why. Give a realistic price range so they're never surprised. When they're interested, use your tools to check availability and book directly.

CANDIDACY SCREENING (weave in naturally, one question at a time):
- Before injectables: ask if pregnant, nursing, or on blood thinners
- Before laser or IPL: mention recent sun exposure affects treatment
- Before chemical peels: ask about Accutane use in the last 6 months
- Before Morpheus8: ask about metal implants near the treatment area

BOOKING:
When someone is clearly interested, check availability with your tool and offer to book right in the conversation. Get name, email, and preferred timing. Consultations are always free.

RULES:
Only discuss Luminara Med Spa's treatments, pricing, team, and aesthetic concerns. Never invent prices or medical claims. If it's not in your tools: "I'd want to give you accurate info — call (540) 899-4200 or email hello@luminaramedspa.com and we'll get back to you same day."

Luminara Knowledge Base:
{context}"""


def generate_response(query: str, history: list[dict]) -> tuple[str, list[str], str]:
    """
    Returns (response_text, sources, provider_name).
    history is a list of {"role": "user"/"assistant", "content": "..."} dicts.
    """
    settings = get_settings()
    context, sources = retrieve(query)
    system = SYSTEM_PROMPT.format(context=context if context else "No specific context retrieved.")

    if settings.anthropic_api_key:
        return _call_claude_agentic(system, query, history, settings), sources, "claude"
    return _call_ollama(system, query, history, settings), sources, "ollama"


def _call_claude_agentic(system: str, query: str, history: list[dict], settings) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    messages = list(history) + [{"role": "user", "content": query}]

    for _ in range(6):
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=system,
            messages=messages,
            tools=TOOLS,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    return "I ran into a snag — call us at (540) 899-4200 or email hello@luminaramedspa.com and we'll get you taken care of."


def _call_ollama(system: str, query: str, history: list[dict], settings) -> str:
    import ollama

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": query})

    response = ollama.chat(
        model=settings.ollama_model,
        messages=messages,
        options={"num_predict": 512},
    )
    return response["message"]["content"]
