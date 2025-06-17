from typing import List, Optional, Tuple
import shlex
from agent_command import CommandInput
import re


def _GetArgs(args_str: str) -> List[str]:
  try:
    return shlex.split(args_str)
  except ValueError:
    # If shlex throws, treat the whole line as a single argument
    return [args_str.strip()]


def ExtractCommands(response: str) -> Tuple[List[CommandInput], List[str]]:
  """
    Parses commands from a ChatGPT response and also collects non-command lines.
    """
  lines = response.splitlines()
  commands: List[CommandInput] = []
  non_command_lines: List[str] = []
  multiline_command: Optional[CommandInput] = None
  end_marker: Optional[str] = None

  multi_line_folded_pattern = re.compile(r".* <<\\n(.*\\n)*#end *$")

  for line in lines:
    if multiline_command is not None:
      # We are receiving multiline-content.
      if line.strip() == end_marker:
        # We reached the end. Flush the command and reset the state.
        commands.append(multiline_command)
        multiline_command = None
        end_marker = None
      else:
        assert multiline_command.multiline_content is not None
        multiline_command.multiline_content.append(line)
      continue

    line = line.strip()
    if not line.startswith("#"):
      non_command_lines.append(line)
      continue

    parts = line[1:].split(maxsplit=1)
    cmd = parts[0].rstrip(':')

    if len(parts) <= 1:
      # No arguments, handle it directly.
      commands.append(CommandInput(command_name=cmd, arguments=[]))
      continue

    args_str: str = parts[1]
    if multi_line_folded_pattern.fullmatch(args_str):
      # The AI sometimes stupidly thinks it should use "backslash n" (i.e.,
      # '\\n') rather than newline characters (i.e., '\n') and will send a
      # whole block in a single line. Rather than try to get the AI to
      # understand that this is wrong… let's just accept it.
      start_marker_pos: int = args_str.index(' <<\\n')
      end_marker_pos: int = args_str.rindex('\\n#end')
      content = args_str[start_marker_pos + 5:end_marker_pos].split('\\n')
      commands.append(
          CommandInput(
              command_name=cmd,
              arguments=_GetArgs(args_str[:start_marker_pos]),
              multiline_content=content))
      continue

    args = _GetArgs(args_str)
    if not args[-1].startswith("<<") or args[-1].startswith("<<\\n"):
      commands.append(CommandInput(command_name=cmd, arguments=args))
      continue

    # Activate multiline mode.
    multiline_command = CommandInput(
        command_name=cmd, arguments=args[:-1], multiline_content=[])
    end_marker = args[-1][2:] or "#end"

  if multiline_command:
    assert multiline_command.multiline_content is not None
    commands.append(multiline_command)

  return commands, non_command_lines
