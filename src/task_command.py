from agent_command import AgentCommand, CommandInput, CommandOutput
from typing import NamedTuple, Callable, Optional, List
import logging


class TaskInformation(NamedTuple):
  task_name: Optional[str]
  task_spec: List[str]


class TaskCommand(AgentCommand):

  def __init__(self, start_new_task: Callable[[TaskInformation],
                                              CommandOutput]):
    self.start_new_task = start_new_task

  def Name(self) -> str:
    return "task"

  def GetDescription(self) -> str:
    return (
        f"#{self.Name()} [task_name] <<\ntask spec …\nspec line 1\n…\n#end\n"
        "  Starts a new conversation with the AI "
        "asking it to implement a sub-task. "
        "Use this for complex commands, "
        "where you would like an agent to implement a specific smaller change. "
        "In the specification, include all information "
        "you think the AI may need. "
        "Some additional information (about the environment) will be included.")

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    if len(command_input.arguments) > 1:
      return CommandOutput(
          output=[],
          errors=[f"#{self.Name()}: Invalid syntax. Too many arguments given."],
          summary=f"Error: #{self.Name()}: Too many arguments.")

    if command_input.multiline_content is None:
      return CommandOutput(
          output=[],
          errors=[
              f"#{self.Name()}: Invalid syntax. Task specification is missing."
          ],
          summary=f"Error: #{self.Name()}: Task specification is missing.")

    task_info = TaskInformation(
        task_name=command_input.arguments[0]
        if len(command_input.arguments) == 1 else None,
        task_spec=command_input.multiline_content)
    logging.info(
        f"Forking sub-task: {task_info.task_name}: {task_info.task_spec}")

    try:
      return self.start_new_task(task_info)
    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"Error forking sub-task '{task_info.task_name}': {e}"],
          summary=f"Error executing {self.Name()} command: {e}")
