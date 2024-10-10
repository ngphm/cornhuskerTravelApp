import datetime
from math import inf
from typing import Set

from database import *
from tracker_app import ListHolder


def get_possible_next_cities(session, city: City, date: datetime.date, day_into_journey: int) -> Set[City]:
    cities = set()
    for airport in city.airports:
        try:
            forecast: Forecast = get_object(session, Forecast, date=date, airport=airport)
            if forecast.temperature <= 45 and forecast.visibility >= 5 and forecast.weather_description not in \
                    ['Thunderstorm', 'Tornado']:
                for operator in airport.operators:
                    if operator.airplane.range <= 4000:
                        for destination in operator.airports:
                            for origin in city.airports:
                                if origin != destination:
                                    distance = get_great_circle_distance(destination.location, origin.location)
                                    if distance < operator.airplane.range:
                                        if day_into_journey < 16:
                                            cities.update(destination.cities)
                                        else:
                                            for destination_city in destination.cities:
                                                if destination_city.name == 'Lincoln' and \
                                                        destination_city.geographic_identity == 'Nebraska':
                                                    cities.add(destination_city)
        except NoResultFound:
            pass

    cities.discard(city)  # Don't just wander back to the same city
    return cities


def chose_city(possible_cities: Set[City], current_city: City) -> City:
    furthest = -inf
    furthest_distance = -inf
    furthest_city = None
    for city in possible_cities:
        if min(abs(furthest - city.latitude), abs(furthest - (city.latitude - 90))) > furthest_distance:
            furthest = city.latitude
            furthest_distance = max(abs(furthest - city.latitude), abs(furthest - (city.latitude - 90)))
            furthest_city = city
    return furthest_city


def generate_itinerary(session: Session, current_city: City, days_into_journey: int, output_itinerary: ListHolder,
                       greedy: bool):
    cities = [current_city]
    have_done_first = False  # Setting up do while
    date = datetime.date.today()
    while not have_done_first or (cities[-1] != cities[0] and days_into_journey < 17):
        inner_cities = get_possible_next_cities(session, cities[-1], date, days_into_journey)
        if len(inner_cities) > 0:
            city = chose_city(inner_cities, cities[-1])
            if city:
                cities.append(city)
            else:
                break
        else:
            break
        days_into_journey += 1
        date += datetime.timedelta(days=1)
        have_done_first = True
    cities = [f'{city.name}, {city.geographic_identity}' for city in cities]
    output_itinerary.populate_list(cities)


def request_itinerary(session, current_city: str, days_into_journey: int, lincoln_or_bust: ListHolder,
                      the_scenic_route: ListHolder) -> str:
    city = current_city.split(', ')
    current_city = get_object(session, City, name=city[0], geographic_identity=city[1])
    generate_itinerary(session, current_city, days_into_journey, lincoln_or_bust, True)
    generate_itinerary(session, current_city, days_into_journey, the_scenic_route, False)
