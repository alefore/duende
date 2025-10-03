from typing import List, Dict, Any
from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, VariableName
from validation import ValidationManager
from file_access_policy import FileAccessPolicy
from select_python import FindPythonDefinition
from selection_manager import Selection


class ReplacePythonCommand(AgentCommand):
  """Command to replace a Python code element based on an identifier."""

  def __init__(self, file_access_policy: FileAccessPolicy,
               validation_manager: ValidationManager | None) -> None:
    self.file_access_policy = file_access_policy
    self.validation_manager = validation_manager

  def Name(self) -> str:
    return self.Syntax().name

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        name="replace_python",
        description="Replaces the definition of the identifier in the specified Python file. Searches in all Python files if no path is provided. The identifier can be the name of a (top-level) function, class (example: `MyClass`), or method (example: `MyClass.__init__`).",
        arguments=[
            Argument(
                name=VariableName("identifier"),
                arg_type=ArgumentContentType.IDENTIFIER,
                description="The identifier of the Python element to replace.",
                required=True),
            Argument(
                name=VariableName("path"),
                arg_type=ArgumentContentType.PATH_INPUT_OUTPUT,
                description="Path to a Python file.",
                required=False),
            Argument(
                name=VariableName("content"),
                arg_type=ArgumentContentType.STRING,
                description="The new definition of the Python element.",
                required=True),
            Argument(
                name=VariableName("reason"),
                arg_type=ArgumentContentType.STRING,
                description="Brief (one or two sentences) explanation of why you are issuing this command (what you want to accomplish).",
                required=False)
        ])

  async def run(self, inputs: Dict[VariableName, Any]) -> CommandOutput:
    identifier: str = inputs[VariableName("identifier")]
    new_content: str = inputs[VariableName("content")]
    validated_path: str | None = inputs.get(VariableName("path"))

    try:
      selections: List[Selection] = await FindPythonDefinition(
          self.file_access_policy, validated_path, identifier)
    except Exception as e:
      return CommandOutput(
          output="",
          errors=f"{self.Name()} error: {str(e)}",
          summary=f"{self.Name()} error: {str(e)}",
          command_name=self.Name())

    if len(selections) == 0:
      return CommandOutput(
          command_name=self.Name(),
          output="",
          errors=f"No matches found for identifier '{identifier}'.",
          summary="No matches found.")
    if len(selections) > 1:
      locations = [
          f"{s.path}:{s.start_index + 1} to {s.end_index + 1}"
          for s in selections
      ]
      return CommandOutput(
          command_name=self.Name(),
          output="",
          errors="\n".join(
              [f"Multiple matches found for identifier '{identifier}':"] +
              locations + ["#end (matches)"]),
          summary="Multiple matches found.")

    await selections[0].Overwrite(new_content)

    if self.validation_manager:
      self.validation_manager.RegisterChange()

    return CommandOutput(
        command_name=self.Name(),
        output="The definition was successfully replaced.",
        errors="",
        summary="Replacement successful.")
