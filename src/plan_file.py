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


@dataclass(frozen=True)
class Task:
  title: str
  description: str
  attempts: list[str]

  @classmethod
  def from_markdown_section(cls, section: MarkdownSection) -> "Task":
    all_sub_sections = list(_group_sections(section.lines, 3))
    parsed_title = section.header.removeprefix("## Task: ").strip()

    if not all_sub_sections:
      return cls(title=parsed_title, description="", attempts=[])

    return cls(
        title=parsed_title,
        description="\n".join([all_sub_sections[0].header] +
                              all_sub_sections[0].lines),
        attempts=[
            attempt_section.header + "\n" + "\n".join(attempt_section.lines)
            for attempt_section in all_sub_sections[1:]
        ])

  def to_markdown_lines(self) -> list[str]:
    return ([f"## Task: {self.title}"] +
            ([self.description] if self.description else []) + self.attempts +
            [""])


class PlanFile:

  def __init__(self, contents: str) -> None:
    self.tasks: list[Task] = []
    goal: str | None = None
    task_pattern = re.compile("## Task: .+$")
    for section in _group_sections(contents.splitlines(), 2):
      if section.header == "## Goal":
        if goal is not None:
          raise ValueError("Multiple `## Goal` sections found.")
        goal = "\n".join(section.lines)
        continue
      if task_pattern.fullmatch(section.header):
        self.tasks.append(Task.from_markdown_section(section))
    if goal is None:
      raise ValueError("Section missing: `## Goal`")
    self.goal: str = goal
    if not self.tasks:
      raise ValueError("No tasks (sections `## Task: …`) were found.")

  def to_string(self) -> str:
    return "\n".join(
        ["## Goal", self.goal, ""] +
        [line for task in self.tasks
         for line in task.to_markdown_lines()]).strip() + "\n"
