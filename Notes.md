# notes

- The use of Langchain is a bit controversial. It is a very powerful tool, but it is a bit complicated to use. You also have that strange feeling of using a blackbox and not knowing exactly what is happening inside.
However, it is a great tool to quickly prototype and test ideas. The LangSmith tool is also great to understand what is happening inside the LLMs.

- Complex function calling for non openai models is still not perfect.

- GPT is an assistant, and it's too smart. It's very hard to make him act as a user. It's like talking to a very smart person that is always trying to help you. It's not a good user experience.

- The LLMUser can fail too

- Date formats
- Agent sometime ask for the name of hotel
- Infinite loops
- Hexagonal architecture
- Dependency injection
- Tests are slow
- Using unittest and pytest
- Nice iteration process
- The test flow depeends on the user persona

Q: What do we want to test?
A: Test that the assistant PROMPT is working for different requests and User behaviour

Q: Do we want to build a product?
A: Probably not, we want to learn how to test llm agents

What’s there already?

- PromptWatch
- DeepEval

Non-deterministic

Dates are a real problem. Even the feedback can’t detect wrong calculations

What do you want to evaluate?

The conversation makes sense?
Were the right questions asked?

All of this experiments and tests were great to detect that the LLM is not very good with dates
To use or not to use langchain?

Try together and anyscale

Langstuff ecosysytem is awesome! Maybe we should try to learn how to build production code with it
However it does imply a steep learning curve

Hotel Reservation Graph:

State of the art:

- LangGraph already has this concept of a simulated User (persona)

- Use langchain?
- TDD
- How to test? Loop with LLMUsers with different personas
- Use LLM to analyse the conversation
- The test feedback is a bit slow

Build and test an LLM agent with BDD

Using user as graph node make the whole process a single thread

The hotel id is still a problem. It seems that with langgraph,the return value from find_hotels is not added to the chat history and so the llm has now way to know the hotel_id (TBC) 

Change from gpt-4 to another model and test it all again

Using several independent agents can reduce costs because we iterate on small prompts

tests: Iteration, regressions

We should be able to run the same tests repeatedly

Sometimes something hungs (langgraph?)

NEXT:

- Try to use another LLMs (not possible??)
- Run the same test several times and show a %
- Run same texts, different personas? Several times?

Test agents like Gatlin

How to test the test framework???
