import sqlite3
import os
from typing import TypedDict, Optional

# ✅ Modern LangChain + LangGraph imports
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langgraph.graph import StateGraph, END

# --- Configuration ---
DB_NAME = "samarth.db"


# --- 1. Define the Graph State ---
class AgentState(TypedDict):
    question: str
    schema: str
    sql_query: str
    data: Optional[str]
    answer: Optional[str]
    retries: int  # ✅ Track retry attempts


# --- 2. Setup Database and LLM ---

def setup_database():
    """Checks if the database file exists and returns both db object and schema."""
    if not os.path.exists(DB_NAME):
        print(f"Error: Database file '{DB_NAME}' not found.")
        print("Please run the 'create_database.py' script first to create it.")
        exit()
    db = SQLDatabase.from_uri(f"sqlite:///{DB_NAME}")
    return db, db.get_table_info()


def setup_llm():
    """Initializes and validates the LLM connection (Groq API or fallback)."""
    global USING_GROQ
    try:
        from langchain_groq import ChatGroq
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.0)
        llm.invoke("Hello!")  # Quick connectivity test
        print("[Agent Setup] Connected to Groq API successfully.")
        USING_GROQ = True
        return llm
    except Exception as e:
        print(f"[Agent Setup] Error connecting to Groq API: {e}")
        print("Switching to local Ollama model (if available)...")
        USING_GROQ = False
        try:
            from langchain_ollama import ChatOllama
            llm = ChatOllama(model="mistral:7b-instruct", temperature=0.0)
            llm.invoke("Hello")
            print("[Agent Setup] Connected to local Ollama successfully.")
            return llm
        except Exception as e2:
            print(f"[Agent Setup] Error connecting to Ollama: {e2}")
            print("Please ensure Ollama is running or provide a valid Groq API key.")
            exit()



# --- Initialize Shared Resources ---
db, DATABASE_SCHEMA = setup_database()
llm = setup_llm()


# --- 3. Define Graph Nodes ---

def generate_sql_node(state: AgentState):
    """Generate a valid SQL query based on user's question and DB schema."""
    print("--- [Node]: Generating SQL ---")
    question = state["question"]
    schema = state["schema"]
    last_error = state.get("data")
    retries = state.get("retries", 0)

    # --- System Prompt for Reliable SQL ---
    system_prompt = (
    "You are a SQL generator. Your only job is to write SQL queries — "
    "no text, no explanation, no markdown. "
    "You will be given a database schema and a natural language question. "
    "Your response must contain only one valid SQL query ending with a semicolon. "
    "The query must use only tables and columns present in the given schema. "
    "Do NOT include ```sql or ``` anywhere.")


    prompt = f"""
{system_prompt}

Database Schema:
{schema}

User Question:
{question}
"""

    if last_error and "Error:" in last_error:
        prompt += f"\nThe previous query failed with this error: {last_error}\nPlease correct and output only SQL."

    try:
        sql_query = llm.invoke(prompt).content.strip()

        # --- Sanitize SQL output ---
        sql_query = (
            sql_query.strip()
            .replace("```sql", "")
            .replace("```", "")
            .replace("*/", "")
            .replace("SQL:", "")
            .strip()
        )

        # Always return sql_query even if invalid
        if not sql_query or len(sql_query) < 10 or not sql_query.lower().startswith(
            ("select", "insert", "update", "delete", "create")
        ):
            print("[Agent] Invalid SQL detected — stopping execution.")
            return {
                "sql_query": "",
                "data": "Error: Invalid SQL generated.",
                "retries": retries,
            }

        print(f"[DEBUG] Generated SQL:\n{sql_query}\n---")
        return {"sql_query": sql_query, "retries": retries}

    except Exception as e:
        print(f"Error during SQL generation: {e}")
        return {
            "sql_query": "",
            "data": f"Error during SQL generation: {e}",
            "retries": retries,
        }


def execute_sql_node(state: AgentState):
    """Executes the generated SQL query using the SQLDatabase utility."""
    print("--- [Node]: Executing SQL ---")
    query = state.get("sql_query", "")
    retries = state.get("retries", 0)

    if not query:
        print("[Agent] Missing or invalid SQL in state — skipping execution.")
        return {"data": "Error: No valid SQL to execute.", "retries": retries}

    query = query.strip().replace("*/", "").replace("```", "").strip()

    if not query.lower().startswith(("select", "insert", "update", "delete", "create")):
        print("[Agent] Invalid or empty SQL detected before execution.")
        return {"data": "Error: Invalid SQL, stopping execution.", "retries": retries}

    try:
        result = db.run(query)
        print(f"Query executed successfully. Rows returned: {len(result) if result else 0}")
        return {"data": str(result), "retries": retries}
    except Exception as e:
        print(f"SQL Execution Error: {e}")
        return {"data": f"Error: {e}", "retries": retries}


def synthesize_answer_node(state: AgentState):
    """Convert query results into a human-readable answer."""
    print("--- [Node]: Synthesizing Answer ---")
    question = state["question"]
    data = state["data"]

    prompt = f"""
You are a data analyst. The user asked a question and the database returned this data.

User Question:
{question}

Database Result:
{data}

Write a clear, concise answer summarizing the result.
- If data is empty or contains an error, explain that politely.
- Do not add information not in the data.
"""

    try:
        answer = llm.invoke(prompt).content.strip()
        print(f"Final Answer: {answer}")
        return {"answer": answer, "retries": state.get("retries", 0)}
    except Exception as e:
        print(f"Error synthesizing answer: {e}")
        return {"answer": f"Error synthesizing answer: {e}", "retries": state.get("retries", 0)}


# --- 4. Conditional Logic ---

def should_continue_or_retry(state: AgentState):
    """Decide whether to retry SQL generation or end."""
    data = state.get("data", "")
    retries = state.get("retries", 0)

    # Stop after 3 retries
    if retries >= 3:
        print(f"[Agent] Max retries ({retries}) reached. Stopping.")
        return "synthesize"

    if "Error:" in data:
        print(f"[Agent] SQL error detected (retry {retries + 1}/3). Retrying SQL generation...")
        state["retries"] = retries + 1
        return "retry"
    else:
        print("SQL executed successfully — proceeding to synthesis.")
        return "synthesize"


# --- 5. Build and Compile LangGraph Agent ---

def get_agent_app():
    """Builds and compiles the LangGraph agent workflow."""
    print("[Agent Setup] Assembling LangGraph agent...")
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("synthesize_answer", synthesize_answer_node)

    # Define edges
    workflow.set_entry_point("generate_sql")
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_edge("synthesize_answer", END)

    # Add conditional edges for retries
    workflow.add_conditional_edges(
        "execute_sql",
        should_continue_or_retry,
        {
            "synthesize": "synthesize_answer",
            "retry": "generate_sql",
        },
    )

    compiled_app = workflow.compile()
    print("[Agent Setup] LangGraph agent compiled successfully.")
    return compiled_app
