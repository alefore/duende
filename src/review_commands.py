import logging
from typing import Any, Callable

from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, VariableName


class AcceptChange(AgentCommand):

  def __init__(self, add_review_result_callback: Callable[[CommandOutput],
                                                          None]):
    self._add_review_result_callback = add_review_result_callback

  def Name(self) -> str:
    return self.Syntax().name

  async def run(self, inputs: dict[VariableName, Any]) -> CommandOutput:
    reason = inputs[VariableName("reason")]
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
        name="accept",
        description="Accepts the proposed code changes. Use after thoroughly reviewing the changes if they meet the evaluation criteria.",
        arguments=[
            Argument(
                name=VariableName("reason"),
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

  async def run(self, inputs: dict[VariableName, Any]) -> CommandOutput:
    reason = inputs[VariableName("reason")]
    logging.info(f"Change rejected with reason: {reason[:50]}...")
    command_output = CommandOutput(
        output=reason,
        errors="",
        summary="Change rejected. Conversation terminated.",
        command_name=self.Syntax().name,
        task_done=True)
    self._add_review_result_callback(command_output)
    return command_output

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="reject",
        description="Rejects the proposed code changes. Use this command if you find issues that prevent them from meeting the criteria. Include a detailed explanation of those issues, ideally making it as actionable as possible (e.g., what is a possible way of addressing those issues).",
        arguments=[
            Argument(
                name=VariableName("reason"),
                arg_type=ArgumentContentType.STRING,
                description="A human-readable description of why the change is being rejected, including specific issues found.",
                required=True)
        ])
