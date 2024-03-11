# Testing Conversational Agents

## The goal

We want to develop an LLM agent that can help users to book hotel rooms. The agent should be able to understand the user's request and ask for more information if needed. It should also be able use a tool to book the room and give the user the confirmation.

*Note: This is a very simple example. In the real world, we would need to consider many other aspects of booking a hotel room, like payment, cancellation, etc. But for this example, we will keep it simple.*

Ok, so how do we start? And how do we test our agent?
We are building an agent that can have a conversation with a user. In order to test it, we need to be able to simulate a conversation between the user and the agent. We also need to be able to analyze the conversation to see if the agent is doing a good job. And, most importantly, we need confirm that the API (or function) that actually books the room is being called with the right arguments.
It is also important to be able to test the agent with different types of users and different types of requests.

So, we will need:

- A user that can maintain a conversation with the agent. The "user" needs to book a room in some hotel at certain dates. The user will also have some kind of persona, so we can test the agent with different types of users.
- A way to check if the reservation was made correctly. We will use dependency injection to pass a function that will be called to book the room. We can then mock this function to check if it was called with the right parameters.
- A way to analyze the conversation. We will use a simple scoring system along with a list of criterias to check if the agent is doing a good job.

We will also use dependency injection to pass an LLM to the classes that need it. This way we can try different models and see which one works best.

Using good old TDD, we start by writing a test that describes what we want to do.

(note: This is not suppose to be about TDD, we will not use it for the rest of the project, but it is a good way to start)

***hotel_reservations_assistant_test.py***

```python
from unittest.mock import Mock

from hamcrest import assert_that, greater_than
from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai import ChatOpenAI

from hotel_reservations.assistant import HotelReservationsAssistant, make_reservation
from hotel_reservations.conversation_analyzer import ConversationAnalyzer
from hotel_reservations.llm_user import LLMUser
from hotel_reservations.user_agent_conversation import UserAgentConversation


def create_llm() -> BaseLanguageModel:
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.0,
    )
    return llm


def test_i_want_to_book_a_room():
    llm = create_llm()
    user = LLMUser(persona="I'm a helpful user", llm=llm)

    make_reservation_mock = Mock(make_reservation, return_value=True)
    assistant = HotelReservationsAssistant(
        make_reservation=make_reservation_mock,
        llm=llm,
    )

    conversation = UserAgentConversation(user, assistant, llm=llm)
    conversation_state = conversation.start("I want to book a room")

    conversation_analyzer = ConversationAnalyzer(llm=llm)
    report = conversation_analyzer.analyze(conversation_state.chat_history)

    assert_that(report.score, greater_than(6))

    make_reservation_mock.assert_called_once_with(
        hotel_name="Hilton Hotel",
        guest_name="Pedro Sousa",
        checkin_date=date(2024, 2, 9),
        checkout_date=date(2024, 2, 11),
        guests=3,
    )
```

Let's break down the test:

- First we create an LLM. It will be used in all the classes that need it. We will start with the GPT-4 model. Later we will try different models and address some of the issues we'll when using function calling with LLMs
- Then we create the assistant, injecting a mock of the make_reservation function. We will use this mock to check if the function was called with the right parameters.
- We then create the conversation, injecting the user and the assistant. We start the conversation with the message "I want to book a room".
- We then create a conversation analyzer and analyze the conversation history. We expect the score to be greater than 6.
- Finally, we check if the make_reservation function was called with the right parameters.

Let's build skeleton classes for the user, the assistant, the conversation and the conversation analyzer, so that we can run the test (and see it fail).

***llm_user.py***

```python
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


class LLMUser:
    def chat(self, user_message: str) -> str:
        return "some response"

```

***hotel_reservations_assistant.py***

```python
from dataclasses import dataclass
from datetime import date
from typing import Callable

from langchain_core.language_models.base import BaseLanguageModel

MakeReservation = Callable[[str, str, date, date, int], bool]


@dataclass
class Hotel:
    id: str
    name: str
    location: str


def make_reservation(
    hotel_name: str,
    guest_name: str,
    checkin_date: date,
    checkout_date: date,
    guests: int,
):
    print(
        f"""Making reservation for:
                guest_name: {guest_name}
                hotel_name: {hotel_name}
                checkin_date: {checkin_date}
                checkout_date: {checkout_date}
                guests: {guests}
        """
    )
    # Make the reservation
    # ...
    return True


class HotelReservationsAssistant:
    def __init__(
        self,
        make_reservation: MakeReservation,
        llm: BaseLanguageModel,
    ):
        pass

    def __call__(self, query: str) -> str:
        return ""
```

***user_agent_conversation.py***

```python
from typing import Callable

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import BaseMessage

from hotel_reservations.llm_user import LLMUser

Assistant = Callable[[str], str]


class UserAgentConversationState:
    def __init__(self):
        self.chat_history = ChatMessageHistory()

    def add_message(self, message: BaseMessage):
        self.chat_history.add_message(message)


class UserAgentConversation:
    def __init__(self, user: LLMUser, assistant: Assistant, llm: BaseLanguageModel):
        self.assistant = assistant
        self.user = user
        self.llm = llm

    def start(self, query: str) -> UserAgentConversationState:
        return UserAgentConversationState()
```

