import logging
import re
from typing import List, Optional, Pattern

from agent_loop import AgentLoop
from agent_loop_options import AgentLoopOptions
from confirmation import ConfirmationState
from conversation import Conversation, ConversationId
from message import Message, ContentSection
from conversation_state import ConversationState


class AgentWorkflow:

  def __init__(self,
               options: AgentLoopOptions,
               confirm_done: str = '') -> None:
    self._options = options
    self._agent_loop = AgentLoop(options)
    self._confirm_done_regex: Optional[Pattern[str]] = re.compile(
        confirm_done) if confirm_done else None

  def _get_human_guidance(self) -> Optional[Message]:
    self._options.conversation.SetState(ConversationState.WAITING_FOR_CONFIRMATION)
    prompt = ("Confirm `done` command? "
              "Enter an empty string to accept and terminate, "
              "or some message to be sent to the AI asking it to continue.")
    guidance = self._options.confirmation_state.RequireConfirmation(
        self._options.conversation.GetId(), prompt)
    if guidance:
      logging.info("Your guidance will be sent to the AI.")
      next_message = Message(role='user')
      next_message.PushSection(
          ContentSection(
              content=f"Notice from human: {guidance}",
              summary="Human decision to continue"))
      return next_message
    return None

  def run(self) -> None:
    while self._agent_loop.next_message:
      self._agent_loop.run()
      if self._confirm_done_regex:
        next_message = self._get_human_guidance()
        if next_message:
          self._agent_loop.set_next_message(next_message)

  def get_conversation_by_id(self, conversation_id: ConversationId) -> Conversation:
    return self._options.conversation_factory.Get(conversation_id)

  def get_all_conversations(self) -> List[Conversation]:
    return self._options.conversation_factory.GetAll()
