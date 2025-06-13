from agent_command import AgentCommand, CommandInput
from typing import List
import sys


class NotifyCommand(AgentCommand):

  def GetDescription(self) -> str:
    return "#notify <message>: Sends a note to the human operator. Use this to explain reasoning, ask for help, or request a manual action. Use `#notify << \n multi-line-content \n #end` for multiple lines."

  def Execute(self, command_input: CommandInput) -> str:
    if not command_input.arguments and not command_input.multiline_content:
      return "Error: #notify requires a message."

    message_parts: List[str] = []
    if command_input.arguments:
      message_parts.append(" ".join(command_input.arguments))
    if command_input.multiline_content:
      message_parts += command_input.multiline_content

    message: str = "\n".join(message_parts)
    print(message, file=sys.stderr)
    return "#notify: Human operator has been notified."
