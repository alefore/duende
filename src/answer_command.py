from agent_command import AgentCommand, CommandOutput, CommandSyntax, Argument, ArgumentContentType, VariableMap, VariableName


class AnswerCommand(AgentCommand):

  def Name(self) -> str:
    return "answer"

  def Syntax(self) -> CommandSyntax:
    return CommandSyntax(
        name="answer",
        description="Provides the answer to the question for this conversation. This command signals the completion of the current task and provides the final answer.",
        arguments=[
            Argument(
                name=VariableName("answer"),
                arg_type=ArgumentContentType.STRING,
                description="The brief answer to the question.",
                required=True,
            )
        ],
        output_type=ArgumentContentType.STRING,
        output_description="The answer provided.",
    )

  async def run(self, inputs: VariableMap) -> CommandOutput:
    answer = inputs[VariableName("answer")]
    assert isinstance(answer, str)
    return CommandOutput(
        command_name=self.Name(),
        output=answer,
        errors="",
        summary=f"Answer provided: {answer}",
        task_done=True,
    )
