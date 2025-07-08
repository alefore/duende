from typing import List
from agent_loop import AgentLoop
from agent_loop_options import AgentLoopOptions
from conversation import Conversation, ConversationId


class AgentWorkflow:

  def __init__(self, options: AgentLoopOptions):
    self._main_agent_loop: AgentLoop = AgentLoop(options)
    self._agent_loops: List[AgentLoop] = [self._main_agent_loop]

  def get_agent_loops(self) -> List[AgentLoop]:
    return self._agent_loops

  def run(self) -> None:
    self._main_agent_loop.run()

  def get_conversation_by_id(self, conversation_id: ConversationId) -> Conversation:
    # This method now raises KeyError if conversation is not found
    return self._main_agent_loop.options.conversation_factory.Get(conversation_id)

  def get_all_conversations(self) -> List[Conversation]:
    return self._main_agent_loop.options.conversation_factory.GetAll()
