from typing import List, Pattern, NamedTuple

from command_registry import CommandRegistry
from confirmation import ConfirmationState
from conversation import Conversation, ConversationFactory
from message import Message
from conversational_ai import ConversationalAI
from file_access_policy import FileAccessPolicy
from validation import ValidationManager


class AgentLoopOptions(NamedTuple):
  conversation: Conversation
  start_message: Message
  # TODO: Rename to command_registry (and fix all customers)
  commands_registry: CommandRegistry
  confirmation_state: ConfirmationState
  file_access_policy: FileAccessPolicy
  conversational_ai: ConversationalAI
  confirm_regex: Pattern[str] | None = None
  skip_implicit_validation: bool = False
  validation_manager: ValidationManager | None = None
