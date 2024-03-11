# Testing Conversational Assistants using BDD

Optimizing Chatbot Performance: A Comprehensive Guide to Behavior-Driven Development Testing | From Theory to Practice: Enhancing Conversational Assistants for Superior User Engagement

## Introduction

The popularity of conversation assistants is on the rise, as they are being integrated into various applications ranging from customer support to personal assistant services. However, a crucial question arises: How can we evaluate their performance? How do we determine if they're meeting their intended objectives effectively?

In this article, we will demonstrate how to assess the performance of a conversational assistant through a simplified example. Although this example may not reflect a real-world scenario, it provides a foundational approach that can be adapted for practical applications.

Additionally, we aim to illustrate the application of Behavior-Driven Development (BDD) in the testing process of conversational assistants. By incorporating BDD, we can create more structured and user-centric tests, enhancing the reliability and effectiveness of our conversational interfaces.

You can find the complete code for this example in the [agents_behave](https://github.com/EqualExperts/agents-behave) repo.

## The Objective

Our objective is to create an assistant capable of facilitating hotel room bookings for users. This assistant should accurately interpret user requests and request additional information when necessary. It will leverage specific tools to fulfill user requests, employing functions for booking rooms and retrieving hotel pricing per night.

*Note: This is a simplified scenario. In practical applications, one must consider various other factors involved in booking hotel rooms, such as payment methods and cancellation policies. However, for the sake of this example, we'll focus on the basics.*

So, what's the starting point? And how do we assess our assistant's performance?

We aim to construct an assistant that can sustain a dialogue with a user. To evaluate its performance, we need the ability to simulate conversations between the user and the assistant, analyse these interactions to gauge the assistant's effectiveness, and, crucially, verify that the booking function (API) is triggered with the correct parameters. It's also vital to test the assistant across diverse user profiles and request types.

Therefore, our requirements include:

- A user persona capable of engaging in dialogue with the assistant, intending to reserve a hotel room for specific dates. This persona will allow us to evaluate the assistant with varying user backgrounds and needs.
- A mechanism to verify correct reservation execution. We will apply dependency injection to introduce a mock function for room booking, enabling us to inspect if it was invoked with appropriate arguments.
- A system to analyse conversational dynamics. We'll employ a straightforward scoring framework paired with criteria to assess the assistant's performance.

## A first test

We'll begin by creating a test that simulates a conversation between a user and the assistant. This test will evaluate the assistant's ability to book a hotel room in London for specific dates, catering to a user's budget and guest requirements. We'll also assess the assistant's conversational quality, ensuring it meets predefined criteria.

Our experiment begins with the creation of two language model instances: one using the `gpt-4-turbo-preview` model and the other utilizing `mixtral-8x7b-instruct`. The choice is driven by Mixtral's proficiency in managing the `LLM User` and the `Conversational Analyzer` tasks. It offers a cost-effective alternative to the GPT-4 model. However, Mixtral struggles with function-based interactions, hence our reliance on the GPT-4 model for the assistant functionalities.

```python
    gpt_4_llm = create_llm("GPT-4", "openai-gpt-4")
  mixtral_llm = create_llm("Mixtral", "openrouter-mixtral")
```

*Note: `create_llm` is a helper function that creates an instance of an LLM. You can look at the complete code in the repo mentioned above.*

We proceed by constructing the Assistant, the central component of our test. It requires functionalities for booking reservations and retrieving hotel pricing information. Through dependency injection, these capabilities are introduced to the assistant.

In our testing environment, we employ mocks for the make_reservation and find_hotels functions. These mocks verify parameter accuracy and return predefined results necessary for evaluation.

We specify that the find_hotels function should yield a collection of London-based hotels, while the make_reservation function is expected to execute successfully.

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

Subsequently, we create an LLM User designed to simulate conversation with the assistant. This user utilizes the LLM to generate responses and is assigned a persona for a more authentic interaction during testing.

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

Following, we introduce the `UserAssistantConversation` class. This entity orchestrates the dialog between the user and the assistant, generating responses from both parties. A termination condition is applied to conclude the interaction based on specific dialogue content.

For this scenario, the conversation concludes when the assistant's last message includes the term "bye".

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

The interaction between the user and the assistant is initiated, marking the final step of our setup:

```python

    conversation_state = conversation.start()
```

## Verifying Results

After concluding the interaction, it's time to validate the outcomes to ensure all functionalities operated correctly. Initially, we conduct deterministic verifications, confirming that functions like make_reservation and find_hotels were invoked correctly with appropriate arguments.

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

Next, we assess the conversation quality. To do this, we employ a straightforward scoring approach, assessing the assistant's performance against predefined criteria. The entire conversation history is supplied to the `ConversationAnalyser`, which, in turn, evaluates it against these standards and returns an assessment score along with feedback.

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

Goobye!
```

Feedback from the Conversation Analyser:

```json
{
    "score": 9,
    "feedback": "The assistant has successfully met all the criteria specified. The assistant has provided the user with the price per night, asked the user if it is ok, asked for all the information needed to make a reservation, made the reservation, and has been very polite and helpful throughout the conversation. However, the assistant could have explicitly confirmed the price per night with the user before proceeding with the reservation."
}```

## Implementing BDD with **`behave`** in Python

Having constructed our initial test, it's time to broaden our approach using Behavior-Driven Development (BDD). In Python, this can be effectively achieved with the ***`behave`*** library.

Firstly, we'll create a feature file delineating the expected behavior of our system. This file will encompass various scenarios, each detailing distinct aspects of our assistant's behavior.

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

-------------------------------------------------------------------------------
```

Feedback:

```json
{
    "score": 9,
    "feedback": "The assistant has met all the criteria specified. It has provided the user with two options for the hotel, asked for the user's preference and confirmed the price per night. The assistant has also made the reservation and has been polite and helpful throughout the conversation. However, the assistant could have been more assertive in asking for the user's confirmation on the price per night, as the user has stated that they don't care about the price."
}
```

BDD enables the development of comprehensive tests that can be understood and authored by both technical and non-technical stakeholders, such as product managers or business analysts, enhancing collaboration and understanding across teams.

## Caveats and Lessons Learned

The example provided here, which appears to be functioning well, did not emerge in isolation. It resulted from extensive trial and error and is still far from perfect. The assistant still struggles with numerous edge cases.

A few things we've learned along the way include:

### Good is better than perfect

During the development of this example, we aimed to optimize the Assistant's performance, possibly too zealously. Conducting these types of tests did helped us enhance the Assistant's capabilities, which is a good thing. However, the goal of this example was to demonstrate the testing process, not to create a perfect Assistant. Lesson learned.

### Mixtral's Limitations in Handling Complex Function Calls

To reduce costs—considering both this development phase and future production environments where tests might run on a CI/CD pipeline—we experimented with Mixtral for the Assistant. We attempted to construct prompts that would direct the model to use specific tools and return a JSON response with the tool name and arguments. Our experiments revealed that Mixtral is unsuitable for this task. It manages simple, one-off examples but cannot handle a conversation involving function calls. The repository contains these experiments, and while they run when the Assistant is equipped with the Mixtral model, the results are subpar.

### GP$-4 is too good for the job

We considered using Mixtral for the LLM User because it is adequate and less costly. However, another reason to prefer it over GPT-4 is that GPT-4 is an exceptionally competent assistant, making it less ideal for simulating a user. Conversations with GPT-4 often begin with the user saying something like:

```text
Hello! I'd be happy to help you book a room in London. Could you please specify the type of room you're looking for and any preferences you might have, such as budget, location, or amenities?
```

It fails to recognize that it should be requesting assistance rather than offering it. Despite numerous attempts with different prompts, we could not achieve satisfactory results. This is an area for future improvement.

### Failures of the LLM User

Occasionally, tests may fail because the LLM User does not act as anticipated. These instances are actually false negatives since the assistant functions correctly. We need to enhance the LLM User to increase its reliability.

## Conclusion

In this article, we've demonstrated how to test a conversational assistant using BDD. We've shown how to create a test that simulates a conversation between a user and an assistant, evaluate the assistant's performance, and verify that the booking function was executed correctly. 

The example provided here is a simplified scenario and does not reflect a real-world application. However, it serves as a foundational approach that can be adapted for practical use. We've also shared some of the caveats and lessons learned during the development of this example, which we hope will be useful to others.  We encourage you to explore the complete code for this example in the [agents_behave](https://github.com/EqualExperts/agents-behave) repo.

We hope this article has been helpful in understanding how to test conversational assistants using BDD. If you have any questions or feedback, please feel free to reach out. Thank you for reading!
