from typing import NamedTuple, Callable, List, Dict, Any
import logging

from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, VariableName


class TaskInformation(NamedTuple):
  task_name: str | None
  task_spec: str


class TaskCommand(AgentCommand):

  def __init__(self, start_new_task: Callable[[TaskInformation],
                                              CommandOutput]):
    self.start_new_task = start_new_task

  def Name(self) -> str:
    return self.Syntax().name

  async def run(self, params: Dict[VariableName, Any]) -> CommandOutput:
    task_name = params.get(VariableName("task_name"))
    task_spec = params[VariableName("task_spec")]

    task_info = TaskInformation(task_name=task_name, task_spec=task_spec)
    logging.info(
        f"Forking sub-task: {task_info.task_name}: {task_info.task_spec}")

    try:
      # self.start_new_task is not an async function yet, so we don't await it.
      # If it becomes async in the future, it would need to be awaited.
      result = self.start_new_task(task_info)
      return CommandOutput(
          output=result.output,
          errors=result.errors,
          summary=result.summary,
          command_name=self.Syntax().name)
    except Exception as e:
      return CommandOutput(
          output="",
          errors=f"Error forking sub-task '{task_info.task_name}': {e}",
          summary=f"Error executing {self.Syntax().name} command: {e}",
          command_name=self.Syntax().name)

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="task",
        description="Starts a new conversation with the AI asking it to implement a sub-task. Use this for complex commands, where you would like an agent to implement a specific smaller change. In the specification, include all information you think the AI may need. Some additional information (about the environment) will be included.",
        arguments=[
            Argument(
                name=VariableName("task_name"),
                arg_type=ArgumentContentType.STRING,
                description="The name of the task",
                required=False),
            Argument(
                name=VariableName("task_spec"),
                arg_type=ArgumentContentType.STRING,
                description="The full specification for the task.",
                required=True)
        ])
