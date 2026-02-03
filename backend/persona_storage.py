"""JSON-based storage for personas."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import PERSONAS_FILE


def _ensure_personas_dir():
    """Ensure the personas directory exists."""
    Path(PERSONAS_FILE).parent.mkdir(parents=True, exist_ok=True)


def _load_personas_data() -> Dict[str, Any]:
    """Load personas from JSON file."""
    _ensure_personas_dir()
    if not os.path.exists(PERSONAS_FILE):
        return {"personas": []}
    with open(PERSONAS_FILE, "r") as f:
        return json.load(f)


def _save_personas_data(data: Dict[str, Any]):
    """Save personas to JSON file."""
    _ensure_personas_dir()
    with open(PERSONAS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def list_personas() -> List[Dict[str, Any]]:
    """
    List all personas.

    Returns:
        List of persona dicts
    """
    data = _load_personas_data()
    return data.get("personas", [])


def get_persona(persona_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a persona by ID.

    Args:
        persona_id: Persona UUID

    Returns:
        Persona dict or None if not found
    """
    personas = list_personas()
    for p in personas:
        if p.get("id") == persona_id:
            return p
    return None


def create_persona(name: str, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new persona.

    Args:
        name: Display name
        prompt: System prompt for the persona
        model: Optional model identifier for display

    Returns:
        Created persona dict
    """
    data = _load_personas_data()
    personas = data.get("personas", [])

    persona = {
        "id": str(uuid.uuid4()),
        "name": name,
        "prompt": prompt,
        "model": model,
        "created_at": datetime.utcnow().isoformat(),
    }

    personas.append(persona)
    data["personas"] = personas
    _save_personas_data(data)

    return persona


def update_persona(
    persona_id: str,
    name: Optional[str] = None,
    prompt: Optional[str] = None,
    model: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update an existing persona.

    Args:
        persona_id: Persona UUID
        name: New name (optional)
        prompt: New prompt (optional)
        model: New model (optional)

    Returns:
        Updated persona dict or None if not found
    """
    data = _load_personas_data()
    personas = data.get("personas", [])

    for i, p in enumerate(personas):
        if p.get("id") == persona_id:
            if name is not None:
                personas[i]["name"] = name
            if prompt is not None:
                personas[i]["prompt"] = prompt
            if model is not None:
                personas[i]["model"] = model
            data["personas"] = personas
            _save_personas_data(data)
            return personas[i]

    return None


def delete_persona(persona_id: str) -> bool:
    """
    Delete a persona.

    Args:
        persona_id: Persona UUID

    Returns:
        True if deleted, False if not found
    """
    data = _load_personas_data()
    personas = data.get("personas", [])

    for i, p in enumerate(personas):
        if p.get("id") == persona_id:
            personas.pop(i)
            data["personas"] = personas
            _save_personas_data(data)
            return True

    return False
