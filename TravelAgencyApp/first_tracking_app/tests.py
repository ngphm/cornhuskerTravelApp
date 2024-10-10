import unittest
from datetime import date, timedelta
from unittest import TestCase

from kivy.uix.label import Label
from kivy.uix.spinner import Spinner

from database import *


def create_in_memory_session() -> Session:
    url = Database.construct_in_memory_url()
    database = Database(url)
    database.ensure_tables_exist()
    return database.create_session() 


class DatabaseTests(TestCase):

    def test_nearby(self):
        session = create_in_memory_session()
        airport = create_object(session, Airport, name='gorge', ICAO_code='JIMM', latitude=5, longitude=5)
        self.assertFalse(get_is_nearby(session, 7, 3, Airport))
        self.assertIn(airport, get_nearby(session, 5, 5, Airport))
        self.assertIn(airport, get_nearby(session, 6, 6, Airport))
        self.assertIn(airport, get_nearby(session, 4, 4, Airport))
        city = create_object(session, City, name='gorge', geographic_identity='JIMM', latitude=5, longitude=5)
        self.assertFalse(get_is_nearby(session, 7, 3, City))
        self.assertIn(city, get_nearby(session, 5, 5, City))
        self.assertIn(city, get_nearby(session, 6, 6, City))
        self.assertIn(city, get_nearby(session, 4, 4, City))

    def test_exists(self):
        session = create_in_memory_session()
        airport = create_object(session, Airport, name='gorge', ICAO_code='JIMM', latitude=5, longitude=5)
        city = create_object(session, City, name='gorge', geographic_identity='JIMM', latitude=5, longitude=5)
        self.assertTrue(get_exists(session, Airport, name='gorge'))
        self.assertEqual(city, get_object(session, City, name='gorge'))
        self.assertIn(airport, get_objects(session, Airport, ICAO_code='JIMM'))


try:
    # noinspection PyUnresolvedReferences
    from tracker_app import TrackerApp


    class TrackerTests(TestCase):

        def test_create_object_empty_dict(self):
            session = create_in_memory_session()

            value = TrackerApp.create_object(session, Airport, {}, {})
            print(value)
            self.assertNotEqual('Airport Added!', value)

        def test_create_object_empty_dict_values(self):
            session = create_in_memory_session()

            value = TrackerApp.create_object(session, Airport, {'ICAO_code': ''},
                                             {'name': '', 'latitude': '', 'longitude': ''})
            print(value)
            self.assertNotEqual('Airport Added!', value)
            self.assertFalse(value.startswith('Database error:'))
            self.assertFalse(value.startswith('error:'))

        def test_create_object_invalid_dict_values(self):
            session = create_in_memory_session()

            value = TrackerApp.create_object(session, Airport, {'ICAO_code': 'FFF'},
                                             {'name': 'fff', 'latitude': 'fff', 'longitude': 'fff'})
            print(value)
            self.assertNotEqual('Airport Added!', value)
            self.assertFalse(value.startswith('Database error:'))
            self.assertFalse(value.startswith('error:'))

        def test_create_object_valid(self):
            session = create_in_memory_session()

            value = TrackerApp.create_object(session, Airport, {'ICAO_code': 'FFF'},
                                             {'name': 'fff', 'latitude': '5', 'longitude': '5'})
            print(value)
            self.assertEqual('Airport added!', value)
            self.assertFalse(value.startswith('Database error:'))
            self.assertFalse(value.startswith('error:'))
            value = TrackerApp.create_object(session, Airport, {'ICAO_code': 'Bible'},
                                             {'name': 'fff', 'latitude': '5', 'longitude': '5'}, False)
            self.assertEqual('', value)

        def test_create_object_duplicate(self):
            session = create_in_memory_session()

            value = TrackerApp.create_object(session, Airport, {'ICAO_code': 'FFF'},
                                             {'name': 'fff', 'latitude': '5', 'longitude': '5'})
            print(value)
            self.assertEqual('Airport added!', value)
            self.assertFalse(value.startswith('Database error:'))
            self.assertFalse(value.startswith('error:'))
            value = TrackerApp.create_object(session, Airport, {'ICAO_code': 'FFF'},
                                             {'name': 'fff', 'latitude': '5', 'longitude': '5'})
            print(value)
            self.assertNotEqual('Airport added!', value)
            self.assertFalse(value.startswith('Database error:'))
            self.assertFalse(value.startswith('error:'))
except ImportError:
    pass

