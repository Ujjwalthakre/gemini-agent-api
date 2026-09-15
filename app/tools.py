# app/tools.py
import json
import sqlite3
import ast
from typing import Dict, Any, Callable

# Setup a seeded demo database for the sql_query tool
_conn = sqlite3.connect(":memory:", check_same_thread=False)
_conn.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, budget REAL)")
_conn.executemany("INSERT INTO customers (name, budget) VALUES (?, ?)", 
                  [("Alice", 1000.0), ("Bob", 500.0), ("Charlie", 150.0)])
_conn.commit()

def web_search(query: str) -> str:
    """Searches the web for current information (Mocked for demo)."""
    # In a real app, integrate Tavily or DuckDuckGo here.
    return f"Search results for '{query}': Current USD to INR conversion rate is ~83.5 INR per USD."


# app/tools.py (Update just this function)

def sql_query(query: str) -> str:
    """
    Executes a query on the customer database (columns: id, name, budget).
    Supported operations: SELECT, INSERT, UPDATE, DELETE, PRAGMA.
    CRITICAL INSTRUCTION: Always fetch all needed records in a SINGLE query.
    """
    try:
        safe_query = query.strip().upper()
        allowed_prefixes = ("SELECT", "PRAGMA", "INSERT", "UPDATE", "DELETE")
        
        if not safe_query.startswith(allowed_prefixes):
            return f"Error: Only {', '.join(allowed_prefixes)} queries are allowed."
        
        cursor = _conn.cursor()
        cursor.execute(query)
        
        # If modifying data, we MUST commit the transaction to save it
        if safe_query.startswith(("INSERT", "UPDATE", "DELETE")):
            _conn.commit()
            return json.dumps({"status": "success", "rows_affected": cursor.rowcount})
        
        # If just reading data (SELECT/PRAGMA), return the rows
        rows = cursor.fetchall()
        return json.dumps(rows)
    except Exception as e:
        return f"Database Error: {str(e)}"

def calculator(expression: str) -> str:
    """Evaluates a mathematical expression."""
    try:
        # Safe evaluation using ast.literal_eval for simple math or a restricted parser
        # For demo purposes, we'll use a restricted eval. In prod, use a math parsing library.
        allowed_names = {"__builtins__": None}
        result = eval(expression, allowed_names, {})
        return str(result)
    except Exception as e:
        return f"Calculation Error: {str(e)}"

def read_csv(filename: str) -> str:
    """Reads summary statistics or contents from a given CSV file."""
    if filename == "data.csv":
        return "CSV Content: Date=2024-05-01, ActiveUsers=450, Revenue=$4000"
    return f"Error: File {filename} not found."


# We just need the list of actual Python functions for Gemini
GEMINI_TOOLS = [web_search, sql_query, calculator, read_csv]

# We keep the map to execute them later
TOOLS_MAP = {func.__name__: func for func in GEMINI_TOOLS}