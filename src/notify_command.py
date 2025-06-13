from agent_command import AgentCommand, CommandInput
import sys


class NotifyCommand(AgentCommand):

  def GetDescription(self) -> str:
    return "#notify <message>: Sends a note to the human operator. Use this to explain reasoning, ask for help, or request a manual action. Use `#notify << \n multi-line-content \n #end` for multiple lines."

  def Execute(self, command_input: CommandInput) -> str:
    if not command_input.arguments and not command_input.multiline_content:
      return "Error: #notify requires a message."
    # TODO: If notify is given both arguments and multiline_content, display
    # both (perhaps the args are pre-pended as a single line before the
    # multiline_content.
    message = (
        command_input.multiline_content if command_input.multiline_content
        is not None else " ".join(command_input.arguments))
    print(message, file=sys.stderr)
    return "#notify: Human operator has been notified."
