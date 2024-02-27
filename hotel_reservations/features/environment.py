from dotenv import load_dotenv
from hotel_reservations.models_config import create_model_config

load_dotenv()


def before_all(context):
    model_config = create_model_config("mixtral")
    context.model_config = model_config
