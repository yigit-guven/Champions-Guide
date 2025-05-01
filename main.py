from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from app.screens.home import HomeScreen
from app.screens.tierlists import TierlistScreen
from app.screens.comp_builder import CompBuilderScreen
from app.screens.settings import SettingsScreen


class ChampionGuideApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(TierlistScreen(name='tierlists'))
        sm.add_widget(CompBuilderScreen(name='comp_builder'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm


if __name__ == '__main__':
    ChampionGuideApp().run()