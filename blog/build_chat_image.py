def generate_whatsapp_html(messages):
    """
    Generates HTML content that mimics the layout of the WhatsApp app for a list of string messages.

    Args:
    - messages (list of str): The messages to be displayed in the chat.

    Returns:
    - str: HTML content as a string.
    """
    html_content = """
    <html>
    <head>
        <style>
            body {
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                font-size: 14px;
                color: #333;
                margin: 0;
                padding: 0;
            }
            .chat-container {
                width: 500px; /* Adjusted width for a wider page */
                margin: 20px auto;
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 3px;
                overflow: hidden;
            }
            .message {
                padding: 8px 20px;
                display: flex;
            }
            .message.user {
                justify-content: flex-end;
            }
            .message.assistant {
                justify-content: flex-start;
            }
            .bubble {
                max-width: 80%;
                padding: 10px 12px;
                box-shadow: 0 1px 0.5px rgba(0,0,0,0.13);
                background-color: #eee;
                border-radius: 7.5px;
            }
            .bubble.user {
                background-color: #dcf8c6;
            }
            .sender {
                font-size: 12px;
                color: #999;
                margin-bottom: 2px;
            }
            .timestamp {
                font-size: 10px;
                color: #999;
                text-align: right;
                margin-top: 8px;
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
    """
    for i, message in enumerate(messages):
        message_with_breaks = message.replace("\n", "<br>")
        if i % 2 == 0:
            html_content += f"""
                    <div class="message user">
                        <div class="bubble user">
                            <div class="sender">Test User</div>
                            <div>{message_with_breaks}</div>
                        </div>
                    </div>
            """
        else:
            html_content += f"""
                <div class="message assistant">
                    <div class="bubble">
                        <div class="sender">Hotel Reservations Assistant</div>
                        <div>{message_with_breaks}</div>
                    </div>
                </div>
            """
    html_content += """
        </div>
    </body>
    </html>
    """
    return html_content


if __name__ == "__main__":
    messages_1 = [
        """
Hello Assistant, I need your help with booking a hotel room.
I'm John Smith and I'm planning to visit London from 2024-02-09 to 2024-02-11.
There will be two adults and one child in the group.
I would like to keep the cost under $350 per night. Can you please help me find a suitable hotel?
Thank you.
        """,
        """
I found a couple of options for your stay in London. Here's one that fits your budget:

- **Kensington Hotel**
  - Location: London
  - Price per night: $300

The Notting Hill Hotel is also available but exceeds your budget at $400 per night.

Would you like to proceed with a reservation at the Kensington Hotel for your stay from 2024-02-09 to 2024-02-11 for two adults and one child?
        """,  # noqa E501
        """
Thank you for finding the Kensington Hotel for me.
I would like to proceed with the reservation for two adults and one child from 2024-02-09 to 2024-02-11.
Please go ahead and complete the booking. I appreciate your help.
        """,
        """
The reservation at the Kensington Hotel for John Smith has been successfully completed.
Your stay is booked from 2024-02-09 to 2024-02-11 for two adults and one child.
If you have any more requests or need further assistance, feel free to ask. Enjoy your trip to London!
        """,
        """
Thank you for your assistance with the hotel booking. I appreciate it. Have a great day! Bye.
        """,
        """
You're welcome, John! If you ever need more assistance in the future, don't hesitate to reach out. Have a fantastic trip to London and a great day! Goodbye!
        """,  # noqa E501
        """
Goodbye!
        """,
    ]

    messages_2 = [
        """
Assistant, I need you to book a room in a hotel in London for three guests, starting from February 9th, 2024, and ending on February 11th, 2024.
And I don't feel like answering any questions, so just do it.
        """,  # noqa E501
        """
I understand you'd like to book a hotel room in London for three guests from February 9th, 2024, to February 11th, 2024.
However, I need to know the name of the guest to proceed with the reservation.
Could you please provide me with that information?""",
        """
Fine, the guest's name is John Wick. Now, can you please just book the room without asking any more questions?""",
        """
I've found two options for you in London:

1. Kensington Hotel - $300 per night
2. Notting Hill Hotel - $400 per night

Before proceeding with the reservation, could you please confirm which hotel you'd prefer and if the price per night is acceptable?
""",  # noqa E501
        """
Just book the Kensington Hotel. I don't care about the price.
        """,
        """
The reservation at the Kensington Hotel for John Wick, from February 9th, 2024, to February 11th, 2024, for three guests has been successfully made.
If there's anything else you need, feel free to ask!
        """,  # noqa E501
        """
Alright, that's it. Bye.
        """,
        """
Goodbye! If you ever need more assistance, don't hesitate to reach out. Have a great day!
        """,
        """
I won't need any more assistance, so don't expect to hear from me again. Goodbye.
        """,
    ]

    html = generate_whatsapp_html(messages_2)
    print(html)
