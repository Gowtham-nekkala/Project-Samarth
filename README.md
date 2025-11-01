🌾 Project Samarth
AI-Driven Text-to-SQL Agriculture Data Analysis System

🧭 Overview

Project Samarth is an intelligent Text-to-SQL Question Answering System that allows users to query Indian agriculture and climate datasets in natural language.
The system automatically converts user questions into optimized SQL queries, executes them on a local database, and visualizes the results — bridging the gap between human language and structured data.

⚙️ System Architecture

Layer	Description
1️⃣ Data Layer	SQLite database (samarth.db) containing crop production and rainfall data across Indian districts and years.
2️⃣ Intelligence Layer (LangGraph Agent)	Handles text-to-SQL conversion, automatic error correction, and multi-step reasoning.
3️⃣ Language Models	☁️ Groq Llama-3.3-70B (online) for high-speed cloud inference.
💻 Mistral 7B Instruct (Ollama, offline) for local execution without internet.
4️⃣ Frontend Layer	Streamlit-based interactive web UI for entering questions and viewing tabular insights.

🧩 Key Features

✅ Natural Language Querying – Ask any question about crops, rainfall, or production.
✅ Automatic SQL Generation – Converts English queries into executable SQL commands.
✅ Self-Correction – Detects and fixes SQL errors automatically.
✅ Dual-Mode Intelligence – Works online via Groq API or offline via local Mistral model.
✅ Fast & Lightweight – Optimized for real-time interaction with small hardware requirements.
✅ Secure – No external data transmission when running in offline mode.

🚀 Getting Started

1️⃣ Clone the Repository
git clone https://github.com/<your-username>/project-samarth.git
cd project-samarth

2️⃣ Create a Virtual Environment
python -m venv pro
pro\Scripts\activate      # Windows
source pro/bin/activate   # Linux/Mac

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Setup API Key (for Groq Cloud)

Create a .env file in your project root:

GROQ_API_KEY=gsk_your_api_key_here


Or set it permanently in PowerShell:

setx GROQ_API_KEY "gsk_your_api_key_here"

5️⃣ Run the Application
streamlit run streamlit_app.py

🧠 Model Management

Mode	Model	Description
Online (Groq)	llama-3.3-70b-versatile	Fast, accurate cloud model used when internet is available.
Offline (Ollama)	mistral:7b-instruct	Runs locally using Ollama for full offline capability.

To install the local model:

ollama pull mistral:7b-instruct
ollama serve

🌍 Deployment Options

Platform	Works	Notes
Streamlit Cloud	✅	Public online demo using Groq API.
Local Machine	✅	Full offline mode with Ollama.
Hugging Face Spaces	✅	Groq-only version for showcasing ML capabilities.

🧾 Example Query

User Input:

“Which are the top 3 rice-producing districts in Telangana in 2012?”

Generated SQL:

SELECT District_Name, SUM(Production_Tonnes) AS Total_Production
FROM crop_production
WHERE State_Name = 'Telangana' AND Crop_Name = 'Rice' AND Year = 2012
GROUP BY District_Name
ORDER BY Total_Production DESC
LIMIT 3;


Result:

District	Total Production (Tonnes)
Nalgonda	89,320
Karimnagar	82,450
Warangal	79,680

🧑‍💻 Tech Stack

Python 3.12

Streamlit

LangChain + LangGraph

Groq API

Ollama + Mistral 7B

SQLite3

🏆 Highlights

Adaptive hybrid design: Works both online and offline

Real-time SQL generation and visualization

Modular architecture ready for domain expansion

Uses open-source models for transparent AI reasoning

📜 License

This project is open-source and released under the MIT License.

💬 Author

Gowtham

Email: nekkalagowtham1801@gmail.com

Project: AI-Driven Crop and Climate Data Analysis – Project Samarth
