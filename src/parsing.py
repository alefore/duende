from typing import List, Optional, Tuple
import shlex
from agent_command import CommandInput


def ExtractCommands(response: str) -> Tuple[List[CommandInput], List[str]]:
  """
    Parses commands from a ChatGPT response and also collects non-command lines.
    """
  lines = response.splitlines()
  commands: List[CommandInput] = []
  non_command_lines: List[str] = []
  current_input: Optional[CommandInput] = None

  for line in lines:
    if current_input is not None:
      if line.strip() == "#end":
        commands.append(current_input)
        current_input = None
      else:
        assert current_input.multiline_content is not None
        current_input.multiline_content.append(line)
      continue

    line = line.strip()
    if line.startswith("#"):
      parts = line[1:].split(maxsplit=1)
      cmd = parts[0].rstrip(':')

      if len(parts) > 1:
        # Single-line command with arguments
        try:
          args = shlex.split(parts[1])
          if args[-1] == "<<":
            current_input = CommandInput(
                command_name=cmd, arguments=args[:-1], multiline_content=[])
          else:
            commands.append(CommandInput(command_name=cmd, arguments=args))
        except ValueError:
          # If shlex throws, treat the whole line as a single argument
          commands.append(CommandInput(command_name=cmd, arguments=[parts[1]]))
      else:
        # Single-line command with no arguments
        commands.append(CommandInput(command_name=cmd, arguments=[]))
    else:
      non_command_lines.append(line)

  if current_input:
    assert current_input.multiline_content is not None
    commands.append(current_input)

  return commands, non_command_lines