try:
    # noinspection PyUnresolvedReferences
    from main import AirportTrackerApp


    class AirportTests(TestCase):
        class MockMain(AirportTrackerApp):
            def create_session(self):
                self.session = create_in_memory_session()

        def test_nearby_airport_populated(self):
            app = AirportTests.MockMain()
            manager = app.build()
            keys = {'name': 'Jim'}
            values = {'longitude': '66', 'latitude': '6'}
            app.handle_confirmation_screen(app.session, City, keys, values, Airport, manager, app.dialog, '')
            screen = manager.get_screen('nearby')
            self.assertEqual('Airport Created', screen.children[0].title)

        def test_nearby_city_populated(self):
            app = AirportTests.MockMain()
            manager = app.build()
            keys = {'name': 'Jim'}
            values = {'longitude': '66', 'latitude': '6'}
            app.handle_confirmation_screen(app.session, Airport, keys, values, City, manager, app.dialog, '')
            screen = manager.get_screen('nearby')
            self.assertEqual('City Created', screen.children[0].title)

        def test_airport_selected(self):
            session = create_in_memory_session()
            spinner = Spinner(disabled=True)
            airport = create_object(session, Airport, name='AAA', ICAO_code='AAAA', latitude='5', longitude='5')
            AirportTrackerApp.airport_selected(session, 'AAA', spinner)
            self.assertTrue(spinner.disabled)
            airport.forecasts.append(create_object(session, Forecast, date=date(2022, 4, 19)))
            AirportTrackerApp.airport_selected(session, 'AAA', spinner)
            self.assertFalse(spinner.disabled)
            self.assertIn(str(airport.forecasts[0].date), spinner.values)

        def test_check_forecast_clicked(self):
            session = create_in_memory_session()
            label = Label()
            AirportTrackerApp.check_forecast_clicked(session, str(date(2022, 4, 19)), 'Bees', label)
            self.assertEqual('', label.text)

        def test_add_joined_clicked(self):
            app = AirportTests.MockMain()
            manager = app.build()
            keys = {'name': 'AAA', 'ICAO_code': 'AAAA', 'longitude': '5', 'latitude': '5'}
            create_object(app.session, City, name='AAA', geographic_identity='AAAA', latitude='5', longitude='5')
            create_object(app.session, Airport, name='AAA', ICAO_code='AAAA', latitude='5', longitude='5')
            self.assertEqual("['AAA'] added to AAA",
                             AirportTrackerApp.add_joined_clicked(app.session, keys, Airport, ['AAA'], City, manager))

        def test_no_decimal_location(self):
            app = AirportTests.MockMain()
            manager = app.build()
            airport = create_object(app.session, Airport, name='DDD', ICAO_code='DDDD', latitude=5, longitude=5)
            city = create_object(app.session, City, name='gorge', geographic_identity='JIMM', latitude=5, longitude=5)
            AirportTrackerApp.add_joined_clicked(app.session,
                                                 {'name': 'gorge', 'geographic_identity': 'JIMM', 'latitude': '5',
                                                  'longitude': '5'}, City, ['DDD', 'DDD'], Airport, manager)
            self.assertIn(airport, city.airports)

        def test_decimal_location(self):
            app = AirportTests.MockMain()
            manager = app.build()
            airport = create_object(app.session, Airport, name='Los Angeles International Airport', ICAO_code='KLAC',
                                    latitude=33.94, longitude=-118.41)
            city = create_object(app.session, City, name='Los Angeles', geographic_identity='California',
                                 latitude=33.94,
                                 longitude=-118.41)
            self.assertNotEqual('sqlalchemy.exc.NoResultFound: No row was found when one was required',
                                AirportTrackerApp.add_joined_clicked(app.session,
                                                                     {'name': 'Los Angeles',
                                                                      'geographic_identity': 'California',
                                                                      'latitude': '33.94',
                                                                      'longitude': '-118.41'}, City,
                                                                     ['Los Angeles International Airport',
                                                                      'Los Angeles International Airport'], Airport,
                                                                     manager))
            self.assertIn(airport, city.airports)


except ImportError:
    pass

