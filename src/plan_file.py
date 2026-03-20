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


@dataclass
class Attempt:
  attempt_number: int
  state: AttemptState
  details: str
  title: str | None = None

  @classmethod
  def from_markdown_section(cls, section: "MarkdownSection") -> "Attempt":
    match = re.compile(
        "### Attempt ([0-9]+)(: (([a-zA-Z]+)(: (.+))?)?)?").fullmatch(
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
    if self.title:
      header += f": {self.title}"
    return [header] + self.details.split("\n")


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


class TaskState(Enum):
  PENDING = "pending"
  DONE = "done"
  OBSOLETE = "obsolete"


ATTEMPT_STATE_TO_TASK_STATE = {
    AttemptState.NEW: TaskState.PENDING,
    AttemptState.ONGOING: TaskState.PENDING,
    AttemptState.FAIL: TaskState.PENDING,
    AttemptState.SUCCESS: TaskState.DONE,
    AttemptState.REVIEW: TaskState.PENDING,
    AttemptState.IMPROVE: TaskState.PENDING,
    AttemptState.COMMIT: TaskState.PENDING,
    AttemptState.OBSOLETE: TaskState.OBSOLETE
}


@dataclass
class Task:
  title: str
  state: TaskState
  description: str
  attempts: list[Attempt]

  @classmethod
  def from_markdown_section(cls, section: MarkdownSection) -> "Task":
    sections = list(_group_sections(section.lines, 3))
    title_pattern = re.compile("## Task: (.*?)( \\((done|obsolete)\\))?")
    title_match = title_pattern.fullmatch(section.header)
    assert title_match

    def _is_attempt(section: MarkdownSection) -> bool:
      return section.header.startswith("### Attempt")

    return cls(
        title=title_match.groups()[0],
        state=TaskState(title_match.groups()[2] or "pending"),
        description=sections[0].contents()
        if sections and not _is_attempt(sections[0]) else "",
        attempts=list(
            map(Attempt.from_markdown_section, filter(_is_attempt, sections))))

  def to_markdown_lines(self) -> list[str]:
    state = "" if self.state == TaskState.PENDING else f" ({self.state.value})"
    return ([f"## Task: {self.title}{state}"] +
            (self.description.split("\n") if self.description else []) + [
                line for attempt in self.attempts
                for line in attempt.to_markdown_lines()
            ])

  def __str__(self):
    return "\n".join(self.to_markdown_lines())


class PlanFile:

  def __init__(self, contents: str) -> None:
    self.tasks: list[Task] = []
    goal_title: str | None = None
    goal_description: str | None = None
    goal_pattern = re.compile("## Goal: (.+)$")
    task_pattern = re.compile("## Task: .+$")
    for section in _group_sections(contents.split("\n"), 2):
      goal_match = goal_pattern.fullmatch(section.header)
      if goal_match:
        if goal_title is not None:
          raise ValueError("Multiple `## Goal` sections found.")
        goal_title = goal_match.group(1)
        goal_description = "\n".join(section.lines)
        continue
      if task_pattern.fullmatch(section.header):
        self.tasks.append(Task.from_markdown_section(section))
        continue
      raise ValueError(f"Unexpected section: {section.header}")
    if goal_title is None or goal_description is None:
      raise ValueError("Section missing: `## Goal`")
    self.goal_title: str = goal_title
    self.goal_description: str = goal_description

  def to_string(self) -> str:
    return "\n".join(
        [f"## Goal: {self.goal_title}", self.goal_description] +
        [line for task in self.tasks for line in task.to_markdown_lines()])

  def index_first_pending(self) -> int | None:
    return next((i for i, task in enumerate(self.tasks)
                 if task.state == TaskState.PENDING), None)
