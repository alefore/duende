import ast
from typing import List, Optional, Tuple, Sequence
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

  def Aliases(self) -> List[str]:
    return []

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

    identifier: str = command_input.arguments[0]
    # 'path' here is already validated by the framework due to ArgumentContentType.PATH_INPUT
    validated_path: Optional[str] = command_input.arguments[1] if len(
        command_input.arguments) > 1 else None

    try:
      selections = FindPythonDefinition(self.file_access_policy, validated_path,
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


def _find_nested_definition_nodes(
    nodes: Sequence[ast.AST], identifier_parts: List[str]
) -> List[ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef]:
  """Recursively finds AST nodes matching the identifier parts."""
  if not identifier_parts:
    return []

  current_part = identifier_parts[0]
  remaining_parts = identifier_parts[1:]
  matching_nodes: List[ast.FunctionDef | ast.AsyncFunctionDef
                       | ast.ClassDef] = []

  for node in nodes:
    # Check if the node is a definition (FunctionDef, AsyncFunctionDef, ClassDef)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
      if node.name == current_part:
        if not remaining_parts:
          # Found the final part of the identifier
          matching_nodes.append(node)
        else:
          # Look for the next part within the current node's body
          # Classes and functions have a 'body' attribute containing nested definitions
          if hasattr(node, 'body'):
            nested_matches = _find_nested_definition_nodes(
                node.body, remaining_parts)
            matching_nodes.extend(nested_matches)
  return matching_nodes


def FindPythonDefinition(file_access_policy: FileAccessPolicy,
                         validated_path: Optional[str],
                         identifier: str) -> List[Selection]:
  """Finds all Python code elements by identifier and returns the selections.

  Args:
      file_access_policy: The file access policy to use for listing files.
      validated_path: An optional path to a specific Python file, already validated
                      by the command input parsing for existence and access.
      identifier: The identifier to search for.

  Returns:
      A list of Selection objects for the found definitions.
  """
  file_list: List[str]

  if validated_path:
    file_list = [validated_path]
  else:
    file_list = [
        file for file in list_all_files(".", file_access_policy)
        if file.endswith(".py")
    ]

  selections = []
  identifier_parts = identifier.split('.')

  for file_path in file_list:
    with open(file_path, "r") as file:
      tree: ast.Module = ast.parse(file.read(), filename=file_path)

    # Start the recursive search from the top-level nodes of the AST
    found_nodes = _find_nested_definition_nodes(tree.body, identifier_parts)

    for node in found_nodes:
      if node.lineno is not None and node.end_lineno is not None:
        selections.append(
            Selection(file_path, node.lineno - 1, node.end_lineno - 1))

  return selections
