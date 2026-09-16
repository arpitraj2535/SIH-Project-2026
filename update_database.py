from database import get_connection


connection = get_connection()
cursor = connection.cursor()

# 1. Create conversations table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# 2. Add conversation_id to messages
cursor.execute("""
    ALTER TABLE messages
    ADD COLUMN IF NOT EXISTS conversation_id INTEGER
""")

# 3. Add foreign-key relationship
cursor.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM pg_constraint
            WHERE conname = 'messages_conversation_id_fkey'
        ) THEN
            ALTER TABLE messages
            ADD CONSTRAINT messages_conversation_id_fkey
            FOREIGN KEY (conversation_id)
            REFERENCES conversations(id)
            ON DELETE CASCADE;
        END IF;
    END
    $$;
""")

connection.commit()

cursor.close()
connection.close()

print("Database structure updated successfully!")