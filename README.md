# Multi-Agent Tool-Calling Assistant

A production-oriented GenAI backend built with **Google Gemini, FastAPI, Python, and SQLAlchemy**. This project demonstrates how to build an AI assistant capable of multi-step reasoning, native function calling, tool execution, conversation memory, telemetry, and real-time response streaming using **Server-Sent Events (SSE)**.

The project also includes a lightweight, responsive web-based chat interface served directly by FastAPI.

---

## Features

### 🤖 Google Gemini Integration

* Powered by Google's `google-genai` SDK.
* Uses Gemini Flash models for fast AI responses.
* Supports native Gemini function calling.
* Enables multi-step agent workflows where the model can decide when a tool is required.

### ⚡ Real-Time Streaming with SSE

* Streams AI responses to the client in real time.
* Streams tool execution events.
* Allows the frontend to display agent activity as it happens.
* Uses **Server-Sent Events (SSE)** instead of waiting for the complete response.

### 💬 Built-in Web UI

* Responsive chat interface built with vanilla HTML, CSS, and JavaScript.
* No separate frontend framework is required.
* Served directly from the FastAPI application.
* Supports multi-turn conversations through session IDs.

### 💾 Asynchronous Persistence

* Uses **SQLAlchemy AsyncIO** for database operations.
* Uses SQLite as the default database.
* Stores conversation history.
* Stores tool execution telemetry and tracing information.
* Designed to support multi-turn agent conversations.

### 🛠️ Custom Tools

| Tool         | Description                                                             |
| ------------ | ----------------------------------------------------------------------- |
| `web_search` | Mocked web search tool for demonstrating external information retrieval |
| `sql_query`  | Executes queries against a local SQLite customer database               |
| `calculator` | Safely evaluates mathematical expressions                               |
| `read_csv`   | Simulates reading data from a local CSV file                            |

### 🔍 Tool Execution Tracing

Tool executions can be tracked with:

* Tool name
* Input arguments
* Tool result
* Execution latency
* Session information

This makes the application useful for understanding and debugging agent behavior.

---

## Architecture

```text
                    ┌─────────────────────┐
                    │     Web Browser      │
                    │   HTML / CSS / JS    │
                    └──────────┬──────────┘
                               │
                               │ POST /chat
                               ▼
                    ┌─────────────────────┐
                    │      FastAPI        │
                    │      Backend        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Agent Runtime    │
                    │                     │
                    │ Gemini + Tool Calls │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌───────────┐    ┌────────────┐   ┌────────────┐
        │ Web Search│    │ SQL Query  │   │ Calculator │
        └───────────┘    └────────────┘   └────────────┘
                               │
                               ▼
                         ┌────────────┐
                         │ SQLite DB  │
                         └────────────┘

                               │
                               ▼
                    ┌─────────────────────┐
                    │ Async SQLAlchemy    │
                    │ Conversation Memory │
                    │ Tool Telemetry      │
                    └─────────────────────┘

                               │
                               ▼
                    ┌─────────────────────┐
                    │    SSE Response     │
                    │ Text + Tool Events  │
                    └─────────────────────┘
```
---
## Prerequisites

Make sure you have the following installed:

* Python 3.10+
* pip
* Git
* A Google Gemini API key

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

Replace the repository URL with your actual GitHub repository URL.

---

### 2. Create a Virtual Environment

#### macOS / Linux

```bash
python -m venv venv
source venv/bin/activate
```

#### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Configuration

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
DATABASE_URL=sqlite+aiosqlite:///./memory.db
```

### Environment Variables

| Variable         | Description                   | Example                           |
| ---------------- | ----------------------------- | --------------------------------- |
| `GEMINI_API_KEY` | Google Gemini API key         | `your_api_key`                    |
| `DATABASE_URL`   | Async SQLAlchemy database URL | `sqlite+aiosqlite:///./memory.db` |

### Important

Never commit your `.env` file or API keys to Git.

Add the following to `.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.pyc
*.db
```

---

## Running the Application

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

The application will start on:

```text
http://localhost:8000
```

Open the following URL in your browser:

```text
http://localhost:8000/
```

You should see the built-in chat interface.

---

## API Endpoints

### `GET /`

Serves the built-in web-based chat UI.

```http
GET /
```

---

### `POST /chat`

Core AI agent endpoint.

It accepts a session ID and user message and returns a **Server-Sent Events (SSE)** stream containing AI responses and tool execution events.

#### Request

```json
{
  "session_id": "demo-session",
  "message": "Calculate 25 * 48"
}
```

#### Example

```bash
curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-session",
    "message": "Calculate 25 * 48"
  }'
```

The response is streamed incrementally using SSE.

---

### `GET /sessions/{session_id}/history`

Returns the conversation history associated with a session.

Example:

```http
GET /sessions/demo-session/history
```

Possible response structure:

```json
{
  "session_id": "demo-session",
  "messages": [
    {
      "role": "user",
      "content": "Calculate 25 * 48"
    },
    {
      "role": "assistant",
      "content": "25 × 48 = 1200"
    }
  ]
}
```

