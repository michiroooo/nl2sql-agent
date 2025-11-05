"""Debug all messages."""
from __future__ import annotations

import sys
sys.path.insert(0, 'function')

from ag2_orchestrator import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()
result = orchestrator.execute('顧客数を教えて')

print("\n=== ALL MESSAGES ===")
msgs = orchestrator.manager.chat_messages.get(orchestrator.user_proxy, [])
for i, msg in enumerate(msgs):
    name = msg.get('name', 'NONAME')
    content = msg.get('content', '')
    print(f"{i}: {name}: {content[:80] if content else '(empty)'}")