try:
    # noinspection PyUnresolvedReferences
    from main import OperatorApp


    class OperatorTests(TestCase):
        def test_add_review(self):
            session = create_in_memory_session()
            self.assertNotEqual('Review has been successfully added.', OperatorApp.add_review(session, 'Jim', '5'))
            OperatorApp.create_object(session, Operator, {'name': 'Jim'}, {'rate_my_pilot_score': '5'})
            self.assertNotEqual('Review has been successfully added.', OperatorApp.add_review(session, 'Jim', ''))
            self.assertNotEqual('Review has been successfully added.', OperatorApp.add_review(session, 'Jimm', '5'))
            self.assertEqual('Review has been successfully added.', OperatorApp.add_review(session, 'Jim', '5'))

        def test_new_operator_clicked(self):
            session = create_in_memory_session()
            spinner = Spinner()  # Already tested in tracker app
            OperatorApp.create_object(session, Operator, {'name': 'Dave'}, {'rate_my_pilot_score': '5'})
            OperatorApp.create_object(session, Airplane, {'name': 'The Bee'}, {'range': '5000'})
            OperatorApp.create_object(session, Airport, {'name': 'The Bees', 'ICAO_code': 'BEE'},
                                      {'longitude': '5', 'latitude': '5'})
            self.assertEqual('Operator Edited!',
                             OperatorApp.new_operator_clicked(session, 'Dave', 'Dave', '5', 'The Bee', ['BEE'],
                                                              spinner), 'Editing operator does not work')
            self.assertEqual('Operator Added!',
                             OperatorApp.new_operator_clicked(session, 'Create New', 'Cheryl', '5', 'The Bee', ['BEE'],
                                                              spinner), 'Adding operator does not work')
            self.assertNotEqual('Operator Added!',
                                OperatorApp.new_operator_clicked(session, 'Create New', 'Dave', '5', 'The Bee', ['BEE'],
                                                                 spinner), 'One should not be able to add a new '
                                                                           'operator with the same name as one on the'
                                                                           ' database')
            self.assertNotEqual('Operator Edited!',
                                OperatorApp.new_operator_clicked(session, 'Dave', 'Cheryl', '5', 'The Bee', ['BEE'],
                                                                 spinner), 'One should not be able to change an '
                                                                           'operators name to one that is on the '
                                                                           'database')

        def test_get_operator_with_populated_fields(self):
            session = create_in_memory_session()
            OperatorApp.create_object(session, Operator, {'name': 'Dave'}, {'rate_my_pilot_score': '5'})
            self.assertEqual('6', OperatorApp.get_operator_with_populated_fields(session, 'Dave', '6',
                                                                                 'Dave').rate_my_pilot_score)
            self.assertEqual('Charlie', OperatorApp.get_operator_with_populated_fields(session, 'Charlie', '6',
                                                                                       'Dave').name)
            self.assertIsNotNone(OperatorApp.get_operator_with_populated_fields(session, 'Mops', '6'))
            self.assertEqual(2, session.query(Operator).count())

except ImportError:
    pass

