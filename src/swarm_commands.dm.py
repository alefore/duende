import datetime

from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, REASON_VARIABLE, VariableMap, VariableName, VariableValueInt
from conversation import ConversationId
from file_access_policy import FileAccessPolicy
from message_bus import Message as BusMessage, END_USER_AGENT, MessageBus, MessageId, TelegramChatId, TelegramMessageId
from message_queue import AgentMessageQueue
from swarm_types import AgentName


class DisplayInfoCommand(AgentCommand):

  def __init__(self, message_bus: MessageBus, conversation_id: ConversationId,
               telegram_chat_id: TelegramChatId,
               telegram_reply_to_id: TelegramMessageId,
               source_agent: AgentName) -> None:
    raise NotImplementedError()  # {{🍄 display info store private fields}}

  def Name(self) -> str:
    return self.Syntax().name

  @classmethod
  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="display_info",
        description="Displays information to the user.",
        arguments=[
            REASON_VARIABLE,
            Argument(
                name=VariableName("content"),
                arg_type=ArgumentContentType.STRING,
                description="The content to send to the user.",
                required=True),
        ])

  async def run(self, inputs: VariableMap) -> CommandOutput:
    """Call write_new_message with a new message.

    {{🦔 target_agent is set to the value in `END_USER_AGENT`.}}
    """
    raise NotImplementedError()  # {{🍄 display info run}}


class PublishMessageCommand(AgentCommand):

  def __init__(self, message_bus: MessageBus, conversation_id: ConversationId,
               telegram_chat_id: TelegramChatId,
               telegram_reply_to_id: TelegramMessageId,
               source_agent: AgentName) -> None:
    raise NotImplementedError()  # {{🍄 publish message store private fields}}

  def Name(self) -> str:
    return self.Syntax().name

  @classmethod
  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="publish_message",
        description="Publishes a new message into the message bus. "
        "The message will be consumed by an agent.",
        arguments=[
            REASON_VARIABLE,
            Argument(
                name=VariableName("content"),
                arg_type=ArgumentContentType.STRING,
                description="The content of the message to publish.",
                required=True),
            Argument(
                name=VariableName("target_agent"),
                arg_type=ArgumentContentType.STRING,
                description="The name of the agent that should consume the message."
            )
        ])

  async def run(self, inputs: VariableMap) -> CommandOutput:
    """Call write_new_message with a new message.

    {{🦔 The message's recipient is always set.}}
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

  @classmethod
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
