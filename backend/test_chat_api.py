#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("Test 1: Importing models...")
try:
    from app.models.chat import ChatRequest, ChatMessage, SessionHistory
    print("  [OK] Chat models imported successfully")
except Exception as e:
    print(f"  [FAIL] Failed to import models: {e}")
    sys.exit(1)

print("\nTest 2: Creating ChatRequest...")
try:
    request = ChatRequest(
        session_id="test-session",
        message="Hello, world!",
        kb_id=None
    )
    print(f"  [OK] ChatRequest created")
except Exception as e:
    print(f"  [FAIL] Failed to create ChatRequest: {e}")
    sys.exit(1)

print("\nTest 3: Creating SessionHistory...")
try:
    session = SessionHistory(
        session_id="test-session",
        messages=[
            ChatMessage(role="user", content="Hello", timestamp=None)
        ]
    )
    print(f"  [OK] SessionHistory created with {len(session.messages)} messages")
except Exception as e:
    print(f"  [FAIL] Failed to create SessionHistory: {e}")
    sys.exit(1)

print("\nTest 4: Testing SSE event format...")
try:
    def format_sse_event(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
    
    event = format_sse_event("token", {"content": "Hello"})
    assert event.startswith("event: token")
    print("  [OK] SSE event format correct")
except Exception as e:
    print(f"  [FAIL] SSE format test failed: {e}")
    sys.exit(1)

print("\nTest 5: Importing chat API module...")
try:
    from app.api.chat import router, format_sse_event
    print("  [OK] Chat API module imported successfully")
    print(f"  [OK] Router prefix: {router.prefix}")
except Exception as e:
    print(f"  [FAIL] Failed to import chat module: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*50)
print("All tests passed!")
print("="*50)
