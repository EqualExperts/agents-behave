# Testing Conversational Assistants using BDD

## Introduction

The popularity of conversational assistants is on the rise, finding applications in various fields such as customer support and personal services. However, evaluating their performance presents a significant challenge, raising questions about how to ensure they meet their intended goals.

This article presents a method for evaluating the performance of conversational assistants, employing a simplified example. Although this example is not derived directly from real-life situations, it sets the foundation for practical applications.

Moreover, the article details how Behavior-Driven Development (BDD) can enhance the testing process for these assistants. By making tests more structured and user-focused, BDD increases the reliability and effectiveness of conversational assistants. The complete code for the example is accessible in the [agents_behave](https://github.com/EqualExperts/agents-behave) repository.

## The Objective

Our objective is to develop an assistant capable of facilitating hotel room bookings for users. This assistant should accurately interpret user requests and request additional information when necessary. It will utilise specific tools to fulfil user requests, employing functionalities for booking rooms and retrieving hotel pricing per night.

*Note: This scenario is simplified. In practical applications, various factors involved in booking hotel rooms, such as payment methods and cancellation policies, must be considered. However, for this example, we will focus on the basics.*

So, what is the starting point, and how do we assess our assistant's performance?

We aim to create an assistant capable of sustaining a dialogue with a user. To evaluate its performance, we will need the ability to simulate conversations between the user and the assistant, analyse these interactions to gauge the assistant's effectiveness, and crucially, ensure that the booking function (API) is triggered with the correct parameters. It is also vital to test the assistant across diverse user profiles and types of requests.

Therefore, our requirements include:

- `LLMUser`: An LLM system capable of engaging in dialogue with the assistant, with the intention of reserving a hotel room for specific dates. This will allow us to evaluate the assistant against various user backgrounds and needs.
- `HotelReservationsAssistant`: Another LLM system capable of booking hotel rooms and retrieving hotel pricing information using tools. This assistant will be evaluated based on its ability to fulfil user requests and the quality of its conversations.
- `UserAssistantConversation`: An entity that orchestrates the dialogue between the user and the assistant, generating responses from both parties. It will also include a termination condition to conclude the interaction based on specific dialogue content.
- `ConversationAnalyser`: An LLM system for analysing conversational dynamics. We will employ a straightforward scoring framework paired with criteria to assess the assistant's performance.

The following diagram illustrates the interaction between these components:

==DIAGRAM==

## A first test

We will begin by creating a test that simulates a conversation between a user and an assistant. This test will evaluate the assistant's ability to book a hotel room in London for specific dates, catering to the user's budget and guest requirements. Additionally, we will assess the conversational quality of the assistant, ensuring it meets predefined criteria.

Our experiment starts with the creation of two language model instances: one using the `gpt-4-turbo-preview` model and the other utilising the `mixtral-8x7b-instruct` model. The choice is driven by Mixtral's proficiency in managing the `LLM User` and `Conversational Analyser` tasks. It offers a cost-effective alternative to the GPT-4 model. However, Mixtral struggles with function-based interactions, leading us to rely on the GPT-4 model for the assistant functionalities. Another reason for using Mixtral for the LLM User will be discussed later.

```python
    gpt_4_llm = create_llm("GPT-4", "openai-gpt-4")
    mixtral_llm = create_llm("Mixtral", "openrouter-mixtral")
```

*Note: `create_llm` is a helper function that creates an instance of an LLM. The complete code is available in the repository mentioned above.*

We then proceed to construct the Assistant, the central component of our test. It requires functionalities for booking reservations and retrieving hotel pricing information. Through dependency injection, these capabilities are introduced to the assistant.

In our testing environment, we employ mocks for the `make_reservation` and `find_hotels` functions. These mocks verify parameter accuracy and return predefined results necessary for evaluation.

We specify that the `find_hotels` function should yield a collection of hotels based in London, while the `make_reservation` function is expected to execute successfully.

```python
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
```

Next, we create an LLM User designed to simulate conversations with the assistant. This user employs the LLM to generate responses and is assigned a persona for a more authentic interaction during testing.

```python

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
```

Finally, we introduce the `UserAssistantConversation` class. This entity orchestrates the dialogue between the user and the assistant, generating responses from both parties. A termination condition is applied to conclude the interaction based on specific dialogue content.

In this scenario, the conversation concludes when the assistant's last message includes the term "bye".

```python
    
    def assistant_chat_wrapper(query: str):
        response = assistant.chat(query)
        return response["output"]

    conversation = UserAssistantConversation(
        assistant=assistant_chat_wrapper,
        user=llm_user,
        stop_condition=lambda state: state.last_assistant_message_contains("bye"),
    )
```

The interaction between the user and the assistant is then initiated, marking the final step of our setup:

```python

    conversation_state = conversation.start()
```

## Verifying Results

Following the conclusion of the interaction, it is essential to validate the outcomes to ensure that all functionalities have performed correctly. Initially, we conduct deterministic verifications, confirming that functions such as `make_reservation` and `find_hotels` were invoked correctly with the appropriate arguments.

```python

    find_hotels_mock.assert_called_once_with("", "London")

    make_reservation_mock.assert_called_once_with(
        "Kensington Hotel",
        "John Smith",
        datetime.date(2024, 2, 9),
        datetime.date(2024, 2, 11),
        3,
    )
```

Next, we assess the quality of the conversation. To achieve this, we utilise a straightforward scoring approach, evaluating the assistant's performance against predefined criteria. The entire conversation history is provided to the `ConversationAnalyser`, which then assesses it against these standards and returns an evaluation score, along with feedback.

```python

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
```

## Running the test

Upon execution, the test results in a pass, indicating that the tools were utilised correctly and the conversation quality was high.

Below are the detailed conversation history:

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

Goobye!
```

Feedback from the Conversation Analyser:

```json
{
    "score": 9,
    "feedback": "The assistant has successfully met all the criteria specified. The assistant has provided the user with the price per night, asked the user if it is ok, asked for all the information needed to make a reservation, made the reservation, and has been very polite and helpful throughout the conversation. However, the assistant could have explicitly confirmed the price per night with the user before proceeding with the reservation."
}```

## Implementing BDD with **`behave`** in Python

Having constructed our initial test, it is time to broaden our approach by using Behaviour-Driven Development (BDD). In Python, this can be effectively achieved with the **`behave`** library.

First, we will create a feature file that delineates the expected behaviour of our system. This file will include various scenarios, each detailing distinct aspects of our assistant's behaviour.

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

By authoring the necessary step definitions, we facilitate the execution of this test through the 'behave' command. A successful run confirms that our assistant meets the Behaviour-Driven Development (BDD) criteria.

Further explorations may involve scenarios featuring less cooperative users:


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

Despite a challenging interaction, the assistant managed to ensure that the booking was completed satisfactorily.

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

-------------------------------------------------------------------------------
```

Feedback:

```json
{
    "score": 9,
    "feedback": "The assistant has met all the criteria specified. It has provided the user with two options for the hotel, asked for the user's preference and confirmed the price per night. The assistant has also made the reservation and has been polite and helpful throughout the conversation. However, the assistant could have been more assertive in asking for the user's confirmation on the price per night, as the user has stated that they don't care about the price."
}
```

BDD facilitates the creation of comprehensive tests that are accessible to both technical and non-technical stakeholders, including product managers and business analysts. This approach enhances collaboration and understanding across teams.

## Caveats and Lessons Learned

The example provided here, which seems to function well, did not develop in isolation. It emerged from extensive trials and errors and remains imperfect. The assistant continues to face challenges with numerous edge cases.

A few insights we've gained include:

### Good is Better Than Perfect

In developing this example, we strived to optimise the Assistant's performance, perhaps overly ambitiously. These tests helped enhance the Assistant's capabilities, which is beneficial. However, the primary aim was to showcase the testing process, not to craft a flawless Assistant. Lesson learnt.

### Mixtral's Limitations in Handling Complex Function Calls

To cut costs—considering both this developmental phase and potential future production scenarios involving CI/CD pipelines—we tested Mixtral for the Assistant. We aimed to craft prompts directing the model to use specific tools and return a JSON response detailing the tool name and arguments. However, our experiments indicated that Mixtral struggles with this task. It can manage simple, isolated examples but fails with conversations that involve multiple function calls. The repository includes these trials; although they function with the Assistant equipped with the Mixtral model, the outcomes are subpar.

### GPT-4's Excessive Competence

We considered employing Mixtral for the LLM User due to its adequacy and lower cost. Yet, another reason for its preference over GPT-4 is the latter's exceptional proficiency, which makes it less suitable for simulating a typical user. Interactions with GPT-4 often start off on the wrong footing, as it tends to offer help instead of seeking it:

```text
Hello! I'd be happy to help you book a room in London. Could you please specify the type of room you're looking for and any preferences you might have, such as budget, location, or amenities?
```

It consistently misinterprets its role, offering instead of requesting help. Despite various attempts with different prompts, we could not secure satisfactory outcomes. This area requires future enhancement.

### Failures of the LLM User

At times, tests may fail because the LLM User does not behave as expected. These cases are essentially false negatives since the assistant functions correctly. The LLM User's accuracy largely depends on the prompt, which should be refined in future updates.

### Costs and Performance

The expense of running these tests is significant. The GPT-4 model is costly, and the Mixtral model less effective. It is essential to ensure that the costs remain under control. Moreover, the performance of the tests is concerning. They are slow, and the duration required to conduct them is considerable. However, we anticipate that with the ongoing advancement of LLMs, achieving faster and more cost-effective solutions will become increasingly feasible.

## Conclusion

In this article, we have demonstrated how to test a conversational assistant using BDD. We have illustrated the process of creating a test that simulates a dialogue between a user and an assistant, evaluating the assistant's performance, and verifying that the booking function operates correctly.

The example provided is a simplified scenario and does not reflect the complexities of a real-world application. Nevertheless, it serves as a fundamental approach that can be customised for practical application. We have also shared several caveats and lessons learnt during the development of this example, which we hope will prove beneficial to others. We encourage you to explore the complete code for this example at the [agents_behave](https://github.com/EqualExperts/agents_behave) repository.

We hope this article has been useful in understanding how to test conversational assistants using BDD. If you have any questions or feedback, please feel free to reach out. Thank you for reading!
