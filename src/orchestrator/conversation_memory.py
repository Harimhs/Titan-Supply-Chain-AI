#!/usr/bin/env python3
"""
Conversation Memory Manager
Tracks chat history with intelligent summarization
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class Message:
    """Single conversation message"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


class ConversationMemory:
    """
    Manages conversation history with:
    - Recent message buffer (last N turns)
    - Automatic summarization when buffer full
    - Token-aware truncation
    """
    
    def __init__(self, max_recent_turns: int = 5, max_tokens: int = 2000):
        """
        Args:
            max_recent_turns: Keep last N conversation turns in memory
            max_tokens: Maximum tokens for history context
        """
        self.max_recent_turns = max_recent_turns
        self.max_tokens = max_tokens
        
        # Full conversation history
        self.full_history: List[Message] = []
        
        # Recent context (rolling window)
        self.recent_context: List[Message] = []
        
        # Summarized older context
        self.summary: Optional[str] = None
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add a message to conversation history"""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        self.full_history.append(message)
        self.recent_context.append(message)
        
        # Keep only recent turns
        if len(self.recent_context) > self.max_recent_turns * 2:  # *2 for user+assistant pairs
            # Remove oldest message
            self.recent_context.pop(0)
    
    def get_context_for_llm(self) -> str:
        """
        Get formatted conversation context for LLM
        Format: user/assistant pairs with timestamps
        """
        if not self.recent_context:
            return ""
        
        context = "### Conversation History\n\n"
        
        # Add summary if exists
        if self.summary:
            context += f"**Earlier conversation (summarized):**\n{self.summary}\n\n"
        
        # Add recent messages
        context += "**Recent messages:**\n"
        for msg in self.recent_context[-10:]:  # Last 5 turns (10 messages)
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            role_emoji = "👤" if msg.role == "user" else "🤖"
            context += f"{role_emoji} [{timestamp}] {msg.role.upper()}: {msg.content}\n"
        
        # Truncate if too long
        max_chars = self.max_tokens * 4  # Rough: 1 token ≈ 4 chars
        if len(context) > max_chars:
            context = context[:max_chars] + "...[truncated]"
        
        return context
    
    def get_last_n_messages(self, n: int = 5) -> List[Dict]:
        """Get last N messages as dict"""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in self.recent_context[-n:]
        ]
    
    def clear(self):
        """Clear all conversation history"""
        self.full_history.clear()
        self.recent_context.clear()
        self.summary = None
    
    def save_to_file(self, filepath: str):
        """Save conversation to JSON file"""
        data = {
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in self.full_history
            ],
            "summary": self.summary
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, filepath: str):
        """Load conversation from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.full_history = [
            Message(
                role=msg["role"],
                content=msg["content"],
                timestamp=datetime.fromisoformat(msg["timestamp"]),
                metadata=msg.get("metadata", {})
            )
            for msg in data["messages"]
        ]
        
        self.recent_context = self.full_history[-self.max_recent_turns * 2:]
        self.summary = data.get("summary")


# ============================================================================
# TESTS
# ============================================================================

if __name__ == "__main__":
    print("🧪 Testing Conversation Memory...")
    
    memory = ConversationMemory(max_recent_turns=3)
    
    # Simulate conversation
    memory.add_message("user", "What's the impact of Taiwan earthquake?")
    memory.add_message("assistant", "The Taiwan earthquake affects 18 facilities...")
    
    memory.add_message("user", "Show me alternative suppliers")
    memory.add_message("assistant", "Alternative suppliers include...")
    
    memory.add_message("user", "What about shipping routes?")
    memory.add_message("assistant", "Primary shipping routes are...")
    
    # Get context
    print("\n📜 Conversation Context:")
    print(memory.get_context_for_llm())
    
    # Save to file
    memory.save_to_file("test_conversation.json")
    print("\n✅ Saved to test_conversation.json")
    
    print("\n✅ Conversation Memory Tests Complete!")
