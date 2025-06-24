from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
import logging

from file_access_policy import FileAccessPolicy


class ReadFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy):
    self.file_access_policy = file_access_policy

  def Name(self) -> str:
    return "read_file"

  @classmethod
  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        description="Outputs the contents of a file.",
        required=[
            Argument(
                name="path",
                arg_type=ArgumentContentType.PATH_INPUT,
                description="The path of the file to be read.")
        ])

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    path = command_input.arguments[0]
    logging.info(f"Read: {path}")

    try:
      with open(path, "r") as f:
        contents = f.readlines()
        line_count = len(contents)
        return CommandOutput(
            output=[
                f"#{self.Name()} {path} <<\n{''.join(contents)}\n#end ({path})"
            ],
            errors=[],
            summary=f"Read file {path} with {line_count} lines.")
    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"#{self.Name()} {path}: {e}"],
          summary=f"{self.Name()} command error: {path}: {e}")