The exact response format depends on the implementation.

---

### `GET /sessions/{session_id}/trace`

Returns tool execution telemetry for a session.

Example:

```http
GET /sessions/demo-session/trace
```

Trace information can include:

```json
{
  "tool": "calculator",
  "arguments": {
    "expression": "25 * 48"
  },
  "result": "1200",
  "latency_ms": 2.41
}
```

This endpoint is useful for debugging and monitoring agent tool usage.

---

### `GET /health`

Health check endpoint for deployment and monitoring systems.

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

---

## Tool Calling

The agent can dynamically decide when a tool should be used.

A typical workflow looks like this:

```text
User
 │
 │ "What is 125 * 37?"
 ▼
Gemini
 │
 │ Decides calculator is required
 ▼
calculator()
 │
 │ 4625
 ▼
Gemini
 │
 │ Generates final response
 ▼
User
```

For a database question:

```text
User
 │
 │ "Find customers from Mumbai"
 ▼
Gemini
 │
 │ Calls sql_query
 ▼
SQLite Customer Database
 │
 │ Query result
 ▼
Gemini
 │
 │ Generates final response
 ▼
User
```

---

## Available Tools

### 1. `web_search`

A mocked web-search tool intended to demonstrate how an external search capability can be integrated into an agent.

Example:

```text
User:
"What is the latest information about Python?"

Agent:
→ Calls web_search
→ Receives search results
→ Generates response
```

> The included implementation is mocked and should be replaced with a real search provider for production use.

---

### 2. `sql_query`

Queries the local SQLite customer database.

Example:

```text
User:
"Show me customers from Pune."
```

The agent can generate an appropriate SQL query and execute it against the database.

#### N+1 Query Prevention

The SQL tool includes prompt/tooling guidance intended to prevent the model from repeatedly querying the database for individual records.

Instead of:

```text
Query customer 1
Query customer 2
Query customer 3
Query customer 4
...
```

the agent should prefer a single query that retrieves the required dataset.

---

### 3. `calculator`

Provides mathematical calculations through a controlled evaluation mechanism.

Example:

```text
User:
"Calculate (150 * 25) / 5"
```

The agent can call the calculator tool and use the result in its final response.

The calculator should only evaluate permitted mathematical expressions and should not be treated as a general-purpose Python execution environment.

---

### 4. `read_csv`

Simulates reading data from a local CSV file.

Example:

```text
User:
"Read the customer CSV and summarize the data."
```

The agent can invoke the CSV tool, receive the available data, and analyze it.

---

## Conversation Memory

The application maintains conversation state using a `session_id`.

For example:

```json
{
  "session_id": "user-123",
  "message": "My name is John."
}
```

A subsequent request using the same session:

```json
{
  "session_id": "user-123",
  "message": "What is my name?"
}
```

can use the previously stored conversation context.

Different session IDs represent separate conversations.

---

## SSE Streaming

The `/chat` endpoint uses **Server-Sent Events** to stream information from the backend to the browser.

Conceptually:

```text
Client
  │
  │ POST /chat
  ▼
FastAPI
  │
  ├── Gemini response
  │
  ├── Tool call event
  │
  ├── Tool result event
  │
  ├── More Gemini output
  │
  └── Final response
  │
  ▼
Client
```

This allows the UI to provide immediate feedback rather than waiting for the entire agent workflow to finish.

Example SSE events may look like:

```text
event: tool_call
data: {"tool":"calculator","arguments":{"expression":"25*48"}}

event: tool_result
data: {"tool":"calculator","result":"1200"}

event: text
data: {"content":"The answer is 1200."}
```

The exact event format depends on the implementation.

---

## Database

The default database uses SQLite with asynchronous access:

```env
DATABASE_URL=sqlite+aiosqlite:///./memory.db
```

The database can be used for:

* Conversation history
* User/session messages
* Tool execution traces
* Tool arguments
* Tool results
* Execution latency

For larger production deployments, the database layer can be adapted to PostgreSQL or another SQLAlchemy-supported database.

---

## Observability & Tracing

Tool executions can be recorded to provide visibility into agent behavior.

A trace entry can contain:

```text
Session ID
Tool Name
Arguments
Result
Execution Time
Timestamp
```

For example:

```json
{
  "session_id": "demo-session",
  "tool_name": "calculator",
  "arguments": {
    "expression": "100 / 4"
  },
  "result": "25",
  "latency_ms": 1.82
}
```

This makes it easier to investigate:

* Which tools the agent uses
* What arguments were passed
* How long tools took
* What results were returned
* How an agent reached its final response

---

## Example Agent Workflow

Consider the following request:

```text
How many customers are in Pune and what is 125 * 40?
```

The agent can perform multiple tool calls:

```text
User
 │
 ▼
Gemini Agent
 │
 ├───────────────┐
 ▼               ▼
sql_query     calculator
 │               │
 ▼               ▼
Customer Count  5000
 │               │
 └───────┬───────┘
         ▼
      Gemini
         │
         ▼
   Final Response
```

