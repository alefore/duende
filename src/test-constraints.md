These tests have a few constraints:

* Mock is NOT allowed in this code. These tests should let all the
  dependencies of code_specs_agent be used directly.
  The only exception is mocking parts of aiofiles in tests that need to
  validate that operations are asynchronous.

* These tests are not allowed to implement BaseAgentLoop directly; instead,
  they must always use AgentLoop and AgentLoopFactory.
  These tests must NOT subclass AgentLoop nor AgentLoopFactory, nor mock any
  of their methods.

* These tests must NOT contain the 🍄 character anywhere (in order to avoid
  possible clashes with Duende, since that is already interpreting markers).

* If they need to get a conversation, these tests must get it from the
  conversation_factory. They must NOT get it from the conversational_ai.
