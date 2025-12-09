"""
Memory management for the medical bot using mem0.
Stores conversation history per user for context-aware responses.
"""

from mem0 import Memory
import logging
import os
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)

# =====================================================
# 🧠 CONFIG — OLLAMA REMOVED (commented out)
# =====================================================

# config = {
#     "llm": {
#         "provider": "ollama",
#         "config": {
#             "model": "qwen3:1.7b",
#             "ollama_base_url": os.getenv("OLLAMA_HOST", "http://ollama:11434")
#         }
#     },
#     "embedder": {
#         "provider": "ollama",
#         "config": {
#             "model": "nomic-embed-text:latest",
#             "ollama_base_url": os.getenv("OLLAMA_HOST", "http://ollama:11434")
#         }
#     },
#     "vector_store": {
#         "provider": "qdrant",
#         "config": {
#             "collection_name": "medical_bot_memory",
#             "host": os.getenv("QDRANT_HOST", "qdrant"),
#             "port": int(os.getenv("QDRANT_PORT", "6333")),
#             "embedding_model_dims": 768,
#         }
#     },
# }

# =====================================================
# ✅ SIMPLE FALLBACK (no external dependencies)
# =====================================================
# This disables external memory and keeps everything local in RAM.
config = None
memory = None

conversation_history = defaultdict(list)
MAX_HISTORY_PER_USER = 10


def add_to_memory(user_id: str, message: str, role: str = "user"):
    """
    Add a message to user's conversation memory (local only).
    """
    try:
        # Add to in-memory conversation history
        conversation_history[user_id].append((role, message, datetime.now()))

        # Keep only last N messages
        if len(conversation_history[user_id]) > MAX_HISTORY_PER_USER:
            conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY_PER_USER:]

        # Disabled long-term memory storage (Ollama + Qdrant)
        # if memory:
        #     memory.add(messages=[{"role": role, "content": message}], user_id=user_id)

        logger.info(f"Added {role} message to in-memory history for user {user_id}")
    except Exception as e:
        logger.error(f"Error adding to memory: {e}")


def get_relevant_context(user_id: str, query: str, limit: int = 5) -> str:
    """
    Retrieve recent conversation context for the user (local only).
    """
    try:
        if user_id not in conversation_history or len(conversation_history[user_id]) == 0:
            return ""

        recent_messages = conversation_history[user_id][-(limit * 2):]

        context_parts = []
        for role, message, timestamp in recent_messages:
            if role == "user":
                context_parts.append(f"User: {message}")
            else:
                context_parts.append(f"Assistant: {message}")

        context = "\n".join(context_parts)
        logger.info(f"Retrieved {len(recent_messages)} conversation messages for user {user_id}")
        return context

    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        return ""


def get_all_memories(user_id: str) -> list:
    """
    Get all in-memory conversation history for a specific user.
    """
    try:
        if user_id not in conversation_history:
            return []
        return [{"memory": msg, "role": role} for role, msg, _ in conversation_history[user_id]]
    except Exception as e:
        logger.error(f"Error getting all memories: {e}")
        return []


def clear_user_memory(user_id: str):
    """
    Clear all in-memory messages for a specific user.
    """
    try:
        if user_id in conversation_history:
            conversation_history[user_id] = []
            logger.info(f"Cleared in-memory conversation history for user {user_id}")

        # Disabled external memory clear (Ollama + Qdrant)
        # if memory:
        #     memories = memory.get_all(user_id=user_id)
        #     for mem in memories:
        #         memory.delete(memory_id=mem["id"])
        #     logger.info(f"Cleared mem0 memory for user {user_id}")
    except Exception as e:
        logger.error(f"Error clearing memory: {e}")
