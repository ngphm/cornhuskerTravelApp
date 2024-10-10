import traceback
from math import sin, cos, acos, radians
from typing import Type, Tuple

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, Date, Boolean
from sqlalchemy.exc import SQLAlchemyError, StatementError, NoResultFound, DataError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

Persisted = declarative_base()


class Airport(Persisted):
    __tablename__ = 'airports'
    airport_id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    ICAO_code = Column(String(4), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    valid = Column(Boolean, default=False)
    forecasts = relationship('Forecast', back_populates='airport', uselist=True)
    cities = relationship('City', uselist=True, secondary='airport_cities', back_populates='airports')
    operators = relationship('Operator', uselist=True, secondary='operator_airports', back_populates='airports')

    @property
    def location(self):
        return self.latitude, self.longitude

    def __repr__(self):
        return self.name


class City(Persisted):
    __tablename__ = 'cities'
    city_id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    geographic_identity = Column(String(256), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    valid = Column(Boolean, default=False)
    airports = relationship('Airport', uselist=True, secondary='airport_cities', back_populates='cities')
    forecasts = relationship('Forecast', back_populates='city', uselist=True)

    @property
    def location(self):
        return self.latitude, self.longitude

    def __repr__(self):
        return self.name


class Forecast(Persisted):
    __tablename__ = 'forecast'
    forecast_id = Column(Integer, primary_key=True)
    airport_id = Column(Integer, ForeignKey('airports.airport_id', ondelete='CASCADE'))
    city_id = Column(Integer, ForeignKey('cities.city_id', ondelete='CASCADE'))
    date = Column(Date, nullable=False)  # Format: YYYY-MM-DD
    temperature = Column(Float)  # Unit: Celsius
    visibility = Column(Integer)  # Unit: kilometers
    precipitation_probability = Column(Float)  # Value: 0(0%) - 1(100%)
    wind_speed = Column(Float)  # Unit: kilometer/hour
    weather_description = Column(String(256))
    airport = relationship('Airport', back_populates='forecasts')
    city = relationship('City', back_populates='forecasts')


class AirportCities(Persisted):
    __tablename__ = 'airport_cities'
    airport_id = Column(Integer, ForeignKey('airports.airport_id', ondelete='CASCADE'), primary_key=True)
    city_id = Column(Integer, ForeignKey('cities.city_id', ondelete='CASCADE'), primary_key=True)


class Airplane(Persisted):
    __tablename__ = 'airplanes'
    airplane_id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    range = Column(Float, nullable=False)  # Unit: kilometer
    operators = relationship('Operator', back_populates='airplane', uselist=True)

    def __repr__(self):
        return self.name


class Operator(Persisted):
    __tablename__ = 'operators'
    operator_id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False)
    rate_my_pilot_score = Column(Float, nullable=False)
    airplane_id = Column(Integer, ForeignKey('airplanes.airplane_id', ondelete='CASCADE'))
    airports = relationship('Airport', uselist=True, secondary='operator_airports', back_populates='operators')
    airplane = relationship('Airplane', back_populates='operators')
    reviews = relationship('Review', back_populates='operator', uselist=True)

    def __repr__(self):
        return self.name


class OperatorAirport(Persisted):
    __tablename__ = 'operator_airports'
    operator_id = Column(Integer, ForeignKey('operators.operator_id', ondelete='CASCADE'), primary_key=True)
    airport_id = Column(Integer, ForeignKey('airports.airport_id', ondelete='CASCADE'), primary_key=True)


class Review(Persisted):
    __tablename__ = 'reviews'
    review_id = Column(Integer, primary_key=True)
    review = Column(Float, nullable=False)
    operator_id = Column(Integer, ForeignKey('operators.operator_id', ondelete='CASCADE'))
    operator = relationship('Operator', back_populates='reviews')


def get_is_nearby(session: Session, latitude: float, longitude: float, sql_type: Type[Persisted],
                  range: float = 1) -> bool:
    return session.query(sql_type).filter(sql_type.latitude >= float(latitude) - range,
                                          sql_type.latitude <= float(latitude) + range,
                                          sql_type.longitude >= float(longitude) - range,
                                          sql_type.longitude <= float(longitude) + range).count() > 0


def get_nearby(session: Session, latitude: float, longitude: float, sql_type: Type[Persisted],
               range: float = 1) -> list:
    return session.query(sql_type).filter(sql_type.latitude >= float(latitude) - range,
                                          sql_type.latitude <= float(latitude) + range,
                                          sql_type.longitude >= float(longitude) - range,
                                          sql_type.longitude <= float(longitude) + range).all()


def get_great_circle_distance(source: Tuple[float, float], destination: Tuple[float, float]):
    lon_1, lat_1, lon_2, lat_2 = map(radians, [source[0], source[1], destination[0], destination[1]])
    distance = 6371 * (acos(sin(lat_1) * sin(lat_2) + cos(lat_1) * cos(lat_2) * cos(lon_1 - lon_2)))
    return distance


def get_exists(session: Session, sql_type: Type[Persisted], **kwargs) -> bool:
    return session.query(sql_type).filter_by(**kwargs).count() > 0


def delete_object(session: Session, sql_type: Type[Persisted], **kwargs) -> Persisted:
    return session.query(sql_type).filter_by(**kwargs).delete()


def get_object(session: Session, sql_type: Type[Persisted], **kwargs) -> Persisted:
    return session.query(sql_type).filter_by(**kwargs).one()


def get_objects(session: Session, sql_type: Type[Persisted], **kwargs) -> list:
    return session.query(sql_type).filter_by(**kwargs).all()


def create_object(session: Session, sql_type: Type[Persisted], **kwargs) -> Persisted:
    new_object = sql_type(**kwargs)
    session.add(new_object)
    session.commit()
    return new_object


def handle_error(e, session) -> str:
    traceback.print_exc()
    if isinstance(e, StatementError):
        session.rollback()
        return 'ICAO codes are only 4 characters long. Please chose a shorter ICAO code'
    elif isinstance(e, SQLAlchemyError) or isinstance(e, DataError):
        session.rollback()
        return f'Database error: {e}'
    elif isinstance(e, TypeError):
        return 'Please complete all required fields and try again.'
    elif isinstance(e, NoResultFound):
        return 'Error in database. Please try again.'
    else:
        return f'error: {e}'


class Database(object):
    @staticmethod
    def construct_mysql_url(authority, port, database, username, password):
        return f'mysql+mysqlconnector://{username}:{password}@{authority}:{port}/{database}'

    @staticmethod
    def construct_in_memory_url():
        return 'sqlite:///'

    def __init__(self, url):
        self.engine = create_engine(url)
        self.Session = sessionmaker()
        self.Session.configure(bind=self.engine)

    def ensure_tables_exist(self):
        Persisted.metadata.create_all(self.engine)

    def create_session(self):
        return self.Session()
