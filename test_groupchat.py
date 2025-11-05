"""Test GroupChat message capture."""
from __future__ import annotations

import sys
sys.path.insert(0, 'function')

from ag2_orchestrator import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()

print("Before execute:")
print(f"  group_chat.messages length: {len(orchestrator.group_chat.messages)}")

result = orchestrator.execute('顧客数を教えて')

print("\nAfter execute:")
print(f"  group_chat.messages length: {len(orchestrator.group_chat.messages)}")
print(f"  result conversation length: {len(result.get('conversation', []))}")
print(f"  result output length: {len(result.get('output', ''))}")
print(f"  result agents: {result.get('agents_involved', [])}")

# Check manager's chat messages
if hasattr(orchestrator.manager, 'chat_messages'):
    print(f"\n  manager.chat_messages keys count: {len(orchestrator.manager.chat_messages.keys())}")
    if orchestrator.user_proxy in orchestrator.manager.chat_messages:
        msgs = orchestrator.manager.chat_messages[orchestrator.user_proxy]
        print(f"  manager->user_proxy messages: {len(msgs)}")
        if msgs:
            print(f"  First: {msgs[0].get('name')}: {msgs[0].get('content')[:50]}")
            print(f"  Last: {msgs[-1].get('name')}: {msgs[-1].get('content')[:50]}")