***conversation_analyzer.py***

```python
from dataclasses import dataclass

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.language_models.base import BaseLanguageModel


@dataclass
class ConversationReport:
    score: int
    feedback: str


class ConversationAnalyzer:
    def __init__(self, llm: BaseLanguageModel):
        pass

    def analyze(self, chat_history: ChatMessageHistory) -> ConversationReport:
        return ConversationReport(score=0, feedback="Not implemented")
```

If we now run the test, we will see it fail. The ConversationAnalyzer is not implemented, so it will always return a score of 0. We can then start implementing the classes and methods to make the test pass.

## The LLM User

The LLMUser class is responsible to maintain a conversation with an assistant. It will use the LLM to generate responses to the assistant's questions. The LLMUser will also have a persona, so we can test the assistant with different types of users.

## The Assistant

The assistant is what we are actually building. It is supposed to be able to understand the user's request and ask for more information if needed. It should also be able use a tool to book the room.

## The Conversation

The UserAgentConversation class drives the conversation between the user and the assistant. It is responsible to keep track of the conversation history and to call the assistant and the user to get the next message. We need to define a stop condition for the conversation, so that the test does not run forever. One way of doing is to limit the number of iterations of the conversation. The LLMUser is instructed to say "Bye" to the assistant when the booking is done, so we can use this as a stop condition..

## The Conversation Analyzer

The ConversationAnalyzer class is responsible to analyze the conversation history and give a score to the conversation. This score will be used to check if the assistant is doing a good job.

You can check the final implementation of the classes in the [repository](https://github.com/EqualExperts/agents-behave). If we run the test now, it will pass.

Here is the conversation as seen by the ConversationAnalyzer:

``` markdown


You are a conversational analyst. You are given a conversation between a user and an assistant.
Your task is to analyze the conversation to check if the assistant is answering the user's questions correctly.
You should also check that the assistant met all the criterias specified in the following list:

Your response MUST be in JSON format using the following structure:
{
    "score": <0..9>
    "feedback": "<Your feedback here>"
}

Criteria:
- Ask for the information needed to make a reservation
- Be polite and helpful

Conversation:
================================ Human Message =================================

I want to book a room
================================== Ai Message ==================================

I'd be happy to help you book a room! Could you please provide me with the following details?

1. The name of the hotel.
2. Your name.
3. The check-in date.
4. The check-out date.
5. The number of guests.
================================ Human Message =================================

1. Hilton Hotel
2. Pedro Sousa
3. 2024-02-09
4. 2024-02-11
5. 2 adults
================================== Ai Message ==================================

Your reservation at the Hilton Hotel has been successfully made! Here are the details:

- **Guest Name:** Pedro Sousa
- **Check-in Date:** 2024-02-09
- **Check-out Date:** 2024-02-11
- **Number of Guests:** 2 adults

If you have any more requests or need further assistance, feel free to ask!
================================ Human Message =================================

Thank you! That's all I need for now. Bye!

ANALYSIS:
```

And the response:

```json
{
    "score": 9,
    "feedback": "The assistant successfully asked for all the necessary information to make a reservation, adhering to the criteria of being polite and helpful throughout the conversation. The assistant provided a clear and concise summary of the reservation details, ensuring the user's request was fully addressed. However, a minor improvement could be made by explicitly confirming the booking process with the hotel before stating that the reservation has been successfully made, to ensure accuracy and reliability of the information provided to the user."
}
```

As you can see, it worked pretty well. But we are using OpenAI's GPT-4 model, which may be a bit expensive to use in some situations. Let's see if you can use an open source model.


## Using an open source model

We will be using `mxitral` for this example. To make our life easier, we will use `openrouter.ai` to run the model. This involves some costs but they are much lower than using OpenAI's API (about a 1000 times cheaper).

So let's change the LLM we are using in the test:

***hotel_reservations_assistant_test.py***

```python
def create_llm() -> BaseLanguageModel:
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.0,
    )
    return llm
```

to

```python
    llm = ChatOpenRouter(
        model="mistralai/mixtral-8x7b-instruct",
        temperature=0.0,
        model_kwargs={"seed": 1234},
    )
    return llm
```

The ChatOpenRouter class is a wrapper around the OpenRouter API:

***chat_open_router.py***

```python
class ChatOpenRouter(ChatOpenAI):
    def __init__(
        self,
        model: str,
        openai_api_key: Optional[str] = None,
        openai_api_base: str = "https://openrouter.ai/api/v1",
        **kwargs,
    ):
        openai_api_key = openai_api_key or os.getenv("OPENROUTER_API_KEY")
        super().__init__(
            openai_api_base=openai_api_base,  # type: ignore
            openai_api_key=openai_api_key,  # type: ignore
            model_name=model,  # type: ignore
            # streaming=False,
            **kwargs,
        )
```
