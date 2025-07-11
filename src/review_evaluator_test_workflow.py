import collections
import glob
import logging
import os
import sys
from typing import Dict, Any, List, Tuple, Callable

from agent_workflow import AgentWorkflow
from agent_loop_options import AgentLoopOptions
from review_utils import run_parallel_reviews, ReviewResult, find_all_evaluators

EvaluatorName = str

# TODO: Create a Namedtuple to contain a TestSpec (fields test_input: str, expect: EvaluatorOutputEnum (declare this enum!)) and store a single dictionary of [str, TestSpec] instead of `reviews_to_run` and `expected_results`.


class ReviewEvaluatorTestWorkflow(AgentWorkflow):
  """A workflow to evaluate the quality of all review evaluators."""

  def __init__(self, options: AgentLoopOptions):
    super().__init__(options.conversation_factory)
    self._options = options

  def run(self) -> None:
    logging.info("Starting Review Evaluator Test Workflow...")

    all_evaluators = find_all_evaluators()
    if not all_evaluators:
      logging.info("No evaluators found. Exiting.")
      return

    reviews_to_run: Dict[str, str] = {}
    expected_results: Dict[str, bool] = {}

    for evaluator_name in all_evaluators:
      accept_tests = glob.glob(f'agent/review/{evaluator_name}/accept/*.txt')
      reject_tests = glob.glob(f'agent/review/{evaluator_name}/reject/*.txt')

      for test_file in accept_tests:
        with open(test_file, 'r') as f:
          content = f.read()
        test_id = f'{evaluator_name}/accept/{os.path.basename(test_file)}'
        reviews_to_run[test_id] = content
        expected_results[test_id] = True

      for test_file in reject_tests:
        with open(test_file, 'r') as f:
          content = f.read()
        test_id = f'{evaluator_name}/reject/{os.path.basename(test_file)}'
        reviews_to_run[test_id] = content
        expected_results[test_id] = False

    if not reviews_to_run:
      logging.info("No tests found for any evaluator. Exiting.")
      sys.exit(1)

    self._process_results(
        run_parallel_reviews(reviews_to_run, self._options), expected_results)

    logging.info("Review Evaluator Test Workflow completed.")

  def _process_results(self, all_review_results: List[ReviewResult],
                       expected_results: Dict[str, bool]) -> None:

    def _create_evaluator_stats_default() -> Dict[str, Any]:
      return {
          'total': 0,
          'passed': 0,
          'incorrect_accept': 0,
          'incorrect_reject': 0,
          'details': []
      }

    # TODO: Create a class EvaluatorResults. This class should internally simply
    # keep a list of ReviewResult and, perhaps, the expected_results. That class should have a method to generate the output (markdown) for a given evaluator.
    # Instead of stupidly updating variables like `total` and `incorrect_XXX`, just compute the values dynamically from the review_results.

    evaluator_stats: Dict[str, Dict[str, Any]] = collections.defaultdict(
        _create_evaluator_stats_default)

    for result in all_review_results:
      parts = result.id.split('/')
      evaluator_name = parts[0]

      expected_to_accept = expected_results.get(result.id)

      stats = evaluator_stats[evaluator_name]
      stats['total'] += 1

      is_correct = False
      if expected_to_accept is True and result.is_accepted is True:
        is_correct = True
        stats['passed'] += 1
      elif expected_to_accept is False and result.is_accepted is False:
        is_correct = True
        stats['passed'] += 1
      elif expected_to_accept is True and result.is_accepted is False:
        stats['incorrect_reject'] += 1
      elif expected_to_accept is False and result.is_accepted is True:
        stats['incorrect_accept'] += 1

      stats['details'].append({
          'test_id': result.id,
          'expected': 'ACCEPT' if expected_to_accept else 'REJECT',
          'actual': 'ACCEPT' if result.is_accepted else 'REJECT',
          'is_correct': is_correct,
          'reason': result.command_output.output
      })

    # Print summary to stdout
    print("\n--- Evaluation Summary ---")
    for evaluator, stats in sorted(evaluator_stats.items()):
      print(
          f"{evaluator}: {stats['passed']} tests passed. {stats['incorrect_accept']} incorrect accept. {stats['incorrect_reject']} incorrect reject."
      )

    # Write detailed results to markdown files
    for evaluator, stats in evaluator_stats.items():
      md_content = f"# Evaluation Results for {evaluator}\n\n"
      md_content += f"Total Tests: {stats['total']}\n"
      md_content += f"Passed: {stats['passed']}\n"
      md_content += f"Incorrect Accepts: {stats['incorrect_accept']}\n"
      md_content += f"Incorrect Rejects: {stats['incorrect_reject']}\n\n"
      md_content += "## Test Details\n\n"

      for detail in stats['details']:
        status = "PASSED" if detail['is_correct'] else "FAILED"
        md_content += f"### {detail['test_id']} - {status}\n"
        md_content += f"- Expected: {detail['expected']}\n"
        md_content += f"- Actual: {detail['actual']}\n"
        if not detail['is_correct']:
          # Using triple quotes for multi-line reason output in markdown
          md_content += f"- Reason:\n```\n{detail['reason']}\n```\n"
        md_content += "\n"

      file_path = f"evaluation-results-{evaluator}.md"
      with open(file_path, 'w') as f:
        f.write(md_content)
      logging.info(f"Wrote detailed results to {file_path}")
