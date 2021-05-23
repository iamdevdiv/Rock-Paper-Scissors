from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen


class MainMenu(Screen):
    @staticmethod
    def quit_game():
        RockPaperScissor().stop()


class SelectMode(Screen):
    pass


class OnePlayerName(Screen):
    pass


class TwoPlayerName(Screen):
    pass


class VsComputer(Screen):
    pass


class VsPlayer(Screen):
    pass


class RockPaperScissor(App):
    def build(self):
        screen_manager = ScreenManager()
        screen_manager.add_widget(MainMenu(name='Main Menu'))
        screen_manager.add_widget(SelectMode(name='Select Mode'))
        screen_manager.add_widget(OnePlayerName(name='One Player Name'))
        screen_manager.add_widget(TwoPlayerName(name='Two Player Name'))
        screen_manager.add_widget(VsComputer(name='Play with Computer'))
        screen_manager.add_widget(VsPlayer(name='Two Player Mode'))
        return screen_manager


if __name__ == '__main__':
    RockPaperScissor().run()
