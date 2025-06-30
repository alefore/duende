from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
from typing import NamedTuple, Callable, Optional, List, Dict, Any
import logging


class TaskInformation(NamedTuple):
  task_name: Optional[str]
  task_spec: str


class TaskCommand(AgentCommand):

  def __init__(self, start_new_task: Callable[[TaskInformation],
                                              CommandOutput]):
    self.start_new_task = start_new_task

  def Name(self) -> str:
    return self.Syntax().name

  def Aliases(self) -> List[str]:
    return ["subtask", "fork"]

  def run(self, params: Dict[str, Any]) -> CommandOutput:
    task_name = params.get("task_name")
    task_spec = params["task_spec"]

    task_info = TaskInformation(task_name=task_name, task_spec=task_spec)
    logging.info(
        f"Forking sub-task: {task_info.task_name}: {task_info.task_spec}")

    try:
      result = self.start_new_task(task_info)
      return CommandOutput(
          output=result.output,
          errors=result.errors,
          summary=result.summary,
          command_name=self.Syntax().name)
    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"Error forking sub-task '{task_info.task_name}': {e}"],
          summary=f"Error executing {self.Syntax().name} command: {e}",
          command_name=self.Syntax().name)

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="task",
        description="Starts a new conversation with the AI asking it to implement a sub-task. Use this for complex commands, where you would like an agent to implement a specific smaller change. In the specification, include all information you think the AI may need. Some additional information (about the environment) will be included.",
        arguments=[
            Argument(
                name="task_name",
                arg_type=ArgumentContentType.STRING,
                description="The name of the task",
                required=False),
            Argument(
                name="task_spec",
                arg_type=ArgumentContentType.STRING,
                description="The full specification for the task.",
                required=True)
        ])
