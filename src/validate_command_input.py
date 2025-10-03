from typing import Generator
import os
from agent_command import CommandSyntax, CommandInput, ArgumentContentType, Argument
from file_access_policy import FileAccessPolicy


def _IsPath(arg_type: ArgumentContentType) -> bool:
  return arg_type in [
      ArgumentContentType.PATH_INPUT, ArgumentContentType.PATH_INPUT_OUTPUT,
      ArgumentContentType.PATH_OUTPUT
  ]


def _InvalidPathError(arg: Argument, value: str, error: str) -> str:
  return f"Argument {arg.name}: {error}: Value: {value}"


def _ValidatePathArg(
    arg: Argument, value: str,
    file_access_policy: FileAccessPolicy) -> Generator[str, None, None]:
  if not file_access_policy.allow_access(value):
    if arg.arg_type == ArgumentContentType.PATH_INPUT:
      yield _InvalidPathError(arg, value, "File not found")
    else:
      yield _InvalidPathError(arg, value, "Permission denied")
  elif arg.arg_type == ArgumentContentType.PATH_INPUT and not os.path.exists(
      value):
    yield _InvalidPathError(arg, value, "File not found")


def ValidateCommandInput(syntax: CommandSyntax, input: CommandInput,
                         file_access_policy: FileAccessPolicy) -> list[str]:
  warnings: list[str] = []

  # Validate arguments based on CommandSyntax.arguments
  for syntax_arg in syntax.arguments:
    value = input.args.get(syntax_arg.name)
    if value is not None:
      assert isinstance(value, str)
      if _IsPath(syntax_arg.arg_type):
        warnings.extend(_ValidatePathArg(syntax_arg, value, file_access_policy))
    elif syntax_arg.required:
      warnings.append(f"Missing required argument: {syntax_arg.name}")

  # Check for unexpected arguments in input.args
  for input_arg_name in input.args:
    found_in_syntax = False
    for syntax_arg in syntax.arguments:
      if input_arg_name == syntax_arg.name:
        found_in_syntax = True
        break
    if not found_in_syntax:
      warnings.append(f"Unexpected argument: {input_arg_name}")

  return warnings
