from typing import Dict, List

from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.dialog import MDDialog

import database
from tracker_app import TrackerApp


class AirportTrackerApp(TrackerApp):

    def after_build(self, _time):
        pass

    @staticmethod
    def airport_selected(session, airport_name, date_spinner) -> str:
        try:
            airport = database.get_object(session, database.Airport, name=airport_name)
            dates = [str(forcast.date) for forcast in airport.forecasts]
            date_spinner.values = dates
            date_spinner.disabled = len(dates) <= 0
        except Exception as e:
            return database.handle_error(e, session)

    @staticmethod
    def check_forecast_clicked(session, date, airport_name, output_box) -> str:
        try:
            if date and airport_name and '' not in [date, airport_name]:
                airport = database.get_object(session, database.Airport, name=airport_name)
                forcast = database.get_object(session, database.Forecast, date=date, airport=airport)
                output_box.text = f'{date}: {forcast.weather_description}, temperature: {forcast.temperature} degrees ' \
                                  f'Celsius, precipitation: {forcast.precipitation_probability * 100}%, ' \
                                  f'visibility: {forcast.visibility}km, wind: {forcast.wind_speed} km/h '
        except Exception as e:
            return database.handle_error(e, session)

    @staticmethod
    def add_joined_clicked(session, parent_keys: Dict[str, str], parent_type, child_list: List[str], child_type,
                           manager: ScreenManager) -> str:
        """
        Handles the relation of airports to cities and cities to airports.

        :returns: Confirmation or error message to send to create popup
        """
        if len(child_list) > 0:
            try:
                if parent_type == database.Airport:
                    parent = database.get_object(session, parent_type, name=parent_keys['name'], ICAO_code=parent_keys['ICAO_code'])
                if parent_type == database.City:
                    parent = database.get_object(session, parent_type, name=parent_keys['name'], geographic_identity=parent_keys['geographic_identity'])
                for child in child_list:
                    child = database.get_object(session, child_type, name=child)
                    parent.__getattribute__(child.__tablename__).append(child)
                manager.current = 'main_menu'
                session.commit()
                return f'{child_list} added to {parent_keys["name"]}'
            except Exception as e:
                return database.handle_error(e, session)
        else:
            manager.current = f'new_{child_type.__name__.lower()}'
            new_screen = manager.get_screen(manager.current)
            new_screen.nearby = parent_keys['name']
            new_screen.ids.latitude.text = parent_keys['latitude']
            new_screen.ids.longitude.text = parent_keys['longitude']

    @staticmethod
    def handle_confirmation_screen(session, child_type, keys: Dict[str, str], other_values: Dict[str, str],
                                   sql_type, manager: ScreenManager, popup: MDDialog,
                                   previous_name: str) -> str:
        """
        When the enter button is pressed, and an error is not presented, the user is taken to a confirmation screen.
        """
        if not popup or popup.text == '':
            try:
                screen = AirportTrackerApp.populate_nearby_screen(child_type, keys, manager, other_values,
                                                                  sql_type)
                nearby_list = database.get_nearby(session, float(other_values['latitude']),
                                                  float(other_values['longitude']),
                                                  child_type)
                screen.ids.list.populate_list([element.name for element in nearby_list])
                for element in screen.ids.list.children:
                    if element.text == previous_name:
                        element.on_pressed()
                manager.current = 'nearby'
            except Exception as e:
                return database.handle_error(e, session)

    @staticmethod
    def populate_nearby_screen(child_type, keys: Dict[str, str], manager: ScreenManager,
                               other_values: Dict[str, str], sql_type):
        screen = manager.get_screen('nearby')
        screen.parent_type = sql_type
        screen.parent_singular = sql_type.__name__
        screen.parent_plural = sql_type.__tablename__
        screen.child_type = child_type
        screen.child_singular = child_type.__name__
        screen.child_plural = child_type.__tablename__
        keys.update(other_values)
        screen.parent_keys = keys
        return screen


if __name__ == '__main__':
    app = AirportTrackerApp()
    app.run()
