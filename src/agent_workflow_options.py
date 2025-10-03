from typing import NamedTuple, List

from agent_loop_options import AgentLoopOptions
from conversation import ConversationFactory
from selection_manager import SelectionManager


class AgentWorkflowOptions(NamedTuple):
  agent_loop_options: AgentLoopOptions
  conversation_factory: ConversationFactory
  selection_manager: SelectionManager
  principle_paths: List[str] | None = None
  input_paths: List[str] | None = None
  original_task_prompt_content: str | None = None
  confirm_done: str = ''
  do_review: bool = False
  review_first: bool = False
