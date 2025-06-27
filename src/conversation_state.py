from enum import Enum, auto


class ConversationState(Enum):
  STARTING = auto()
  WAITING_FOR_AI_RESPONSE = auto()
  WAITING_FOR_REVIEW_FEEDBACK = auto()
  RUNNING_COMMANDS = auto()
  PARSING_COMMANDS = auto()
  EXECUTING_IMPLICIT_VALIDATION = auto()
  WAITING_FOR_CONFIRMATION = auto()
