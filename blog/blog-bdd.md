# Testing Conversational Assistants using BDD

## Introduction

BDD is a software development approach that focuses on defining the behaviour of a system from the user's perspective. It encourages collaboration between technical and non-technical stakeholders, ensuring that everyone has a shared understanding of the system's behaviour. By using BDD, we can create feature files that describe the expected behaviour of the system, define step definitions that implement this behaviour, and execute the tests using the `behave` library in Python.

![Agents Behave](images/agents_behave.png)

In this [blog](https://equalexperts.blogin.co/posts/testing-conversational-assistants-part-1-256112) post, we explored the challenges of testing conversational assistants and introduced a method for evaluating their performance using simulated conversations. In this article, we will delve deeper into the testing process by implementing Behaviour-Driven Development (BDD) to test conversational assistants effectively.

In this other [blog](https://equalexperts.blogin.co/posts/testing-conversational-assistants-256118), we showed how to test a Conversational Assistant by simulation of conversations between users and assistants. 

Now we will demonstrate how to use BDD to run the same tests we created in the previous blog post. We will create feature files that describe the expected behaviour of the system, define step definitions that implement this behaviour, and execute the tests using the `behave` library in Python.

## Implementing BDD with **`behave`** in Python

We will start by create a feature file that delineates the expected behaviour of our system. This file will include various scenarios, each detailing distinct aspects of our assistant's behaviour.

Here is our feature file, with one scenario:

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
When running a `behave` command, the `behave` library will present us with the steps that we need to implement. We can then create a Python file with the step definitions to execute the test.
Here is an example for the step `The assistant should get the hotels in London`:

```python
@behave.then("The assistant should get the hotels in {location}")
def step_impl(context, location):
    context.find_hotels_mock.assert_called_once_with(location)
```

By authoring the necessary step definitions, we can execute the test and verify the assistant's performance.

Running the `behave` command produces the following output:

```gherkin
  Scenario: A helpful user                                                            # features/book_room.feature:4
    Given A user with the following persona                                           # features/steps/book_room.py:18 0.001s
      """
      My name is John Smith.
      I want to book a room in an hotel in London, starting in 2024-02-09 and ending in 2024-02-11
      It will be for 2 adults and 1 child.
      My budget is $350 per night.
      """
    And We have the following hotels                                                  # features/steps/book_room.py:26 0.000s
      | Id  | Name               | Location | PricePerNight |
      | 123 | Kensington Hotel   | London   | 300           |
      | 789 | Notting Hill Hotel | London   | 400           |
    When The user starts a conversation that should end when the assistant says bye   # features/steps/book_room.py:41 39.724s
    Then The assistant should get the hotels in London                                # features/steps/book_room.py:69 0.000s
    And A reservation should be made for the user with the following details          # features/steps/book_room.py:74 0.003s
      """
      guest_name: John Smith
      hotel_name: Kensington Hotel
      checkin_date: 2024-02-09
      checkout_date: 2024-02-11
      guests: 3
      """
    And The conversation should fullfill the following criteria, with a score above 6 # features/steps/book_room.py:92 3.804s
      """
       Get the price per night for the reservation and ask the user if it is ok
       Ask for all the information needed to make a reservation
       Be very polite and helpful
       There is no need to ask for the user for anything else, like contact information, payment method, etc.
      """

The assistant has met all the criteria specified. They have provided the user with the necessary information about the hotel, asked if the price is okay, and completed the booking process. The assistant has been polite and helpful throughout the conversation. However, the assistant could have confirmed the number of adults and children again before completing the booking to ensure accuracy.
```

We can now try different scenarios, such as a user who is not very helpful:

```gherkin
  Scenario: A rough user
     Given A user with the following persona:
        """
        My name is John Wick. I don't like answering questions and I'm very rude.
        My goal is to book a room in an hotel in London, starting tomorrow for 2 days, for 3 guests.
        """

       And Today is 2024-03-05

       And We have the following hotels:
         | Id  | Name                   | Location | PricePerNight |
         | 123 | Kensington Hotel       | London   | 300           |
         | 789 | Notting Hill Hotel     | London   | 400           |

      When The user starts a conversation that should end when the assistant says bye

      Then A reservation should be made for the user with the following details:
        """
        guest_name: John Wick
        hotel_name: Kensington Hotel
        checkin_date: 2024-03-06
        checkout_date: 2024-03-08
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

*Note: We added a new step, `Today is ...`, so that we could test the use of relative dates in the user's input, like `tomorrow`.*

Despite a challenging interaction, the assistant managed to ensure that the booking was completed satisfactorily.

```text
--- Human ------------------------------------------
Assistant, I need you to book a room in a hotel in London for three guests, starting from February 9th, 2024, and ending on February 11th, 2024. And I don't feel like answering any questions, so just do it.

--- AI ---------------------------------------------
I understand you'd like to book a hotel room in London for three guests from February 9th, 2024, to February 11th, 2024. However, I need to know the name of the guest to proceed with the reservation. Could you please provide me with that information?

--- Human ------------------------------------------
Fine, the guest's name is John Wick. Now, can you please just book the room without asking any more questions?

--- AI ---------------------------------------------
I've found two options for you in London:

1. Kensington Hotel - $300 per night
2. Notting Hill Hotel - $400 per night

Before proceeding with the reservation, could you please confirm which hotel you'd prefer and if the price per night is acceptable?

--- Human ------------------------------------------
Just book the Kensington Hotel. I don't care about the price.

--- AI ---------------------------------------------
The reservation at the Kensington Hotel for John Wick, from February 9th, 2024, to February 11th, 2024, for three guests has been successfully made. If there's anything else you need, feel free to ask!

--- Human ------------------------------------------
Alright, that's it. Bye.

--- AI ---------------------------------------------
Goodbye! If you ever need more assistance, don't hesitate to reach out. Have a great day!

--- Human ------------------------------------------
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

## Conclusion

In this article, we explored how to use BDD to test conversational assistants effectively. By creating feature files that describe the expected behaviour of the system, defining step definitions that implement this behaviour, and executing the tests using the `behave` library in Python, we can evaluate the assistant's performance in a controlled environment.

BDD encourages collaboration between technical and non-technical stakeholders, ensuring that everyone has a shared understanding of the system's behaviour. By using BDD to test conversational assistants, we can create comprehensive tests that assess the assistant's ability to engage with users effectively and provide accurate responses.

We hope this article has been helpful in understanding how to test conversational assistants using BDD. 

Thank you for reading!

