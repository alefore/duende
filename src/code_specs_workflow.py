import aiofiles
import asyncio
import logging
import pathlib
import re
import shutil
import subprocess
import tempfile
from typing import NamedTuple, NewType, Pattern, Sequence

from agent_loop import AgentLoop
from agent_loop_options import AgentLoopOptions
from command_registry import CommandRegistry
from conversation import Conversation, ConversationId, ConversationFactory
from message import Message, ContentSection
from conversation_state import ConversationState
from agent_workflow import AgentWorkflow, AgentWorkflowFactory
from agent_workflow_options import AgentWorkflowOptions
from agent_command import Argument, ArgumentContentType, VariableMap, VariableName, VariableValue
from done_command import DoneCommand, DoneValuesValidator
from file_access_policy import FileAccessPolicy
from list_files_command import ListFilesCommand
from read_file_command import ReadFileCommand
from write_file_command import WriteFileCommand
from validation import ValidationResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

implementation_variable = VariableName('implementation')

# The local path to a DM file (including the `.dm.` part).
dm_path_variable = VariableName('dm_path')

# A shell command that can be used to validate that the output file (with some
# DM markers expanded) is correct. If the DM file being expanded contains unit
# tests, this typically just runs it.
validator_variable = VariableName('validator')

# A comma-separated list of local files that someone implementing a DM marker
# may want to have access to.
relevant_paths_variable = VariableName('relevant_paths')

# A string with a shell command including the token `{path}`, which will be
# expanded (with `validator.format(…)`) to the path to be validated. Validation
# is successful if this command exits with 0.
DMValidator = NewType('DMValidator', str)


class PathAndValidator(NamedTuple):
  dm_path: pathlib.Path
  validator: DMValidator


MarkerName = NewType('MarkerName', str)


def _get_comment_char(path: pathlib.Path) -> str:
  """Returns the comment character based on the file extension (e.g., `#`).

  Supported extensions: py, sh, cc, h, js, ts, java"""
  # ✨ get comment char
  suffix = path.suffix.lstrip('.')
  if suffix in ['py', 'sh']:
    return '#'
  elif suffix in ['cc', 'h', 'js', 'ts', 'java']:
    return '//'
  # ✨
  raise ValueError(f"Unknown file suffix: {path.suffix}")


class MarkerImplementation:

  def __init__(self, name: MarkerName, value: str,
               expected_comment_char: str) -> None:
    """Stores attributes and validates the format of `value`.

    Raises:
         ValueError if value lacks valid beginning and end comments."""
    # ✨ marker implementation constructor
    self._name = name
    self._value = value

    # Validate the format of 'value'
    lines = value.splitlines()
    if not lines:
      raise ValueError("Implementation value cannot be empty.")

    start_marker_pattern = re.compile(
        f"^\\s*{re.escape(expected_comment_char)} ✨ {re.escape(name)}\\s*$")
    end_marker_pattern = re.compile(
        f"^\\s*{re.escape(expected_comment_char)} ✨\\s*$")

    if not start_marker_pattern.match(lines[0]):
      raise ValueError(
          f"Implementation value must start with a line matching '{expected_comment_char} ✨ {name}'. Got: '{lines[0]}'"
      )
    if not end_marker_pattern.match(lines[-1]):
      raise ValueError(
          f"Implementation value must end with a line matching '{expected_comment_char} ✨'. Got: '{lines[-1]}'"
      )
    # ✨

  # ✨ `name` and `value` getters
  @property
  def name(self) -> MarkerName:
    return self._name

  @property
  def value(self) -> str:
    return self._value

  # ✨

  async def save(self, path: pathlib.Path) -> None:
    """Rewrites `path`, storing our implementation.

    Raises:
        ValueError if the marker doesn't occur exactly once in `path`."""
    # ✨ marker implementation save
    async with aiofiles.open(
        path, mode='r') as f:
      content = await f.read()

    comment_char = _get_comment_char(path)
    marker_pattern = re.compile(
        r"{comment_char}\s*{open_tag}🍄\s*{name}\s*{close_tag}*".format(
            open_tag=re.escape("{{"),
            close_tag=re.escape("}}"),
            comment_char=re.escape(comment_char),
            name=re.escape(self.name)))
    logging.info(marker_pattern)

    logging.info(content)
    lines = content.splitlines()
    found_marker_indices = []
    for i, line in enumerate(lines):
      if marker_pattern.search(line):
        found_marker_indices.append(i)

    if len(found_marker_indices) != 1:
      raise ValueError(
          f"Marker '{{{{🍄 {self._name}}}}}' found {len(found_marker_indices)} times in '{path}'. Expected exactly one."
      )

    marker_line_index = found_marker_indices[0]
    lines[marker_line_index:marker_line_index + 1] = self._value.splitlines()
    new_content = '\n'.join(lines)

    async with aiofiles.open(path, mode='w') as f:
      await f.write(new_content)
    # ✨


