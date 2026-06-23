"""Brain backends (PR-6 占位骨架).

按 ARCHITECTURE § 3.2.6, backends 在后续 iteration 拆为
独立模块. 当前阶段 _legacy.PilotModel (ollama) 和 _chat
(anthropic/openai/engine-subscription) 是实际实现.

Future modules:
- ollama.py     从 _legacy.PilotModel 拆出
- anthropic.py  从 _chat._chat_anthropic 拆出
- openai.py     从 _chat._chat_openai 拆出
- stub.py       新建, 启发式 fallback
"""
