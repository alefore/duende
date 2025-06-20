from typing import List, Optional
from agent_command import AgentCommand, CommandInput, CommandOutput, CommandSyntax, Argument, ArgumentContentType, ArgumentMultiline
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
    return "replace_python"

  def GetDescription(self) -> str:
    return (
        f"#{self.Name()} <identifier> [path] <<\n"
        "new definition line 0\n"
        "line 1\n"
        "...\n"
        "#end\n"
        "  Replaces the definition of the identifier in the specified Python file.\n"
        "  Searches in all Python files if no path is provided.\n"
        "  The identifier can be the name of a (top-level) function, class, or method."
    )

  @classmethod
  def Syntax(cls) -> CommandSyntax:
    return CommandSyntax(
        required=[
            Argument(
                name="identifier",
                arg_type=ArgumentContentType.IDENTIFIER,
                description="The identifier of the Python element to replace."),
        ],
        optional=[
            Argument(
                name="path",
                arg_type=ArgumentContentType.PATH,
                description="Path to a Python file."),
        ],
        multiline=ArgumentMultiline(
            required=True,
            description="The new definition of the Python element."))

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    if len(command_input.arguments) < 1 or len(command_input.arguments) > 2:
      return CommandOutput([], [
          "replace_python requires one or two arguments: <identifier> [path]."
      ], "Invalid arguments for replace_python command.")

    if command_input.multiline_content is None:
      return CommandOutput([], [
          "replace_python requires multiline-content. For example:",
          "#{self.name} ReadPassword <<", "new definition line 0", "line 1",
          "line 2", "...", "#end"
      ], "Replacement content missing.")

    identifier: str = command_input.arguments[0]
    path: Optional[str] = command_input.arguments[1] if len(
        command_input.arguments) == 2 else None
    matches: List[Selection] = FindPythonDefinition(self.file_access_policy,
                                                    path, identifier)

    if len(matches) == 0:
      return CommandOutput([],
                           [f"No matches found for identifier '{identifier}'."],
                           "No matches found.")
    if len(matches) > 1:
      locations = [
          f"{s.path}:{s.start_index + 1} to {s.end_index + 1}" for s in matches
      ]
      return CommandOutput(
          [], [f"Multiple matches found for identifier '{identifier}':"] +
          locations + ["#end (matches)"], "Multiple matches found.")

    matches[0].Overwrite(command_input.multiline_content)

    if self.validation_manager:
      self.validation_manager.RegisterChange()

    return CommandOutput(["The definition was successfully replaced."], [],
                         "Replacement successful.")
