import json
import os
from abc import ABC, abstractmethod

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.modules import inspector
from kivy.properties import ListProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineListItem, MDList, TwoLineListItem

import database
from database import Database


class ListHolder(MDList):
    def __draw_shadow__(self, origin, end, context=None):
        pass

    selected_elements = ListProperty()

    def populate_two_line_list(self, elements):
        self.selected_elements.clear()
        self.clear_widgets()
        for element in elements:
            item = TwoListItem(text=str(element), secondary_text=elements[element][0])
            item.id = elements[element][1]
            self.add_widget(item)

    def populate_list(self, elements):
        self.selected_elements.clear()
        self.clear_widgets()
        for element in elements:
            item = ListItem(text=element)
            self.add_widget(item, len(self.children))

    def __repr__(self):
        return self.children.__repr__()


class TwoListItem(TwoLineListItem):

    def on_pressed(self):
        if len(self.parent.selected_elements) == 0:
            self.bg_color = [.9, .9, .9, 1]
            self.parent.selected_elements.append(self)
        elif len(self.parent.selected_elements) == 1:
            if not self.bg_color or self.bg_color != [.9, .9, .9, 1]:
                pass
            else:
                self.bg_color = 'gray'
                self.parent.selected_elements.remove(self)

    def __repr__(self):
        return self.text


class ListItem(OneLineListItem):

    def on_pressed(self):
        if not self.bg_color or self.bg_color != [.9, .9, .9, 1]:
            self.bg_color = [.9, .9, .9, 1]
            self.parent.selected_elements.append(self.text)
        else:
            self.bg_color = 'gray'
            self.parent.selected_elements.remove(self.text)

    def __repr__(self):
        return self.text


class TrackerApp(MDApp, ABC):
    Builder.load_file('custom_widgets.kv')
    Window.size = (320, 600)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = None
        self.operator_database = None
        self.create_session()

    def create_session(self):
        with open('../credentials.json') as file:
            data = json.loads(file.read())

        url = Database.construct_mysql_url(str(data['Database Authority']), str(data['Database Port']), str(data['Database Name']), str(data['Database Username']), str(data['Database Password']))
        self.operator_database = Database(url)
        self.session = self.operator_database.create_session()

    @abstractmethod
    def after_build(self, _time):
        pass

    def build(self):
        inspector.create_inspector(Window, self)  # For inspection (press control-e to toggle).
        screen_manager: ScreenManager = ScreenManager()
        for path in os.listdir('Screens'):
            screen: Screen = Builder.load_file('Screens/' + path)
            screen_manager.add_widget(screen)
        screen_manager.current = 'main_menu'
        Clock.schedule_once(self.after_build)
        return screen_manager

    @staticmethod
    def populate_spinner(session, sql_type, spinner, editable=False) -> str:
        try:
            objects = session.query(sql_type).all()
            object_list = []
            if editable:
                object_list.append('Create New')
            for element in objects:
                if sql_type == database.Forecast and str(element.date) not in object_list:
                    object_list.append(str(element.date))
                elif sql_type != database.Forecast:
                    object_list.append(element.name)
            spinner.values = object_list
            return ""
        except Exception as e:
            return database.handle_error(e, session)

    @staticmethod
    def create_object(session, sql_type: database.Persisted, unique_checks: dict, other_values: dict,
                      show_confirmation_message=True):
        other_values.update(unique_checks)
        for key in other_values:
            if other_values[key] == '':
                return 'Please fill out all fields'
        try:
            if database.get_exists(session, sql_type, **unique_checks):
                return f'{sql_type.__name__} already added! Please try again'
            else:
                database.create_object(session, sql_type, **other_values)
                return f'{sql_type.__name__} added!' if show_confirmation_message else ''
        except Exception as e:
            return database.handle_error(e, session)

    dialog = None

    def create_popup(self, text):
        """
        Show a MDDialog to the user.
        If text is None or an empty string, this method will do nothing.
        If a popup is already being displayed, the text will be added onto the current message.
        Used primarily for error handling.
        """
        if not self.dialog or len(self.dialog.buttons) > 1:
            self.dialog = MDDialog(
                buttons=[MDFlatButton(
                    text='Ok',
                    theme_text_color="Custom",
                    text_color=self.theme_cls.primary_color,
                    on_press=self.close_popup
                )
                ]
            )
        if text and text != '':
            if self.dialog.text != '':
                self.dialog.text += '\n'
            self.dialog.text += text
            self.dialog.open()

    def create_choice_popup(self, text, first_button_clicked, second_button_clicked):
        self.dialog = MDDialog(
            buttons=[MDFlatButton(
                text='Keep my data',
                theme_text_color="Custom",
                text_color=self.theme_cls.primary_color,
                on_press=first_button_clicked
            ), MDFlatButton(
                text='Use official data',
                theme_text_color="Custom",
                text_color=self.theme_cls.primary_color,
                on_press=second_button_clicked
            )
            ])
        if self.dialog.text != '':
            self.dialog.text += '\n'
        self.dialog.text += text
        self.dialog.open()

    def close_popup(self, _obj):
        self.dialog.text = ''
        self.dialog.dismiss()
