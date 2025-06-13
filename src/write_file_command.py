from typing import List

from agent_command import AgentCommand, CommandInput
import logging
from file_access_policy import FileAccessPolicy

# TODO: We should implement a new command that can modify only parts of files.
# Often the ai just wants to modify one or two small sections in a large file,
# so there should be a better way than having to rewrite the whole file. This
# requires coming up with the ideal "language" for the AI to express the types
# of modifications it wants to apply and implement it. One option would be a
# "patch" command, but I'm not sure (it may be tricky for the ai to get the line
# offests right, no?). Ideally it would be something very expressive like
# "rewrite function MyClass.MethodFoo in file agent_bar.py << ... contents" but
# that would require us to implement the parser for python files, which may be
# tricky. Consider whether you can come up with a generic approach for various
# text-oriented formats (e.g., c++, Java, Python…) or, if you prefer, implement
# something specific to Python.


class WriteFileCommand(AgentCommand):

  def __init__(self, file_access_policy: FileAccessPolicy):
    self.file_access_policy = file_access_policy

  def GetDescription(self) -> str:
    return "#write path << … multi-line-content … #end: Writes the given content to a specified file. Creates the file if it does not exist."

  def Execute(self, command_input: CommandInput) -> str:
    if len(command_input.arguments) != 1 or not command_input.multiline_content:
      return (
          f"Error: {command_input.command_name} expects exactly one argument: "
          "the file path and requires content.")

    path = command_input.arguments[0]
    content: List[str] = command_input.multiline_content
    logging.info(f"Write: {path}")

    if not self.file_access_policy.allow_access(path):
      return (f"Error: Access to '{path}' is not allowed. "
              "Only files in the current directory (and subdirectories) "
              "can be written to and must satisfy the access policy.")

    try:
      with open(path, "w") as f:
        f.write("\n".join(content))
      return f"#{command_input.command_name} {path}: Success."
    except Exception as e:
      return f"Error writing to {path}: {str(e)}"
