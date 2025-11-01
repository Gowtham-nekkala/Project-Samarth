import streamlit as st
from local_langgraph_agent import get_agent_app, DATABASE_SCHEMA

# --- Page Configuration ---
st.set_page_config(
    page_title="Project Samarth Q&A",
    page_icon="🌾",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Load Agent ---
@st.cache_resource
def load_agent():
    """Loads the compiled LangGraph agent once."""
    app = get_agent_app()
    import local_langgraph_agent
    if getattr(local_langgraph_agent, "USING_GROQ", False):
        st.sidebar.success("🛰️ Connected to **Groq Cloud (Llama-3.3-70B)**")
    else:
        st.sidebar.info("💻 Running on **Local Ollama (Mistral 7B Instruct)** — Fallback Mode")
    return app

try:
    agent_app = load_agent()
    st.sidebar.success("✅ Agent Loaded Successfully")
except Exception as e:
    st.sidebar.error(f"❌ Failed to load agent: {e}")
    st.stop()

# --- App UI ---
st.title("🌾 Project Samarth Q&A")
st.markdown("""
Welcome! Ask a question about India's agriculture and climate data.  
This system runs 100% locally on your machine, ensuring **data privacy**.
""")

with st.sidebar:
    st.header("About this Prototype")
    st.markdown("""
### 🧠 System Overview

An intelligent **Text-to-SQL Q&A** system for **Project Samarth** — analyzing Indian agriculture and climate datasets.

#### Architecture:
1. **Data Layer:**
   - SQLite database (**`samarth.db`**) with crop production & rainfall statistics.

2. **Backend (LangGraph Agent):**
   - Generates, executes & refines SQL queries automatically.
   - Retries failed queries up to **3 times** before stopping.

3. **Models:**
   - ☁️ **Llama-3.3-70B (Groq)** → *primary cloud model (fast, accurate)*  
   - 💻 **Mistral 7B Instruct (Ollama)** → *offline fallback for local execution*

4. **Frontend:**
   - Built with **Streamlit**, fully local, providing real-time visualization.

**Key Features:**
✅ Automatic SQL error correction  
✅ Offline capability  
✅ Deterministic query generation (`temperature=0.0`)  
✅ Safe error handling (no recursion loops)
""")
    st.subheader("Database Schema")
    with st.expander("View tables and columns"):
        st.code(DATABASE_SCHEMA, language="sql")

# --- Chat Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Input Handler ---
if question := st.chat_input("e.g., 'Top 5 rice producing districts in Bihar in 2010?'"):
    # 1️⃣ Display user input
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # 2️⃣ Run agent
    with st.chat_message("assistant"):
        with st.spinner("Analyzing data... please wait ⏳"):
            # Initialize inputs with retry tracking
            inputs = {
                "question": question,
                "schema": DATABASE_SCHEMA,
                "sql_query": "",
                "data": "",
                "answer": "",
                "retries": 0
            }

            try:
                final_state = {}
                # Limit recursion safely (agent handles retries internally)
                for s in agent_app.stream(inputs, {"recursion_limit": 10}):
                    final_state = s

                # Extract final answer safely
                if "synthesize_answer" in final_state:
                    answer = final_state["synthesize_answer"].get("answer", "")
                else:
                    answer = "⚠️ I'm sorry, I couldn't generate an answer. Please try again."

            except Exception as e:
                # Catch recursion or connection errors
                error_str = str(e)
                if "GraphRecursionError" in error_str:
                    answer = "⚠️ The agent exceeded its reasoning depth after multiple retries. Try rephrasing your question."
                elif "Connection refused" in error_str:
                    answer = "🚫 Cannot reach the local Ollama model. Please ensure Ollama is running."
                else:
                    answer = f"❌ Unexpected error: {error_str}"

            # Display answer
            st.markdown(answer)

    # 3️⃣ Add assistant message to chat history
    st.session_state.messages.append({"role": "assistant", "content": answer})