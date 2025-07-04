import logging
from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
from typing import Any, Dict, List, Optional, Callable


class AcceptChange(AgentCommand):

  def __init__(self, add_review_result_callback: Callable[[CommandOutput],
                                                          None]):
    self._add_review_result_callback = add_review_result_callback

  def Name(self) -> str:
    return self.Syntax().name

  def run(self, inputs: Dict[str, Any]) -> CommandOutput:
    reason = inputs["reason"]
    logging.info(f"Change accepted with reason: {reason[:50]}...")
    command_output = CommandOutput(
        output="Change accepted.",
        errors="",
        summary="Change accepted. Conversation terminated.",
        command_name=self.Syntax().name,
        task_done=True)
    self._add_review_result_callback(command_output)
    return command_output

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="accept_change",
        description="Accepts the proposed code changes. Use after thoroughly reviewing the changes if they meet the evaluation criteria.",
        arguments=[
            Argument(
                name="reason",
                arg_type=ArgumentContentType.STRING,
                description="A human-readable description of why the change is being accepted.",
                required=True)
        ])


class RejectChange(AgentCommand):

  def __init__(self, add_review_result_callback: Callable[[CommandOutput],
                                                          None]):
    self._add_review_result_callback = add_review_result_callback

  def Name(self) -> str:
    return self.Syntax().name

  def run(self, inputs: Dict[str, Any]) -> CommandOutput:
    reason = inputs["reason"]
    logging.info(f"Change rejected with reason: {reason[:50]}...")
    command_output = CommandOutput(
        output="Change rejected.",
        errors="",
        summary="Change rejected. Conversation terminated.",
        command_name=self.Syntax().name,
        task_done=True)
    self._add_review_result_callback(command_output)
    return command_output

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="reject_change",
        description="Rejects the proposed code changes. Use this command if you find issues that prevent them from meeting the criteria.",
        arguments=[
            Argument(
                name="reason",
                arg_type=ArgumentContentType.STRING,
                description="A human-readable description of why the change is being rejected, including specific issues found.",
                required=True)
        ])
