"""FastAPI backend for LLM Council."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
import json
import asyncio

from . import storage
from . import persona_storage
from .config import COUNCIL_MODELS, CHAIRMAN_MODEL
from .council import (
    run_full_council,
    generate_conversation_title,
    stage1_collect_responses,
    stage2_collect_rankings,
    stage3_synthesize_final,
    calculate_aggregate_rankings,
)


def _resolve_personas(persona_ids: List[str] | None) -> tuple[List[Dict[str, Any]], List[str]]:
    """
    Resolve persona IDs to (personas, models). Dynamic council - only selected personas.
    Returns ([persona dicts], [model ids]). Raises HTTPException if any ID invalid.
    If no persona_ids, returns ([], []) - caller uses COUNCIL_MODELS fallback.
    """
    if not persona_ids:
        return [], []

    # Filter out empty IDs
    ids = [pid for pid in persona_ids if pid and str(pid).strip()]

    if not ids:
        return [], []

    personas = []
    models = []
    for pid in ids:
        p = persona_storage.get_persona(pid)
        if p is None:
            raise HTTPException(status_code=400, detail=f"Invalid persona ID: {pid}")
        if not p.get("model"):
            raise HTTPException(
                status_code=400,
                detail=f"Persona '{p.get('name', '')}' has no model assigned",
            )
        personas.append(p)
        models.append(p["model"])

    return personas, models

app = FastAPI(title="LLM Council API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    pass


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    content: str
    persona_ids: List[str] | None = None  # One per council member, in order


class CreatePersonaRequest(BaseModel):
    """Request to create a persona."""
    name: str
    prompt: str
    model: str | None = None


class UpdatePersonaRequest(BaseModel):
    """Request to update a persona."""
    name: str | None = None
    prompt: str | None = None
    model: str | None = None


class ConversationMetadata(BaseModel):
    """Conversation metadata for list view."""
    id: str
    created_at: str
    title: str
    message_count: int


class Conversation(BaseModel):
    """Full conversation with all messages."""
    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Council API"}


@app.get("/api/config")
async def get_config():
    """Get council configuration and providers/models for frontend.
    Models are fetched from provider APIs (cached 5 min). Falls back to static list when API fails."""
    from .models_fetcher import get_providers_models

    providers_models = await get_providers_models()
    return {
        "council_models": COUNCIL_MODELS,
        "chairman_model": CHAIRMAN_MODEL,
        "providers_models": providers_models,
    }


@app.post("/api/config/refresh-models")
async def refresh_models():
    """Force refresh of models cache (fetch from provider APIs again)."""
    from .models_fetcher import clear_models_cache, get_providers_models

    clear_models_cache()
    providers_models = await get_providers_models()
    return {"providers_models": providers_models}


@app.get("/api/personas")
async def list_personas():
    """List all personas."""
    return persona_storage.list_personas()


@app.post("/api/personas")
async def create_persona(request: CreatePersonaRequest):
    """Create a new persona."""
    return persona_storage.create_persona(
        name=request.name,
        prompt=request.prompt,
        model=request.model,
    )


@app.put("/api/personas/{persona_id}")
async def update_persona(persona_id: str, request: UpdatePersonaRequest):
    """Update an existing persona."""
    result = persona_storage.update_persona(
        persona_id=persona_id,
        name=request.name,
        prompt=request.prompt,
        model=request.model,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Persona not found")
    return result


@app.delete("/api/personas/{persona_id}")
async def delete_persona(persona_id: str):
    """Delete a persona."""
    if not persona_storage.delete_persona(persona_id):
        raise HTTPException(status_code=404, detail="Persona not found")
    return {"status": "ok"}


@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    """List all conversations (metadata only)."""
    return storage.list_conversations()


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(conversation_id)
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all its messages."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.post("/api/conversations/{conversation_id}/message")
async def send_message(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and run the 3-stage council process.
    Returns the complete response with all stages.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Add user message
    storage.add_user_message(conversation_id, request.content)

    # If this is the first message, generate a title
    if is_first_message:
        title = await generate_conversation_title(request.content)
        storage.update_conversation_title(conversation_id, title)

    # Resolve personas and get models (dynamic council)
    personas, models = _resolve_personas(request.persona_ids)
    if not models:
        models = COUNCIL_MODELS
        personas = None

    # Run the 3-stage council process
    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        request.content, models, personas
    )

    # Add assistant message with all stages
    storage.add_assistant_message(
        conversation_id,
        stage1_results,
        stage2_results,
        stage3_result
    )

    # Return the complete response with metadata
    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata
    }


@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and stream the 3-stage council process.
    Returns Server-Sent Events as each stage completes.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Resolve personas and get models (raises 400 if invalid)
    personas, models = _resolve_personas(request.persona_ids)
    if not models:
        models = COUNCIL_MODELS
        personas = None

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    async def event_generator():
        try:
            # Add user message
            storage.add_user_message(conversation_id, request.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(generate_conversation_title(request.content))

            # Stage 1: Collect responses
            yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"
            stage1_results = await stage1_collect_responses(
                request.content, models, personas
            )
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2: Collect rankings
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            stage2_results, label_to_model = await stage2_collect_rankings(
                request.content, stage1_results, models, personas
            )
            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Stage 3: Synthesize final answer
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            stage3_result = await stage3_synthesize_final(request.content, stage1_results, stage2_results)
            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            # Wait for title generation if it was started
            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            # Save complete assistant message
            storage.add_assistant_message(
                conversation_id,
                stage1_results,
                stage2_results,
                stage3_result
            )

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
