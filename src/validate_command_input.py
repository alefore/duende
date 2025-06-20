from typing import Generator, List, Optional
import os
from agent_command import CommandSyntax, CommandInput, ArgumentContentType, Argument, ArgumentMultiline
from file_access_policy import FileAccessPolicy


def _ValidateMultilineInfo(syntax: Optional[ArgumentMultiline],
                           input: bool) -> Generator[str, None, None]:
  if syntax:
    if syntax.required and not input:
      yield (f"Missing required multiline content. "
             f"Description: {syntax.description}.")
  elif input:
    yield "Unexpected multiline content provided."


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
                         file_access_policy: FileAccessPolicy) -> List[str]:
  warnings: List[str] = list(
      _ValidateMultilineInfo(syntax.multiline, bool(input.multiline_content)))

  required_count: int = len(syntax.required)
  optional_count: int = len(syntax.optional)

  if len(input.arguments) < required_count:
    missing_args: List[str] = [
        arg.name for arg in syntax.required[len(input.arguments):]
    ]
    warnings.append(f"Missing required arguments: {', '.join(missing_args)}. "
                    f"Expected {required_count}, got {len(input.arguments)}.")
  elif not syntax.repeatable_final and len(
      input.arguments) > required_count + optional_count:
    max_args: int = required_count + optional_count
    warnings.append(
        f"Too many arguments provided. "
        f"Expected a maximum of {max_args}, got {len(input.arguments)}. "
        f"Arguments rejected: {', '.join(input.arguments[max_args:])}")
  else:
    for index, value in enumerate(input.arguments):
      arg: Argument
      if index < required_count:
        arg = syntax.required[index]
      elif index < required_count + optional_count:
        arg = syntax.optional[index - required_count]
      else:
        assert syntax.repeatable_final
        arg = syntax.repeatable_final
      if _IsPath(arg.arg_type):
        warnings.extend(_ValidatePathArg(arg, value, file_access_policy))
  return warnings
