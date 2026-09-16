from database import get_connection
from psycopg.rows import dict_row
from services.rag_client import ask_rag

def generate_response(message: str) -> dict:
    rag_result = ask_rag(message)

    return {
        "response": rag_result["answer"],
        "confidence": rag_result["confidence"],
        "sources": rag_result["sources"]
    }


def create_conversation() -> int:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO conversations DEFAULT VALUES
        RETURNING id
        """
    )

    conversation_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()
    connection.close()

    return conversation_id


def conversation_exists(conversation_id: int) -> bool:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT EXISTS(
            SELECT 1
            FROM conversations
            WHERE id = %s
        )
        """,
        (conversation_id,)
    )

    exists = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return exists


def save_message(
    conversation_id: int,
    user_message: str,
    assistant_response: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO messages
        (conversation_id, user_message, assistant_response)
        VALUES (%s, %s, %s)
        """,
        (conversation_id, user_message, assistant_response)
    )

    connection.commit()

    cursor.close()
    connection.close()


def get_conversation_messages(conversation_id: int):
    connection = get_connection()
    cursor = connection.cursor(row_factory=dict_row)

    cursor.execute(
        """
        SELECT id, user_message, assistant_response, created_at
        FROM messages
        WHERE conversation_id = %s
        ORDER BY id ASC
        """,
        (conversation_id,)
    )

    messages = cursor.fetchall()

    cursor.close()
    connection.close()

    return messages