async def _run_validator(path: pathlib.Path,
                         validator: DMValidator) -> ValidationResult:
  """Runs `validator` (expanding `path`), returning ValidationResult."""
  # ✨ def run validator
  command = validator.format(path=path)
  logger.info(f"Running validator command: {command}")
  process = await asyncio.create_subprocess_shell(
      command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
  stdout, stderr = await process.communicate()

  if process.returncode == 0:
    return ValidationResult(
        success=True, output=stdout.decode().strip(), error='')
  else:
    return ValidationResult(
        success=False,
        output=stdout.decode().strip(),
        error=stderr.decode().strip())
  # ✨


async def _list_markers(path: pathlib.Path) -> list[MarkerName]:
  """Returns all markers in `path` in the order in which they appear.

  Raises:
      ValueError if the file does not contain any markers or contains repeated
      markers."""
  # ✨ list markers
  async with aiofiles.open(
      path, mode='r') as f:
    content = await f.read()

  # Pattern to match {{🍄 marker_name}}
  # marker_name is optional and can contain any characters except '}'
  marker_pattern = re.compile(r"\{\{🍄\s*([^}]*?)\s*\}\}")

  found_marker_names: list[MarkerName] = []
  repeated: set[MarkerName] = set()

  for line in content.splitlines():
    match = marker_pattern.search(line)
    if match:
      marker_name = MarkerName(match.group(1).strip())
      if marker_name in found_marker_names:
        repeated.add(marker_name)
      else:
        found_marker_names.append(marker_name)

  if not found_marker_names:
    raise ValueError(f"No DM markers found in '{path}'")

  if repeated:
    raise ValueError(
        f"Repeated DM markers found in '{path}': {', '.join(sorted(repeated))}")

  return found_marker_names
  # ✨


class CodeSpecsWorkflow(AgentWorkflow):

  def __init__(self, options: AgentWorkflowOptions) -> None:
    self._options = options

  async def run(self) -> None:

    inputs = await self._get_initial_parameters()
    output_path = await self._prepare_output(inputs)
    relevant_paths = await self._find_relevant_paths(output_path)
    await self._implement_file(inputs, output_path, relevant_paths)

    logger.info("CodeSpecsWorkflow completed successfully.")

  def _get_command_registry(self, arguments: list[Argument],
                            validator: DoneValuesValidator) -> CommandRegistry:
    """Creates a command registry with a `done` command expecting `arguments`.

    The registry includes only `read_file`, `list_files` and `done`."""
    # ✨ get command registry
    registry = CommandRegistry()
    file_access_policy = self._options.agent_loop_options.file_access_policy
    registry.Register(ReadFileCommand(file_access_policy))
    registry.Register(ListFilesCommand(file_access_policy))
    registry.Register(DoneCommand(arguments, values_validator=validator))
    return registry
    # ✨

  async def _get_initial_parameters(self) -> PathAndValidator:
    """Ask the user for a valid DM file.

    Runs an AgentLoop where the user specifies values for dm_path_variable and
    validator_variable (given to `done` and validated).

    The starting message for the AgentLoop should instruct the conversational AI
    to prompt the user for the appropriate values. Something like:

    > Please ask the user (through text conversation) for approprivate values to
    > use for the variables expected by `done`. Once the user has given you
    > appropriate values, your goal is achieved and you should run `done`.
    """

    class DoneValidator(DoneValuesValidator):
      """Validates inputs given to `done`.

      Confirms that `inputs[dm_path_variable]` is a valid DM specs file and that
      `inputs[validator_variable]` …

      * … includes the string `{path}`
      * … validates a copy of `inputs[dm_path_variable]` in /tmp."""

      # ✨ initial validator
      async def validate(self, inputs: VariableMap) -> ValidationResult:
        dm_path = inputs.get(dm_path_variable)
        validator_value = inputs.get(validator_variable)
        logging.info('Inputs: %s', inputs.items())

        if not isinstance(dm_path, pathlib.Path) or not dm_path:
          return ValidationResult(
              success=False,
              output='',
              error=f"Variable '{dm_path_variable}' must be a non-empty string."
          )

        if not isinstance(validator_value, str) or not validator_value:
          return ValidationResult(
              success=False,
              output='',
              error=f"Variable '{validator_variable}' must be a non-empty string."
          )

        if '.dm.' not in str(dm_path):
          return ValidationResult(
              success=False,
              output='',
              error=f"DM file path '{dm_path}' must contain '.dm.'.")

        if '{path}' not in validator_value:
          return ValidationResult(
              success=False,
              output='',
              error=f"Validator '{validator_value}' must contain '{{path}}'.")

        if not dm_path.is_file():
          return ValidationResult(
              success=False,
              output='',
              error=f"DM file '{dm_path}' does not exist.")

        with tempfile.NamedTemporaryFile(dir='/tmp', delete=True) as tmp_file:
          tmp_path = pathlib.Path(tmp_file.name)
          shutil.copy(dm_path, tmp_path)
          return await _run_validator(tmp_path, DMValidator(validator_value))
        # ✨

    # ✨ initial parameters
    done_arguments = [
        Argument(
            name=dm_path_variable,
            arg_type=ArgumentContentType.PATH_INPUT,
            description="The path to the DM file."),
        Argument(
            name=validator_variable,
            arg_type=ArgumentContentType.STRING,
            description="Shell command to validate the output file."),
    ]
    conversation = self._options.conversation_factory.New(
        "Get initial parameters",
        self._get_command_registry(done_arguments, DoneValidator()))
    start_message = Message(
        role="user",
        content_sections=[
            ContentSection(
                content=(
                    "Please ask the user (through text conversation) for "
                    "approprivate values to use for the variables expected by "
                    "`done`. Once the user has given you appropriate values, "
                    "your goal is achieved and you should run `done`."))
        ])
    agent_loop = AgentLoop(
        self._options.agent_loop_options._replace(
            conversation=conversation,
            start_message=start_message,
            commands_registry=conversation.command_registry))
    await agent_loop.run()

    # Get the last message from the conversation
    last_message = conversation.messages[-1]
    # Get the last content section, which should contain the CommandOutput from the 'done' command.
    last_content_section = last_message.GetContentSections()[-1]

    # Ensure command_output is not None before accessing output_variables
    assert last_content_section.command_output, "Expected a CommandOutput from the 'done' command."

    done_command_output_variables = last_content_section.command_output.output_variables

    dm_path = done_command_output_variables[dm_path_variable]
    assert isinstance(dm_path, pathlib.Path)
    validator_str = done_command_output_variables[validator_variable]
    assert isinstance(validator_str, str)
    return PathAndValidator(
        dm_path=dm_path, validator=DMValidator(validator_str))
    # ✨

  async def _prepare_output(self, inputs: PathAndValidator) -> pathlib.Path:
    """Reads the input DM file and prepares the output file.

    No markers are expanded. Prepends the "DO NOT EDIT" header at the top."""
    # ✨ prepare output
    output_path = pathlib.Path(str(inputs.dm_path).replace('.dm.', '.'))

    async with aiofiles.open(inputs.dm_path, mode='r') as f:
      content = await f.read()

    comment_char = _get_comment_char(output_path)
    header = f"{comment_char} DO NOT EDIT. This file is automatically generated by Duende.\n"
    new_content = header + content

    async with aiofiles.open(output_path, mode='w') as f:
      await f.write(new_content)

    return output_path
    # ✨

  async def _find_relevant_paths(
      self, path: pathlib.Path) -> dict[MarkerName, set[pathlib.Path]]:
    """Finds all relevant paths to implement each DM marker.

    Does it by starting concurrent conversations for all markers."""
    # ✨ find relevant paths loop
    markers = await _list_markers(path)
    tasks = []
    for marker in markers:
      tasks.append(self._find_relevant_paths_marker(path, marker))

    # Run all tasks concurrently and collect results
    all_relevant_paths_for_markers = await asyncio.gather(*tasks)

    # Aggregate results into a dictionary
    result_map: dict[MarkerName, set[pathlib.Path]] = {}
    for marker_name, relevant_paths_set in zip(markers,
                                               all_relevant_paths_for_markers):
      result_map[marker_name] = relevant_paths_set
    return result_map
    # ✨

  async def _find_relevant_paths_marker(
      self, path: pathlib.Path, marker: MarkerName) -> set[pathlib.Path]:
    """Finds all relevant paths to implement a single DM marker.

    Runs an AgentLoop focused exclusively on `marker`, to identify the
    approriate value for relevant_paths_variable."""

    class DoneValidator(DoneValuesValidator):
      """Verifies that all inputs[relevant_paths_variable] values are readable.

      Each path must:

      1. Be authorized by the file_access_policy.
      2. Be readable (not just exist, but confirm that it can be opened)."""

      # ✨ relevant paths validator
      def __init__(self, file_access_policy: FileAccessPolicy) -> None:
        self._file_access_policy = file_access_policy

      async def validate(self, inputs: VariableMap) -> ValidationResult:
        relevant_paths_value = inputs.get(relevant_paths_variable)

        if not isinstance(relevant_paths_value, str):
          return ValidationResult(
              success=False,
              output='',
              error=f"Variable '{relevant_paths_variable}' must be a string.")

        if not relevant_paths_value:
          return ValidationResult(success=True, output='', error='')

        paths = [p.strip() for p in relevant_paths_value.split(',')]
        for path_str in paths:
          path = pathlib.Path(path_str)

          if not self._file_access_policy.allow_access(str(path)):
            return ValidationResult(
                success=False,
                output='',
                error=f"Path '{path_str}' is not authorized by file access policy."
            )

          if not path.is_file():
            return ValidationResult(
                success=False,
                output='',
                error=f"Relevant path '{path_str}' does not exist or is not a file."
            )

          try:
            async with aiofiles.open(path, mode="r") as f:
              await f.read(1)  # Try to read a character to ensure readability
          except Exception as e:
            return ValidationResult(
                success=False,
                output='',
                error=f"Relevant path '{path_str}' is not readable: {e}")
        return ValidationResult(success=True, output='', error='')

    # ✨

    # ✨ find relevant paths
    done_arguments = [
        Argument(
            name=relevant_paths_variable,
            arg_type=ArgumentContentType.STRING,
            description="Comma-separated list of relevant file paths.",
            required=False)
    ]
    conversation = self._options.conversation_factory.New(
        f"Find relevant paths for marker: {marker}",
        self._get_command_registry(
            done_arguments,
            DoneValidator(self._options.agent_loop_options.file_access_policy)))
    start_message = Message(
        role="user",
        content_sections=[
            ContentSection(
                content=(
                    f"The current DM marker is '{marker}'. The DM file is at "
                    f"'{path}'. Your task is to identify all *other* files "
                    "(besides the DM file itself) that are relevant to "
                    "implementing this marker. You should read the contents "
                    "of the DM file (and any other relevant files you find), "
                    "and then call `done` with the `relevant_paths` argument. "
                    "This argument should be a comma-separated list of all "
                    "identified relevant file paths, *including* the DM file "
                    f"itself ('{path}')."))
        ])
    agent_loop = AgentLoop(
        self._options.agent_loop_options._replace(
            conversation=conversation,
            start_message=start_message,
            commands_registry=conversation.command_registry,
        ))
    await agent_loop.run()

    last_message = conversation.messages[-1]
    last_content_section = last_message.GetContentSections()[-1]
    assert last_content_section.command_output, "Expected a CommandOutput from the 'done' command."
    done_command_output_variables = last_content_section.command_output.output_variables

    relevant_paths_str = done_command_output_variables.get(
        relevant_paths_variable, '')
    assert isinstance(relevant_paths_str, str)

    found_paths: set[pathlib.Path] = set()
    if relevant_paths_str:
      for p_str in relevant_paths_str.split(','):
        stripped_p_str = p_str.strip()
        if stripped_p_str:
          found_paths.add(pathlib.Path(stripped_p_str))
    found_paths.add(path)  # Always include the DM file itself

    return found_paths
    # ✨

  async def _implement_file(
      self, inputs: PathAndValidator, output_path: pathlib.Path,
      relevant_paths: dict[MarkerName, set[pathlib.Path]]) -> None:
    """Implements all DM markers sequentially."""
    # ✨ implement file
    markers = await _list_markers(output_path)
    for marker in markers:
      await self._implement_marker(marker, relevant_paths[marker],
                                   inputs.validator, output_path)
    # ✨

  async def _implement_marker(self, marker: MarkerName,
                              relevant_paths: set[pathlib.Path],
                              validator: DMValidator,
                              output_path: pathlib.Path) -> None:
    """Runs an AgentLoop and uses the output to implement `marker`.

    The AgentLoop is focused on `marker`. Instructs the AI to read all
    `relevant_paths` *and* `output_path` before doing anything else. The AI
    should then pass the implementation code to `done` (see
    `implementation_variable`). The prompt given to the AI is crafted carefully,
    to explain how it must infer the desired intent from `output_path`.

    Once the `AgentLoop` returns, expands the marker in `output_path`."""

    class DoneValidator(DoneValuesValidator):
      """Validates implementation of marker on a tmp copy of output path."""

      # ✨ implement validator
      def __init__(self, marker_name: MarkerName,
                   file_access_policy: FileAccessPolicy,
                   original_output_path: pathlib.Path,
                   dm_validator: DMValidator) -> None:
        self._marker_name = marker_name
        self._file_access_policy = file_access_policy
        self._original_output_path = original_output_path
        self._dm_validator = dm_validator

      async def validate(self, inputs: VariableMap) -> ValidationResult:
        implementation_value = inputs.get(implementation_variable)

        if not isinstance(implementation_value,
                          str) or not implementation_value:
          return ValidationResult(
              success=False,
              output='',
              error=f"Variable '{implementation_variable}' must be a non-empty string."
          )

        try:
          comment_char = _get_comment_char(self._original_output_path)
          marker_impl = MarkerImplementation(self._marker_name,
                                             implementation_value, comment_char)
        except ValueError as e:
          return ValidationResult(success=False, output='', error=str(e))

        # Create a temporary directory and copy the original_output_path to it.
        # Then apply the marker implementation to the temporary file.
        with tempfile.TemporaryDirectory() as tmpdir:
          tmp_path = pathlib.Path(tmpdir) / self._original_output_path.name
          shutil.copy(self._original_output_path, tmp_path)
          await marker_impl.save(tmp_path)
          return await _run_validator(tmp_path, self._dm_validator)

    # ✨

    # ✨ implement single marker
    comment_char = _get_comment_char(output_path)
    done_arguments = [
        Argument(
            name=implementation_variable,
            arg_type=ArgumentContentType.STRING,
            description="The code to implement the marker, including `✨` start and end markers.",
        )
    ]

    files_to_read = [f"- '{output_path}'"]
    for p in sorted(list(relevant_paths)):
      if p != output_path:  # Avoid duplicating output_path if it's already in relevant_paths
        files_to_read.append(f"- '{p}'")
    files_to_read_bullet_list = "\n".join(files_to_read)

    conversation = self._options.conversation_factory.New(
        f"Implement marker: {marker}",
        self._get_command_registry(
            done_arguments,
            DoneValidator(marker,
                          self._options.agent_loop_options.file_access_policy,
                          output_path, validator),
        ),
    )

    start_message = Message(
        role="user",
        content_sections=[
            ContentSection(
                content=(
                    "You are tasked with implementing a Duende Mushroom (DM) marker. "
                    "A DM marker, like '{{🍄 name}}', indicates a specific location in the code "
                    "where functionality needs to be added.\n\n"
                    "To implement this marker, you will provide the *code content* for an "
                    "implementation block. This block will replace the line containing the "
                    f"'{{{{🍄 {marker}}}}}' marker in the file '{output_path}'.\n\n"
                    "The implementation block *must* strictly follow this format:\n"
                    f"- It *must* begin with a line exactly like: '{comment_char} ✨ {marker}'.\n"
                    f"- It *must* end with a line exactly like: '{comment_char} ✨'.\n\n"
                    "Before attempting any implementation, you *must* read the contents "
                    "of the following files to gather all necessary context:\n"
                    f"{files_to_read_bullet_list}\n\n"
                    f"The specific DM marker you are implementing is '{{{{🍄 {marker}}}}}' "
                    f"in the file '{output_path}'. Carefully analyze the code surrounding "
                    "this marker in '{output_path}' and the contents of all the relevant files "
                    "to fully understand the desired functionality and how your "
                    "implementation should integrate.\n\n"
                    "Once you have written the complete and correct implementation code, "
                    "call the `done` command. The `done` command requires a "
                    f"variable named `{implementation_variable}`. The value for "
                    f"`{implementation_variable}` *must* be your full implementation block "
                    "as a single string, including both the "
                    f"'{comment_char} ✨ {marker}' beginning marker and the "
                    f"'{comment_char} ✨' ending marker. "
                    "Do not try to write to any files directly; simply provide the "
                    "complete implementation block via the `done` command."))
        ],
    )

    agent_loop = AgentLoop(
        self._options.agent_loop_options._replace(
            conversation=conversation,
            start_message=start_message,
            commands_registry=conversation.command_registry))
    await agent_loop.run()

    last_message = conversation.messages[-1]
    last_content_section = last_message.GetContentSections()[-1]
    assert last_content_section.command_output, "Expected a CommandOutput from the 'done' command."
    done_command_output_variables = last_content_section.command_output.output_variables

    implementation_str = done_command_output_variables[implementation_variable]
    assert isinstance(implementation_str, str)

    marker_implementation = MarkerImplementation(marker, implementation_str,
                                                 comment_char)
    await marker_implementation.save(output_path)
    # ✨


class CodeSpecsWorkflowFactory(AgentWorkflowFactory):

  def name(self) -> str:
    return "dm"

  async def new(self, agent_workflow_options: AgentWorkflowOptions,
                args: dict[str, str]) -> AgentWorkflow:
    return CodeSpecsWorkflow(agent_workflow_options)
