from typing import List, Optional, Pattern, NamedTuple

from command_registry import CommandRegistry
from confirmation import ConfirmationState
from conversation import Conversation, ConversationFactory
from message import Message
from conversational_ai import ConversationalAI
from file_access_policy import FileAccessPolicy
from validation import ValidationManager


class AgentLoopOptions(NamedTuple):
  task_prompt_content: str
  conversation_factory: ConversationFactory
  conversation: Conversation
  start_message: Message
  commands_registry: CommandRegistry
  confirmation_state: ConfirmationState
  file_access_policy: FileAccessPolicy
  conversational_ai: ConversationalAI
  confirm_regex: Optional[Pattern[str]] = None
  skip_implicit_validation: bool = False
  validation_manager: Optional[ValidationManager] = None
  do_review: bool = False
  review_first: bool = False
