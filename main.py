import os
import requests
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.core.window import Window
from kivy.utils import get_color_from_hex as hex
from kivy.properties import (StringProperty, DictProperty, 
                           ObjectProperty, ListProperty, NumericProperty)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.uix.togglebutton import ToggleButton
from kivy.clock import Clock, mainthread
from kivy.lang import Builder
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.network.urlrequest import UrlRequest

# API Configuration
RIOT_API_KEY = 'YOUR_RIOT_API_KEY'  # Replace with your API key
DATA_DRAGON_BASE = 'https://ddragon.leagueoflegends.com/cdn'
LATEST_VERSION = None  # Will be fetched at runtime

# Load KV files
Builder.load_file('widgets.kv')
Builder.load_file('screens/home.kv')
Builder.load_file('screens/tier_list.kv')
Builder.load_file('screens/comp_builder.kv')
Builder.load_file('screens/settings.kv')

class RiotAPI:
    @staticmethod
    def get_latest_version():
        url = 'https://ddragon.leagueoflegends.com/api/versions.json'
        response = requests.get(url)
        return response.json()[0] if response.ok else '13.24.1'

    @staticmethod
    def get_champions(version):
        url = f'{DATA_DRAGON_BASE}/{version}/data/en_US/champion.json'
        response = requests.get(url)
        if response.ok:
            data = response.json()
            return [{
                'id': champ['id'],
                'key': champ['key'],
                'name': champ['name'],
                'title': champ['title'],
                'tags': champ['tags'],
                'image': f"{DATA_DRAGON_BASE}/{version}/img/champion/{champ['image']['full']}"
            } for champ in data['data'].values()]
        return []

    @staticmethod
    def get_champion_icon(version, champion_id):
        return f"{DATA_DRAGON_BASE}/{version}/img/champion/{champion_id}.png"

class ChampionCard(ButtonBehavior, BoxLayout):
    champion = DictProperty({})
    theme = DictProperty({})
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(theme=self.update_style)
        Clock.schedule_once(self.update_style)
    
    def update_style(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(rgba=hex(self.theme['card'] + 'CC'))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])

class TierListItem(BoxLayout):
    champion = DictProperty({})
    tier = StringProperty('')
    role = StringProperty('')
    theme = DictProperty({})

class CompChampionSlot(ButtonBehavior, BoxLayout):
    role = StringProperty('')
    champion = DictProperty(None)
    theme = DictProperty({})

class ThemeButton(ToggleButton):
    theme_name = StringProperty('')
    
    def on_state(self, instance, value):
        if value == 'down':
            app = App.get_running_app()
            app.set_theme(self.theme_name)

class BaseScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        self.update_theme(app.theme)
    
    def update_theme(self, theme):
        pass

class HomeScreen(BaseScreen):
    pass

class TierListScreen(BaseScreen):
    tier_data = ListProperty([])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_tier_data()
    
    def load_tier_data(self):
        # This would normally come from a tier list API
        # For demo, we'll create sample data
        app = App.get_running_app()
        self.tier_data = [{
            'champion': champ,
            'tier': 'S' if i % 5 == 0 else 'A' if i % 5 == 1 else 'B',
            'role': champ['tags'][0] if champ['tags'] else 'UNKNOWN'
        } for i, champ in enumerate(app.champions[:20])]

class CompBuilderScreen(BaseScreen):
    team_comp = ListProperty([None]*5)  # Top, Jungle, Mid, ADC, Support
    
    def add_champion(self, champion, role):
        role_index = ['TOP', 'JUNGLE', 'MID', 'ADC', 'SUPPORT'].index(role.upper())
        self.team_comp[role_index] = champion

class SettingsScreen(BaseScreen):
    pass

class ChampionGuideApp(App):
    theme = DictProperty()
    current_theme = StringProperty('noxus')
    champions = ListProperty([])
    loading_progress = NumericProperty(0)
    
    THEMES = {
        'noxus': {
            'name': 'Noxus',
            'primary': '#5C0000',
            'secondary': '#3A0000',
            'accent': '#C4A56A',
            'text': '#E3DCC7',
            'card': '#2A2A2A',
            'background': '#121212'
        },
        'ionia': {
            'name': 'Ionia',
            'primary': '#6A5ACD',
            'secondary': '#4B3AA8',
            'accent': '#8A6BBE',
            'text': '#FFFFFF',
            'card': '#3A3A56',
            'background': '#1A1A2E'
        },
        'rift': {
            'name': 'Summoner\'s Rift',
            'primary': '#1C4D5A',
            'secondary': '#0A323C',
            'accent': '#D9B56B',
            'text': '#E8E1D5',
            'card': '#2A4D5A',
            'background': '#0A2329'
        }
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme = self.THEMES['noxus']
        self.data_dragon_version = None
    
    def build(self):
        self.sm = ScreenManager(transition=FadeTransition())
        self.sm.add_widget(HomeScreen(name='home'))
        self.sm.add_widget(TierListScreen(name='tier_list'))
        self.sm.add_widget(CompBuilderScreen(name='comp_builder'))
        self.sm.add_widget(SettingsScreen(name='settings'))
        
        Window.size = (360, 640)
        self.load_data()
        return self.sm
    
    def load_data(self):
        # First get the latest version
        self.loading_progress = 0.1
        UrlRequest(
            'https://ddragon.leagueoflegends.com/api/versions.json',
            on_success=self.on_versions_loaded,
            on_failure=self.on_api_error,
            on_error=self.on_api_error
        )
    
    def on_versions_loaded(self, req, versions):
        self.data_dragon_version = versions[0]
        self.loading_progress = 0.3
        
        # Now load champions
        UrlRequest(
            f'{DATA_DRAGON_BASE}/{self.data_dragon_version}/data/en_US/champion.json',
            on_success=self.on_champions_loaded,
            on_failure=self.on_api_error,
            on_error=self.on_api_error
        )
    
    @mainthread
    def on_champions_loaded(self, req, data):
        self.loading_progress = 0.8
        champions = []
        for champ_id, champ_data in data['data'].items():
            champions.append({
                'id': champ_data['id'],
                'key': champ_data['key'],
                'name': champ_data['name'],
                'title': champ_data['title'],
                'tags': champ_data['tags'],
                'image': f"{DATA_DRAGON_BASE}/{self.data_dragon_version}/img/champion/{champ_data['image']['full']}"
            })
        
        self.champions = sorted(champions, key=lambda x: x['name'])
        self.loading_progress = 1.0
    
    def on_api_error(self, req, error):
        print(f"API Error: {error}")
        # Fallback to sample data if API fails
        self.champions = [{
            'id': 'aatrox',
            'name': 'Aatrox',
            'tags': ['Fighter', 'Tank'],
            'image': 'https://ddragon.leagueoflegends.com/cdn/13.24.1/img/champion/Aatrox.png'
        }]
        self.loading_progress = 1.0
    
    def set_theme(self, theme_name):
        self.current_theme = theme_name
        self.theme = self.THEMES[theme_name]
        Window.clearcolor = hex(self.theme['background'])
        
        for screen in self.sm.screens:
            if hasattr(screen, 'update_theme'):
                screen.update_theme(self.theme)

if __name__ == '__main__':
    ChampionGuideApp().run()