import collections
import glob
import logging
import os
import sys
from typing import Dict, Any, List, Tuple, Callable, NamedTuple

from agent_workflow import AgentWorkflow
from agent_loop_options import AgentLoopOptions
from review_utils import run_parallel_reviews, ReviewResult, find_all_evaluators, ReviewDecision
from conversation import ConversationFactory

EvaluatorName = str

class _TestSpec(NamedTuple):
  test_input: str
  expect: ReviewDecision

class EvaluatorResults:
  def __init__(self, review_results: List[ReviewResult], expected_decisions: Dict[str, ReviewDecision]):
    self._review_results = review_results
    self._expected_decisions = expected_decisions

  @property
  def total_tests(self) -> int:
    return len(self._review_results)

  @property
  def passed_tests(self) -> int:
    return sum(self._expected_decisions[r.id] == r.decision for r in self._review_results)

  @property
  def incorrect_accepts(self) -> int:
    return sum(1 for r in self._review_results if self._expected_decisions[r.id] == ReviewDecision.REJECT and r.decision == ReviewDecision.ACCEPT)

  @property
  def incorrect_rejects(self) -> int:
    return sum(1 for r in self._review_results if self._expected_decisions[r.id] == ReviewDecision.ACCEPT and r.decision == ReviewDecision.REJECT)

  def generate_markdown_output(self, evaluator_name: EvaluatorName) -> str:
    md_content = f"# Evaluation Results for {evaluator_name}\n\n"
    md_content += f"Total Tests: {self.total_tests}\n"
    md_content += f"Passed: {self.passed_tests}\n"
    md_content += f"Incorrect Accepts: {self.incorrect_accepts}\n"
    md_content += f"Incorrect Rejects: {self.incorrect_rejects}\n\n"
    md_content += "## Test Details\n\n"

    for result in self._review_results:
      is_correct = (self._expected_decisions[result.id] == result.decision)

      md_content += f"### {result.id} - {"PASSED" if is_correct else "FAILED"}\n"
      md_content += f"- Expected: {self._expected_decisions[result.id].name}\n"
      md_content += f"- Actual: {result.decision.name}\n"
      if not is_correct:
        md_content += f"- Reason:\n```\n{result.command_output.output}\n```\n"
      md_content += "\n"
    return md_content


class ReviewEvaluatorTestWorkflow(AgentWorkflow):
  """A workflow to evaluate the quality of all review evaluators."""

  def __init__(self, options: AgentLoopOptions, conversation_factory: ConversationFactory):
    super().__init__(conversation_factory)
    self._options = options

  def run(self) -> None:
    logging.info("Starting Review Evaluator Test Workflow...")

    all_evaluators = find_all_evaluators()
    if not all_evaluators:
      logging.info("No evaluators found. Exiting.")
      return

    tests_to_run: Dict[str, _TestSpec] = {}

    for evaluator_name in all_evaluators:
      for test_file in glob.glob(f'agent/review/{evaluator_name}/accept/*.txt'):
        with open(test_file, 'r') as f:
          content = f.read()
        tests_to_run[f'{evaluator_name}/accept/{os.path.basename(test_file)}'] = _TestSpec(test_input=content, expect=ReviewDecision.ACCEPT)

      for test_file in glob.glob(f'agent/review/{evaluator_name}/reject/*.txt'):
        with open(test_file, 'r') as f:
          content = f.read()
        tests_to_run[f'{evaluator_name}/reject/{os.path.basename(test_file)}'] = _TestSpec(test_input=content, expect=ReviewDecision.REJECT)

    if not tests_to_run:
      logging.info("No tests found for any evaluator. Exiting.")
      sys.exit(1)

    self._process_results(
        run_parallel_reviews({test_id: spec.test_input for test_id, spec in tests_to_run.items()}, self._options, self._conversation_factory), 
        {test_id: spec.expect for test_id, spec in tests_to_run.items()})

    logging.info("Review Evaluator Test Workflow completed.")

  def _process_results(self, all_review_results: List[ReviewResult],
                       expected_decisions: Dict[str, ReviewDecision]) -> None:

    evaluator_grouped_results: Dict[EvaluatorName, List[ReviewResult]] = collections.defaultdict(list)
    for result in all_review_results:
      evaluator_grouped_results[result.id.split('/')[0]].append(result)

    evaluator_stats: Dict[EvaluatorName, EvaluatorResults] = {}
    for evaluator_name, results in evaluator_grouped_results.items():
      evaluator_stats[evaluator_name] = EvaluatorResults(results, expected_decisions)

    # Print summary to stdout
    print("\n--- Evaluation Summary ---")
    for evaluator, eval_results in sorted(evaluator_stats.items()):
      print(
          f"{evaluator}: {eval_results.passed_tests} tests passed. {eval_results.incorrect_accepts} incorrect accept. {eval_results.incorrect_rejects} incorrect reject."
      )

    # Write detailed results to markdown files
    for evaluator, eval_results in evaluator_stats.items():
      md_content = eval_results.generate_markdown_output(evaluator)
      file_path = f"evaluation-results-{evaluator}.md"
      with open(file_path, 'w') as f:
        f.write(md_content)
      logging.info(f"Wrote detailed results to {file_path}")
