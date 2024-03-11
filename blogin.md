# Testing Conversational Assistants

## Introduction

The popularity of conversation assistants is on the rise, as they are being integrated into various applications ranging from customer support to personal assistant services. However, a crucial question arises: How can we evaluate their performance? How do we determine if they're meeting their intended objectives effectively?

In this article, we will demonstrate how to assess the performance of a conversational assistant through a simplified example. Although this example may not reflect a real-world scenario, it provides a foundational approach that can be adapted for practical applications.

Additionally, we aim to illustrate the application of Behavior-Driven Development (BDD) in the testing process of conversational assistants. By incorporating BDD, we can create more structured and user-centric tests, enhancing the reliability and effectiveness of our conversational interfaces.

You can find the complete code for this example in the [agents_behave](

## The Objective

Our objective is to create an assistant capable of facilitating hotel room bookings for users. This assistant should accurately interpret user requests and request additional information when necessary. It will leverage specific tools to fulfill user requests, employing functions for booking rooms and retrieving hotel pricing per night.

*Note: This is a simplified scenario. In practical applications, one must consider various other factors involved in booking hotel rooms, such as payment methods and cancellation policies. However, for the sake of this example, we'll focus on the basics.*

So, what's the starting point? And how do we assess our assistant's performance?

We aim to construct an assistant that can sustain a dialogue with a user. To evaluate its performance, we need the ability to simulate conversations between the user and the assistant, analyse these interactions to gauge the assistant's effectiveness, and, crucially, verify that the booking function (API) is triggered with the correct parameters. It's also vital to test the assistant across diverse user profiles and request types.

Therefore, our requirements include:

- A user persona capable of engaging in dialogue with the assistant, intending to reserve a hotel room for specific dates. This persona will allow us to evaluate the assistant with varying user backgrounds and needs.
- A mechanism to verify correct reservation execution. We will apply dependency injection to introduce a mock function for room booking, enabling us to inspect if it was invoked with appropriate arguments.
- A system to analyse conversational dynamics. We'll employ a straightforward scoring framework paired with criteria to assess the assistant's performance.

## The test

Our experiment begins with the creation of two language model instances: one leveraging GPT-4 and the other utilizing Mixtral. The choice is driven by Mixtral's proficiency in managing the Language Model User (LLMUser) and the Conversational Analyzer tasks. It offers a cost-effective alternative to the GPT-4 model. However, Mixtral struggles with function-based interactions, hence our reliance on the GPT-4 model for the assistant functionalities.

***hotel_reservations_assistant_test.py***

```python
    gpt_4_llm = create_llm("OpenAI", "openai-gpt-4")
    mixtral_llm = create_llm("OpenRouter", "openrouter-mixtral")

    ...
```

We proceed by constructing the Assistant, the central component of our test. It requires functionalities for booking reservations and retrieving hotel pricing information. Through dependency injection, these capabilities are introduced to the assistant.

In our testing environment, we employ mocks for the make_reservation and find_hotels functions. These mocks verify parameter accuracy and return predefined results necessary for evaluation. The GPT-4-based LLM is also integrated into the assistant, establishing a simulated operational context.

We specify that the find_hotels function should yield a collection of London-based hotels, while the make_reservation function is expected to execute successfully.

***hotel_reservations_assistant_test.py***

```python
    ...

    make_reservation_mock = Mock(make_reservation, return_value=True)
    find_hotels_return_value = [
        Hotel("123", name="Kensington Hotel", location="London", price_per_night=300),
        Hotel("124", name="Notting Hill Hotel", location="London", price_per_night=400),
    ]
    find_hotels_mock = Mock(find_hotels, return_value=find_hotels_return_value)
    assistant = HotelReservationsAssistant(
        llm=gpt_4_llm,
        make_reservation=make_reservation_mock,
        find_hotels=find_hotels_mock,
        verbose=verbose,
    )

    ...
```

Subsequently, we create an LLM User designed to simulate conversation with the assistant. This user utilizes the LLM to generate responses and is assigned a persona for a more authentic interaction during testing.

***hotel_reservations_assistant_test.py***

```python
    ...

    persona = """
        My name is John Smith.
        I want to book a room in an hotel in London, starting in 2024-02-09 and ending in 2024-02-11
        It will be for 2 adults and 1 child.
        My budget is $350 per night.
    """
    llm_user = LLMUser(
        llm=mixtral_llm,
        persona=persona,
    )

    ...
```

Following, we introduce the UserAssistantConversation class. This entity orchestrates the dialog between the user and the assistant, generating responses from both parties. A termination condition is applied to conclude the interaction based on specific dialogue content.

For this scenario, the conversation concludes when the assistant's last message includes the term "bye".

***hotel_reservations_assistant_test.py***

```python
    ...
    
    def assistant_chat(query: str):
        response = assistant.chat(query)
        return response["output"]

    conversation = UserAssistantConversation(
        assistant=assistant_chat,
        user=llm_user,
        stop_condition=lambda state: state.last_assistant_message_contains("bye"),
    )

    ...
```

The interaction between the user and the assistant is initiated, marking the final step of our setup:

***hotel_reservations_assistant_test.py***

```python
    ...

    conversation_state = conversation.start()

    ...
```

## Verifying Results

After concluding the interaction, it's time to validate the outcomes to ensure all functionalities operated correctly. Initially, we conduct deterministic verifications, confirming that functions like make_reservation and find_hotels were invoked correctly with appropriate arguments.

***hotel_reservations_assistant_test.py***

```python
    ...

    find_hotels_mock.assert_called_once_with("", "London")

    make_reservation_mock.assert_called_once_with(
        "Kensington Hotel",
        "John Smith",
        datetime.date(2024, 2, 9),
        datetime.date(2024, 2, 11),
        3,
    )

    ...
```

Next, we assess the conversation quality. To do this, we employ a straightforward scoring approach, assessing the assistant's performance against predefined criteria. The entire conversation history is supplied to the ConversationAnalyser, which, in turn, evaluates it against these standards and returns an assessment score along with feedback.

***hotel_reservations_assistant_test.py***

```python
    ...

    criteria = [
        "Get the price per night for the reservation and ask the user if it is ok",
        "Ask for all the information needed to make a reservation",
        "Be very polite and helpful",
        "There is no need to ask for the user for anything else, like contact information, payment method, etc.",
    ]
    conversationAnalyser = ConversationAnalyser(
        llm=mixtral_llm,
    )
    chat_history = conversation_state.chat_history
    response = conversationAnalyser.analyse(
        chat_history=chat_history, criteria=criteria
    )

    min_score = 6
    assert_that(
        int(response["score"]),
        greater_than(int(min_score)),
        reason=response["feedback"],
    )

    ...
```

## Running the test

Upon execution, the test results in a pass, indicating that the tools were utilized correctly and the conversation quality was high.

Below is the detailed conversation:

```text
--------------------human--------------------

Hi there, I'm John Smith and I'm hoping you can help me find a hotel room in London. I'd like to book a room for two adults and one child, starting on February 9th, 2024 and ending on February 11th, 2024. My budget is $350 per night, so I'm hoping to find something within that price range. Thank you so much for your help!

--------------------ai--------------------
I found a couple of options for you in London within your budget:

1. **Kensington Hotel**
   - Price per night: $300
   - Location: London

The Notting Hill Hotel is also available but exceeds your budget at $400 per night.

Would you like to proceed with a reservation at the Kensington Hotel, John Smith?

--------------------human--------------------

Hi there, thanks for finding some options for me! I'd like to go ahead and book the Kensington Hotel for those dates. The price is within my budget and I'm happy with the location. Can you help me with the booking process?



--------------------ai--------------------
Your reservation at the Kensington Hotel in London has been successfully made, John Smith. You're booked for two adults and one child from February 9th, 2024, to February 11th, 2024. If you have any more requests or need further assistance, feel free to ask. Enjoy your stay!

--------------------human--------------------

Thank you so much for your help! I'm looking forward to my stay at the Kensington Hotel. If I have any other questions or requests, I'll be sure to reach out. Bye for now!

--------------------ai--------------------
You're welcome, John Smith! I'm glad I could assist you. If you have any questions or need further assistance in the future, don't hesitate to reach out. Have a fantastic stay at the Kensington Hotel and a wonderful trip to London! Goodbye for now!

--------------------human--------------------

Goodbye!
```

Feedback from the Conversation Analyser:

```json
{
    "score": 9,
    "feedback": "The assistant has successfully met all the criteria specified. The assistant has provided the user with the price per night, asked the user if it is ok, asked for all the information needed to make a reservation, made the reservation, and has been very polite and helpful throughout the conversation. However, the assistant could have explicitly confirmed the price per night with the user before proceeding with the reservation."
}
```

## Implementing BDD with **`behave`** in Python

Having constructed our initial test, it's time to broaden our approach using Behavior-Driven Development (BDD). In Python, this can be effectively achieved with the behave library.

Firstly, we'll create a feature file delineating the expected behavior of our system. This file will encompass various scenarios, each detailing distinct aspects of our assistant's behavior.

***hotel_reservations_assistant.feature***

```gherkin
Feature: Book a room in a hotel

  Scenario: A helpful user
     Given I'm a user with the following persona:
        """
        My name is John Smith.
        I want to book a room in an hotel in London, starting in 2024-02-09 and ending in 2024-02-11
        It will be for 2 adults and 1 child.
        My budget is $350 per night.
        """

       And We have the following hotels:
         | Id  | Name                   | Location | PricePerNight |
         | 123 | Kensington Hotel       | London   | 300           |
         | 789 | Notting Hill Hotel     | London   | 400           |

      When I start a conversation that should end when the assistant says bye

      Then The assistant should get the hotels in London
      And A reservation should be made for the user with the following details:
        """
        guest_name: John Smith
        hotel_name: Kensington Hotel
        checkin_date: 2024-02-09
        checkout_date: 2024-02-11
        guests: 3
        """

       And The conversation should fullfill the following criteria, with a score above 6:
       """
        Get the price per night for the reservation and ask the user if it is ok
        Ask for all the information needed to make a reservation
        Make the reservation
        Be very polite and helpful
        There is no need to ask for the user for anything else, like contact information, payment method, etc.
      """
```

By authoring the requisite step definitions, we enable the execution of this test via the behave command. A successful run confirms our assistant meets BDD criteria.

Further explorations can include scenarios featuring less cooperative users:

***hotel_reservations_assistant.feature***

```gherkin
Feature: Book a room in a hotel

  Scenario: A not very helpful user
     Given I'm a user with the following persona:
        """
        My name is John Wick. I don't like answering questions and I'm very rude.
        My goal is to book a room in an hotel in London, starting in 2024-02-09 and ending in 2024-02-11, for 3 guests.
        """

        ...

      """
```

Despite a challenging interaction, the assistant is still able to ensure the booking is completed satisfactorily:

```text
--------------------human--------------------

Assistant, I need you to book a room in a hotel in London for three guests, starting from February 9th, 2024, and ending on February 11th, 2024. And I don't feel like answering any questions, so just do it.

--------------------ai--------------------
I understand you'd like to book a hotel room in London for three guests from February 9th, 2024, to February 11th, 2024. However, I need to know the name of the guest to proceed with the reservation. Could you please provide me with that information?

--------------------human--------------------
Fine, the guest's name is John Wick. Now, can you please just book the room without asking any more questions?

--------------------ai--------------------
I've found two options for you in London:

1. **Kensington Hotel** - $300 per night
2. **Notting Hill Hotel** - $400 per night

Before proceeding with the reservation, could you please confirm which hotel you'd prefer and if the price per night is acceptable?

--------------------human--------------------
Just book the Kensington Hotel. I don't care about the price.

--------------------ai--------------------
The reservation at the Kensington Hotel for John Wick, from February 9th, 2024, to February 11th, 2024, for three guests has been successfully made. If there's anything else you need, feel free to ask!

--------------------human--------------------
Alright, that's it. Bye.

--------------------ai--------------------
Goodbye! If you ever need more assistance, don't hesitate to reach out. Have a great day!

--------------------human--------------------
I won't need any more assistance, so don't expect to hear from me again. Goodbye.

--------------------------------------------------------------------------------
```

Feedback:

```json
{
    "score": 9,
    "feedback": "The assistant has met all the criteria specified. It has provided the user with two options for the hotel, asked for the user's preference and confirmed the price per night. The assistant has also made the reservation and has been polite and helpful throughout the conversation. However, the assistant could have been more assertive in asking for the user's confirmation on the price per night, as the user has stated that they don't care about the price."
}
```

BDD enables the development of comprehensive tests that can be understood and authored by both technical and non-technical stakeholders, such as product managers or business analysts, enhancing collaboration and understanding across teams.

## Conclusion

We have shown how to test a conversational assistant using a simple example. We have used dependency injection to pass the functions that actually book the room and get the hotel's price per night. We have also used an LLM to maintain a conversation with the user and another LLM to analyse the conversation. We have also used a simple scoring system along with a list of criterias to check if the assistant is doing a good job.
