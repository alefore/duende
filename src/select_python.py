import ast
from typing import List, Optional, Tuple
from list_files import list_all_files
from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
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

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        description=(
            "Selects the definition of an identifier in a Python file. "
            "Searches all Python files if no path is given."),
        required=[
            Argument(
                name="identifier",
                arg_type=ArgumentContentType.IDENTIFIER,
                description="The name of the identifier to be selected.")
        ],
        optional=[
            Argument(
                name="path",
                arg_type=ArgumentContentType.PATH_INPUT,
                description="Path to a specific Python file to search within.")
        ])

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    self.selection_manager.clear_selection()

    if not (1 <= len(command_input.arguments) <= 2):
      return CommandOutput(
          output=[],
          errors=[
              f"#{self.Name()} requires one or two arguments: "
              "<identifier> [path]."
          ],
          summary="Select python command failed due to incorrect arguments.")

    identifier: str = command_input.arguments[0]
    path: Optional[str] = command_input.arguments[1] if len(
        command_input.arguments) > 1 else None

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
