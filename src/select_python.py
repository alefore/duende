import ast
from typing import List
from agent_command import AgentCommand, CommandInput, CommandOutput
from file_access_policy import FileAccessPolicy
from selection_manager import Selection, SelectionManager


class SelectPythonCommand(AgentCommand):
  """Command to select Python code elements based on identifier."""

  def __init__(self, file_access_policy: FileAccessPolicy,
               selection_manager: SelectionManager) -> None:
    self.file_access_policy = file_access_policy
    self.selection_manager = selection_manager

  def Name(self) -> str:
    return "select_python"

  def GetDescription(self) -> str:
    return (
        f"#{self.Name()} <path> <identifier>: "
        "Selects the definition of the identifier in the python file (path). "
        "The identifier can be the name of a (top-level) function, the name "
        "of a class, or the name of a method. The entire definition (body) "
        "will be selected.")

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    if len(command_input.arguments) != 2:
      return CommandOutput(
          output=[],
          errors=[
              "select_python requires exactly two arguments: <path> <identifier>."
          ],
          summary="Select python command failed due to incorrect arguments.")

    path: str = command_input.arguments[0]
    identifier: str = command_input.arguments[1]

    if not self.file_access_policy.allow_access(path):
      return CommandOutput(
          output=[],
          errors=[f"Access to '{path}' is not allowed."],
          summary="Select python command access denied.")

    try:
      with open(path, "r") as file:
        lines: List[str] = file.readlines()
        file.seek(0)  # Rewind file to read from the start for parsing
        tree: ast.Module = ast.parse(file.read(), filename=path)

      # Looking for classes, functions, or methods with the given identifier
      for node in ast.walk(tree):
        if isinstance(node,
                      (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
          if node.name == identifier and node.lineno is not None and node.end_lineno is not None:
            selection = Selection(path, node.lineno - 1, node.end_lineno - 1)
            selected_lines: List[str] = selection.Read()
            self.selection_manager.set_selection(selection)
            return CommandOutput(
                output=[f"select <<\n{''.join(selected_lines)}\n#end ({path})"],
                errors=[],
                summary=f"Selected content from file {path}.")

      raise ValueError(f"Could not find a definition for '{identifier}'.")

    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"select_python error: {str(e)}"],
          summary=f"Select python command encountered an error: {str(e)}")
