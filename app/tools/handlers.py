"""
Tool execution handlers for Luminara Med Spa.
Each function maps to one tool definition and returns a plain dict.
"""
from app.tools.mock_db import (
    get_available_slots,
    create_appointment,
    find_appointment,
    get_treatment_details,
    _OPEN_DAYS,
    _SLOT_TIMES,
)


def handle_check_availability(treatment: str, preferred_date: str = "") -> dict:
    return get_available_slots(treatment, preferred_date or None)


def handle_book_consultation(name: str, email: str, treatment: str,
                              date: str, time: str,
                              phone: str = "", notes: str = "") -> dict:
    # Validate slot is still open
    slots_data = get_available_slots(treatment, date)
    available_for_date = next(
        (entry["available_times"] for entry in slots_data.get("availability", [])
         if entry["date"] == date),
        None,
    )
    if available_for_date is None:
        return {
            "success": False,
            "error": f"No slots available for {treatment} on {date}. Check availability first.",
        }
    if time not in available_for_date:
        return {
            "success": False,
            "error": f"{time} on {date} is already taken. Open slots: {available_for_date}.",
        }
    result = create_appointment(name, email, phone, treatment, date, time, notes)
    if result.get("success"):
        result["message"] = (
            f"Appointment confirmed for {name} — {treatment} with {result['provider']} "
            f"on {date} at {time}. Confirmation: {result['confirmation_code']}. "
            "We'll see you at Luminara!"
        )
    return result


def handle_get_treatment_info(treatment: str) -> dict:
    return get_treatment_details(treatment)


def handle_check_my_appointment(lookup: str) -> dict:
    results = find_appointment(lookup)
    if not results:
        return {
            "found": False,
            "message": f"No appointments found for '{lookup}'. Check the spelling or try your email.",
        }
    return {"found": True, "count": len(results), "appointments": results}


def execute_tool(name: str, inputs: dict) -> dict:
    """Dispatch tool call by name."""
    if name == "check_appointment_availability":
        return handle_check_availability(
            treatment=inputs["treatment"],
            preferred_date=inputs.get("preferred_date", ""),
        )
    if name == "book_consultation":
        return handle_book_consultation(
            name=inputs["name"],
            email=inputs["email"],
            treatment=inputs["treatment"],
            date=inputs["date"],
            time=inputs["time"],
            phone=inputs.get("phone", ""),
            notes=inputs.get("notes", ""),
        )
    if name == "get_treatment_info":
        return handle_get_treatment_info(treatment=inputs["treatment"])
    if name == "check_my_appointment":
        return handle_check_my_appointment(lookup=inputs["lookup"])
    return {"error": f"Unknown tool: {name}"}
