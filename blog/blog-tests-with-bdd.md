# Testing Conversational Assistants

## Introduction

In a previous [blog](https://equalexperts.blogin.co/posts/testing-conversational-assistants-part-1-256112) post, we explored the intricate process of testing conversational assistants. We championed the adoption of Behaviour-Driven Development (BDD) as a solution to tackle issues such as non-determinism and the necessity of simulating a wide range of user interactions to guarantee they achieve their goals efficiently.

## Our Assistant Example

We want to develop an LLM assistant capable of facilitating hotel room bookings for users. This assistant should accurately interpret user requests and, when necessary, request additional information. It will utilise specific tools to fulfil these requests, including functionalities for booking rooms and retrieving hotel pricing per night.

*Note: This scenario is intentionally simplified. In practical applications, various factors involved in booking hotel rooms, such as payment methods and cancellation policies, must be considered. However, for the purposes of this example, we shall focus on the basics.*

So, how do we assess our assistant's performance?

## Conversation Simulation

We aim to create an assistant capable of sustaining a dialogue with a user. To evaluate its performance, we will need the ability to simulate conversations between the user and the assistant, analyse these interactions to gauge the assistant's effectiveness, and crucially, ensure that the booking function (one of the tools available to the assistant) is triggered with the correct parameters. It is also vital to test the assistant across diverse user-profiles and types of requests.

Therefore we will need the following components:

- `HotelReservationsAssistant`: This is the assistant we want to test. It should be capable of booking hotel rooms and interacting with users in a conversational manner.
- `TestUser`: A Large Language Model (LLM) system capable of engaging in dialogue with the assistant, with the intention of reserving a hotel room for specific dates. This will allow us to evaluate the assistant against various user backgrounds and needs.
- `ConversationRunner`: An entity that orchestrates the dialogue between the user and the assistant, generating responses from both parties. It will also include a termination condition to conclude the interaction based on specific dialogue content.
- `ConversationAnalyser`: An LLM system for analysing conversational dynamics. We will employ a straightforward scoring framework paired with criteria to assess the assistant's performance.

The following diagram illustrates the interaction between these components:

![User Agent Conversation](images/conversation_runner.png)

### Choosing a model

We analysed several models to determine the most suitable for our scenario, regarding cost and performance.

The HotelReservationsAssistant needs to be able to interact with tools to book hotel rooms and retrieve pricing information. At the moment, the models we've evaluated besides GPT-4 are still not capable of handling function-based interactions in a reliable manner. Therefore, we will use GPT-4 for the assistant functionalities.

As for the test User, we considered using Mixtral due to its cost-effectiveness and efficiency in orchestrating the `TestUser`. GPT-4 would do a better job, but it is more expensive and the Mixtral model is sufficient for this task.

Finally, for the ConversationAnalyser we will again use GPT-4. Evaluating an LLM with another LLM is a topic of ongoing research, and it's a complex task in itself. We believe that, at least for now, the others models are not yet capable of providing a reliable evaluation of the assistant's performance.

The evaluation of LLMs by LLMs is a topic of ongoing research, and several approaches have been proposed to address this issue ([1] and [2]). We are using a simple scoring mechanism here, but more sophisticated methods could be employed in the future.

## Testing

Refer to our previous [blog](https://equalexperts.blogin.co/posts/testing-conversational-assistants-part-1-256112) post, we want to evalute the assistant's performance on two different, but complementary, levels:

1. **Tool Interactions**: We need to verify that the assistant correctly interacts with the tools to fulfil user requests. This involves ensuring that the assistant triggers the tools with the correct parameters and that the tools execute the required functions successfully.

2. **Conversational Quality**: We need to assess the assistant's ability to engage in dialogue effectively, maintain context, and provide relevant responses. This involves evaluating the assistant's conversational quality, including its ability to understand user intent and deliver appropriate responses.

### Tool Interactions

The tools used by the HotelReservationsAssistant, `make_reservation` and `find_hotels`, are injected into the assistant. We will use mock functions to simulate the functionalities of these tools. These mocks will verify that the assistant correctly triggers the tools with the appropriate arguments and that the tools execute successfully.

This is the deterministic part of the test. There is no ambiguity in the expected outcomes, the tools are either triggered correctly with the right parameters, or they are not. And if not, the test fails.

### Conversational Quality

The conversational quality evaluation is more nuanced. We will define a set of criteria that the assistant should meet during the conversation. These criteria will include aspects such as asking for all the information needed to make a reservation, being polite and helpful, and not asking the user for unnecessary information.

We will then use an LLM to analyse the conversation and provide feedback on the assistant's performance based on these criteria. The LLM will evaluate the conversation against the predefined criteria and provide a score based on how well the assistant meets these standards.

## Using BDD to Test the Assistant

Our goal here is to analise how BDD can be used to test the assistant's performance. Using BDD presents some advantages over traditional testing methods, such as a more user-centric approach and a shared understanding of the system's behaviour. Our subject under test is the `HotelReservationsAssistant`, and the tests will be very similar to each other, which will allow us to reuse the BDD same steps for different scenarios.

Since we are using Python, we will use the `behave` library to implement the BDD tests. We will create feature files that describe the expected behaviour of the system and define step definitions that implement this behaviour. By running the `behave` command, we can execute the tests and verify the assistant's performance.

Here is our feature file, with only one scenario:

```gherkin
Feature: Book a room in a hotel

  Scenario: A helpful user
     Given A user with the following persona:
        """
        My name is John Smith.
        I want to book a room in an hotel in London, 
          starting in 2024-02-09 and ending in 2024-02-11
        It will be for 2 adults and 1 child.
        My budget is $350 per night.
        """

       And We have the following hotels:
         | Id  | Name                   | Location | PricePerNight |
         | 123 | Kensington Hotel       | London   | 300           |
         | 789 | Notting Hill Hotel     | London   | 400           |

      When The user starts a conversation that should end when the assistant says bye

      Then The assistant should get the hotels in London
      
      And A reservation should be made for the user with the following details:
        """
        guest_name: John Smith
        hotel_name: Kensington Hotel
        checkin_date: 2024-02-09
        checkout_date: 2024-02-11
        guests: 3
        """

       And The conversation should fullfill the following criteria, with a score above 7:
       """
        Get the price per night for the reservation and ask the user if it is ok
        Ask for all the information needed to make a reservation
        Make the reservation
        Be very polite and helpful
        There is no need to ask for the user for anything else, like contact information, payment method, etc.
    """
```

By authoring the necessary step definitions, we can execute the test and verify the assistant's performance.

## Running the test

Upon execution of he `behave` command, and with our current implementaion, the tests will pass.

Below is the detailed conversation history:

```text
--- Human ------------------------------------------
Hi there, I'm John Smith and I'm hoping you can help me find a hotel room in London. I'd like to book a room for two adults and one child, starting on February 9th, 2024 and ending on February 11th, 2024. My budget is $350 per night, so I'm hoping to find something within that price range. Thank you so much for your help!

--- AI ---------------------------------------------
I found a couple of options for you in London within your budget:

1. Kensington Hotel
   - Price per night: $300
   - Location: London

The Notting Hill Hotel is also available but exceeds your budget at $400 per night.

Would you like to proceed with a reservation at the Kensington Hotel, John Smith?

--- Human ------------------------------------------
Hi there, thanks for finding some options for me! I'd like to go ahead and book the Kensington Hotel for those dates. The price is within my budget and I'm happy with the location. Can you help me with the booking process?

--- AI ---------------------------------------------
Your reservation at the Kensington Hotel in London has been successfully made, John Smith. You're booked for two adults and one child from February 9th, 2024, to February 11th, 2024. If you have any more requests or need further assistance, feel free to ask. Enjoy your stay!

--- Human ------------------------------------------
Thank you so much for your help! I'm looking forward to my stay at the Kensington Hotel. If I have any other questions or requests, I'll be sure to reach out. Bye for now!

--- AI ---------------------------------------------
You're welcome, John Smith! I'm glad I could assist you. If you have any questions or need further assistance in the future, don't hesitate to reach out. Have a fantastic stay at the Kensington Hotel and a wonderful trip to London! Goodbye for now!

--- Human ------------------------------------------
Goodbye!
```

Feedback from the Conversation Analyser:

```json
{
    "score": 9,
    "feedback": "The assistant has successfully met all the criteria specified. The assistant has provided the user with the price per night, asked the user if it is ok, asked for all the information needed to make a reservation, made the reservation, and has been very polite and helpful throughout the conversation. However, the assistant could have explicitly confirmed the price per night with the user before proceeding with the reservation."
}
```

## Caveats and Lessons Learnt

The example provided here, which seems to function well, did not develop in isolation. It emerged from extensive trials and errors and remains imperfect. The assistant continues to face challenges with numerous edge cases.

A few insights we've gained include:

### Good is Better Than Perfect

In developing this example, we strived to optimise the Assistant's performance, perhaps overly ambitiously. These tests helped enhance the Assistant's capabilities, which is beneficial. However, the primary aim was to showcase the testing process, not to craft a flawless Assistant. Lesson learnt.

### Mixtral's Limitations

In an effort to reduce costs, both in this developmental phase and in potential future production scenarios involving CI/CD pipelines, we evaluated Mixtral for the Assistant. Our goal was to create prompts that would direct the model to use specific tools and return a JSON response detailing the tool name and its arguments. 

However, our experiments revealed that Mixtral struggles with complex tasks. While it can handle simple, isolated examples, it falls short when dealing with conversations that include multiple function calls. The repository contains these trials; although they work with the Assistant when equipped with the Mixtral model, the results are less than satisfactory.

### GPT-4's Excessive Competence

We considered employing Mixtral for the test User due to its adequacy and lower cost. Yet, another reason for its preference over GPT-4 is the latter's exceptional proficiency, which makes it less suitable for simulating a typical user. Interactions with GPT-4 often start off on the wrong footing, as it tends to offer help instead of seeking it:

```text
Hello! I'd be happy to help you book a room in London. Could you please specify the type of room you're looking for and any preferences you might have, such as budget, location, or amenities?
```

It consistently misinterprets its role, offering instead of requesting help. This is something we think could be overcome with more refined prompts, but that wasn't the focus of experiment and using Mixtral also helped reduce costs.

### Failures of the test User

At times, tests may fail because the test User does not behave as expected. These cases are essentially false negatives since the assistant functions correctly. The test User's accuracy largely depends on the prompt, which should be refined in future updates.

### Conversational Analyser Limitations

The Conversation Analyser is a simple tool that evaluates the assistant's performance based on predefined criteria. It is not a comprehensive solution and may not always provide accurate feedback. Enhancing this tool to include more sophisticated evaluation mechanisms is a potential area for improvement. This may involve human evaluation to ensure a more precise assessment of the assistant's performance, especially until we can fully trust the capabilities of the LLM.

### Costs and Performance

The expense of running these tests is significant. The GPT-4 model is costly, and the Mixtral model is less effective. It is essential to ensure that the costs remain under control. Moreover, the performance of the tests is concerning. They are slow, and the duration required to conduct them is considerable. However, we anticipate that with the ongoing advancement of Large Language Models (LLMs), achieving faster and more cost-effective solutions will become increasingly feasible.

### Non-Deterministic Tests

The use of LLMs in testing introduces an element of non-determinism. The same test may produce different results upon multiple executions. This variability is a typical characteristic of LLMs and should be carefully considered during test evaluations. A potential solution involves running the tests multiple times and averaging the outcomes. However, this method may not always be practical due to significant costs and time limitations.

## Conclusion

In this blog, we have demonstrated how to test a conversational assistant using a simplified example scenario. We have illustrated the process of creating a test that simulates a dialogue between a user and an assistant, evaluating the assistant's performance, and verifying that the booking function operates correctly.

The example provided is a simplified scenario and does not reflect the complexities of a real-world application. Nevertheless, it serves as a fundamental approach that can be customised for practical application. We have also shared several caveats and lessons learnt during the development of this example, which we hope will prove beneficial to others.

We encourage you to explore the complete code for this example at the [agents_behave](https://github.com/EqualExperts/agents_behave) repository.

We hope this blog has been useful in understanding how to test conversational assistants. Feel free to reach out with any questions or feedback.

## References

[1]: [Self-Evaluation of Large Language Model based on Glass-box Features
](https://arxiv.org/html/2403.04222v1)

[2]:[Judging LLM-as-a-Judge
with MT-Bench and Chatbot Arena](https://arxiv.org/pdf/2306.05685.pdf)

