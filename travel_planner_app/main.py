import traceback
from datetime import datetime
from json import dumps
from math import inf
from typing import Iterator, List

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.uix.label import Label

import csv_handler
import database
from database import Database
from itineraries import request_itinerary
from rest import RESTConnection
from tracker_app import TrackerApp, ListHolder, TwoListItem

lincoln_latitude = '40.8'
lincoln_longitude = '-96.7'
UNITS = 'metric'
airport_list = csv_handler.store_airports('airports.csv')


class TravelApp(TrackerApp):
    Window.size = (700, 600)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.records = []
        self.user_api = None

    def after_build(self, _time):
        self.root.current = 'credentials'

    def create_session(self):
        pass  # overrides the startup session creation

    def validate_ratings_clicked(self):
        reviews = database.get_objects(self.session, database.Review)
        to_validate_reviews = {}
        for review in reviews:
            current_rating = database.get_object(self.session, database.Operator,
                                                 operator_id=review.operator_id).rate_my_pilot_score
            to_validate_reviews[f'New rating: {review.review}'] = [f'Current Average Rating: {current_rating}',
                                                                   review.review_id]
        self.root.get_screen('update_ratings').ids.update_rating_list.populate_two_line_list(
            to_validate_reviews)
        self.root.transition.direction = 'left'
        self.root.current = 'update_ratings'

    def accept_rating_clicked(self):
        try:
            if len(self.root.get_screen('update_ratings').ids.update_rating_list.selected_elements) > 0:
                review_id = self.root.get_screen('update_ratings').ids.update_rating_list.selected_elements[0].id
                review = database.get_object(self.session, database.Review,
                                             review_id=review_id)
                operator = review.operator
                current_score = operator.rate_my_pilot_score
                new_score = review.review
                operator.rate_my_pilot_score = (current_score + new_score) / 2
                database.delete_object(self.session, database.Review, review_id=review_id)
                selected_item = self.root.get_screen('update_ratings').ids.update_rating_list.selected_elements[0]
                selected_item.parent.selected_elements.clear()
                selected_item.parent.remove_widget(selected_item)
                self.root.get_screen('main_menu').to_update -= 1
                self.session.commit()
                self.create_popup('Operator\'s rating updated successfully')
            else:
                self.create_popup('Please select an item')
        except Exception as exception:
            traceback.print_exc()
            self.create_popup(f'Database connection failed!\nCause: {exception}')

    def validate_location_clicked(self):
        if len(self.root.get_screen('validate_locations').ids.validate_locations_list.selected_elements) > 0:
            item_selected = self.root.get_screen('validate_locations').ids.validate_locations_list.selected_elements[0]
            item_type = item_selected.secondary_text
            item_name = item_selected.text
            if 'Airport' in item_type:
                self.call_csv_by_identifier(item_selected)
            elif 'City' in item_type:
                self.call_geocoding_api_by_name(item_name)

    def validate_locations(self, records):
        distances = []
        selected_item = self.root.get_screen('validate_locations').ids.validate_locations_list.selected_elements[0]
        city_name = self.root.get_screen('validate_locations').ids.validate_locations_list.selected_elements[0].text
        invalid_city = database.get_object(self.session, database.City, name=city_name)
        latitude = invalid_city.latitude
        longitude = invalid_city.longitude
        try:
            for record in records:
                real_latitude = record['lat']
                real_longitude = record['lon']
                if latitude - 1 <= real_latitude <= latitude + 1 and longitude - 1 <= real_longitude <= longitude + 1:
                    updating_city = database.get_object(self.session, database.City, name=city_name)
                    updating_city.valid = 1
                    self.session.commit()
                    selected_item.parent.selected_elements.clear()
                    selected_item.parent.remove_widget(selected_item)
                    self.root.get_screen('main_menu').to_validate -= 1
                    return self.create_popup('City was successfully validated.')
                distance = database.get_great_circle_distance((latitude, longitude), (real_latitude, real_longitude))
                distances.append(distance)
            shortest_distance = inf
            shortest_distance_index = inf
            if len(distances) != 0:
                for i in range(len(distances)):
                    if distances[i] < shortest_distance:
                        shortest_distance = distances[i]
                        shortest_distance_index = i
                closest_city = records[shortest_distance_index]
                closest_city_latitude = closest_city['lat']
                closest_city_longitude = closest_city['lon']
                self.create_choice_popup(
                    f'City could not be validated. A nearby city with the same name has longitude: {closest_city_longitude} and latitude: {closest_city_latitude}. Do you want to use this data or keep your data?',
                    lambda _obj: self.keep_my_data_clicked(invalid_city),
                    lambda _obj: self.use_official_data_clicked(invalid_city, closest_city_latitude,
                                                                closest_city_longitude))


            else:
                selected_item.parent.selected_elements.clear()
                selected_item.parent.remove_widget(selected_item)
                self.create_popup('No city with such name found. City could not be validated and will be deleted.')
                database.delete_object(self.session, database.City, city_id=invalid_city.city_id)
                self.root.get_screen('main_menu').to_validate -= 1
                self.session.commit()
        except Exception as e:
            traceback.print_exc()
            print(e)

    def remove_item_widget(self):
        selected_item = self.root.get_screen('validate_locations').ids.validate_locations_list.selected_elements[0]
        selected_item.parent.selected_elements.clear()
        selected_item.parent.remove_widget(selected_item)

    def keep_my_data_clicked(self, element):
        element.valid = True
        self.session.commit()
        self.remove_item_widget()
        self.root.get_screen('main_menu').to_validate -= 1
        self.close_popup(None)

    def use_official_data_clicked(self, element, new_latitude, new_longitude, new_name=None):
        element.latitude = new_latitude
        element.longitude = new_longitude
        if new_name is not None:
            element.name = new_name
        element.valid = True
        self.session.commit()
        self.remove_item_widget()
        self.root.get_screen('main_menu').to_validate -= 1
        self.close_popup(None)

    def post_init_create_session(self, authority: str, port: str, database_name: str, username: str,
                                 password: str):
        if password == '':
            self.create_popup('Please enter the password.')
        else:
            try:
                url = Database.construct_mysql_url(authority, port, database_name, username, password)
                self.operator_database = Database(url)
                self.session = self.operator_database.create_session()
                _connection = self.session.connection()  # raises error if connection is not made
            except Exception as exception:
                traceback.print_exc()
                self.create_popup(f'Database connection failed!\nCause: {exception}')

    def on_records_loaded(self, _, response):
        print(dumps(response, indent=4, sort_keys=True))
        # issue with unfilled parameter
        # self.records = self.format_forecast_record(self.session, response,)

    def on_records_not_loaded(self, _, error):
        Logger.error(f'{self.__class__.__name__}: {error}')

    # def connect_to_weather_api(self, authority: str, port: str, api_key: str):
    def connect_to_weather_api(self, authority: str, port: str, api_key: str, latitude, longitude):
        self.records = []
        if api_key == '':
            return 'Please enter the API key.'
        else:
            try:
                connection = RESTConnection(authority, port, '/data/2.5')
                connection.send_request(
                    'onecall',
                    {
                        'appid': api_key,
                        'lat': latitude,
                        'lon': longitude,
                        'units': UNITS,
                        'exclude': 'minutely,hourly,alerts'
                    },
                    None,
                    self.on_records_loaded,
                    self.on_records_not_loaded,
                    self.on_records_not_loaded
                )
                self.user_api = api_key
            except Exception as error:
                return f'Call OpenWeather API failed!\nCause: {error}'

    def use_credentials(self, authority: str, port: str, database_name: str, username: str, password: str,
                        open_weather_authority: str,
                        open_weather_port: str, api_key: str):
        self.root.transition.direction = 'left'
        self.root.current = 'loading'
        loading_text: Label = self.root.get_screen('loading').ids.loading
        iterator = self._on_loading_screen(authority, port, database_name, username, password, open_weather_authority,
                                           open_weather_port, api_key)

        def use_loading_screen(_time):
            try:
                message = iterator.__next__()
                loading_text.text += f'{message}\n'
                if self.dialog and self.dialog.text != '':
                    self.root.transition.direction = 'right'
                    self.root.current = 'credentials'
                    return
                else:
                    Clock.schedule_once(use_loading_screen)
            except StopIteration:
                self.root.transition.direction = 'left'
                self.root.current = 'main_menu'

        Clock.schedule_once(use_loading_screen, 1)

    @staticmethod
    def populate_invalid_locations(session, manager) -> str:
        try:
            invalids: List[database.Persisted] = []
            invalids.extend(database.get_objects(session, database.City, valid=False))
            invalids.extend(database.get_objects(session, database.Airport, valid=False))
            invalids_dict: dict = {}
            for element in invalids:
                invalids_dict[element.name] = [f'Type: {element.__class__.__name__}',
                                               element.__getattribute__(f'{element.__class__.__name__.lower()}_id')]
            manager.get_screen('validate_locations').ids.validate_locations_list.populate_two_line_list(invalids_dict)
            manager.get_screen('main_menu').to_validate = len(invalids_dict)
        except Exception as e:
            return database.handle_error(e, session)

    @staticmethod
    def populate_unvalidated_ratings(session, manager):
        try:
            invalids = database.get_objects(session, database.Review)
            invalids_dict: dict = {}
            for element in invalids:
                operator = database.get_object(session, database.Operator, operator_id=element.operator_id)
                invalids_dict[element.review] = [f'Name: {operator.name}',
                                                 element.__getattribute__(f'{element.__class__.__name__.lower()}_id')]
            manager.get_screen('update_ratings').ids.update_rating_list.populate_two_line_list(invalids_dict)
            manager.get_screen('main_menu').to_update = len(invalids_dict)
        except Exception as e:
            return database.handle_error(e, session)

    def _on_loading_screen(self, authority: str, port: str, database_name: str, username: str, password: str,
                           open_weather_authority: str,
                           open_weather_port: str, api_key: str) -> Iterator[str]:
        self.create_popup(self.post_init_create_session(authority, port, database_name, username, password))
        yield 'Logged into sql_database'
        self.create_popup(self.populate_invalid_locations(self.session, self.root))
        yield 'Populated invalidated locations'
        self.create_popup(self.populate_unvalidated_ratings(self.session, self.root))
        yield 'Populated unvalidated reviews'
        self.create_popup(
            self.connect_to_weather_api(open_weather_authority, open_weather_port, api_key, lincoln_latitude,
                                        lincoln_longitude))
        yield 'Superfluous open weather connection may have been created'  # TODO figure out how to check if it worked

    def reject_rating_clicked(self):
        try:
            if len(self.root.get_screen('update_ratings').ids.update_rating_list.selected_elements) > 0:
                review_id = self.root.get_screen('update_ratings').ids.update_rating_list.selected_elements[0].id
                database.delete_object(self.session, database.Review,
                                       review_id=review_id)
                self.session.commit()
                selected_item = self.root.get_screen('update_ratings').ids.update_rating_list.selected_elements[0]
                selected_item.parent.selected_elements.clear()
                selected_item.parent.remove_widget(selected_item)
                self.root.get_screen('main_menu').to_update -= 1
                self.create_popup('Operator\'s rating rejected successfully')

            else:
                self.create_popup('Please select an item')
        except Exception as exception:
            traceback.print_exc()
            self.create_popup(f'Database connection failed!\nCause: {exception}')

    def call_geocoding_api_by_name(self, city_name):
        self.records = []
        connection = RESTConnection('api.openweathermap.org', 443, '/geo/1.0')
        connection.send_request(
            'direct',
            {
                'appid': self.user_api,
                'q': city_name,
                'limit': 20
            },
            None,
            self.on_geo_records_loaded,
            self.on_records_not_loaded,
            self.on_records_not_loaded
        )

    def on_geo_records_loaded(self, _, response):
        self.validate_locations(response)
        # for city in response:
        #     self.records = [self.validate_locations(city)]
        print(dumps(response, indent=4, sort_keys=True))
        return self.records

    def call_geocoding_api_by_location(self, latitude, longitude):
        connection = RESTConnection('api.openweathermap.org', 443, '/geo/1.0')
        connection.send_request(
            'reverse',
            {
                'appid': self.user_api,
                'lat': latitude,
                'lon': longitude
            },
            None,
            self.on_records_loaded,
            self.on_records_not_loaded,
            self.on_records_not_loaded
        )

    def call_csv_by_identifier(self, selected_airport: TwoListItem):
        airport = database.get_object(self.session, database.Airport, airport_id=selected_airport.id)
        validated_airport = csv_handler.check_airport(airport_list, airport.ICAO_code)
        if validated_airport is not None:
            self.create_choice_popup(
                f'An airport with the same ICAO code {airport.ICAO_code} '
                f'exists at longitude: {validated_airport["longitude"]} and latitude: {validated_airport["latitude"]}. '
                f'Do you want to use this data or keep your data?',
                lambda _obj: self.keep_my_data_clicked(airport),
                lambda _obj: self.use_official_data_clicked(airport, validated_airport["latitude"],
                                                            validated_airport["longitude"],
                                                            validated_airport["airport_name"]))

        else:
            self.create_popup(
                f'Airport with ICAO code {airport.ICAO_code} not found. Airport removed from the database.')
            self.session.delete(airport)
            self.session.commit()
            selected_airport.parent.selected_elements.clear()
            selected_airport.parent.remove_widget(selected_airport)
            self.root.get_screen('main_menu').to_validate -= 1

    def advance_calendar(self):
        screen = self.root.get_screen('itineraries')
        lincoln_or_bust_selected = screen.ids.lincoln_or_bust_button.down
        the_scenic_route_selected = screen.ids.the_scenic_route_button.down
        if lincoln_or_bust_selected or the_scenic_route_selected:
            itinerary = screen.ids['lincoln_or_bust' if lincoln_or_bust_selected else 'the_scenic_route']
            other_itinerary: ListHolder = screen.ids[
                'lincoln_or_bust' if the_scenic_route_selected else 'the_scenic_route']
            if len(itinerary.children) >= screen.days_into_journey + 1:
                previous_locations = [child.text for child in itinerary.children]
                previous_locations = previous_locations[:screen.days_into_journey]
                other_itinerary.populate_list(previous_locations)
                screen.days_into_journey += 1
                screen.current_location = itinerary.children[screen.days_into_journey].text
                itinerary.children[screen.days_into_journey - 1].on_pressed()
                other_itinerary.children[screen.days_into_journey - 1].on_pressed()

    @staticmethod
    def request_itinerary(session, current_city: str, days_into_journey: int, lincoln_or_bust: ListHolder,
                          the_scenic_route: ListHolder) -> str:
        try:
            return request_itinerary(session, current_city, days_into_journey, lincoln_or_bust, the_scenic_route)
        except Exception as e:
            database.handle_error(e, session)

    # itinerary
    # unsure if data will be added to database
    def format_forecast_record(self, record, session, airport_name, city_name):
        airport = database.get_object(session, database.Airport, name=airport_name)
        city = database.get_object(session, database.City, name=city_name)
        for forecast in record['daily']:
            forecast_date = datetime.fromtimestamp(forecast['dt']).strftime('%m/%d/%Y')
            forecast_temperature = (forecast['temp']['max'] + forecast['temp']['min']) / 2
            forecast_precipitation = forecast['pop']
            forecast_wind = forecast['wind_speed']
            forecast_description = forecast['weather'][0]['description']

            if city == '':
                database.create_object(self.session, database.Forecast,
                                       airport_id=airport, date=forecast_date, temperature=forecast_temperature,
                                       precipitation_probability=forecast_precipitation,
                                       wind_speed=forecast_wind,
                                       weather_description=forecast_description)
            else:
                database.create_object(self.session, database.Forecast,
                                       city_id=city, date=forecast_date, temperature=forecast_temperature,
                                       precipitation_probability=forecast_precipitation,
                                       wind_speed=forecast_wind,
                                       weather_description=forecast_description)


if __name__ == '__main__':
    app = TravelApp()
    app.run()
