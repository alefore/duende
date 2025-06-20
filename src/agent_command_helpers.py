from agent_command import CommandSyntax, Argument, ArgumentMultiline


def HelpText(name: str, syntax: CommandSyntax) -> str:
  """Renders a help string corresponding to the `syntax` object."""
  parts = [f"#{name}"]

  # Required arguments
  for arg in syntax.required:
    parts.append(arg.name)

  # Optional positional arguments
  for arg in syntax.optional:
    parts.append(f"[{arg.name}]")

  # Repeatable final argument
  if syntax.repeatable_final:
    parts.append(f"[{syntax.repeatable_final.name}…]")

  header = " ".join(parts)
  output = []
  output.append(header)

  if syntax.multiline:
    output[0] = output[0] + " <<"
    if syntax.multiline.description:
      output.append(syntax.multiline.description)
      output.append("…")
    output.append("#end")

  output.append(f"  {syntax.description}")
  return "\n".join(output)
