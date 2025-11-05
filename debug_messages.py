"""Debug AG2 message storage."""
from __future__ import annotations

import sys
sys.path.insert(0, 'function')

from ag2_orchestrator import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()

result = orchestrator.execute('顧客数を教えて')

print("\n=== DEBUGGING MESSAGE STORAGE ===")
print(f"GroupChat.messages: {len(orchestrator.group_chat.messages)}")
print(f"\nUserProxy.chat_messages keys: {list(orchestrator.user_proxy.chat_messages.keys())}")

for agent_name, messages in orchestrator.user_proxy.chat_messages.items():
    print(f"\n{orchestrator.user_proxy.name} -> {agent_name}: {len(messages)} messages")
    if messages:
        print(f"  First message: {messages[0]}")
        print(f"  Last message: {messages[-1]}")

print(f"\nManager.chat_messages keys: {list(orchestrator.manager.chat_messages.keys())}")
for agent_name, messages in orchestrator.manager.chat_messages.items():
    print(f"\n{orchestrator.manager.name} -> {agent_name}: {len(messages)} messages")

print(f"\nSQL Agent.chat_messages keys: {list(orchestrator.sql_agent.chat_messages.keys())}")
for agent_name, messages in orchestrator.sql_agent.chat_messages.items():
    print(f"\n{orchestrator.sql_agent.name} -> {agent_name}: {len(messages)} messages")
