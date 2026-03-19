from dataclasses import dataclass
import re
from typing import Iterator


@dataclass(frozen=True)
class MarkdownSection:
  header: str
  lines: list[str]


def _is_header(line: str, header_depth: int) -> bool:
  return line.startswith("#" * header_depth + " ")


def _group_sections(contents: list[str],
                    header_depth: int) -> Iterator[MarkdownSection]:
  current: list[str] = []
  for line in contents:
    if _is_header(line, header_depth):
      if len(current) > 0:
        yield MarkdownSection(current[0], current[1:])
      current = []
    current.append(line)
  if len(current) > 0:
    yield MarkdownSection(current[0], current[1:])


class PlanFile:

  def __init__(self, contents: str) -> None:
    self.tasks: list[MarkdownSection] = []
    goal: str | None = None
    task_pattern = re.compile("## Task: .+$")
    for section in _group_sections(contents.splitlines(), 2):
      if section.header == "## Goal":
        if goal is not None:
          raise ValueError("Multiple `## Goal` sections found.")
        goal = "\n".join(section.lines)
        continue
      if task_pattern.fullmatch(section.header):
        self.tasks.append(section)
    if goal is None:
      raise ValueError("Section missing: `## Goal`")
    self.goal: str = goal
    if not self.tasks:
      raise ValueError("No tasks (sections `## Task: …`) were found.")