try:
    from main import TravelApp
    import rest
    import csv_handler
    from itineraries import *


    class TravelTests(TestCase):
        pass


    def setup_end_state(session, range=3000, start_location: Tuple[float, float] = (45, 45),
                        extra_location: Tuple[float, float] = (46, 46),
                        lincoln_location: Tuple[float, float] = (44, 44)):
        operator = create_object(session, Operator, name='The Plane Guys', rate_my_pilot_score=10)
        airplane = create_object(session, Airplane, range=range, name='The plane')
        operator.airplane = airplane
        make_traversable_city(session, operator, start_location, 'Beginning Town', 'Start-port',
                              'Republic of Genesis', 'GOGO', date.today())
        make_traversable_city(session, operator, extra_location, 'Extra ville', 'Surplus Airport', 'Iowa', 'PLUS',
                              date.today() + timedelta(days=1))
        make_traversable_city(session, operator, lincoln_location, 'Lincoln',
                              'You would think that I would know the name of the local airport', 'Nebraska', 'GUES',
                              date.today() + timedelta(days=1))
        session.commit()


    def make_traversable_city(session, operator: Operator, location: Tuple[float, float], name: str, airport_name: str,
                              geographic_identity: str, icao_code: str, forecast_date: date):
        city = create_object(session, City, name=name, geographic_identity=geographic_identity,
                             latitude=location[0],
                             longitude=location[1])
        airport = create_object(session, Airport, name=airport_name, ICAO_code=icao_code,
                                latitude=location[0],
                                longitude=location[0])
        city.airports.append(airport)
        operator.airports.append(airport)
        forecast = create_object(session, Forecast, date=forecast_date, temperature=30, visibility=20,
                                 weather_description='clear')
        airport.forecasts.append(forecast)
        return city


    def create_city_loop(session: Session, loop_size: int):
        lincoln_operator: Operator = create_object(session, Operator, name='The Plane Guys', rate_my_pilot_score=10)
        airplane = create_object(session, Airplane, range=2000, name='The plane')
        lincoln_operator.airplane = airplane
        make_traversable_city(session, lincoln_operator, (0, 45), 'Lincoln', 'Lincoln\'s airport', 'Nebraska', 'LNNK',
                              date.today())
        for i in range(1, loop_size - 2):
            operator: Operator = create_object(session, Operator, name=f'{i - 1}-{i} connection',
                                               rate_my_pilot_score=10)
            operator.airplane = airplane
            operator.airports.append(get_object(session, Airport, airport_id=i))
            city: City = make_traversable_city(session, operator, ((180 / float(loop_size)) * i, 0), str(i),
                                               f'{str(i)}\'s airport',
                                               'index', f'{str(i)}', date.today() + timedelta(days=i))
        lincoln_operator.airports.append(city.airports[0])


    class ItineraryTests(TestCase):
        class MockMain(TravelApp):
            def create_session(self):
                self.session = create_in_memory_session()

        def setUp(self) -> None:
            self.app = ItineraryTests.MockMain()  # Using app so that KivyMD doesn't cause exception
            self.app.build()
            self.session = self.app.session
            self.itinerary = ListHolder()

        def test_lincoln_is_first_stop(self):
            setup_end_state(self.session, 2000, (2, 2), (4, 4), (0, 0))
            lincoln = get_object(self.session, City, name='Lincoln')
            generate_itinerary(self.session, lincoln, 0, self.itinerary, True)
            self.assertEqual('Lincoln, Nebraska', self.itinerary.children[0].text, 'Lincoln was first but wasn\'t')

        def test_lincoln_is_last_stop(self):
            setup_end_state(self.session)
            start_city = get_object(self.session, City, city_id=1)

            generate_itinerary(self.session, start_city, 17, self.itinerary, True)
            self.assertEqual('Lincoln, Nebraska', self.itinerary.children[-1].text, 'Lincoln is viable, but not the '
                                                                                    'last stop')

        def test_range(self):
            setup_end_state(self.session, 100)
            start_city = get_object(self.session, City, city_id=1)

            generate_itinerary(self.session, start_city, 17, self.itinerary, True)
            self.assertNotEqual('Lincoln, Nebraska', self.itinerary.children[-1].text,
                                'Lincoln shouldn\'t be close enough '
                                'to get to')

            start_city.airports[0].operators[0].airplane.range = 5000
            generate_itinerary(self.session, start_city, 17, self.itinerary, True)
            self.assertNotEqual('Lincoln, Nebraska', self.itinerary.children[-1].text,
                                'Herbie shouln\'t get on a plane faster than 4000 km')

            start_city.airports[0].operators[0].airplane.range = 2000
            generate_itinerary(self.session, start_city, 17, self.itinerary, True)
            self.assertEqual('Lincoln, Nebraska', self.itinerary.children[-1].text,
                             'Lincoln should be close enough to get '
                             'to')

        def test_weather(self):
            setup_end_state(self.session)
            start_city = get_object(self.session, City, city_id=1)
            forecast: Forecast = start_city.airports[0].forecasts[0]

            forecast.temperature = 46
            generate_itinerary(self.session, start_city, 17, self.itinerary, True)
            self.assertNotEqual('Lincoln, Nebraska', self.itinerary.children[-1].text, 'The plane shouldn\'t be able '
                                                                                       'to take off because the '
                                                                                       'temperature is too high')

            forecast.temperature = 44
            forecast.visibility = 4
            generate_itinerary(self.session, start_city, 17, self.itinerary, True)
            self.assertNotEqual('Lincoln, Nebraska', self.itinerary.children[-1].text, 'The plane shouldn'
                                                                                       '\'t be able to take off because'
                                                                                       ' the visibility is too low')

            forecast.visibility = 6
            forecast.weather_description = 'Thunderstorm'
            generate_itinerary(self.session, start_city, 17, self.itinerary, True)
            self.assertNotEqual('Lincoln, Nebraska', self.itinerary.children[-1].text, 'The plane shouldn'
                                                                                       '\'t be able to take off because'
                                                                                       ' there is a thunderstorm')

            forecast.weather_description = 'Tornado'
            generate_itinerary(self.session, start_city, 17, self.itinerary, True)
            self.assertNotEqual('Lincoln, Nebraska', self.itinerary.children[-1].text, 'The plane shouldn'
                                                                                       '\'t be able to take off because'
                                                                                       ' there is a tornado')

            forecast.weather_description = 'Clear'
            generate_itinerary(self.session, start_city, 17, self.itinerary, True)
            self.assertEqual('Lincoln, Nebraska', self.itinerary.children[-1].text, 'The weather shouldn\'t stop the '
                                                                                    'plane from taking off')

        def test_meridians(self):
            create_city_loop(self.session, 18)
            lincoln = get_object(self.session, City, city_id=1)
            generate_itinerary(self.session, lincoln, 0, self.itinerary, True)
            index = 0
            for child in self.itinerary.children:
                if index in [0, 17]:
                    self.assertEqual('Lincoln, Nebraska', child.text)
                else:
                    self.assertEqual(f'{index}, index', child.text)
                index += 1
            self.assertEqual(18, index)
            
except ImportError:
    pass

try:
    import installer


    class InstallerTests(TestCase):
        pass
except ImportError:
    pass

if __name__ == '__main__':
    unittest.main()
