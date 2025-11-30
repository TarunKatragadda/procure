# ==============================================================================
# QUERY AGENT - Information Retrieval Specialist
# ==============================================================================
#
# This agent specializes in searching the procurement knowledge base using
# RAG (Retrieval Augmented Generation) with ChromaDB vector database.
#
# DESIGN PATTERN: RAG (Retrieval Augmented Generation)
#
# The query agent implements a simple but effective RAG pattern:
#   1. User asks a question in natural language
#   2. Agent uses query_chroma tool to search vector database
#   3. ChromaDB returns semantically similar documents with metadata
#   4. Agent formats results and presents to user
#
# TOOLS:
#   - query_chroma: Searches ChromaDB using vector similarity
#
# BEHAVIOR:
#   - Stateless: Each query is independent
#   - Grounded: Only answers from knowledge base, never hallucinates
#   - Metadata-rich: Returns sender, date, and content
#
# ==============================================================================

from google.adk.agents.llm_agent import Agent
import sys
import os

# Add parent directory to path for local imports when running with ADK
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.chroma_db import query_collection

# ==============================================================================
# TOOL DEFINITION
# ==============================================================================


def query_chroma(query: str) -> str:
    """
    Searches the internal knowledge base (emails, documents) for information.
    
    Uses ChromaDB's vector similarity search to find semantically related content.
    The search is based on embedding similarity, not just keyword matching.
    
    Args:
        query: Natural language question or search term
        
    Returns:
        Formatted string with matching documents and metadata
        Returns "No relevant information found." if no matches
        
    Example:
        query_chroma("brick order status")
        → "Date: 2023-10-25, Sender: bob@brickco.com
           Content: Order for 5000 bricks delivering Monday..."
    """
    # Query ChromaDB vector database with semantic search
    results = query_collection(query)
    
    # Handle empty results
    if not results['documents'] or not results['documents'][0]:
         return "No relevant information found."
         
    # Extract documents and metadata from ChromaDB response
    documents = results['documents'][0]
    metadatas = results['metadatas'][0]
    
    # Format results with metadata for better context
    context = ""
    for doc, meta in zip(documents, metadatas):
        context += f"Date: {meta.get('date')}, Sender: {meta.get('sender')}\nContent: {doc}\n---\n"
    
    return context if context else "No relevant information found."

# ==============================================================================
# AGENT DEFINITION
# ==============================================================================

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
