import asyncio
import uuid
from datetime import datetime
from src.utils.mcp_client import get_mcp_client
from src.utils.chroma_db import add_documents
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

async def fetch_unread_emails():
    """Fetch unread emails from Gmail using MCP."""
    try:
        async with get_mcp_client() as session:
            await session.initialize()
            
            # List unread emails (Gmail MCP typically has a list_messages or search tool)
            result = await session.call_tool(
                "gmail_search",
                arguments={"query": "is:unread label:inbox"}
            )
            
            return result
    except Exception as e:
        print(f"⚠ MCP connection failed: {e}")
        print("📧 Using mock data for demonstration")
        return None

async def get_email_content(email_id):
    """Get the full content of an email by ID."""
    try:
        async with get_mcp_client() as session:
            await session.initialize()
            
            result = await session.call_tool(
                "gmail_get_message",
                arguments={"message_id": email_id}
            )
            
            return result
    except Exception as e:
        print(f"Failed to get email {email_id}: {e}")
        return None

def extract_email_metadata(email_body: str, sender: str) -> dict:
    """
    Use Gemini to extract structured information from email.
    Returns: {type: str, summary: str}
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""Analyze this procurement-related email and extract:
1. Type: One of [Invoice, Quote, Delay, Update, Order Confirmation, General]
2. Summary: A one-sentence summary of the key information

Email from: {sender}
Content: {email_body}

Respond in JSON format:
{{"type": "...", "summary": "..."}}
"""
    
    try:
        response = model.generate_content(prompt)
        # Parse the JSON response
        import json
        metadata = json.loads(response.text.strip())
        return metadata
    except Exception as e:
        print(f"Failed to extract metadata: {e}")
        return {"type": "General", "summary": "Email from " + sender}

async def mark_as_read(email_id):
    """Mark an email as read in Gmail."""
    try:
        async with get_mcp_client() as session:
            await session.initialize()
            
            result = await session.call_tool(
                "gmail_modify_message",
                arguments={
                    "message_id": email_id,
                    "remove_labels": ["UNREAD"]
                }
            )
            
            return result
    except Exception as e:
        print(f"Failed to mark email as read: {e}")
        return None

def ingest_mock_data():
    """Fallback: Ingest mock procurement emails into ChromaDB."""
    print("📧 Using mock data (MCP not available)")
    
    mock_emails = [
        {
            "body": "Hi, the order for 5000 bricks will be delivered on Monday. - Bob, BrickCo",
            "metadata": {"sender": "bob@brickco.com", "date": "2023-10-25", "type": "Update", "summary": "Brick delivery update"}
        },
        {
            "body": "Invoice #12345 for $500.00 is attached. Please pay by Friday. - Alice, SuppliesInc",
            "metadata": {"sender": "alice@suppliesinc.com", "date": "2023-10-26", "type": "Invoice", "summary": "Invoice for supplies"}
        },
        {
            "body": "We are out of stock on the 2x4 lumber. Expect a 2 week delay. - Charlie, WoodWorks",
            "metadata": {"sender": "charlie@woodworks.com", "date": "2023-10-27", "type": "Delay", "summary": "Lumber stockout delay"}
        }
    ]
    
    documents = [e["body"] for e in mock_emails]
    metadatas = [e["metadata"] for e in mock_emails]
    ids = [str(uuid.uuid4()) for _ in mock_emails]
    
    add_documents(documents, metadatas, ids)
    print(f"✓ Ingested {len(documents)} mock documents.")

async def ingest_real_emails():
    """
    Real ingestion: Fetch unread emails from Gmail via MCP, 
    extract metadata using Gemini, and store in ChromaDB.
    """
    print("🔄 Fetching unread emails from Gmail via MCP...")
    
    # Fetch unread emails
    emails_result = await fetch_unread_emails()
    
    if not emails_result:
        # Fallback to mock data
        ingest_mock_data()
        return
    
    # Parse the email list from MCP result
    # The exact format depends on the Gmail MCP server response
    # Typically it returns a list of message IDs
    
    email_ids = []
    # TODO: Parse emails_result to extract message IDs
    # Example: email_ids = [msg['id'] for msg in emails_result['messages']]
    
    if not email_ids:
        print("✓ No new unread emails to ingest")
        return
    
    print(f"Found {len(email_ids)} unread emails")
    
    documents = []
    metadatas = []
    ids = []
    
    for email_id in email_ids[:10]:  # Limit to 10 emails per run
        # Get full email content
        email_data = await get_email_content(email_id)
        
        if not email_data:
            continue
        
        # Extract fields
        # TODO: Parse email_data based on Gmail MCP response format
        sender = email_data.get('from', 'unknown@example.com')
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        date = email_data.get('date', datetime.now().isoformat())
        
        # Use Gemini to extract structured metadata
        ai_metadata = extract_email_metadata(body, sender)
        
        # Prepare for ChromaDB
        documents.append(f"Subject: {subject}\n\n{body}")
        metadatas.append({
            "sender": sender,
            "date": date,
            "type": ai_metadata.get("type", "General"),
            "summary": ai_metadata.get("summary", subject)
        })
        ids.append(str(uuid.uuid4()))
        
        # Mark as read
        await mark_as_read(email_id)
        
        print(f"  ✓ Processed: {sender} - {ai_metadata.get('type')}")
    
    if documents:
        add_documents(documents, metadatas, ids)
        print(f"\n✓ Ingested {len(documents)} emails into ChromaDB")
    else:
        print("⚠ No emails were processed successfully")

async def run_ingestion_loop(interval_seconds=300):
    """
    Run continuous ingestion loop.
    Checks for new emails every interval_seconds.
    """
    print(f"🔁 Starting ingestion loop (checking every {interval_seconds}s)")
    print("Press Ctrl+C to stop\n")
    
    while True:
        try:
            await ingest_real_emails()
        except Exception as e:
            print(f"❌ Error during ingestion: {e}")
        
        print(f"\n😴 Sleeping for {interval_seconds} seconds...\n")
        await asyncio.sleep(interval_seconds)

def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--loop":
        # Run continuous loop
        asyncio.run(run_ingestion_loop())
    else:
        # Run once
        print("Running single ingestion (use --loop for continuous mode)")
        asyncio.run(ingest_real_emails())

if __name__ == "__main__":
    main()
