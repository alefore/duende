import aiofiles
import ast
import asyncio
import pathlib
from typing import Tuple, Sequence, Any

from list_files import list_all_files
from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, VariableMap, VariableName, VariableValue
from file_access_policy import FileAccessPolicy
from selection_manager import Selection, SelectionManager


class SelectPythonCommand(AgentCommand):
  """Command to select Python code elements based on identifier."""

  def __init__(self, file_access_policy: FileAccessPolicy,
               selection_manager: SelectionManager) -> None:
    self.file_access_policy = file_access_policy
    self.selection_manager = selection_manager

  def Name(self) -> str:
    return self.Syntax().name

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        name="select_python",
        description=("Selects the definition of an identifier."),
        arguments=[
            Argument(
                name=VariableName("identifier"),
                arg_type=ArgumentContentType.IDENTIFIER,
                description="The name of the identifier to be selected.",
                required=True),
            Argument(
                name=VariableName("path"),
                arg_type=ArgumentContentType.PATH_INPUT,
                description="Path to a Python file to search within. Omit this to search in all Python files.",
                required=False)
        ])

  async def run(self, inputs: VariableMap) -> CommandOutput:
    self.selection_manager.clear_selection()

    identifier: VariableValue = inputs[VariableName("identifier")]
    assert isinstance(identifier, str)
    validated_path: VariableValue | None = inputs.get(VariableName("path"))
    assert isinstance(validated_path, pathlib.Path | None)

    try:
      selections = await FindPythonDefinition(self.file_access_policy,
                                              validated_path, identifier)

      if len(selections) == 0:
        return CommandOutput(
            output="",
            errors=f"Could not find a definition for '{identifier}'.",
            summary=f"Definition for '{identifier}' not found.",
            command_name=self.Name())

      if len(selections) > 1:
        return CommandOutput(
            output="",
            errors=f"Multiple definitions found for '{identifier}'.",
            summary="Multiple matches found, unable to select.",
            command_name=self.Name())

      self.selection_manager.set_selection(selections[0])
      return CommandOutput(
          output="select <<\n" + "\n".join(await selections[0].Read()) +
          f"\n#end (selection in {selections[0].path})",
          errors="",
          summary=selections[0].ProvideSummary(),
          command_name=self.Name())

    except Exception as e:
      return CommandOutput(
          output="",
          errors=f"select_python error: {str(e)}",
          summary=f"Select python command encountered an error: {str(e)}",
          command_name=self.Name())


def _find_nested_definition_nodes(
    nodes: Sequence[ast.AST], identifier_parts: list[str]
) -> list[ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef]:
  """Recursively finds AST nodes matching the identifier parts."""
  if not identifier_parts:
    return []

  current_part = identifier_parts[0]
  remaining_parts = identifier_parts[1:]
  matching_nodes: list[ast.FunctionDef | ast.AsyncFunctionDef
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


async def FindPythonDefinition(file_access_policy: FileAccessPolicy,
                               validated_path: pathlib.Path | None,
                               identifier: str) -> list[Selection]:
  """Finds all Python code elements by identifier and returns the selections.

  Args:
      file_access_policy: The file access policy to use for listing files.
      validated_path: An optional path to a specific Python file, already validated
                      by the command input parsing for existence and access.
      identifier: The identifier to search for.

  Returns:
      A list of Selection objects for the found definitions.
  """
  file_list: list[pathlib.Path]

  if validated_path:
    file_list = [validated_path]
  else:
    file_list = []
    async for file in list_all_files(".", file_access_policy):
      if file.endswith(".py") and file_access_policy.allow_access(file):
        # TODO: Remove the pathlib.Path wrapping here.
        file_list.append(pathlib.Path(file))

  selections = []
  identifier_parts = identifier.split('.')

  for file_path in file_list:
    try:
      async with aiofiles.open(file_path,
                               "r") as file_obj:  # Renamed 'file' to 'file_obj'
        file_content = await file_obj.read()
      tree: ast.Module = ast.parse(file_content, filename=file_path)

      # Start the recursive search from the top-level nodes of the AST
      found_nodes = _find_nested_definition_nodes(tree.body, identifier_parts)

      for node in found_nodes:
        if node.lineno is not None and node.end_lineno is not None:
          selections.append(
              Selection(str(file_path), node.lineno - 1, node.end_lineno - 1))
    except Exception as e:
      # Log error or add to a list of errors if file cannot be parsed
      # For now, just continue to the next file
      print(f"Error parsing {file_path}: {e}")
      continue

  return selections
