from agent_command import AgentCommand, CommandInput
import logging
from file_access_policy import FileAccessPolicy


class ReadFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy):
    self.file_access_policy = file_access_policy

  def GetDescription(self) -> str:
    return "read <path>: Outputs the contents of a file under the current directory. Rejects paths outside this tree."

  def Execute(self, command_input: CommandInput) -> str:
    if len(command_input.arguments) != 1:
      # TODO: Use command_input.command_name in the error message (rather than
      # hard-coding "read").
      return "Error: read expects exactly one argument: the file path."
    path = command_input.arguments[0]
    logging.info(f"Read: {path}")

    if not self.file_access_policy.allow_access(path):
      return (f"Error: Access to '{path}' is not allowed. "
              "Only files in the current directory (and subdirectories) "
              "can be read and must satisfy the access policy.")

    try:
      with open(path, "r") as f:
        contents = f.read()
        return f"#read {path} <<\n{contents}\n#end ({path})"
    except FileNotFoundError:
      return f"Error: File not found: {path}"
    except Exception as e:
      return f"Error: #read {path}: {e}"
