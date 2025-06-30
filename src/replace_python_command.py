from typing import List, Optional, Dict, Any
from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType
from validation import ValidationManager
from file_access_policy import FileAccessPolicy
from select_python import FindPythonDefinition
from selection_manager import Selection


class ReplacePythonCommand(AgentCommand):
  """Command to replace a Python code element based on an identifier."""

  def __init__(self, file_access_policy: FileAccessPolicy,
               validation_manager: Optional[ValidationManager]) -> None:
    self.file_access_policy = file_access_policy
    self.validation_manager = validation_manager

  def Name(self) -> str:
    return self.Syntax().name

  def Aliases(self) -> List[str]:
    return []

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        name="replace_python",
        description="Replaces the definition of the identifier in the specified Python file. Searches in all Python files if no path is provided. The identifier can be the name of a (top-level) function, class (example: `MyClass`), or method (example: `MyClass.__init__`).",
        arguments=[
            Argument(
                name="identifier",
                arg_type=ArgumentContentType.IDENTIFIER,
                description="The identifier of the Python element to replace.",
                required=True),
            Argument(
                name="path",
                arg_type=ArgumentContentType.PATH_INPUT_OUTPUT,
                description="Path to a Python file.",
                required=False),
            Argument(
                name="content",
                arg_type=ArgumentContentType.STRING,
                description="The new definition of the Python element.",
                required=True)
        ])

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    assert False

  def run(self, inputs: Dict[str, Any]) -> CommandOutput:
    identifier: str = inputs['identifier']
    new_content: str = inputs['content']
    validated_path: Optional[str] = inputs.get('path')

    try:
      selections: List[Selection] = FindPythonDefinition(
          self.file_access_policy, validated_path, identifier)
    except Exception as e:
      return CommandOutput(
          output=[],
          errors=[f"{self.Name()} error: {str(e)}"],
          summary=f"{self.Name()} error: {str(e)}",
          command_name=self.Name())

    if len(selections) == 0:
      return CommandOutput([],
                           [f"No matches found for identifier '{identifier}'."],
                           "No matches found.",
                           command_name=self.Name())
    if len(selections) > 1:
      locations = [
          f"{s.path}:{s.start_index + 1} to {s.end_index + 1}"
          for s in selections
      ]
      return CommandOutput(
          [], [f"Multiple matches found for identifier '{identifier}':"] +
          locations + ["#end (matches)"],
          "Multiple matches found.",
          command_name=self.Name())

    # TODO: Change Overwrite to take a `str` rather than a `list[str]`.
    selections[0].Overwrite(new_content.splitlines())

    if self.validation_manager:
      self.validation_manager.RegisterChange()

    return CommandOutput(["The definition was successfully replaced."], [],
                         "Replacement successful.",
                         command_name=self.Name())
