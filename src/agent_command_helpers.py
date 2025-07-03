from typing import List
from agent_command import AgentCommand, CommandSyntax, Argument
from conversation import ContentSection


def HelpText(name: str, syntax: CommandSyntax) -> str:
  """Renders a help string corresponding to the `syntax` object."""
  header_parts = [f"#{name}"]
  for arg in syntax.arguments:
    if arg.required:
      header_parts.append(arg.name)
    else:
      header_parts.append(f"[{arg.name}]")

  output_list: List[str] = [" ".join(header_parts)]
  output_list.append(f"  {syntax.description}")
  output_list.append("")
  return "\n".join(output_list)


def FormatHelp(commands: List[AgentCommand]) -> str:
  output_list: List[str] = []
  for command in sorted(commands, key=lambda c: c.Name()):
    output_list.append(HelpText(command.Name(), command.Syntax()))

  return "\n".join(output_list)
