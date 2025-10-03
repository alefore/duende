import logging
from typing import Any
import aiofiles

from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, VariableName
from file_access_policy import FileAccessPolicy


class ReadFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy):
    self.file_access_policy = file_access_policy

  def Name(self) -> str:
    return self.Syntax().name

  @classmethod
  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="read_file",
        description="Outputs the contents of a file. It can optionally read specific lines.",
        arguments=[
            Argument(
                name=VariableName("path"),
                arg_type=ArgumentContentType.PATH_INPUT,
                description="The path of the file to be read.",
                required=True),
            Argument(
                name=VariableName("start_line"),
                arg_type=ArgumentContentType.INTEGER,
                description="The starting line number (inclusive) to read from.",
                required=False),
            Argument(
                name=VariableName("end_line"),
                arg_type=ArgumentContentType.INTEGER,
                description="The ending line number (inclusive) to read up to.",
                required=False)
        ])

  async def run(self, inputs: dict[VariableName, Any]) -> CommandOutput:
    path = inputs[VariableName("path")]
    start_line = inputs.get(VariableName("start_line"))
    end_line = inputs.get(VariableName("end_line"))

    if start_line is not None and start_line < 1:
      return CommandOutput(
          command_name=self.Syntax().name,
          output="",
          errors=f"#{self.Name()} {path}: start_line must be a positive integer.",
          summary=f"{self.Name()} command error: start_line must be a positive integer."
      )

    if end_line is not None and end_line < 1:
      return CommandOutput(
          command_name=self.Syntax().name,
          output="",
          errors=f"#{self.Name()} {path}: end_line must be a positive integer.",
          summary=f"{self.Name()} command error: end_line must be a positive integer."
      )

    if start_line is not None and end_line is not None and start_line > end_line:
      return CommandOutput(
          command_name=self.Syntax().name,
          output="",
          errors=f"#{self.Name()} {path}: start_line ({start_line}) cannot be greater than end_line ({end_line}).",
          summary=f"{self.Name()} command error: start_line cannot be greater than end_line."
      )

    logging.info(f"Read: {path=}, {start_line=}, {end_line=}")

    try:
      async with aiofiles.open(path, mode="r") as f:
        lines = await f.readlines()

        # Adjust for 0-based indexing if start_line is provided
        # If start_line is 1, it means index 0. So, start_index = start_line - 1
        start_index = 0 if start_line is None else start_line - 1

        # If end_line is 1, it means index 0 (and only that line). So end_index = end_line
        end_index = len(lines) if end_line is None else end_line

        if start_index >= len(lines):
          return CommandOutput(
              command_name=self.Syntax().name,
              output="",
              errors=f"#{self.Name()} {path}: start_line {start_line} is beyond the file's {len(lines)} lines.",
              summary=f"{self.Name()} command error: start_line out of bounds.")
        if end_index > len(lines):
          # If end_line is specified and beyond file length, read till end of file
          end_index = len(lines)

        contents = "".join(lines[start_index:end_index])
        actual_lines_read = len(lines[start_index:end_index])

    except Exception as e:
      return CommandOutput(
          command_name=self.Syntax().name,
          output="",
          errors=f"#{self.Name()} {path}: {e}",
          summary=f"{self.Name()} command error: {path}: {e}")

    summary_msg = f"Read file {path}"
    if start_line is not None and end_line is not None:
      summary_msg += f" from line {start_line} to {end_line}."
    elif start_line is not None:
      summary_msg += f" from line {start_line}."
    elif end_line is not None:
      summary_msg += f" up to line {end_line}."
    else:
      summary_msg += f" entirely."

    summary_msg += f" ({actual_lines_read} lines)."

    return CommandOutput(
        command_name=self.Syntax().name,
        output=contents,
        errors="",
        summary=summary_msg)
