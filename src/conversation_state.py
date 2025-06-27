from enum import Enum, auto
from typing import Mapping


class ConversationState(Enum):
  STARTING = auto()
  WAITING_FOR_AI_RESPONSE = auto()
  WAITING_FOR_REVIEW_FEEDBACK = auto()
  RUNNING_COMMANDS = auto()
  PARSING_COMMANDS = auto()
  EXECUTING_IMPLICIT_VALIDATION = auto()
  WAITING_FOR_CONFIRMATION = auto()

  def to_emoji(self) -> str:
    """Returns an emoji representation of the state."""
    return _STATE_TO_EMOJI[self]


_STATE_TO_EMOJI: Mapping[ConversationState, str] = {
    ConversationState.STARTING: "🚀",
    ConversationState.WAITING_FOR_AI_RESPONSE: "🤖",
    ConversationState.WAITING_FOR_REVIEW_FEEDBACK: "🔎",
    ConversationState.RUNNING_COMMANDS: "🏃",
    ConversationState.PARSING_COMMANDS: "🧩",
    ConversationState.EXECUTING_IMPLICIT_VALIDATION: "⚙️",
    ConversationState.WAITING_FOR_CONFIRMATION: "❓",
}

# This ensures that any new ConversationState member must be added to the
# _STATE_TO_EMOJI map, raising an error on startup if any are missing.
defined_states = set(_STATE_TO_EMOJI.keys())
all_states = set(ConversationState)
if defined_states != all_states:
  missing = all_states - defined_states
  extra = defined_states - all_states
  error_message = "Mismatch between ConversationState and _STATE_TO_EMOJI mapping."
  if missing:
    error_message += f" Missing states: {[s.name for s in missing]}."
  if extra:
    error_message += f" Extra states: {[s.name for s in extra]}."
  raise NotImplementedError(error_message)
