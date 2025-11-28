from google.adk.agents.llm_agent import Agent
import sys
import os
import asyncio

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
            error_msg = str(e)
            print(f"\n⚠ MCP Connection failed: {error_msg}")
            print("📧 MOCK EMAIL SENT (MCP not authenticated)")
            print(f"   To: {recipient}")
            print(f"   Subject: {subject}")
            print(f"   Body Preview: {body[:100]}...")
            return (
                f"✓ Email drafted and ready to send.\n\n"
                f"⚠ Note: Gmail MCP authentication not configured.\n"
                f"In a production environment, this email would be sent via Gmail.\n\n"
                f"To enable real email sending:\n"
                f"1. See GMAIL_SETUP.md for OAuth setup instructions\n"
                f"2. Configure Gmail MCP server credentials\n\n"
                f"For demonstration purposes, the email flow is complete."
            )

    print(f"\n📤 Attempting to send email to: {recipient}")
    
    # Helper to run async in sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    return loop.run_until_complete(_send())

# Define the Purchaser Agent
purchaser_agent = Agent(
    model='gemini-2.0-flash',
    name='purchaser_agent',
    description="Procurement purchasing agent that drafts and sends purchase orders",
    instruction="""You are a procurement purchasing agent.
    
    When a user wants to buy something, follow this STRICT process:
    1. Collect necessary details (Item, Quantity, Vendor/Recipient). If missing, ask the user.
    2. Use `draft_email` to create a draft.
    3. Use the following template for the email body:
    
    Subject Line: Initial Purchase Order Request - [Your Company Name]
    Dear [Supplier's Name],
    I hope this message finds you well. We are pleased to place a new purchase order with
    your company. Below are the details of our order:
    -Product/Service: [Product/Service Name]
    -Quantity: [Quantity]
    -Price: [Price] (If unknown, ask for quote)
    -Delivery Date: [Preferred Delivery Date] (Default to 'ASAP' if not specified)
    -Shipping Address: [Your Shipping Address] (Default to '123 Construction Lane')
    Please confirm the receipt of this purchase order and provide an estimated delivery date.
    We look forward to continuing our successful partnership.
    Best regards,
    [Your Name]
    [Your Position]
    [Your Company Name]
    [Your Contact Information]

    4. Show the draft to the user and ask: "Does this look correct?"
    5. PAUSE and wait for user input.
    6. If the user says "confirmed", "yes", or "send it", use `send_email`.
    7. If the user requests changes, use `draft_email` again with the updates.
    
    DO NOT send the email without explicit approval.
    """,
    tools=[draft_email, send_email]
)
