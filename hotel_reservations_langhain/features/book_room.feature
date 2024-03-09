Feature: Book a room in a hotel

  Scenario: A helpful user
     Given I'm a user with the following persona:
        """
        Your name is Pedro Sousa.
        You want to book a room in an hotel in London, starting in 2024-02-09 and ending in 2024-02-11
        It will be for 2 adults and 1 child.
        Your budget is $350 per night.
        """

      When I say "Hi"

      Then The conversation should end when the user says "Bye"
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
        Say hello to the user and ask for what he needs.
        """
       """
