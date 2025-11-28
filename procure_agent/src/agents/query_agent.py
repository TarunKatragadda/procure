from google.adk.agents.llm_agent import Agent
import sys
import os

# Add parent directory to path for local imports when running with ADK
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.chroma_db import query_collection

def query_chroma(query: str) -> str:
    """
    Searches the internal knowledge base (emails, documents) for information relevant to the query.
    Use this tool to find status updates, invoices, or past communications.
    """
    results = query_collection(query)
    
    if not results['documents'] or not results['documents'][0]:
         return "No relevant information found."
         
    documents = results['documents'][0]
    metadatas = results['metadatas'][0]
    
    context = ""
    for doc, meta in zip(documents, metadatas):
        context += f"Date: {meta.get('date')}, Sender: {meta.get('sender')}\nContent: {doc}\n---\n"
    
    return context if context else "No relevant information found."

# Define the Query Agent
query_agent = Agent(
    model='gemini-2.0-flash',
    name='query_agent',
    description="Procurement research assistant that searches the knowledge base",
    instruction="""You are a procurement research assistant.
    Your goal is to answer user questions using the `query_chroma` tool.
    
    1. Always use the `query_chroma` tool to find information.
    2. Answer the user's question based ONLY on the information returned by the tool.
    3. If the tool returns no information, state that you don't know.
    """,
    tools=[query_chroma]
)
