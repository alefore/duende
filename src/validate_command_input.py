import logging
import os
import pathlib
from typing import Generator

from agent_command import CommandSyntax, CommandInput, ArgumentContentType, Argument, VariableMap, VariableName, VariableValue, VariableValueInt
from command_registry import CommandRegistry
from file_access_policy import FileAccessPolicy


class CommandValidationError(Exception):
  pass


def _IsPath(arg_type: ArgumentContentType) -> bool:
  return arg_type in {
      ArgumentContentType.PATH_INPUT, ArgumentContentType.PATH_INPUT_OUTPUT,
      ArgumentContentType.PATH_OUTPUT
  }


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


def validate_command_input(cmd_input: CommandInput,
                           command_registry: CommandRegistry,
                           file_access_policy: FileAccessPolicy) -> VariableMap:
  command = command_registry.Get(cmd_input.command_name)
  if not command:
    error_msg = (f"Error: Unknown command: {cmd_input.command_name}. " +
                 command_registry.available_commands_str())
    logging.error(error_msg)
    raise CommandValidationError(error_msg)

  warnings: list[str] = []

  # Validate arguments based on CommandSyntax.arguments
  for syntax_arg in command.Syntax().arguments:
    name: VariableName = syntax_arg.name
    value: VariableValue | None = cmd_input.args.get(syntax_arg.name)
    if value is not None:
      assert isinstance(value, str)
      if _IsPath(syntax_arg.arg_type):
        warnings.extend(_ValidatePathArg(syntax_arg, value, file_access_policy))
    elif syntax_arg.required:
      warnings.append(f"Missing required argument: {syntax_arg.name}")

  # Check for unexpected arguments:
  for input_arg_name in cmd_input.args:
    found_in_syntax = False
    for syntax_arg in command.Syntax().arguments:
      if input_arg_name == syntax_arg.name:
        found_in_syntax = True
        break
    if not found_in_syntax:
      warnings.append(f"Unexpected argument: {input_arg_name}")

  syntax_args_dict: dict[VariableName, Argument] = {
      a.name: a for a in command.Syntax().arguments
  }

  if warnings:
    logging.info(f"Warnings: {','.join(warnings)}")
    raise CommandValidationError("\n".join([
        f"Warning {command.Syntax().name}: {warning}" for warning in warnings
    ]))

  output = VariableMap({})
  for k, v in cmd_input.args.items():
    if _IsPath(syntax_args_dict[k].arg_type):
      assert isinstance(v, str)
      output[k] = pathlib.Path(v)
    elif syntax_args_dict[k].arg_type == ArgumentContentType.INTEGER:
      assert isinstance(v, int | str)
      output[k] = VariableValueInt(int(v))
    else:
      output[k] = v
  return output
