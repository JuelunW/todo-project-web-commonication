import os, psycopg

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg.connect(DATABASE_URL, autocommit=True, row_factory=psycopg.rows.dict_row)

def create_schema():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS todo_users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR NOT NULL,
                    api_key VARCHAR NOT NULL
                );

                CREATE TABLE IF NOT EXISTS todo_categories (
                    id SERIAL PRIMARY KEY,
                    category_name VARCHAR NOT NULL
                );

                CREATE TABLE IF NOT EXISTS todo_tasks (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES todo_users(id) ON DELETE CASCADE,
                    category_id INT REFERENCES todo_categories(id) ON DELETE SET NULL,
                    title VARCHAR NOT NULL,
                    done BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
    except Exception as e:
        print(f"Error while creating schema: {e}")

def seed_data():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # 1. Insert Dummy Users
            users = [
                ("alice", "key_abc123"),
                ("bob", "key_xyz789"),
                ("charlie", "key_qwerty")
            ]
            cur.executemany(
                "INSERT INTO todo_users (username, api_key) VALUES (%s, %s)",
                users
            )
            print("Inserted users.")

            # 2. Insert Categories
            categories = [
                ("Work",),
                ("Personal",),
                ("Groceries",)
            ]
            cur.executemany(
                "INSERT INTO todo_categories (category_name) VALUES (%s)",
                categories
            )
            print("Inserted categories.")

            # 3. Insert Tasks (linking to User 1 and Category 1)
            # Assuming IDs 1 and 1 exist after the above inserts
            tasks = [
                (1, 1, "Finish the FastAPI report", False),
                (1, 2, "Buy coffee beans", False),
                (2, 1, "Bob's work task", True)
            ]
            cur.executemany(
                "INSERT INTO todo_tasks (user_id, category_id, title, done) VALUES (%s, %s, %s, %s)",
                tasks
            )
            print("Inserted tasks.")

    except Exception as e:
        print(f"Error seeding data: {e}")
