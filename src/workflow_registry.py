from implement_workflow import ImplementAndReviewWorkflowFactory
from agent_workflow import AgentWorkflowFactoryContainer
from code_specs_workflow import CodeSpecsWorkflowFactory


def StandardWorkflowFactoryContainer() -> AgentWorkflowFactoryContainer:
  output = AgentWorkflowFactoryContainer()
  output.add(ImplementAndReviewWorkflowFactory())
  output.add(CodeSpecsWorkflowFactory())
  return output
