from implement_workflow import ImplementAndReviewWorkflowFactory
from agent_workflow import AgentWorkflowFactoryContainer


def StandardWorkflowFactoryContainer() -> AgentWorkflowFactoryContainer:
  output = AgentWorkflowFactoryContainer()
  output.add(ImplementAndReviewWorkflowFactory())
  return output
