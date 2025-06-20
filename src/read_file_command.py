from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
import logging

from file_access_policy import FileAccessPolicy


class ReadFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy):
    self.file_access_policy = file_access_policy

  def Name(self) -> str:
    return "read_file"

  def GetDescription(self) -> str:
    return f"#{self.Name()} <path>: Outputs the contents of a file."

  @classmethod
  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(required=[
        Argument(
            name="path",
            arg_type=ArgumentContentType.PATH,
            description="The path of the file to be read.")
    ])

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    if len(command_input.arguments) != 1:
      return CommandOutput(
          output=[],
          errors=[
              f"{self.Name()} expects exactly one argument: the file path."
          ],
          summary=f"Failed to execute {self.Name()} command due to incorrect argument count."
      )

    path = command_input.arguments[0]
    logging.info(f"Read: {path}")

    if not self.file_access_policy.allow_access(path):
      return CommandOutput(
          output=[],
          errors=[
              f"Access to '{path}' is not allowed. Only files in the current directory (and subdirectories) can be read and must satisfy the access policy."
          ],
          summary=f"{self.Name()} command access denied.")

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
