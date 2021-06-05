# Rock Paper Scissors
# -- Created by Divyanshu Tiwari --

# Imports
from kivy.app import App
from kivy.core.audio import SoundLoader, Sound
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, WipeTransition, NoTransition


# Sound and music related stuff
from kivy.uix.widget import Widget

Sound.volume = 1

bg_music = SoundLoader.load('Sounds/bg.mp3')
bg_music.loop = True
main_game_music = SoundLoader.load('Sounds/main_game.mp3')
main_game_music.loop = True


# Global Variables
screen_manager = ScreenManager(transition=WipeTransition())
name_of_user = ''
main_game = None  # for resetting the game when user exits from 'MainGame' screen
exit_prompt = None  # prevents creation of more 'ExitPrompt' if one already exists


# First screen of game: Main Menu
class MainMenu(Screen):
    click_sound = SoundLoader.load('Sounds/click.ogg')

    @staticmethod
    def quit_game():
        RockPaperScissorApp().stop()

    # This method will toggle the music of the game.
    def toggle_music(self):
        Sound.volume = 1 if Sound.volume == 0 else 0  # toggle mute the music by changing volume level
        bg_music.stop() if bg_music.state == "play" else bg_music.play()  # toggles state of background music

        # Change the source of image for representing the current state of music
        if self.ids.audio_switch_btn.source == "Images/audio_on.png":
            self.ids.audio_switch_btn.source = "Images/audio_off.png"
        else:
            self.click_sound.play()
            self.ids.audio_switch_btn.source = "Images/audio_on.png"


# This screen appears after 'Play' button click of Main Menu: For getting name of user
class EnterName(Screen):
    click_sound = SoundLoader.load('Sounds/click.ogg')
    begin_sound = SoundLoader.load('Sounds/begin.ogg')

    def begin_game(self):
        global name_of_user
        name_of_user = self.ids.username.text.upper()  # store username given by user
        bg_music.stop()
        screen_manager.transition = NoTransition()

        def change_screen(delta_time):
            self.ids.username.text = ""
            screen_manager.current = "Main Game"
            main_game_music.play()
            screen_manager.transition = WipeTransition()

        Clock.schedule_once(change_screen, 2)

    def validate_username(self):
        self.ids.username.text = self.ids.username.text.upper()  # capitalizing name

        # If no name is given, disable the 'Start' button else enable it
        self.ids.start_button.disabled = False if len(self.ids.username.text) != 0 else True

        if len(self.ids.username.text) > 12 or ' ' in self.ids.username.text:  # prevents entering whitespace in name
            self.ids.username.text = self.ids.username.text[:len(self.ids.username.text) - 1]


# This screen appears after 'Start' button click of 'EnterName' screen: A blank screen just for
# representing that game is loading
class BlankScreen(Screen):
    pass


# This screen appears after 2 seconds when 'BlankScreen' appears on 'Start' button click of 'EnterName' screen
# This is the screen where the game will be played
class MainGame(Screen):
    click_sound = SoundLoader.load('Sounds/click.ogg')

    def show_exit_prompt(self):
        global exit_prompt
        if exit_prompt is None:
            self.ids.background_image.opacity = 0.4
            self.ids.switch_to_home.opacity = 0.4
            self.ids.game_actions.opacity = 0.4
            exit_prompt = ExitPrompt()
            self.add_widget(exit_prompt)


# This is actually a widget which will be shown when user clicks on 'exit.png' image of 'MainGame' screen
# It will show a prompt asking user if he/she is sure of getting back to 'MainMenu' screen
class ExitPrompt(Screen):
    click_sound = SoundLoader.load('Sounds/click.ogg')

    @staticmethod
    def go_to_main_menu():
        global main_game
        main_game_music.stop()
        screen_manager.current = "Main Menu"
        screen_manager.remove_widget(main_game)
        main_game = MainGame(name='Main Game')
        screen_manager.add_widget(main_game)
        if Sound.volume == 1:
            bg_music.play()

    def remove_prompt(self):
        global exit_prompt
        exit_prompt = None
        main_game.ids.background_image.opacity = 0.7
        main_game.ids.switch_to_home.opacity = 1
        main_game.ids.game_actions.opacity = 1
        self.clear_widgets()


# This is the root widget of all the screens and widgets of the game
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


# Starting the game
if __name__ == '__main__':
    RockPaperScissorApp().run()
