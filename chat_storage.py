"""
Chat History Storage Module
Stores and retrieves chat history using SQLite database for persistence.
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = "chat_history.db"

def init_database():
    """Initialize the SQLite database with the chat history table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query TEXT NOT NULL,
            assistant_response TEXT NOT NULL,
            tool_used TEXT,
            context_data TEXT,
            timestamp TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create index for faster search
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_query ON chat_history(user_query)
    """)
    
    conn.commit()
    conn.close()

def save_chat(user_query: str, assistant_response: str, tool_used: Optional[str] = None, context_data: Optional[Dict] = None):
    """Save a chat interaction to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    context_json = json.dumps(context_data) if context_data else None
    
    cursor.execute("""
        INSERT INTO chat_history (user_query, assistant_response, tool_used, context_data, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (user_query, assistant_response, tool_used, context_json, timestamp))
    
    conn.commit()
    conn.close()

def get_all_chats(limit: Optional[int] = None) -> List[Dict]:
    """Retrieve all chat history from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT id, user_query, assistant_response, tool_used, context_data, timestamp FROM chat_history ORDER BY timestamp DESC"
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    chats = []
    for row in rows:
        chats.append({
            'id': row[0],
            'user_query': row[1],
            'assistant_response': row[2],
            'tool_used': row[3],
            'context_data': json.loads(row[4]) if row[4] else None,
            'timestamp': row[5]
        })
    
    conn.close()
    return chats

def search_chats_by_query(query: str, limit: int = 5) -> List[Dict]:
    """Search chat history by user query (simple text matching)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Use LIKE for partial matching
    cursor.execute("""
        SELECT id, user_query, assistant_response, tool_used, context_data, timestamp
        FROM chat_history
        WHERE user_query LIKE ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (f"%{query}%", limit))
    
    rows = cursor.fetchall()
    
    chats = []
    for row in rows:
        chats.append({
            'id': row[0],
            'user_query': row[1],
            'assistant_response': row[2],
            'tool_used': row[3],
            'context_data': json.loads(row[4]) if row[4] else None,
            'timestamp': row[5]
        })
    
    conn.close()
    return chats

def get_recent_chats(count: int = 10) -> List[Dict]:
    """Get the most recent chat interactions."""
    return get_all_chats(limit=count)

def clear_chat_history():
    """Clear all chat history from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history")
    conn.commit()
    conn.close()

def get_chat_count() -> int:
    """Get the total number of chat interactions stored."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM chat_history")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# Initialize database on module import
if not os.path.exists(DB_PATH):
    init_database()

