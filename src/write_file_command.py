from agent_command import AgentCommand, CommandInput
import logging
from file_access_policy import FileAccessPolicy


class WriteFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy):
    self.file_access_policy = file_access_policy

  def GetDescription(self) -> str:
    return "#write path << … multi-line-content … #end: Writes the given content to a specified file. Creates the file if it does not exist."

  def Execute(self, command_input: CommandInput) -> str:
    if len(command_input.arguments) != 1 or not command_input.multiline_content:
      # TODO: Use command_input.command_name in the error message (rather than
      # hard-coding "write").
      return "Error: write expects exactly one argument: the file path and requires content."

    path = command_input.arguments[0]
    content = command_input.multiline_content
    logging.info(f"Write: {path}")

    if not self.file_access_policy.allow_access(path):
      return (f"Error: Access to '{path}' is not allowed. "
              "Only files in the current directory (and subdirectories) "
              "can be written to and must satisfy the access policy.")

    try:
      with open(path, "w") as f:
        f.write(content)
      return f"#write {path}: Success."
    except Exception as e:
      return f"Error writing to {path}: {str(e)}"
