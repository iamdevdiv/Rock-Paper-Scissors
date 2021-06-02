from kivy.app import App
from kivy.core.audio import SoundLoader, Sound
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, SwapTransition, FallOutTransition,  CardTransition, \
    FadeTransition, WipeTransition, FallOutTransition, RiseInTransition
from kivy.properties import ObjectProperty, NumericProperty

Sound.volume = 1

screen_manager = ScreenManager(transition=WipeTransition())

bg_music = SoundLoader.load('Sounds/bg.mp3')
bg_music.loop = True
main_game_music = SoundLoader.load('Sounds/main_game.wav')
main_game_music.loop = True

name_of_user = ''


class MainMenu(Screen):
    click_sound = SoundLoader.load('Sounds/click.ogg')
    audio_switch_btn = ObjectProperty(None)

    @staticmethod
    def quit_game():
        RockPaperScissorApp().stop()

    def toggle_sound(self):
        Sound.volume = 1 if Sound.volume == 0 else 0
        bg_music.stop() if bg_music.state == "play" else bg_music.play()
        if self.audio_switch_btn.source == "Images/audio_on.png":
            self.audio_switch_btn.source = "Images/audio_off.png"
        else:
            self.audio_switch_btn.source = "Images/audio_on.png"
            self.click_sound.play()


class EnterName(Screen):
    click_sound = SoundLoader.load('Sounds/click.ogg')
    begin_sound = SoundLoader.load('Sounds/begin.ogg')
    main_game_music = SoundLoader.load('Sounds/main_game.wav')
    main_game_music.loop = True
    username = ObjectProperty(None)
    start_button = ObjectProperty(None)

    def begin_game(self):
        bg_music.stop()

        def change_screen(delta_time):
            self.username.text = ""
            screen_manager.current = "Main Game"
            main_game_music.play()

        Clock.schedule_once(change_screen, 2)

    def check_length(self):
        self.username.text = self.username.text.upper()
        self.start_button.disabled = False if len(self.username.text) != 0 else True
        if len(self.username.text) > 12 or ' ' in self.username.text:
            self.username.text = self.username.text[:len(self.username.text) - 1]

    def set_name(self):
        global name_of_user
        name_of_user = self.username.text.upper()


class BlankScreen(Screen):
    pass


class MainGame(Screen):
    click_sound = SoundLoader.load('Sounds/click.ogg')

    def quit_game(self):
        self.add_widget(ExitPrompt())


class ExitPrompt(Screen):
    click_sound = SoundLoader.load('Sounds/click.ogg')

    @staticmethod
    def quit_game():
        global main_game
        main_game_music.stop()
        screen_manager.current = "Main Menu"
        screen_manager.remove_widget(main_game)
        main_game = MainGame(name='Main Game')
        screen_manager.add_widget(main_game)
        if Sound.volume == 1:
            bg_music.play()


main_game = None


class RockPaperScissorApp(App):
    def build(self):
        global main_game
        screen_manager.add_widget(MainMenu(name='Main Menu'))
        screen_manager.add_widget(EnterName(name='Enter Name'))
        screen_manager.add_widget(BlankScreen(name='Blank Screen'))
        main_game = MainGame(name='Main Game')
        screen_manager.add_widget(main_game)
        screen_manager.add_widget(ExitPrompt(name='Exit Prompt'))
        bg_music.play()
        return screen_manager


if __name__ == '__main__':
    RockPaperScissorApp().run()
