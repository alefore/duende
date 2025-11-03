import abc
from typing import Pattern, NamedTuple

from agent_command import VariableMap
from command_registry import CommandRegistry
from confirmation import ConfirmationState
from conversation import Conversation, ConversationFactory
from conversational_ai import ConversationalAI
from file_access_policy import FileAccessPolicy
from message import Message
from validation import ValidationManager


class AgentLoopOptions(NamedTuple):
  conversation: Conversation
  start_message: Message
  command_registry: CommandRegistry
  confirmation_state: ConfirmationState
  file_access_policy: FileAccessPolicy
  conversational_ai: ConversationalAI
  confirm_regex: Pattern[str] | None = None
  skip_implicit_validation: bool = False
  validation_manager: ValidationManager | None = None


class BaseAgentLoop(abc.ABC):

  @abc.abstractmethod
  async def run(self) -> VariableMap:
    pass


class BaseAgentLoopFactory(abc.ABC):

  @abc.abstractmethod
  def new(self, options: AgentLoopOptions) -> BaseAgentLoop:
    pass
