from implement_workflow import ImplementAndReviewWorkflowFactory
from agent_workflow import AgentWorkflowFactoryContainer
from code_specs_workflow import CodeSpecsWorkflowFactory
from code_specs_tests_skeleton import CodeSpecsTestsSkeletonWorkflowFactory


def StandardWorkflowFactoryContainer() -> AgentWorkflowFactoryContainer:
  output = AgentWorkflowFactoryContainer()
  output.add(ImplementAndReviewWorkflowFactory())
  output.add(CodeSpecsWorkflowFactory())
  output.add(CodeSpecsTestsSkeletonWorkflowFactory())
  return output
