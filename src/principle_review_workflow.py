import asyncio
import logging
import os
from typing import List, Dict, Optional

from agent_loop_options import AgentLoopOptions
from agent_workflow import AgentWorkflow
from message import ContentSection, Message
import review_utils
from conversation import ConversationFactory
from agent_workflow_options import AgentWorkflowOptions
from agent_loop import AgentLoop
from command_registry import CommandRegistry
from write_file_command import WriteFileCommand
from agent_command import AgentCommand, CommandOutput


class PrincipleReviewWorkflow(AgentWorkflow):

  def __init__(self, options: AgentWorkflowOptions) -> None:
    super().__init__(options)

    if not options.principle_paths:
      raise ValueError(
          "PrincipleReviewWorkflow requires principle_paths in AgentWorkflowOptions."
      )
    self._principle_paths: List[str] = options.principle_paths

    if not options.input_path:
      raise ValueError(
          "PrincipleReviewWorkflow requires input_path in AgentWorkflowOptions."
      )
    self._input_path: str = options.input_path

  def _get_principle_prompt(self, principle_file: str,
                            input_content: str) -> str:
    with open(principle_file, 'r') as f:
      principle_content = f.read()

    return f"""# Your task

You must review if a given input abides by a principle (given below) and either:

* If the input meets the principle: run the `accept` function (with a `reason` parameter).

* If the input does NOT meet the principle: run the `reject` function. In the `reason` parameter, explain your decision, including steps to improve the input. This info will be given to an AI tasked with fixing the input. That AI does not know this principle, so convey enough details to enable the AI to succesfully fixing the input (to meet the principle).

You MUST run the function `accept` or the function `reject`. Anything else (other than the `reason` parameter) will be ignored.

# PRINCIPLE (REQUIREMENT)

{principle_content}

# INPUT TO ANALYZE

{input_content}"""

  async def run(self) -> None:
    logging.info(f"Starting Principle Review Workflow: {self._input_path}")

    with open(self._input_path, 'r') as f:
      input_content = f.read()

    reviews_to_run: Dict[str, str] = {
        os.path.basename(p).replace('.md', ''):
            self._get_principle_prompt(p, input_content)
        for p in self._principle_paths
    }
    if not reviews_to_run:
      logging.warning(
          "No valid principle files found or processed. No reviews will be run."
      )
      return

    logging.info(f"Running {len(reviews_to_run)} parallel principle reviews.")
    all_review_results = await review_utils.run_parallel_reviews(
        reviews_to_run=reviews_to_run,
        parent_options=self._options.agent_loop_options,
        conversation_factory=self._options.conversation_factory,
        expose_read_commands=False)

    logging.info("\n--- Principle Review Results ---")
    if not all_review_results:
      logging.info("No review results received.")
    else:
      for result in all_review_results:
        logging.info(f"Review ID: {result.id}")
        logging.info(f"  Decision: {result.decision.value.upper()}")
        if result.command_output.output:
          logging.info(f"  Reason: {result.command_output.output}")
        if result.command_output.errors:
          logging.error(f"  Errors: {result.command_output.errors}")
    logging.info("--- End of Principle Review Results ---")

    feedback_sections = review_utils.reject_output_content_sections(
        all_review_results)

    if not feedback_sections:
      return

    logging.info("Starting AI conversation to fix input based on rejections.")
    commands_registry = CommandRegistry()
    commands_registry.Register(
        WriteFileCommand(self._options.agent_loop_options.validation_manager,
                         self._options.selection_manager, self._input_path))

    await AgentLoop(
        AgentLoopOptions(
            conversation=await self._options.conversation_factory.New(
                name=f"AI Fixer: {self._options.agent_loop_options.conversation.GetName()}",
                path=None),
            start_message=Message(
                'system',
                content_sections=([
                    ContentSection(
                        content="You are going to receive some suggestions for improvements to a file. Rewrite the file to address these suggestions using the `write_file` command. The `write_file` command has been pre-configured to write to the correct file.",
                        summary="Instructions for fixing the file.")
                ] + feedback_sections + [
                    ContentSection(
                        content=f"Original file content:\n```\n{input_content}\n```",
                        summary="Original file content")
                ])),
            commands_registry=commands_registry,
            confirmation_state=self._options.agent_loop_options
            .confirmation_state,
            file_access_policy=self._options.agent_loop_options
            .file_access_policy,
            conversational_ai=self._options.agent_loop_options
            .conversational_ai,
            confirm_regex=None,
            skip_implicit_validation=True,
            validation_manager=self._options.agent_loop_options
            .validation_manager,
        )).run()
    logging.info("AI fix loop finished.")
