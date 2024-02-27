from dotenv import load_dotenv
from runner import build_conversation

load_dotenv()


def run():
    make_reservation_mock, find_hotels_mock, conversation_state, response = (
        build_conversation()
    )
    print(response)


if __name__ == "__main__":
    run()
