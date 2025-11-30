from google.adk.agents.llm_agent import Agent
import sys
import os
import asyncio
import nest_asyncio

# ============================================================================
# ASYNC IMPLEMENTATION NOTE
# ============================================================================
# The Google ADK runtime manages its own event loop. 
# Since our MCP client is asynchronous, calling it from within a tool 
# (which runs inside the existing loop) causes a "This event loop is already running" error.
# We use `nest_asyncio` to patch the loop and allow nested execution, ensuring 
# compatibility between the synchronous Tool definition and the async MCP call.
nest_asyncio.apply()

# Add parent directory to path for local imports when running with ADK
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.mcp_client import get_mcp_client

def draft_email(recipient: str, subject: str, body: str) -> str:
    """
    Creates a draft email. Use this tool FIRST to show the user what you plan to send.
    """
    return f"--- DRAFT EMAIL ---\nTo: {recipient}\nSubject: {subject}\n\n{body}\n-------------------"

def send_email(recipient: str, subject: str, body: str) -> str:
    """
    Sends the email. Use this tool ONLY after the user has explicitly confirmed the draft.
    """
    async def _send():
        try:
            print(f"🔌 Connecting to MCP to send email to {recipient}...")
            async with get_mcp_client() as session:
                # Try to initialize the session
                await session.initialize()
                
                # Call the Gmail send tool
                result = await session.call_tool(
                    "gmail_send_email",
                    arguments={"to": recipient, "subject": subject, "body": body}
                )
                return f"✓ Email sent successfully via Gmail MCP.\nResult: {result}"
        except Exception as e:
            # Graceful fallback for demo/testing purposes
            return (
                f"✓ Email drafted and ready to send.\n"
                f"⚠ Demo Mode: Email not sent (MCP Connection Error: {e})\n"
                f"Body Preview: {body[:50]}..."
            )

    
    # Helper to run async in sync context
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return loop.run_until_complete(_send())
        else:
            return loop.run_until_complete(_send())
    except RuntimeError:
        return asyncio.run(_send())

# Define the Purchaser Agent
purchaser_agent = Agent(
    model='gemini-2.0-flash',
    name='purchaser_agent',
    description="Procurement purchasing agent that drafts and sends purchase orders",
    instruction="""You are a procurement purchasing agent.
    
    YOUR GOAL: Draft emails, get approval and send them.

    STEP 1: CHECK DETAILS
    - Need: Item, Quantity, Vendor Email.
    - If missing, ASK.
    
    STEP 2: DRAFT (The Tool)
    - If you have details, call `draft_email`.

    EMAIL TEMPLATE:
    Subject: Purchase Order - [Item]
    Body:
    Dear Supplier,
    Please ship [Quantity] of [Item].
    Shipping Address: 123 Construction Lane.
    Please confirm delivery date.
    
    Thanks,
    Construction Manager
    
    STEP 3: REPORT (The Output)
    - **CRITICAL:** Once the tool returns the draft text, **YOU MUST PASTE THAT DRAFT INTO YOUR FINAL RESPONSE.**
    - Do not just say "Draft created."
    - Say: "Here is the draft: [Paste Tool Output Here]. Please confirm."
    
    STEP 4: SEND
    - If the user says "Send it" OR if the Supervisor provides the full email details in the prompt:
    - **CHECK:** Do you have the `recipient`, `subject`, and `body`?
    - **ACTION:** If yes, IMMEDIATELY call `send_email`.
    - If details are missing, ask for them (but this shouldn't happen if the Supervisor does their job).

    """,
    tools=[draft_email, send_email]
)
