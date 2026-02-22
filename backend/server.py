from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import time
from typing import List

DB = "data.sqlite"

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    public_key_spki TEXT
                   )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user TEXT,
                    to_user TEXT,
                    enc_key TEXT,
                    nonce TEXT,
                    ciphertext TEXT,
                    timestamp INTEGER
                   )""")
    conn.commit()
    conn.close()


init_db()
app = FastAPI()

# ✅ FIX FOR CORS (Required for frontend on port 8080)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # allow requests from any origin (frontend)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RegisterRequest(BaseModel):
    username: str
    public_key_spki_b64: str

class MessageBlob(BaseModel):
    from_user: str
    to_user: str
    enc_key: str
    nonce: str
    ciphertext: str
    timestamp: int

@app.post("/register")
async def register(r: RegisterRequest):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE username = ?", (r.username,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="user exists")
    cur.execute("INSERT INTO users (username, public_key_spki) VALUES (?, ?)",
                (r.username, r.public_key_spki_b64))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/users", response_model=List[str])
async def list_users():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT username FROM users")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

@app.get("/public-key/{username}")
async def get_public_key(username: str):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT public_key_spki FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    return {"public_key_spki_b64": row[0]}

@app.post("/send")
async def send_message(m: MessageBlob):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE username = ?", (m.to_user,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="recipient not found")
    cur.execute("""INSERT INTO messages (from_user, to_user, enc_key, nonce, ciphertext, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (m.from_user, m.to_user, m.enc_key, m.nonce, m.ciphertext, m.timestamp))
    conn.commit()
    conn.close()
    return {"stored": True}

@app.get("/fetch/{username}")
async def fetch_messages(username: str):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, from_user, enc_key, nonce, ciphertext, timestamp FROM messages WHERE to_user = ? ORDER BY id ASC",
                (username,))
    rows = cur.fetchall()
    cur.execute("DELETE FROM messages WHERE to_user = ?", (username,))
    conn.commit()
    conn.close()

    messages = []
    for r in rows:
        messages.append({
            "id": r[0],
            "from_user": r[1],
            "enc_key": r[2],
            "nonce": r[3],
            "ciphertext": r[4],
            "timestamp": r[5]
        })
    return {"messages": messages}
