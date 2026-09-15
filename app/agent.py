# app/agent.py
import json
import time
import asyncio
from typing import AsyncGenerator, List, Union
from google import genai
from google.genai import types

from app.config import settings
from app.tools import GEMINI_TOOLS, TOOLS_MAP
from app.db import save_message, save_trace

client = genai.Client(api_key=settings.gemini_api_key)

async def run_agent(session_id: str, history_contents: List[types.Content], user_message: str, max_iterations: int = 5) -> AsyncGenerator[str, None]:
    
    # Properly declare the system prompt and tools here
    config = types.GenerateContentConfig(
        system_instruction=(
            "You are a helpful AI assistant. Use tools when necessary. "
            "When pulling data from a database, ALWAYS write a single comprehensive SQL query. "
            "CRITICAL SECURITY RULE: Before you execute any INSERT, UPDATE, or DELETE query, "
            "you MUST stop and ask the user for explicit permission. Do not run the tool until they say yes."
        ),
        tools=GEMINI_TOOLS,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )

    # Initialize the native Chat session. The SDK will manage the history internally!
    chat = client.aio.chats.create(
        model='gemini-3.5-flash',  # Update this to 'gemini-3.8-flash' if you are using that specific endpoint
        config=config,
        history=history_contents
    )

    iteration = 0
    current_input: Union[str, List[types.Part]] = user_message

    while iteration < max_iterations:
        iteration += 1
        
        # Send the message (or the tool results) to the chat session
        response_stream = await chat.send_message_stream(current_input)
        
        content_buffer = ""
        fc_parts = {}

        async for chunk in response_stream:
            # Stream text output
            if chunk.text:
                content_buffer += chunk.text
                yield f"data: {json.dumps({'type': 'token', 'content': chunk.text})}\n\n"
            
            # Extract function calls safely
            if chunk.candidates and chunk.candidates[0].content.parts:
                for part in chunk.candidates[0].content.parts:
                    if part.function_call:
                        fc = part.function_call
                        key = getattr(fc, 'id', fc.name)
                        fc_parts[key] = fc

        if content_buffer:
            await save_message(session_id, "model", content_buffer)

        # Break the loop if the model didn't request any tools
        if not fc_parts:
            break
            
        # Execute tools and prepare the response parts
        result_parts = []
        for fc in fc_parts.values():
            tool_name = fc.name
            
            # Google sometimes prefixes function names with default_api:
            clean_name = tool_name.replace("default_api:", "")
            
            args_dict = fc.args if fc.args else {}
            if not isinstance(args_dict, dict):
                try: args_dict = dict(args_dict)
                except: args_dict = {}
                    
            raw_args_str = json.dumps(args_dict)
            yield f"data: {json.dumps({'type': 'tool_start', 'name': clean_name, 'args': raw_args_str})}\n\n"
            
            start_time = time.time()
            try:
                if clean_name not in TOOLS_MAP:
                    result = f"Error: Tool '{clean_name}' not found."
                else:
                    result = await asyncio.to_thread(TOOLS_MAP[clean_name], **args_dict)
            except Exception as e:
                result = f"Error executing tool: {str(e)}"
            
            latency = time.time() - start_time
            await save_trace(session_id, clean_name, raw_args_str, str(result), latency)
            
            yield f"data: {json.dumps({'type': 'tool_result', 'name': clean_name, 'result': result})}\n\n"
            
            # Mirror the exact tool name and ID back to Gemini
            func_resp = types.FunctionResponse(name=tool_name, response={"result": str(result)})
            if hasattr(fc, 'id') and fc.id:
                func_resp.id = fc.id
            
            result_parts.append(types.Part(function_response=func_resp))
            
        # The input for the NEXT loop iteration is the tool results
        current_input = result_parts

    if iteration == max_iterations:
         yield f"data: {json.dumps({'type': 'token', 'content': '[Warning: Maximum reasoning steps reached.]'})}"