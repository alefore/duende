from agent_command import AgentCommand, CommandInput, CommandOutput
from typing import Optional
import logging


class TaskCommand(AgentCommand):

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

    task_name: str = command_input.arguments[0] if len(
        command_input.arguments) == 1 else "<anonymous task>"
    task_details = "\n".join(command_input.multiline_content).strip()

    logging.info(f"Forking sub-task: {task_name} with details: {task_details}")

    # Logic to initialize and handle a sub-task goes here
    try:
      # Simulate task forking with task details (to be replaced with actual sub-task logic)
      sub_task_result = f"Sub-task '{task_name}' forked successfully with details: {task_details}"
      return CommandOutput(
          output=[sub_task_result],
          errors=[],
          summary=f"Successfully forked sub-task '{task_name}'.")
    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[
              f"Error forking sub-task '{task_name}' with details '{task_details}': {e}"
          ],
          summary=f"Error executing {self.Name()} command: {e}")
