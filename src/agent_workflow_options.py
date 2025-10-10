from typing import NamedTuple

from agent_loop_options import AgentLoopOptions, BaseAgentLoopFactory
from conversation import ConversationFactory
from selection_manager import SelectionManager


class AgentWorkflowOptions(NamedTuple):
  agent_loop_options: AgentLoopOptions
  agent_loop_factory: BaseAgentLoopFactory
  conversation_factory: ConversationFactory
  selection_manager: SelectionManager
  principle_paths: list[str] | None = None
  input_paths: list[str] | None = None
  original_task_prompt_content: str | None = None
  confirm_done: str = ''
  do_review: bool = False
  review_first: bool = False
