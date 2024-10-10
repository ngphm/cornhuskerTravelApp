import traceback
from sys import stderr

from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from database import Operator, Airplane, Airport, get_exists, create_object, handle_error, get_object, \
    get_objects, Review
from tracker_app import TrackerApp, ListHolder


class OperatorApp(TrackerApp):

    def after_build(self, _time):
        pass

    @staticmethod
    def add_review(session, name: str, score: str) -> str:
        """
        Adds a review to an operator. Used instead of create_object to find operator by name and do error handling

        :returns: Confirmation or error message to be sent to create_popup
        """
        try:
            operator = get_object(session, Operator, name=name)
            operator.reviews.append(Review(review=score))
            session.commit()
            return 'Review has been successfully added.'
        except Exception as e:
            return handle_error(e, session)

    @staticmethod
    def new_operator_clicked(session, selected: str, name: str, score: str, airplane_name: str,
                             selected_airports: List[str], spinner: Spinner) -> str:
        """
        Creates or edits operator selected to match parameters. Used instead of create_object because of editing
        capabilities and reading from selected airports

        :param session:
        :param selected: 'Create New' or name of operator to be edited
        :param name:
        :param score:
        :param airplane_name:
        :param selected_airports:
        :param spinner:
        :returns: Confirmation or error message to be sent to create_popup
        """
        try:
            if selected == 'Create New' and get_exists(session, Operator, name=name):
                return f'Operator {name} already exist. Please edit their entry instead of adding a new one'
            elif selected != 'Create New' and name != selected and get_exists(session, Operator, name=name):
                return f'Operator {name} already exist. You cannot have two operators with the same name'
            elif len(selected_airports) <= 0:
                return 'Please select airports for the operator.'
            elif airplane_name == '':
                return 'Please select an airplane for the operator.'
            elif name == '':
                return 'Please enter a name.'
            else:
                operator = OperatorApp.get_operator_with_populated_fields(session, name, score, selected)
                operator.airplane = get_object(session, Airplane, name=airplane_name)
                operator.airports = []
                for airport in get_objects(session, Airport):
                    if airport.ICAO_code in selected_airports:
                        operator.airports.append(airport)
                session.commit()
                out = f'Operator {"Added" if selected == "Create New" else "Edited"}!'
                return out + OperatorApp.populate_spinner(session, Operator, spinner, True)
        except Exception as e:
            return handle_error(e, session)

    @staticmethod
    def get_operator_with_populated_fields(session, name: str, score: str, selected: str = 'Create New') -> Operator:
        """
        Helper method for new_operator_clicked.

        :param session:
        :param name: 'Create New' or name of operator to be edited
        :param score:
        :param selected:
        :returns: Operator with non-nullable fields not null
        """
        if selected == 'Create New':
            operator = create_object(session, Operator, name=name, rate_my_pilot_score=score)
        else:
            operator = get_object(session, Operator, name=selected)
            operator.name = name
            operator.rate_my_pilot_score = score
        return operator

    @staticmethod
    def on_operator_spinner_clicked(session, selected_operator: str, operator_grid: Widget, airports_list: ListHolder,
                                    operator_name: TextInput,
                                    operator_score: TextInput,
                                    airplane_spinner: Spinner) -> str:
        """
        Repopulates fields provided with information about the newly specified operator

        :param selected_operator:
        :param session:
        :param operator_grid: 
        :param airports_list: 
        :param operator_name: 
        :param operator_score: 
        :param airplane_spinner: 
        :returns: error message to be sent to create_popup
        """
        try:
            operator_grid.disabled = False
            airports_list.disabled = False
            operator_name.text = ''
            operator_score.text = ''
            airplane_spinner.text = ''
            airports = get_objects(session, Airport)
            airport_codes = [element.ICAO_code for element in airports]
            airports_list.populate_list(airport_codes)
            if selected_operator != 'Create New':
                operator = get_object(session, Operator, name=selected_operator)
                operator_name.text = operator.name
                operator_score.text = str(operator.rate_my_pilot_score)
                airplane_spinner.text = operator.airplane.name
                for airport in operator.airports:
                    for airport_element in airports_list.children:
                        if airport_element.text == airport.ICAO_code:
                            airport_element.on_pressed()
        except Exception as e:
            return handle_error(e, session)


if __name__ == '__main__':
    try:
        app = OperatorApp()
        app.run()
    except SQLAlchemyError as exception:
        traceback.print_exc()
        print('Database connection failed!', file=stderr)
        print(f'Cause: {exception}', file=stderr)
        exit(1)
