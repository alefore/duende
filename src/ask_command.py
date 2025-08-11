import logging
from typing import Any, Dict, Optional

from agent_command import AgentCommand, CommandOutput, CommandSyntax, Argument, ArgumentContentType
from conversation import ConversationFactory
from conversational_ai import ConversationalAI
from confirmation import ConfirmationState
from file_access_policy import FileAccessPolicy
from agent_loop import AgentLoop
from agent_loop_options import AgentLoopOptions
from message import Message, ContentSection
from command_registry import CommandRegistry
from validation import ValidationManager


class AskCommand(AgentCommand):

  def __init__(self, conversation_factory: ConversationFactory,
               conversational_ai: ConversationalAI,
               confirmation_state: ConfirmationState,
               file_access_policy: FileAccessPolicy,
               command_registry: CommandRegistry,
               validation_manager: Optional[ValidationManager]):
    self._conversation_factory = conversation_factory
    self._conversational_ai = conversational_ai
    self._confirmation_state = confirmation_state
    self._file_access_policy = file_access_policy
    self._command_registry = command_registry
    self._validation_manager = validation_manager

  def Name(self) -> str:
    return "ask"

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="ask",
        description="Forks a separate AI conversation to investigate the codebase and answer a specific question. Use this when you need detailed information that cannot be trivially obtained with existing commands. The AI in the forked conversation will have read-only access.",
        arguments=[
            Argument(
                name="question",
                arg_type=ArgumentContentType.STRING,
                description="The question to be answered by the forked AI.",
                required=True,
            )
        ],
        output_type=ArgumentContentType.STRING,
        output_description="The answer provided by the forked AI.",
    )

  async def run(self, inputs: Dict[str, Any]) -> CommandOutput:
    question = inputs["question"]

    sub_conversation = await self._conversation_factory.New(
        name="ask_conversation",
        path=None,
        command_registry=self._command_registry)

    start_message = Message(
        role='user',
        content_sections=[
            ContentSection(
                content=f"Please investigate the codebase to answer the following question: {question}. Once you have the answer, use the 'answer' command to provide it."
            )
        ],
    )

    sub_agent_options = AgentLoopOptions(
        conversation=sub_conversation,
        start_message=start_message,
        commands_registry=self._command_registry,
        confirmation_state=self._confirmation_state,
        file_access_policy=self._file_access_policy,
        conversational_ai=self._conversational_ai,
        validation_manager=self._validation_manager,
    )

    agent_loop = AgentLoop(sub_agent_options)
    await agent_loop.run()

    answer_content: Optional[str] = None
    for message in reversed(sub_conversation.GetMessagesList()):
      for section in message.GetContentSections():
        if section.command and section.command.command_name == "answer":
          answer_content = section.command.args["answer"]
          logging.info(f"Found answer: {answer_content}")
          break
      if answer_content is not None:
        break

    if answer_content is None:
      logging.fatal("Could not retrieve answer from sub-agent.")
    assert answer_content
    return CommandOutput(
        command_name=self.Name(),
        output=answer_content,
        errors="",
        summary=f"Question '{question}' answered by sub-agent: {answer_content}",
        task_done=False,
    )
