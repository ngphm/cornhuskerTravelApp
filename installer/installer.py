import json
from datetime import date
from sys import stderr

from sqlalchemy.exc import SQLAlchemyError

from database import Database, City, Forecast, Operator, OperatorAirport, Airport, Airplane

from travel_planner_app import csv_handler


def add_starter_data(session):
    lincoln = City(name='Lincoln', geographic_identity='Nebraska', latitude=40.8, longitude=-96.7, valid=True)
    bellevue = City(name='Bellevue', geographic_identity='Nebraska', latitude=41.2, longitude=-95.9, valid=True)

    lincoln_airport = Airport(name='Lincoln Airport', ICAO_code='KLNK', latitude=40.85, longitude=-96.76,
                              cities=[lincoln], valid=True)

    eppley_airfield = Airport(name='Eppley Airfield', ICAO_code='KOMA', latitude=41.30, longitude=-95.89,
                              cities=[lincoln, bellevue], valid=True)

    lincoln_first_forecast = Forecast(date=date(2022, 4, 18), temperature=11, visibility=15,
                                      precipitation_probability=0.0,
                                      wind_speed=7.61,
                                      weather_description='clear sky',
                                      airport=lincoln_airport)

    lincoln_second_forecast = Forecast(date=date(2022, 4, 19), temperature=17, visibility=16,
                                       precipitation_probability=0.1,
                                       wind_speed=4.52,
                                       weather_description='clear sky',
                                       airport=lincoln_airport)

    eppley_first_forecast = Forecast(date=date(2022, 4, 18), temperature=14, visibility=10,
                                     precipitation_probability=0.0,
                                     wind_speed=8.05,
                                     weather_description='broken clouds',
                                     airport=eppley_airfield)

    eppley_second_forecast = Forecast(date=date(2022, 4, 19), temperature=5, visibility=11,
                                      precipitation_probability=0.3,
                                      wind_speed=10.21,
                                      weather_description='overcast clouds',
                                      airport=eppley_airfield)

    kansas_airport = Airport(name='Kansas City International Airport', ICAO_code='KMCI', latitude=39.30,
                             longitude=-94.71, valid=True)
    tampa_airport = Airport(name='Tampa International Airport', ICAO_code='KTPA', latitude=27.98, longitude=-82.53,
                            valid=True)
    detroit_airport = Airport(name='Detroit Metro Airport', ICAO_code='KDTW', latitude=42.22, longitude=-83.36,
                              valid=True)

    joey_airways = Operator(name='Joey Airways', rate_my_pilot_score=4.5, airports=[kansas_airport, tampa_airport])
    flightee = Operator(name='Flightee', rate_my_pilot_score=5.0, airports=[tampa_airport, detroit_airport])
    walter_airlines = Operator(name='Walter Airlines', rate_my_pilot_score=3.8,
                               airports=[lincoln_airport, tampa_airport, detroit_airport])

    embraer_airplane = Airplane(name='Embraer 135', range=3100,
                                operators=[joey_airways, flightee])  # range in kilometers
    bombardier_airplane = Airplane(name='Bombardier CRJ700LR', range=3700, operators=[walter_airlines])

    session.add(lincoln)
    session.add(bellevue)

    session.add(lincoln_airport)
    session.add(eppley_airfield)

    session.add(lincoln_first_forecast)
    session.add(lincoln_second_forecast)
    session.add(eppley_first_forecast)
    session.add(eppley_second_forecast)

    session.add(kansas_airport)
    session.add(tampa_airport)
    session.add(detroit_airport)

    session.add(joey_airways)
    session.add(flightee)
    session.add(walter_airlines)

    session.add(embraer_airplane)
    session.add(bombardier_airplane)


def main():
    try:
        with open('../credentials.json') as file:
            data = json.loads(file.read())

        url = Database.construct_mysql_url(str(data['Database Authority']), str(data['Database Port']),
                                           str(data['Database Name']), str(data['Database Username']),
                                           str(data['Database Password']))

        airport_database = Database(url)
        airport_database.ensure_tables_exist()
        print('Tables created.')
        session = airport_database.create_session()
        add_starter_data(session)
        session.commit()
        print('Records created.')
    except SQLAlchemyError as exception:
        print('Database setup failed!', file=stderr)
        print(f'Cause: {exception}', file=stderr)
        exit(1)


if __name__ == '__main__':
    main()
