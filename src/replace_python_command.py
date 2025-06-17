from typing import List
from agent_command import AgentCommand, CommandInput, CommandOutput
from file_access_policy import FileAccessPolicy
from list_files import list_all_files
from select_python import FindPythonDefinition


class ReplacePythonCommand(AgentCommand):
  """Command to replace a Python code element based on an identifier."""

  def __init__(self, file_access_policy: FileAccessPolicy) -> None:
    self.file_access_policy = file_access_policy

  def Name(self) -> str:
    return "replace_python"

  def GetDescription(self) -> str:
    return (
        f"#{self.Name()} <identifier> [path]: Replaces the definition of the identifier in the specified Python file. Searches in all Python files if no path is provided."
    )

  def Execute(self, command_input: CommandInput) -> CommandOutput:
    if len(command_input.arguments) < 1 or len(command_input.arguments) > 2:
      return CommandOutput([], [
          "replace_python requires one or two arguments: <identifier> [path]."
      ], "Invalid arguments for replace_python command.")

    identifier = command_input.arguments[0]
    path = command_input.arguments[1] if len(
        command_input.arguments) == 2 else None
    file_list: List[str] = []

    # Determine the relevant files
    if path:
      if not self.file_access_policy.allow_access(path):
        return CommandOutput([], [f"Access to '{path}' is not allowed."],
                             "File access denied.")
      file_list = [path]
    else:
      # List all .py files
      file_list = [
          file for file in list_all_files(".", self.file_access_policy)
          if file.endswith(".py")
      ]

    matches = []

    # Search for identifier in each file
    for file_path in file_list:
      selections = FindPythonDefinition(self.file_access_policy, file_path,
                                        identifier)
      if len(selections) > 1:
        return CommandOutput([], [
            f"Multiple matches found for identifier '{identifier}' in '{file_path}'."
        ], "Multiple matches found.")
      elif len(selections) == 1:
        matches.append((file_path, selections[0]))

    if len(matches) == 0:
      return CommandOutput([],
                           [f"No matches found for identifier '{identifier}'."],
                           "No matches found.")
    elif len(matches) > 1:
      locations = [
          f"{match[0]}: lines {match[1].start_index + 1}-{match[1].end_index + 1}"
          for match in matches
      ]
      return CommandOutput([], [
          f"Multiple matches found for identifier '{identifier}': {', '.join(locations)}"
      ], "Multiple matches found.")

    # Exactly one match found, proceed with replacement
    if command_input.multiline_content:
      file_path, selection = matches[0]
      with open(file_path, "r") as file:
        lines = file.readlines()

      # Replace the lines in the file
      lines[selection.start_index:selection.end_index + 1] = command_input.multiline_content

      with open(file_path, "w") as file:
        file.writelines(lines)

      return CommandOutput(["The definition was successfully replaced."], [],
                           "Replacement successful.")

    return CommandOutput(
        [], ["No replacement content provided for the identifier."],
        "Replacement content missing.")