This demonstrates the multi-tool agent pattern.

---

## API Flow

```text
                    User Message
                         │
                         ▼
                  POST /chat
                         │
                         ▼
                  FastAPI Endpoint
                         │
                         ▼
                    Agent Loop
                         │
                  ┌──────┴──────┐
                  │             │
             No tool needed   Tool needed
                  │             │
                  │             ▼
                  │        Execute Python Tool
                  │             │
                  │             ▼
                  │        Tool Result
                  │             │
                  └──────┬──────┘
                         ▼
                    Gemini Model
                         │
                         ▼
                  Final AI Response
                         │
                         ▼
                    SSE Stream
                         │
                         ▼
                    Web Client
```

---

## Testing

Start the server:

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://localhost:8000/
```

Try prompts such as:

```text
Calculate 125 * 37
```

```text
Find customers from Pune.
```

```text
Search for information about FastAPI.
```

```text
Read the CSV data and summarize it.
```

You can also combine multiple capabilities:

```text
Find the number of customers in Mumbai and calculate what that number would be if it increased by 15%.
```

---

## Production Considerations

This project is intended as a production-oriented demonstration, but additional hardening should be performed before deploying it to an untrusted public environment.

### Security

* Never expose your Gemini API key to the frontend.
* Keep secrets in environment variables or a secret manager.
* Validate all incoming API requests.
* Authenticate users where required.
* Authorize access to session history and traces.
* Restrict database queries.
* Never allow unrestricted arbitrary Python execution.
* Apply rate limiting to public endpoints.

### Database

SQLite is convenient for local development and demonstrations.

For larger production deployments, consider PostgreSQL with an appropriate connection pool and migration strategy.

### Tool Safety

Tools are a critical security boundary in an agent system.

Each tool should:

* Validate its inputs.
* Restrict accessible resources.
* Handle errors safely.
* Apply timeouts where appropriate.
* Avoid unrestricted filesystem access.
* Avoid arbitrary code execution.
* Log important execution information.

### Streaming

For production SSE deployments, consider:

* Connection timeouts
* Reverse-proxy configuration
* Client disconnect handling
* Request cancellation
* Rate limiting
* Concurrent connection limits

---

## Error Handling

The application should gracefully handle common failures such as:

* Invalid API keys
* Gemini API errors
* Tool execution errors
* Invalid SQL queries
* Invalid calculator expressions
* Database connection errors
* Malformed requests
* Client disconnections

A production deployment should also ensure that internal exceptions and secrets are not exposed in API responses.

---

## Environment Variables

Example `.env` configuration:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
DATABASE_URL=sqlite+aiosqlite:///./memory.db
```

Do not commit this file to Git.

---

## Requirements

The project uses technologies such as:

* Python
* FastAPI
* Uvicorn
* Google `google-genai`
* SQLAlchemy
* `aiosqlite`
* SQLite
* Server-Sent Events
* HTML/CSS/JavaScript

Install all Python dependencies with:

```bash
pip install -r requirements.txt
```

---

## Future Improvements

Potential extensions include:

* Replace mocked web search with a real search API.
* Add authentication and user accounts.
* Add PostgreSQL support.
* Add Redis for distributed session/state management.
* Add structured logging.
* Add OpenTelemetry tracing.
* Add streaming tool output.
* Add more specialized tools.
* Add human-in-the-loop approval for sensitive tools.
* Add automated evaluation of agent responses.
* Add Docker and Docker Compose support.
* Add CI/CD with GitHub Actions.
* Add automated unit and integration tests.
* Add configurable Gemini model selection.
* Add tool permission policies.

---

## Docker Support

A Docker-based deployment can be added using:

```text
Dockerfile
docker-compose.yml
```

A typical production architecture could look like:

```text
                 ┌──────────────┐
                 │   Browser    │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ Reverse Proxy│
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │   FastAPI    │
                 │    Agent     │
                 └──────┬───────┘
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
       ┌───────────┐         ┌────────────┐
       │ PostgreSQL│         │ Gemini API │
       └───────────┘         └────────────┘
```

---

## License

No license has been specified for this project.

If you intend to allow others to use, modify, or redistribute the project, consider adding an appropriate open-source license in the future.

---

## Contributing

Contributions, improvements, and bug fixes are welcome.

### Development Workflow

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
# venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

---

## Quick Start

If you already have Python and a Gemini API key configured:

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Then open:

```text
http://localhost:8000/
```

---

## Summary

This project demonstrates a complete AI-agent backend architecture combining:

```text
Gemini
   +
Native Function Calling
   +
FastAPI
   +
Python Tools
   +
SSE Streaming
   +
Async SQLAlchemy
   +
SQLite
   +
Conversation Memory
   +
Tool Telemetry
   +
Built-in Web UI
```

It provides a practical foundation for experimenting with **multi-step AI agents, tool calling, streaming responses, persistent memory, and observability** using Python and FastAPI.

---

### Disclaimer

This project is provided for educational, experimental, and development purposes. Review and secure all components appropriately before using the application in a production environment.
