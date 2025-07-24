from typing import NamedTuple, List, Optional

from agent_loop_options import AgentLoopOptions
from conversation import ConversationFactory


class AgentWorkflowOptions(NamedTuple):
  agent_loop_options: AgentLoopOptions
  conversation_factory: ConversationFactory
  principle_paths: Optional[List[str]] = None
  input_path: Optional[str] = None
  original_task_prompt_content: Optional[str] = None
  confirm_done: str = ''
  do_review: bool = False
  review_first: bool = False
