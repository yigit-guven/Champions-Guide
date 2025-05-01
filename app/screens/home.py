from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_widget(Label(text="Welcome to Champion's Guide - Home"))