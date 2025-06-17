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
      selections = FindPythonDefinition(self.file_access_policy, path,
                                        identifier)
      if len(selections) == 1:
        self.selection_manager.set_selection(selections[0])
        selected_lines = selections[0].Read()
        return CommandOutput(
            output=[f"select <<\n{''.join(selected_lines)}\n#end ({path})"],
            errors=[],
            summary=selections[0].ProvideSummary())

      if len(selections) > 1:
        return CommandOutput(
            output=[],
            errors=[f"Multiple definitions found for '{identifier}'."],
            summary="Multiple matches found, unable to select.")

      return CommandOutput(
          output=[],
          errors=[f"Could not find a definition for '{identifier}'."],
          summary=f"Definition for '{identifier}' not found.")

    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"select_python error: {str(e)}"],
          summary=f"Select python command encountered an error: {str(e)}")


def FindPythonDefinition(file_access_policy: FileAccessPolicy, path: str,
                         identifier: str) -> List[Selection]:
  """Finds all Python code elements by identifier and returns the selections."""
  if not file_access_policy.allow_access(path):
    raise PermissionError(f"Access to '{path}' is not allowed.")

  with open(path, "r") as file:
    lines: List[str] = file.readlines()
    file.seek(0)
    tree: ast.Module = ast.parse(file.read(), filename=path)

  selections = []
  for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
      if node.name == identifier and node.lineno is not None and node.end_lineno is not None:
        selection = Selection(path, node.lineno - 1, node.end_lineno - 1)
        selections.append(selection)

  return selections
