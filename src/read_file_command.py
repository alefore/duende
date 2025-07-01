from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
import logging
from typing import Any, Dict, List

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
        description="Outputs the contents of a file.",
        arguments=[
            Argument(
                name="path",
                arg_type=ArgumentContentType.PATH_INPUT,
                description="The path of the file to be read.",
                required=True)
        ])

  def run(self, inputs: Dict[str, Any]) -> CommandOutput:
    path = inputs['path']
    logging.info(f"Read: {path}")

    try:
      with open(path, "r") as f:
        contents = f.readlines()
    except Exception as e:
      return CommandOutput(
          command_name=self.Syntax().name,
          output=[],
          errors=[f"#{self.Name()} {path}: {e}"],
          summary=f"{self.Name()} command error: {path}: {e}")

    line_count = len(contents)

    output_lines = [f"#{self.Name()} {path} <<"]
    output_lines.extend(line.rstrip('\n') for line in contents)
    output_lines.append(f"#end ({path})")

    return CommandOutput(
        command_name=self.Syntax().name,
        output=output_lines,
        errors=[],
        summary=f"Read file {path} with {line_count} lines.")
