from typing import List
from src.agent_command import CommandSyntax, CommandInput, ArgumentContentType


def ValidateCommandInput(syntax: CommandSyntax,
                         input: CommandInput) -> List[str]:
  warnings: List[str] = []

  missing_args: List[str] = [
      arg.name for arg in syntax.required[len(input.arguments):]
  ]
  if missing_args:
    warnings.append(
        f"Missing required arguments: {', '.join(missing_args)}. "
        f"Expected {len(syntax.required)}, got {len(input.arguments)}.")

  if not syntax.repeatable_final:
    max_args: int = len(syntax.required) + len(syntax.optional)
    if len(input.arguments) > max_args:
      warnings.append(
          f"Too many arguments provided. "
          f"Expected a maximum of {max_args}, got {len(input.arguments)}.")

  if syntax.multiline and syntax.multiline.required and not input.multiline_content:
    warnings.append(f"Missing required multiline content. "
                    f"Description: {syntax.multiline.description}.")
  elif not syntax.multiline and input.multiline_content:
    warnings.append("Unexpected multiline content provided.")

  return warnings
