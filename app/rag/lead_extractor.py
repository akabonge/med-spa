import json
import re
from app.config import get_settings
from app.models import Lead
from app.lead_store import upsert_lead, get_lead, new_lead

EXTRACTION_PROMPT = """You are an aesthetic client intake analyst. Read this conversation between a prospective client and Luna (a med spa AI consultant), then extract all available lead information and score the lead.

Conversation:
{conversation}

Return a JSON object with these fields (use null for anything not mentioned):
{{
  "name": null,
  "email": null,
  "phone": null,
  "concerns": [],
  "treatments_interested": [],
  "is_first_time": null,
  "passed_candidacy": null,
  "preferred_date": null,
  "timeline": null,
  "budget_range": null,
  "conversation_summary": "one sentence summary of what the client is interested in",
  "score": 0,
  "score_reasoning": "explanation of the score"
}}

Lead scoring criteria (1-10):
- 9-10: Ready to book — named specific treatment(s), asked about pricing or availability, provided contact info or requested consultation
- 7-8: High intent — described specific concerns, expressed clear interest in a treatment, asking detailed questions
- 5-6: Engaged — actively asking about treatments, exploring options, some personal details shared
- 3-4: Browsing — general curiosity, vague questions, no specific concerns or treatments mentioned yet
- 1-2: Very early — single vague message, no qualifying information at all

Bonus points: multiple treatments interested (+1), package interest (+1), timeline mentioned as soon (+1), contact info captured (+2).

Return ONLY valid JSON. No explanation, no markdown fences."""


def extract_and_score(session_id: str, history: list[dict]) -> Lead:
    settings = get_settings()
    conversation_text = "\n".join(
        f"{msg['role'].capitalize()}: {msg['content']}" for msg in history
    )
    raw_json = _call_llm(conversation_text, settings)
    extracted = _parse(raw_json)

    existing = get_lead(session_id) or new_lead(session_id)

    for field, value in extracted.items():
        if value is not None and value != [] and value != "":
            setattr(existing, field, value)

    if extracted.get("score"):
        existing.score = extracted["score"]
    if extracted.get("score_reasoning"):
        existing.score_reasoning = extracted["score_reasoning"]
    if extracted.get("conversation_summary"):
        existing.conversation_summary = extracted["conversation_summary"]

    upsert_lead(existing)
    return existing


def _call_llm(conversation: str, settings) -> str:
    prompt = EXTRACTION_PROMPT.format(conversation=conversation)

    if settings.anthropic_api_key:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    import ollama
    response = ollama.chat(
        model=settings.ollama_model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"]


def _parse(raw: str) -> dict:
    try:
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return {}
