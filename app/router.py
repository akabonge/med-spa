import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from app.models import ChatRequest, ChatResponse, ContactRequest, StatusUpdateRequest, LeadListResponse
from app.rag.pipeline import generate_response
from app.rag.lead_extractor import extract_and_score
from app.lead_store import get_lead, new_lead, upsert_lead, get_all_leads, update_lead_status
from app.guardrails import check_input, check_output

router = APIRouter()

# In-memory session history: session_id -> list of {role, content}
_sessions: dict[str, list[dict]] = {}
_MAX_HISTORY = 12


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, background_tasks: BackgroundTasks):
    guard = check_input(req.message, req.session_id)
    if not guard.allowed:
        return ChatResponse(
            response=guard.reason,
            sources=[],
            session_id=req.session_id,
            provider="guardrail",
            lead_captured=False,
        )

    history = _sessions.get(req.session_id, [])

    response_text, sources, provider = generate_response(guard.cleaned_input, history)
    _, response_text = check_output(response_text)

    history.append({"role": "user", "content": guard.cleaned_input})
    history.append({"role": "assistant", "content": response_text})
    _sessions[req.session_id] = history[-_MAX_HISTORY:]

    background_tasks.add_task(
        extract_and_score,
        req.session_id,
        _sessions[req.session_id],
    )

    lead = get_lead(req.session_id)
    lead_captured = bool(lead and (lead.name or lead.email))

    return ChatResponse(
        response=response_text,
        sources=sources,
        session_id=req.session_id,
        provider=provider,
        lead_captured=lead_captured,
    )


@router.post("/leads/contact")
async def save_contact(req: ContactRequest):
    lead = get_lead(req.session_id) or new_lead(req.session_id)
    lead.name = req.name
    lead.email = req.email
    if req.phone:
        lead.phone = req.phone
    upsert_lead(lead)
    return {"ok": True}


@router.patch("/leads/{session_id}/status")
async def update_status(session_id: str, req: StatusUpdateRequest):
    valid = {"new", "consult_booked", "converted"}
    if req.status not in valid:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {valid}")
    lead = update_lead_status(session_id, req.status)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"ok": True, "status": req.status}


@router.get("/leads", response_model=LeadListResponse)
async def list_leads():
    leads = get_all_leads()
    leads.sort(key=lambda x: x.score, reverse=True)
    return LeadListResponse(total=len(leads), leads=leads)


@router.get("/leads/{session_id}/follow-up")
async def draft_follow_up(session_id: str):
    lead = get_lead(session_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    settings_import = __import__("app.config", fromlist=["get_settings"])
    settings = settings_import.get_settings()

    treatments = ", ".join(lead.treatments_interested) if lead.treatments_interested else "aesthetic treatments"
    concerns = ", ".join(lead.concerns) if lead.concerns else "your aesthetic goals"

    prompt = f"""Write a warm, professional follow-up email from Luminara Med Spa to a prospective client.

Client name: {lead.name or 'there'}
Treatments they expressed interest in: {treatments}
Their concerns: {concerns}
Consultation summary: {lead.conversation_summary or 'Inquired about treatments'}

The email should:
- Be warm, personalized, and non-pushy
- Reference their specific treatment interest
- Invite them to book a free consultation
- Include our contact info: (540) 899-4200 | hello@luminaramedspa.com
- Be signed by "The Luminara Team"
- Be 3-4 short paragraphs

Write only the email body, no subject line."""

    if settings.anthropic_api_key:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        email_body = response.content[0].text
    else:
        import ollama
        response = ollama.chat(
            model=settings.ollama_model,
            messages=[{"role": "user", "content": prompt}],
        )
        email_body = response["message"]["content"]

    subject = f"Your Luminara Consultation — {treatments}"
    recipient = lead.email or ""
    mailto = f"mailto:{recipient}?subject={subject}&body={email_body}"

    return {"email_body": email_body, "subject": subject, "mailto": mailto}
