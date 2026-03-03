from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, REASON_VARIABLE, VariableMap, VariableName, VariableValueInt
from file_access_policy import FileAccessPolicy
from message_bus import Message as BusMessage, MessageBus, MessageId, SenderName, SessionId, write_new_message


class DisplayInfoCommand(AgentCommand):

  def __init__(self, message_bus: MessageBus, sender: SenderName,
               session_id: SessionId) -> None:
    raise NotImplementedError()  # {{🍄 store private fields}}

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
                name=VariableName("message"),
                arg_type=ArgumentContentType.STRING,
                description="The message to send to the user.",
                required=True),
        ])

  async def run(self, inputs: VariableMap) -> CommandOutput:
    """Call write_new_message with a new message.

    {{🦔 The message's recipient is None.}}
    """
    raise NotImplementedError()  # {{🍄 provide confirmation}}
