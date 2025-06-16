from agent_command import AgentCommand, CommandInput, CommandOutput
import logging

from file_access_policy import FileAccessPolicy


class ReadFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy):
    self.file_access_policy = file_access_policy

  def GetDescription(self) -> str:
    return "read <path>: Outputs the contents of a file under the current directory. Rejects paths outside this tree."

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    if len(command_input.arguments) != 1:
      return CommandOutput(
          output=[],
          errors=[
              f"{command_input.command_name} expects exactly one argument: the file path."
          ],
          summary="Failed to execute read command due to incorrect argument count."
      )

    path = command_input.arguments[0]
    logging.info(f"Read: {path}")

    if not self.file_access_policy.allow_access(path):
      return CommandOutput(
          output=[],
          errors=[
              f"Access to '{path}' is not allowed. Only files in the current directory (and subdirectories) can be read and must satisfy the access policy."
          ],
          summary="Read command access denied.")

    try:
      with open(path, "r") as f:
        contents = f.readlines()
        line_count = len(contents)
        return CommandOutput(
            output=[
                f"#{command_input.command_name} {path} <<\n{''.join(contents)}\n#end ({path})"
            ],
            errors=[],
            summary=f"Read file {path} with {line_count} lines.")
    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"#read {path}: {e}"],
          summary=f"Read command error: {path}: {e}")
