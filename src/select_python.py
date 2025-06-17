import ast
from typing import List, Optional, Tuple
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
    self.selection_manager.clear_selection()

    if len(command_input.arguments) != 2:
      return CommandOutput(
          output=[],
          errors=[
              "select_python requires exactly two arguments: <path> <identifier>."
          ],
          summary="Select python command failed due to incorrect arguments.")

    path: str = command_input.arguments[0]
    identifier: str = command_input.arguments[1]

    try:
      selection, selected_lines = find_python_definition(
          self.file_access_policy, path, identifier)
      if selection is not None:
        self.selection_manager.set_selection(selection)
        return CommandOutput(
            output=[f"select <<\n{''.join(selected_lines)}\n#end ({path})"],
            errors=[],
            summary=selection.ProvideSummary())

      return CommandOutput(
          output=[],
          errors=[f"Could not find a definition for '{identifier}'."],
          summary=f"Definition for '{identifier}' not found.")

    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"select_python error: {str(e)}"],
          summary=f"Select python command encountered an error: {str(e)}")


def find_python_definition(
    file_access_policy: FileAccessPolicy, path: str,
    identifier: str) -> Tuple[Optional[Selection], List[str]]:
  """Finds the Python code element by identifier and returns the selection and lines."""
  if not file_access_policy.allow_access(path):
    raise PermissionError(f"Access to '{path}' is not allowed.")

  with open(path, "r") as file:
    lines: List[str] = file.readlines()
    file.seek(0)  # Rewind file to read from the start for parsing
    tree: ast.Module = ast.parse(file.read(), filename=path)

  # Looking for classes, functions, or methods with the given identifier
  for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
      if node.name == identifier and node.lineno is not None and node.end_lineno is not None:
        selection = Selection(path, node.lineno - 1, node.end_lineno - 1)
        return selection, lines[selection.start_index:selection.end_index + 1]

  return None, []
