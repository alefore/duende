from typing import List, Any, Dict
import logging

from agent_command import AgentCommand, CommandOutput, CommandSyntax, ArgumentContentType, Argument


class DoneCommand(AgentCommand):

  def Name(self) -> str:
    return self.Syntax().name

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="done",
        description="Signals that the current task is completed.",
        arguments=[],
    )

  def run(self, inputs: Dict[str, Any]) -> CommandOutput:
    logging.info("Done command runs!")
    return CommandOutput(self.Name(), "", "", "Task completed.", task_done=True)
