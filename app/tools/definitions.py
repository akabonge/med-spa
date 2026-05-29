"""Anthropic tool_use schemas for Luminara Med Spa."""

TOOLS = [
    {
        "name": "check_appointment_availability",
        "description": (
            "Check available appointment slots for a specific treatment at Luminara Med Spa. "
            "Returns the next 3 available days with open times. Preferred date is optional."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "treatment": {
                    "type": "string",
                    "description": (
                        "Treatment name. Options: Botox, Dysport, Dermal Fillers, Morpheus8, "
                        "Kybella, HydraFacial, Chemical Peels, IPL Photofacial, PDO Threads, "
                        "Sculptra, Laser Hair Removal."
                    ),
                },
                "preferred_date": {
                    "type": "string",
                    "description": "Optional preferred date YYYY-MM-DD. Defaults to next available.",
                },
            },
            "required": ["treatment"],
        },
    },
    {
        "name": "book_consultation",
        "description": (
            "Book a consultation or treatment appointment at Luminara Med Spa. "
            "Always check availability first. Returns a confirmation code."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Client's full name."},
                "email": {"type": "string", "description": "Client's email address."},
                "phone": {"type": "string", "description": "Client's phone number (optional)."},
                "treatment": {"type": "string", "description": "Treatment being booked."},
                "date": {"type": "string", "description": "Appointment date YYYY-MM-DD."},
                "time": {"type": "string", "description": "Appointment time HH:MM (24-hour)."},
                "notes": {
                    "type": "string",
                    "description": "Any concerns, questions, or medical notes for the provider.",
                },
            },
            "required": ["name", "email", "treatment", "date", "time"],
        },
    },
    {
        "name": "get_treatment_info",
        "description": (
            "Get detailed information about a treatment including description, downtime, "
            "expected results, and starting price."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "treatment": {
                    "type": "string",
                    "description": "Treatment name (e.g. Botox, Morpheus8, HydraFacial).",
                },
            },
            "required": ["treatment"],
        },
    },
    {
        "name": "check_my_appointment",
        "description": "Look up an existing appointment by client name, phone number, or email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lookup": {
                    "type": "string",
                    "description": "Client name, phone number, or email to search by.",
                },
            },
            "required": ["lookup"],
        },
    },
]
