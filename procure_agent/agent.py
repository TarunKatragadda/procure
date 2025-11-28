from google.adk.agents.llm_agent import Agent
import sys
import os

# Add current directory to path for local imports
sys.path.insert(0, os.path.dirname(__file__))

from src.agents.query_agent import query_agent
from src.agents.purchaser_agent import purchaser_agent

def query_tool(query: str) -> str:
    """
    Call this tool when the user asks a question or wants information about procurement data.
    """
    # Import here to avoid circular dependencies
    from src.utils.chroma_db import query_collection
    
    # Query ChromaDB directly (simulating what query_agent does)
    results = query_collection(query)
    
    if not results['documents'] or not results['documents'][0]:
        return "No relevant information found in the knowledge base."
         
    documents = results['documents'][0]
    metadatas = results['metadatas'][0]
    
    context = ""
    for doc, meta in zip(documents, metadatas):
        context += f"Date: {meta.get('date')}, Sender: {meta.get('sender')}\nContent: {doc}\n---\n"
    
    return context if context else "No relevant information found."

def purchasing_tool(message: str) -> str:
    """
    Call this tool when the user wants to buy something, place an order, or draft an email.
    Also use this tool to pass the user's approval ("yes", "send it") or changes back to the purchasing agent.
    """
    import google.generativeai as genai
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    # Use Gemini to extract purchase details from the message
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    extraction_prompt = f"""Extract purchase order details from this message:
"{message}"

Extract and return in JSON format:
{{
  "item": "what to buy",
  "quantity": "how many",
  "vendor_name": "supplier name if mentioned",
  "vendor_email": "email if provided",
  "price": "total or unit price if mentioned",
  "needs_info": ["list of missing required fields"]
}}

If critical info is missing, list it in needs_info.
"""
    
    try:
        response = model.generate_content(extraction_prompt)
        import json
        details = json.loads(response.text.strip())
        
        # Check if we have enough info to draft
        if details.get("needs_info") and len(details["needs_info"]) > 0:
            missing = ", ".join(details["needs_info"])
            return f"""I'd be happy to draft a purchase order! However, I need some more information:

Missing details: {missing}

Please provide:
- Item/Product name
- Quantity
- Vendor name and email address
- Price (if known)
"""
        
        # Draft the email using the template
        item = details.get("item", "Unknown Item")
        quantity = details.get("quantity", "N/A")
        vendor_name = details.get("vendor_name", "Supplier")
        vendor_email = details.get("vendor_email", "supplier@example.com")
        price = details.get("price", "Please provide quote")
        
        draft = f"""--- DRAFT PURCHASE ORDER EMAIL ---

To: {vendor_email}
Subject: Initial Purchase Order Request - Construction Co

Dear {vendor_name},

I hope this message finds you well. We are pleased to place a new purchase order with your company. Below are the details of our order:

- Product/Service: {item}
- Quantity: {quantity}
- Price: {price}
- Delivery Date: ASAP
- Shipping Address: 123 Construction Lane

Please confirm the receipt of this purchase order and provide an estimated delivery date.

We look forward to continuing our successful partnership.

Best regards,
Construction Manager
Construction Co
manager@constructionco.com

-----------------------------------

📋 **Next Steps:**
This is a DRAFT only. To send this email:

**Option 1 - CLI (Recommended for actual sending):**
```
adk run .
```
Then follow the Human-in-the-Loop approval process.

**Option 2 - Web UI (Draft only):**
Review the draft above. If you'd like to make changes, please let me know what to modify.

⚠️ Note: The web interface can draft emails but cannot actually send them without the full CLI workflow for security reasons.
"""
        return draft
        
    except Exception as e:
        return f"""Error processing purchase request: {e}

Please provide purchase details in a clear format:
- "I want to buy [quantity] [item] from [vendor] at [vendor@email.com] for $[price]"
"""

# Define the root Supervisor Agent
root_agent = Agent(
    model='gemini-2.0-flash',
    name='supervisor_agent',
    description="Construction manager assistant that routes requests to specialist agents",
    instruction="""You are a construction manager assistant. 
    Your job is to route user requests to the appropriate specialist agent.
    
    - If the user asks for information, status, or history, call the `query_tool`.
    - If the user wants to buy something, place an order, or is responding to a draft (e.g., "yes", "change it"), call the `purchasing_tool`.
    
    Always pass the user's full message to the tool.
    When the tool returns a response, output that response to the user EXACTLY as is.
    Do not summarize or alter the sub-agent's response.
    """,
    tools=[query_tool, purchasing_tool]
)
