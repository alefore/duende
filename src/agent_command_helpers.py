from typing import List
from agent_command import AgentCommand, CommandSyntax, Argument
from conversation import MultilineContent


def HelpText(name: str, syntax: CommandSyntax) -> MultilineContent:
  """Renders a help string corresponding to the `syntax` object."""
  header_parts = [f"#{name}"]
  for arg in syntax.arguments:
    if arg.required:
      header_parts.append(arg.name)
    else:
      header_parts.append(f"[{arg.name}]")

  output: MultilineContent = [" ".join(header_parts)]
  output.append(f"  {syntax.description}")
  output.append("")
  return output


def FormatHelp(commands: List[AgentCommand]) -> MultilineContent:
  output: MultilineContent = []
  for command in sorted(commands, key=lambda c: c.Name()):
    output.extend(HelpText(command.Name(), command.Syntax()))

  return output
