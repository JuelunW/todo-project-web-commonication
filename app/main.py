from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from app.db import *

app = FastAPI()

origins = ["*",]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_schema()
#seed_data()

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def validate_key(api_key: str = Depends(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=401, detail={"error": "API key is missing"})
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT *
            FROM todo_users
            WHERE api_key = %s
        """, (api_key,))
        guest = cur.fetchone()
        if not guest:
            raise HTTPException(status_code=401, detail={"error": "Invalid API key"})
    return guest



@app.get("/")
def default_endpoint():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT version()")
        return cur.fetchone()

@app.get("/todos")
def get_todos(user: dict = Depends(validate_key)):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
                SELECT
                    t.id,
                    t.user_id,
                    u.username,
                    t.title,
                    t.done,
                    t.category_id,
                    c.category_name,
                    t.created_at,
                    t.updated_at
                FROM todo_tasks t
                JOIN todo_categories c ON c.id = t.category_id
                JOIN todo_users u ON u.id = t.user_id
                WHERE t.user_id = %s
                """, (user["id"],))
        return cur.fetchall()

class Todo(BaseModel):
    category_id: int
    title: str
    done: bool | None = False

@app.post("/todos")
def post_todos(todo: Todo, user: dict = Depends(validate_key)):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
                INSERT INTO todo_tasks (user_id, category_id, title, done)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """, (user["id"], todo.category_id, todo.title, todo.done,))
        return cur.fetchone()

@app.put("/todos/{id}")
def put_todos(id: int, todo: Todo, user: dict = Depends(validate_key)):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT * FROM todo_tasks
            WHERE id = %s AND user_id = %s
        """, (id, user['id']))
        if not cur.fetchall(): return {"error": f"Task {id} not found or you {user['username']} don't have permission to update this task."}

        cur.execute("""
                UPDATE todo_tasks
                SET category_id = %s, title = %s, done = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND user_id = %s
                RETURNING id
                """, (todo.category_id, todo.title, todo.done, id, user['id'],))
        return cur.fetchall()

@app.delete("/todos/{id}")
def delete_todos(id: int, user: dict = Depends(validate_key)):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT * FROM todo_tasks
            WHERE id = %s AND user_id = %s
        """, (id, user['id'],))
        if not cur.fetchall(): return {"error": f"Task {id} not found or you {user['username']} don't have permission to delete this task."}

        cur.execute("""
                DELETE FROM todo_tasks
                WHERE id = %s AND user_id = %s
                RETURNING id
                """, (id, user['id'],))
        return cur.fetchall()