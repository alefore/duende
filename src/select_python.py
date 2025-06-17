import ast
from typing import List, Optional, Tuple
from list_files import list_all_files
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
              f"#{self.Name()} requires exactly two arguments: "
              "<path> <identifier>."
          ],
          summary="Select python command failed due to incorrect arguments.")

    path: str = command_input.arguments[0]
    identifier: str = command_input.arguments[1]

    try:
      selections = FindPythonDefinition(self.file_access_policy, path,
                                        identifier)
      if len(selections) == 0:
        return CommandOutput(
            output=[],
            errors=[f"Could not find a definition for '{identifier}'."],
            summary=f"Definition for '{identifier}' not found.")

      if len(selections) > 1:
        return CommandOutput(
            output=[],
            errors=[f"Multiple definitions found for '{identifier}'."],
            summary="Multiple matches found, unable to select.")

      self.selection_manager.set_selection(selections[0])
      selected_lines = selections[0].Read()
      return CommandOutput(
          output=[f"select <<"] + selections[0].Read() +
          [f"#end (selection in {selections[0].path})"],
          errors=[],
          summary=selections[0].ProvideSummary())

    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"select_python error: {str(e)}"],
          summary=f"Select python command encountered an error: {str(e)}")


def FindPythonDefinition(file_access_policy: FileAccessPolicy,
                         path: Optional[str],
                         identifier: str) -> List[Selection]:
  """Finds all Python code elements by identifier and returns the selections."""
  file_list: List[str]

  if path:
    if not file_access_policy.allow_access(path):
      raise PermissionError(f"Access to '{path}' is not allowed.")
    file_list = [path]
  else:
    file_list = [
        file for file in list_all_files(".", file_access_policy)
        if file.endswith(".py")
    ]

  selections = []

  for file_path in file_list:
    with open(file_path, "r") as file:
      tree: ast.Module = ast.parse(file.read(), filename=file_path)

    for node in ast.walk(tree):
      if isinstance(node,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if node.name == identifier and node.lineno is not None and node.end_lineno is not None:
          selections.append(
              Selection(file_path, node.lineno - 1, node.end_lineno - 1))

  return selections
