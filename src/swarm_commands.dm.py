import dataclasses
import datetime
import pathlib

from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, REASON_VARIABLE, VariableMap, VariableName, VariableValueInt
from conversation import ConversationId
from file_access_policy import FileAccessPolicy
from message_bus import Message as BusMessage, END_USER_AGENT, MessageBus, MessageContent, MessageId, TelegramChatId, TelegramMessageId
from message_queue import AgentMessageQueue
from pathbox import PathBox
from swarm_types import AgentName

_TARGET_AGENT_ARGUMENT = Argument(
    name=VariableName("target_agent"),
    arg_type=ArgumentContentType.STRING,
    description="The name of the agent that should consume the message.",
    required=True)

_CONTENT_ARGUMENT = Argument(
    name=VariableName("content"),
    arg_type=ArgumentContentType.STRING,
    description="The content to send to the user.",
    required=True)


class DisplayInfoCommand(AgentCommand):

  def __init__(self, message_bus: MessageBus, conversation_id: ConversationId,
               telegram_chat_id: TelegramChatId,
               telegram_reply_to_id: TelegramMessageId,
               source_agent: AgentName) -> None:
    raise NotImplementedError()  # {{🍄 display info store private fields}}

  def Name(self) -> str:
    return self.Syntax().name

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="display_info",
        description="Displays information to the user.",
        arguments=[REASON_VARIABLE, _CONTENT_ARGUMENT])

  async def run(self, inputs: VariableMap) -> CommandOutput:
    """Call write_new_message with a new message.

    {{🦔 target_agent is set to the value in `END_USER_AGENT`.}}
    """
    raise NotImplementedError()  # {{🍄 display info run}}


@dataclasses.dataclass(frozen=True)
class PublishMessageConfig:
  allow_list: frozenset[AgentName]


# publish_message set's the children's agent `local_directory` to the cwd of the
# parent.
class PublishMessageCommand(AgentCommand):

  def __init__(self, config: PublishMessageConfig, message_bus: MessageBus,
               cwd: PathBox, telegram_chat_id: TelegramChatId,
               telegram_reply_to_id: TelegramMessageId,
               source_agent: AgentName) -> None:
    raise NotImplementedError()  # {{🍄 publish message store private fields}}

  def Name(self) -> str:
    return self.Syntax().name

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="publish_message",
        description="Publishes a new message into the message bus. "
        "The message will be consumed by an agent.",
        arguments=[REASON_VARIABLE, _TARGET_AGENT_ARGUMENT, _CONTENT_ARGUMENT])

  async def run(self, inputs: VariableMap) -> CommandOutput:
    """Call write_new_message with a new message.

    {{🦔 The message's target_agent is always set.}}
    {{🦔 If self._cwd is not '.', the message's local_directory is set
         accordingly (otherwise is None).}}
    {{🦔 Returns an error `CommandOutput` if the target agent is missing from
         `config.allow_list`.}}
    """
    raise NotImplementedError()  # {{🍄 publish message run}}


class AskUserCommand(AgentCommand):

  def __init__(self, message_bus: MessageBus, queue: AgentMessageQueue,
               conversation_id: ConversationId,
               telegram_chat_id: TelegramChatId,
               telegram_reply_to_id: TelegramMessageId,
               source_agent: AgentName) -> None:
    raise NotImplementedError()  # {{🍄 ask user store private fields}}

  def Name(self) -> str:
    return self.Syntax().name

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="ask_user",
        description="Sends a message to the user and waits for a response.",
        arguments=[
            REASON_VARIABLE,
            Argument(
                name=VariableName("question"),
                arg_type=ArgumentContentType.STRING,
                description="The content of the question to send to the user.",
                required=True),
        ])

  async def run(self, inputs: VariableMap) -> CommandOutput:
    """Waits until self._queue has messages and returns them.

    {{🦔 The CommandOutput.output is set to a str containing all the messages
         read from the queue.}}
    """
    raise NotImplementedError()  # {{🍄 ask user run}}


@dataclasses.dataclass(frozen=True)
class DelegateRequestConfig:
  allow_list: frozenset[AgentName]


# delegate_request does not allow the agent to change the `local_directory`.
# Whatever value the parent had, the child will have.
class DelegateRequestCommand(AgentCommand):

  def __init__(self, config: DelegateRequestConfig, message_bus: MessageBus,
               local_directory: pathlib.Path | None,
               telegram_chat_id: TelegramChatId,
               telegram_reply_to_id: TelegramMessageId, source_agent: AgentName,
               user_request: MessageContent) -> None:
    raise NotImplementedError()  # {{🍄 delegate request store private fields}}

  def Name(self) -> str:
    return self.Syntax().name

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="delegate_request",
        description="Forwards the user request to another agent and terminates the session.",
        arguments=[REASON_VARIABLE, _TARGET_AGENT_ARGUMENT])

  async def run(self, inputs: VariableMap) -> CommandOutput:
    """Call write_new_message with a new message with self._user_request.

    {{🦔 Returns an error `CommandOutput` if the target agent is missing from
         `config.allow_list`.}}
    {{🦔 The message's `target_agent` is always set.}}
    {{🦔 The returned value has `task_done = True`.}}
    {{🦔 The message's local_directory is set to `self._local_directory`.}}
    """
    raise NotImplementedError()  # {{🍄 delegate request run}}
