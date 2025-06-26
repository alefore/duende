from typing import List
from agent_command import AgentCommand, CommandSyntax, Argument, ArgumentMultiline
from conversation import MultilineContent


def HelpText(name: str, syntax: CommandSyntax) -> MultilineContent:
  """Renders a help string corresponding to the `syntax` object."""
  header_parts = ([f"#{name}"] + [arg.name for arg in syntax.required] +
                  [f"[{arg.name}]" for arg in syntax.optional])
  if syntax.repeatable_final:
    header_parts.append(f"[{syntax.repeatable_final.name}…]")
  if syntax.multiline:
    header_parts.append(" <<")

  output: MultilineContent = [" ".join(header_parts)]

  if syntax.multiline:
    if syntax.multiline.description:
      output.append(syntax.multiline.description)
      output.append("…")
    output.append("#end")

  output.append(f"  {syntax.description}")
  return output


def FormatHelp(commands: List[AgentCommand]) -> MultilineContent:
  output: MultilineContent = []
  for command in sorted(commands, key=lambda c: c.Name()):
    output.extend(HelpText(command.Name(), command.Syntax()))

  return output
