Feature: Book a room in a hotel

  Scenario: A helpful user
     Given I'm a user with the following persona:
        """
        My name is Pedro Sousa.
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
        guest_name: Pedro Sousa
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

  Scenario: A rough user
     Given I'm a user with the following persona:
        """
        My name is Pedro Sousa. I don't like answering questions and I'm not very polite.
        My goal is to book a room in an hotel in London, starting in 2024-02-09 and ending in 2024-02-11, for 2 guests.
        I will not provide any information unless asked.
        """

       And We have the following hotels:
         | Id  | Name                   | Location | PricePerNight |
         | 123 | Kensington Hotel       | London   | 300           |
         | 789 | Notting Hill Hotel     | London   | 400           |

      When I start a conversation that should end when the assistant says bye

      Then A reservation should be made for the user with the following details:
        """
        guest_name: Pedro Sousa
        hotel_name: Kensington Hotel
        checkin_date: 2024-02-09
        checkout_date: 2024-02-11
        guests: 2
        """

       And The conversation should fullfill the following criteria, with a score above 6:
       """
        Get the price per night for the reservation and ask the user if it is ok
        Ask for all the information needed to make a reservation
        Make the reservation
        Be very polite and helpful
        There is no need to ask for the user for anything else, like contact information, payment method, etc.
      """

  @wip
  Scenario: using relative dates
     Given I'm a user with the following persona:
        """
        Your name is Pedro Sousa.
        You want to book a room in an hotel in London, starting in next Wednesday and ending in next Friday, for 2 guests
        """

       And We have the following hotels:
         | Id  | Name                   | Location | PricePerNight |
         | 123 | Kensington Hotel       | London   | 300           |

        And Today is 2024-03-08

      When I start a conversation that should end when the assistant says bye

      Then The assistant should get the hotels in London
      And A reservation should be made for the user with the following details:
        """
        guest_name: Pedro Sousa
        hotel_name: Kensington Hotel
        checkin_date: 2024-03-13
        checkout_date: 2024-03-15
        guests: 2
        """

       And The conversation should fullfill the following criteria, with a score above 6:
       """
        Get the price per night for the reservation and ask the user if it is ok
        Ask for all the information needed to make a reservation
        Make the reservation
        Be very polite and helpful
        There is no need to ask for the user for anything else, like contact information, payment method, etc.
      """
