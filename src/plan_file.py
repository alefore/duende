from dataclasses import dataclass
import re
from typing import Iterator
from enum import Enum


class AttemptState(Enum):
  NEW = "New"
  ONGOING = "Ongoing"
  FAIL = "Fail"
  SUCCESS = "Success"
  REVIEW = "Review"
  IMPROVE = "Improve"
  COMMIT = "Commit"
  OBSOLETE = "Obsolete"


@dataclass(frozen=True)
class Attempt:
  attempt_number: int
  state: AttemptState
  details: str
  title: str | None = None

  @classmethod
  def from_markdown_section(cls, section: "MarkdownSection") -> "Attempt":
    match = re.compile(
        "### Attempt ([0-9]+)(: (([a-zA-Z]+)(: (.*)?))?").fullmatch(
            section.header)
    if not match:
      raise ValueError(f"Unable to parse attempt header: {section.header}")
    groups = match.groups()
    return cls(
        attempt_number=int(groups[0]),
        state=AttemptState(groups[3]) if len(groups) >= 3 else AttemptState.NEW,
        title=(groups[5] if len(groups) > 5 else None),
        details="\n".join(section.lines))

  def to_markdown_lines(self) -> list[str]:
    header = f"### Attempt {self.attempt_number}: {self.state.value}"
    if self.title is not None:
      header += f": {self.title}"
    return [header] + (self.details.splitlines() if self.details else [])


@dataclass(frozen=True)
class MarkdownSection:
  header: str
  lines: list[str]

  def contents(self) -> str:
    return "\n".join([self.header] + self.lines)


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
  attempts: list[Attempt]

  @classmethod
  def from_markdown_section(cls, section: MarkdownSection) -> "Task":
    sections = list(_group_sections(section.lines, 3))
    parsed_title = section.header.removeprefix("## Task: ").strip()

    def _is_attempt(section: MarkdownSection) -> bool:
      return section.header.startswith("### Attempt")

    return cls(
        title=parsed_title,
        description=sections[0].contents()
        if sections and not _is_attempt(sections[0]) else "",
        attempts=list(
            map(Attempt.from_markdown_section, filter(_is_attempt, sections))))

  def to_markdown_lines(self) -> list[str]:
    return ([f"## Task: {self.title}"] +
            (self.description.splitlines() if self.description else []) + [
                line for attempt in self.attempts
                for line in attempt.to_markdown_lines()
            ])


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
