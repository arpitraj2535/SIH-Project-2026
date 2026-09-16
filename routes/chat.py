from fastapi import APIRouter, HTTPException

from models.chat import (
    ChatRequest,
    ChatResponse,
    ConversationResponse
)

from services.chat_service import (
    generate_response,
    save_message,
    create_conversation,
    conversation_exists,
    get_conversation_messages
)


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:

    # Create a new conversation if this is a new chat
    if request.conversation_id is None:
        conversation_id = create_conversation()

    else:
        # Check whether the conversation exists
        if not conversation_exists(request.conversation_id):
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

        conversation_id = request.conversation_id

    # Generate assistant response using RAG
    rag_result = generate_response(request.message)

    # Save only the answer text in PostgreSQL
    save_message(
        conversation_id=conversation_id,
        user_message=request.message,
        assistant_response=rag_result["response"]
    )

    return ChatResponse(
        response=rag_result["response"],
        confidence=rag_result["confidence"],
        sources=rag_result["sources"],
        conversation_id=conversation_id
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse
)
def get_conversation(conversation_id: int):

    # Check whether the conversation exists
    if not conversation_exists(conversation_id):
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    messages = get_conversation_messages(conversation_id)

    return {
        "conversation_id": conversation_id,
        "messages": messages
    }