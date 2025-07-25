import logging
import os
from typing import List, Dict

from agent_loop_options import AgentLoopOptions
from agent_workflow import AgentWorkflow
from message import ContentSection, Message
import review_utils
from conversation import ConversationFactory


class PrincipleReviewWorkflow(AgentWorkflow):

  def __init__(self, options: AgentLoopOptions, principle_paths: List[str],
               input_path: str,
               conversation_factory: ConversationFactory) -> None:
    super().__init__(conversation_factory)
    self._options = options
    self._principle_paths = principle_paths
    self._input_path = input_path

  def _get_principle_prompt(self, principle_file: str,
                            input_content: str) -> str:
    with open(principle_file, 'r') as f:
      principle_content = f.read()

    return f"""# Your task

You must review if a given input abides by a principle (given below) and either:

* If the input meets the principle: run the `accept` function (with a `reason` parameter).

* If the input does NOT meet the principle: run the `reject` function. In the `reason` parameter, explain your decision, including steps to improve the input. This info will be given to an AI tasked with fixing the input. That AI does not know this principle, so convey enough details to enable the AI to succesfully fixing the input (to meet the principle).

# PRINCIPLE (REQUIREMENT)

{principle_content}

# INPUT TO ANALYZE

{input_content}"""

  def run(self) -> None:
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
    all_review_results = review_utils.run_parallel_reviews(
        reviews_to_run=reviews_to_run,
        parent_options=self._options,
        conversation_factory=self._conversation_factory)

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
