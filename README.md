# Multi-Agent Tool-Calling Assistant (Gemini + FastAPI)

A production-grade GenAI backend demonstrating how to build an AI agent that reasons over multiple steps, calls actual Python tools, and streams its thought process and final answers in real-time via Server-Sent Events (SSE). Includes a built-in Web UI.

## Features

- **Google Gemini Integration:** Uses `google-genai` and Gemini Flash models for advanced reasoning and native function calling.
- **Real-Time Streaming (SSE):** Streams individual text tokens and live tool-execution events to the client.
- **Built-in UI:** Serves a responsive, vanilla HTML/JS chat interface directly from FastAPI.
- **Asynchronous Persistence:** Uses async SQLAlchemy and SQLite to store multi-turn conversation memory and tool-execution telemetry (tracing).
- **Custom Tools:**
  - `web_search`: Mocked web search.
  - `sql_query`: Queries a local SQLite customer database. Includes prompt engineering to prevent N+1 query loops.
  - `calculator`: Safely evaluates math expressions.
  - `read_csv`: Simulates reading local file data.

## Architecture

```mermaid
graph TD
    UI[Web UI / Browser] -->|SSE Stream| FastAPI[FastAPI App]
    FastAPI <-->|Stores/Reads State| SQLite[Async SQLite DB]
    FastAPI --> AgentLoop[Agent Reasoning Loop]
    AgentLoop <-->|Chat API| Gemini[Google Gemini API]
    AgentLoop -->|Executes| Tools[Web Search, SQL, Calculator, CSV]
    Tools --> AgentLoop



## Architecture
Clone the repository:
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd your-repo-name

Create and activate a virtual environment:
Bash
python -m venv venv
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

Install dependencies:
Bash
pip install -r requirements.txt
Configure Environment Variables:

Create a .env file in the root directory and add your Gemini API key:
Code snippet
GEMINI_API_KEY=your_google_gemini_api_key_here
DATABASE_URL=sqlite+aiosqlite:///./memory.db

Run the FastAPI Server:
Bash
uvicorn app.main:app --reload
Test the Application:

Open your browser and navigate to http://localhost:8000/ to use the built-in Chat UI.

API Endpoints
GET / - Serves the web-based Chat UI.

POST /chat - The core AI endpoint. Accepts {"session_id": "...", "message": "..."} and returns a Server-Sent Events (SSE) stream of text and tool calls.

GET /sessions/{session_id}/history - Returns the full chat history for a given session.

GET /sessions/{session_id}/trace - Returns telemetry (arguments, results, execution latency) for every tool called during a session.

GET /health - Health check endpoint for deployment platforms.