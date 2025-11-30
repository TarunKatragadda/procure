# ==============================================================================
# SUPERVISOR AGENT - Root Entry Point for Multi-Agent System
# ==============================================================================
#
# This file defines the root_agent which orchestrates the multi-agent system
# using the "Memory Bank" pattern to solve the stateless sub-agent problem.
#
# DESIGN PATTERN: Supervisor (Router) + Memory Bank
# 
# The supervisor analyzes user intent and routes requests to specialist agents:
#   - query_agent: For information retrieval (RAG with ChromaDB)
#   - purchaser_agent: For purchase orders (HITL email automation)
#
# KEY INNOVATION - Memory Bank Pattern:
# ADK's AgentTool() creates stateless sub-agents that don't remember previous
# conversation turns. The supervisor solves this by:
#   1. Maintaining full conversation history (via ADK's native session)
#   2. Analyzing context before each delegation
#   3. Combining multi-turn information into complete instructions
#   4. Extracting draft details for approvals
#
# This enables complex workflows (multi-turn data gathering, HITL approvals)
# without requiring persistent state storage in sub-agents.
#
# ==============================================================================

from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool, FunctionTool
import sys
import os

# Add current directory to path for local imports
sys.path.insert(0, os.path.dirname(__file__))

# Import specialist agents
from src.agents.query_agent import query_agent
from src.agents.purchaser_agent import purchaser_agent

# ==============================================================================
# ROOT AGENT DEFINITION
# ==============================================================================

root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='supervisor_agent',
    description='Construction procurement supervisor that routes requests to specialist agents',
    instruction="""You are a construction procurement supervisor managing specialist agents.

Your role is to analyze user requests, delegate and be the **memory bank** for specialist agents.

**Use query_agent when the user:**
- Asks for information, status, or history
- Wants to know about orders, invoices, delays
- Needs to search past communications
Examples: "What's the status of the brick order?", "Show me recent invoices"

**Use purchaser_agent when the user:**
- Wants to buy something or place an order
- Is responding to a draft email ("yes", "send it", "no", "cancel")
- Wants to initiate any purchase action
Examples: "I want to buy 100 bricks", "yes, send it"

ROUTING RULES:
1. **Context Management:** The specialist agents have NO MEMORY. You must provide full details in every call.
   - If user says "bob@brickco.com", DO NOT just send the email.
   - Send: "Order [Item] [Quantity] from bob@brickco.com" (Look at chat history for item/qty).

2. **Confirmation Rule:** If the user says "yes", "confirm", or "send it", the `purchaser_agent` WILL NOT REMEMBER the draft.
   - **YOU MUST** look at the conversation history where you showed the draft.
   - **YOU MUST** extract the `To`, `Subject`, and `Body` from that draft.
   - **YOU MUST** command the purchaser: "User confirmed. Send the email to [To] with subject [Subject] and body [Body]...".

3. **OUTPUT RULE (CRITICAL):** - When the `purchaser_agent` returns a draft or a question, **YOU MUST REPEAT IT TO THE USER.**
   - **NEVER** output raw JSON like `{"result": "..."}`.
   - **NEVER** say "Draft sent."
   - **ALWAYS** show the actual content the agent gave you.
   
   Example:
   - Bad: "The draft was created."
   - Good: "Here is the draft created by the purchaser agent: [Insert Full Draft Text]"
   - User: "Send it"
   - BAD Command to Agent: "User confirmed." (Agent crashes)
   - GOOD Command to Agent: "User confirmed. Send the email to bob@brickco.com with subject 'Purchase Order' and body 'Dear Supplier...'"

CRITICAL CONTEXT RULES (PREVENT AMNESIA):
The `purchaser_agent` has NO MEMORY of previous messages. You are the memory bank.
1. When the user adds new information (e.g., provides a missing email), you must **COMBINE** it with the previous details (item, quantity) from the conversation history.
2. Send a **COMPLETE, SELF-CONTAINED INSTRUCTION** to the purchaser_agent every time.

**Bad Example (Do not do this):**
User: "Order bricks" -> You send: "Order bricks" -> Agent asks for email.
User: "bob@gmail.com" -> You send: "bob@gmail.com" -> Agent fails (forgot about bricks).

**Good Example (Do this):**
User: "Order bricks" -> You send: "Order bricks" -> Agent asks for email.
User: "bob@gmail.com" -> You send: "Order bricks from bob@gmail.com" -> Agent succeeds.

Always return the specialist agent's response exactly.

When in doubt:
- query_agent for information
- purchaser_agent for purchases/orders
""",
    tools=[
        AgentTool(query_agent),       # Wraps query_agent as a callable tool
        AgentTool(purchaser_agent)    # Wraps purchaser_agent as a callable tool
    ]
)

# ==============================================================================
# HOW AGENT-AS-TOOL WORKS IN ADK
# ==============================================================================
#
# When we pass Agent objects wrapped in AgentTool() to the tools parameter:
#
# 1. ADK creates tool schemas using the agent's name and description:
#   - Tool name: "query_agent" (from agent.name)
#   - Tool description: "Procurement research assistant..." (from agent.description)
#
# 2. When the supervisor needs to use a tool, it analyzes intent and selects:
#   - "User asks about order status" → Use query_agent tool
#   - "User wants to buy something" → Use purchaser_agent tool
#
# 3. Tool invocation:
#   - Supervisor passes the message to the selected agent
#   - Sub-agent processes with its own tools and instructions
#   - Returns result back to supervisor
#   - Supervisor relays to user
#
# 4. State Management (Critical):
#   - Sub-agents are STATELESS - they don't remember previous turns
#   - Supervisor manages state through its conversation history
#   - Before calling a tool, supervisor extracts relevant context
#   - Passes complete, self-contained instructions each time
#
# Example:
#   Turn 1: User: "Order bricks"
#          Supervisor → purchaser_agent: "Order bricks"
#          Response: "Need vendor email"
#   
#   Turn 2: User: "bob@example.com"
#          Supervisor (Memory Bank):
#            - Looks at Turn 1: User wanted "bricks"
#            - Combines: "Order bricks from bob@example.com"
#          Supervisor → purchaser_agent: "Order bricks from bob@example.com"
#          Response: Draft email (success!)
#
# This pattern enables multi-turn workflows without persistent state.
# ==============================================================================
