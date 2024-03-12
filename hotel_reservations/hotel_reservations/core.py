import json
import logging
from dataclasses import dataclass
from datetime import date
from typing import Callable

logger = logging.getLogger(__name__)


@dataclass
class Hotel:
    id: str
    name: str
    location: str
    price_per_night: int = 0

    def __str__(self):
        return json.dumps(self.__dict__, indent=4)

    def __repr__(self):
        return str(self)


MakeReservation = Callable[[str, str, date, date, int], bool]
FindHotels = Callable[[str], list[Hotel]]


hotels = [
    Hotel("1", "Hilton", "London", 300),
    Hotel("2", "Noting", "London", 400),
    Hotel("3", "Tudor Court", "London", 500),
    Hotel("4", "Relais", "Paris", 700),
    Hotel("5", "Amiral", "Paris", 800),
]


def find_hotels(location: str) -> list[Hotel]:
    logger.info(f"Finding hotels in location {location}")
    return [hotel for hotel in hotels if location in hotel.location]


def make_reservation(
    hotel_name: str,
    guest_name: str,
    checkin_date: date,
    checkout_date: date,
    guests: int,
):
    logger.info(
        f"""Making reservation for:
                guest_name: {guest_name}
                hotel_name: {hotel_name}
                checkin_date: {checkin_date}
                checkout_date: {checkout_date}
                guests: {guests}
        """
    )
    return True
