# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select
from google.genai import types

from app.db import init_db, save_message, get_history, AsyncSessionLocal, ToolTrace
from app.agent import run_agent

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Agent API", lifespan=lifespan)

class ChatRequest(BaseModel):
    session_id: str
    message: str

# --- UI ENDPOINT ---
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serves a simple web UI directly from FastAPI."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GenAI Agent UI</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 20px; display: flex; justify-content: center; }
            #chat-container { background: white; width: 100%; max-width: 800px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; flex-direction: column; height: 90vh; overflow: hidden; }
            #chat-box { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
            .msg { padding: 12px 16px; border-radius: 8px; max-width: 85%; word-wrap: break-word; line-height: 1.5; }
            .user-msg { background-color: #2563eb; color: white; align-self: flex-end; border-bottom-right-radius: 2px; }
            .agent-msg { background-color: #f3f4f6; color: #1f2937; align-self: flex-start; border-bottom-left-radius: 2px; }
            .tool-msg { background-color: #fef3c7; color: #92400e; font-size: 0.9em; align-self: center; border-radius: 20px; padding: 6px 12px; font-family: monospace; }
            #input-area { padding: 16px; background: #fff; border-top: 1px solid #e5e7eb; display: flex; gap: 10px; }
            input[type="text"] { flex: 1; padding: 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 16px; outline: none; }
            input[type="text"]:focus { border-color: #2563eb; }
            button { padding: 12px 24px; background: #2563eb; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; transition: background 0.2s; }
            button:hover { background: #1d4ed8; }
            button:disabled { background: #9ca3af; cursor: not-allowed; }
        </style>
    </head>
    <body>
        <div id="chat-container">
            <div id="chat-box">
                <div class="msg agent-msg">Hello! I am your AI assistant. I can search the web, calculate math, and query the customer database. How can I help?</div>
            </div>
            <div id="input-area">
                <input type="text" id="user-input" placeholder="Type your message..." autocomplete="off" onkeypress="handleEnter(event)">
                <button id="send-btn" onclick="sendMessage()">Send</button>
            </div>
        </div>

        <script>
            // Generate a random session ID for this browser tab
            const sessionId = "session_" + Math.random().toString(36).substring(2, 9);
            const chatBox = document.getElementById("chat-box");
            const userInput = document.getElementById("user-input");
            const sendBtn = document.getElementById("send-btn");

            function handleEnter(e) {
                if (e.key === 'Enter') sendMessage();
            }

            function appendMessage(text, className, id = null) {
                let div = id ? document.getElementById(id) : null;
                if (!div) {
                    div = document.createElement("div");
                    div.className = "msg " + className;
                    if (id) div.id = id;
                    chatBox.appendChild(div);
                }
                div.innerHTML = text; // simple innerHTML for demo formatting
                chatBox.scrollTop = chatBox.scrollHeight;
                return div;
            }

            async function sendMessage() {
                const message = userInput.value.trim();
                if (!message) return;

                userInput.value = "";
                sendBtn.disabled = true;
                appendMessage(message, "user-msg");

                const agentMsgId = "agent_" + Date.now();
                appendMessage("<i>Thinking...</i>", "agent-msg", agentMsgId);

                try {
                    const response = await fetch("/chat", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ session_id: sessionId, message: message })
                    });

                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let currentAgentText = "";

                    while (true) {
                        const { value, done } = await reader.read();
                        if (done) break;
                        
                        const chunk = decoder.decode(value, { stream: true });
                        const lines = chunk.split('\\n');
                        
                        for (let line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.substring(6));
                                    
                                    if (data.type === 'token') {
                                        currentAgentText += data.content;
                                        // Update the current agent message div
                                        document.getElementById(agentMsgId).innerHTML = currentAgentText.replace(/\\n/g, "<br>");
                                    } 
                                    else if (data.type === 'tool_start') {
                                        appendMessage(`🔧 Using tool: <b>${data.name}</b>`, "tool-msg");
                                    } 
                                    else if (data.type === 'tool_result') {
                                        appendMessage(`✅ Tool finished.`, "tool-msg");
                                    }
                                    chatBox.scrollTop = chatBox.scrollHeight;
                                } catch (e) {
                                    console.error("Error parsing SSE chunk:", e);
                                }
                            }
                        }
                    }
                } catch (error) {
                    appendMessage("⚠️ Error connecting to server.", "tool-msg");
                } finally {
                    sendBtn.disabled = false;
                    userInput.focus();
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Streams the agent reasoning process and final answer using Gemini."""
    raw_history = await get_history(req.session_id)
    
    history_contents = []
    for msg in raw_history:
        role = "model" if msg["role"] == "assistant" else msg["role"]
        history_contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
        )
    
    await save_message(req.session_id, "user", req.message)

    return StreamingResponse(
        run_agent(req.session_id, history_contents, req.message), 
        media_type="text/event-stream"
    )

@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    history = await get_history(session_id)
    return {"session_id": session_id, "history": history}

@app.get("/sessions/{session_id}/trace")
async def get_session_trace(session_id: str):
    async with AsyncSessionLocal() as session:
        stmt = select(ToolTrace).where(ToolTrace.session_id == session_id).order_by(ToolTrace.created_at)
        result = await session.execute(stmt)
        traces = result.scalars().all()
        return {
            "session_id": session_id,
            "traces": [
                {
                    "tool": t.tool_name, 
                    "args": t.arguments, 
                    "result": t.result, 
                    "latency_ms": round(t.latency * 1000, 2)
                } for t in traces
            ]
        }