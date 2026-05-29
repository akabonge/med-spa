#!/usr/bin/env python3
"""
Luminara Med Spa — MCP Server

Exposes Luna's appointment tools as an MCP server so any MCP-compatible
client (Claude Desktop, other agents) can connect.

Usage (local):
  python mcp_server.py

Claude Desktop config:
  {
    "mcpServers": {
      "luminara-medspa": {
        "command": "python",
        "args": ["/absolute/path/to/luminara_medspa/mcp_server.py"]
      }
    }
  }
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from app.tools.mock_db import init_db
from app.tools.handlers import (
    handle_check_availability,
    handle_book_consultation,
    handle_get_treatment_info,
    handle_check_my_appointment,
)

init_db()
mcp = FastMCP("Luminara Med Spa")


@mcp.tool()
def check_availability(treatment: str, preferred_date: str = "") -> dict:
    """Check open appointment slots for a treatment at Luminara Med Spa."""
    return handle_check_availability(treatment, preferred_date)


@mcp.tool()
def book_appointment(
    name: str,
    email: str,
    treatment: str,
    date: str,
    time: str,
    phone: str = "",
    notes: str = "",
) -> dict:
    """Book a consultation or treatment appointment at Luminara Med Spa."""
    return handle_book_consultation(name, email, treatment, date, time, phone, notes)


@mcp.tool()
def treatment_info(treatment: str) -> dict:
    """Get detailed info about a treatment: description, downtime, results, and pricing."""
    return handle_get_treatment_info(treatment)


@mcp.tool()
def lookup_appointment(lookup: str) -> dict:
    """Find an existing appointment by client name, phone, or email."""
    return handle_check_my_appointment(lookup)


if __name__ == "__main__":
    mcp.run()
