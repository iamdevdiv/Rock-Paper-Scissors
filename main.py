# Rock Paper Scissors
# -- Created by Divyanshu Tiwari --

# Imports
import random
from functools import partial
from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader, Sound
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen, WipeTransition, NoTransition
from kivy.base import stopTouchApp

# Sound and music related stuff
Sound.volume = 1
to_play_music = True

bg_music = SoundLoader.load('Sounds/bg.ogg')
bg_music.loop = True
main_game_music = SoundLoader.load('Sounds/main_game.ogg')
main_game_music.loop = True
main_game_music.volume = 1


# Global Variables
screen_manager = ScreenManager(transition=WipeTransition())
name_of_user = ''
main_game = None  # for resetting the game when user exits from 'MainGame' screen
cheats_screen = None  # for resetting cheats when user triple tap anywhere on 'MainGame' screen


# First screen of game: Main Menu
class MainMenu(Screen):
    click_sound = SoundLoader.load('Sounds/click.ogg')

    # This method will toggle the music of the game.
    def toggle_music(self):
        global to_play_music
        Sound.volume = 1 if Sound.volume == 0 else 0  # toggles the music by changing volume level
        bg_music.stop() if bg_music.state == "play" else bg_music.play()  # toggles state of background music
        # Change the source of image for representing the current state of music
        if self.ids.audio_switch_btn.source == "atlas://Images/myatlas/audio_on":
            self.ids.audio_switch_btn.source = "atlas://Images/myatlas/audio_off"
            to_play_music = False
        else:
            self.click_sound.play()
            self.ids.audio_switch_btn.source = "atlas://Images/myatlas/audio_on"
            to_play_music = True

    @staticmethod
    def add_screens():  # method to add screens to the screen manager when user clicks on 'Play' button
        global main_game, cheats_screen
        if "Enter Name" not in screen_manager.screen_names:
            screen_manager.add_widget(EnterName(name="Enter Name"))
        screen_manager.current = "Enter Name"
        if "Blank Screen" not in screen_manager.screen_names:
            screen_manager.add_widget(BlankScreen(name='Blank Screen'))
            main_game = MainGame(name='Main Game')
            screen_manager.add_widget(main_game)
            screen_manager.add_widget(PauseScreen(name='Pause Screen'))
            cheats_screen = CheatsScreen(name='Cheats Screen')
            screen_manager.add_widget(cheats_screen)

    @staticmethod
    def switch_to_rules():
        if "Rules Screen" not in screen_manager.screen_names:
            screen_manager.add_widget(RulesScreen(name="Rules Screen"))
        screen_manager.current = "Rules Screen"

    @staticmethod
    def switch_to_credits():
        if "Credits Screen" not in screen_manager.screen_names:
            screen_manager.add_widget(CreditsScreen(name="Credits Screen"))
        screen_manager.current = "Credits Screen"


# This screen appears after 'Play' button click of Main Menu: For getting name of user
class EnterName(Screen):
    click_sound = SoundLoader.load('Sounds/click.ogg')
    begin_sound = SoundLoader.load('Sounds/begin.ogg')

    def begin_game(self):
        global name_of_user
        # if user has entered any name, store it else name will be 'You'
        name_of_user = self.ids.username.text.title() if self.ids.username.text != "" else 'You'
        main_game.ids.user_name.text = name_of_user  # set name of user in game
        # Stop music and remove screen switch transition
        bg_music.stop()
        main_game.unmute_music()
        screen_manager.transition = NoTransition()

        def change_screen(delta_time):  # function to change screen from EnterName to MainGame
            self.ids.username.text = ""
            screen_manager.current = "Main Game"
            if to_play_music:
                main_game_music.play()
            screen_manager.transition = WipeTransition()

        def start_game(delta_time):
            main_game.start_round()

        # Start the game after 2 seconds
        Clock.schedule_once(change_screen, 2)
        Clock.schedule_once(start_game, 2)

    def validate_username(self):
        self.ids.username.text = self.ids.username.text.upper()  # capitalizing name
        if len(self.ids.username.text) > 12 or ' ' in self.ids.username.text:  # prevents entering whitespace in name
            self.ids.username.text = self.ids.username.text[:len(self.ids.username.text) - 1]


# This screen appears after 'Start' button click of 'EnterName' screen: A blank screen just for
# representing that game is loading
class BlankScreen(Screen):
    pass


# This screen appears after 2 seconds when 'BlankScreen' appears on click of 'Start' button of 'EnterName' screen
# This is the screen where the game will be played
class MainGame(Screen):
    click_sound = SoundLoader.load("Sounds/click.ogg")
    rock_clicked_sound = SoundLoader.load("Sounds/rock.ogg")
    paper_clicked_sound = SoundLoader.load("Sounds/paper.ogg")
    scissor_clicked_sound = SoundLoader.load("Sounds/scissor.ogg")
    you_win_sound = SoundLoader.load("Sounds/you_win.ogg")
    you_lose_sound = SoundLoader.load("Sounds/you_lose.ogg")
    winner_sound = SoundLoader.load("Sounds/winner.ogg")
    loser_sound = SoundLoader.load("Sounds/loser.ogg")
    tie_sound = SoundLoader.load("Sounds/tie.ogg")
    tie_breaker_sound = SoundLoader.load("Sounds/tie_breaker.ogg")
    round_one_sound = SoundLoader.load("Sounds/round_1.ogg")
    round_two_sound = SoundLoader.load("Sounds/round_2.ogg")
    round_three_sound = SoundLoader.load("Sounds/round_3.ogg")
    round_four_sound = SoundLoader.load("Sounds/round_4.ogg")
    round_five_sound = SoundLoader.load("Sounds/round_5.ogg")
    final_round_sound = SoundLoader.load("Sounds/final_round.ogg")
    round_sounds = {1: round_one_sound, 2: round_two_sound, 3: round_three_sound, 4: round_four_sound,
                    5: round_five_sound, 6: final_round_sound, 7: tie_breaker_sound}
    sounds_for_mute_unmute_stop = [click_sound, rock_clicked_sound, paper_clicked_sound, scissor_clicked_sound,
                                   you_win_sound, you_lose_sound, winner_sound, loser_sound, tie_sound,
                                   tie_breaker_sound]

    user_name = ObjectProperty(None)
    message = ObjectProperty(None)
    round_on_screen = ObjectProperty(None)
    select_rock = ObjectProperty(None)
    select_paper = ObjectProperty(None)
    select_scissor = ObjectProperty(None)
    user_points = ObjectProperty(None)
    user_choice_text = ObjectProperty(None)
    computer_points = ObjectProperty(None)
    computer_choice_text = ObjectProperty(None)
    play_again_button = ObjectProperty(None)

    points = {"user": 0, "computer": 0}
    current_round = 1
    winner = ""
    schedule_timings = {"rst": 2, "rsp": 1.7}  # rst: round_start_time, rsp: round_sound_play
    game_playable = True

    # Cheats related variables
    always_win = False
    always_lose = False
    clicks = 0

    def show_exit_prompt(self):
        if self.game_playable:
            # Lower the opacity of all the widgets
            self.ids.background_image.opacity = 0.4
            self.ids.switch_to_home.opacity = 0.4
            self.ids.game_actions.opacity = 0.4
            self.ids.pause_game.opacity = 0.4

            self.play_again_button.disabled = True
            self.game_playable = False
            self.add_widget(ExitPrompt())

    def set_message(self, text: str, delta_time, set_computer_choice=False, choice=""):
        self.message.text = text
        if text == "It's your turn !!":
            self.user_choice_text.text = ""
            self.computer_choice_text.text = ""
        if set_computer_choice:
            self.computer_choice_text.text = choice

    def toggle_buttons_state(self, delta_time=0):
        if self.select_rock.disabled:  # if one button is disabled, means all buttons are disabled
            self.select_rock.disabled = False
            self.select_rock.opacity = 1
            self.select_paper.disabled = False
            self.select_paper.opacity = 1
            self.select_scissor.disabled = False
            self.select_scissor.opacity = 1
        else:
            self.select_rock.disabled = True
            self.select_rock.opacity = 0.7
            self.select_paper.disabled = True
            self.select_paper.opacity = 0.7
            self.select_scissor.disabled = True
            self.select_scissor.opacity = 0.7

    # This method will get the choice of computer. If any cheat is activated, choice will be based on that cheat,
    # otherwise choice will be random.
    def get_computer_choice(self, user_choice: str):
        choices = ["Rock", "Paper", "Scissor"]
        choices_for_win = {"Rock": "Scissor", "Paper": "Rock", "Scissor": "Paper"}
        choices_for_lose = {"Rock": "Paper", "Paper": "Scissor", "Scissor": "Rock"}

        if self.always_win:
            return choices_for_win[user_choice]
        elif self.always_lose:
            return choices_for_lose[user_choice]
        else:
            return random.choice(choices)

    def set_computer_choice(self, choice):
        self.computer_choice_text.text = choice

    # This method will compare the choices of player and computer and then return the winner
    def get_winner(self, choices: dict, delta_time):
        choices_list = list(choices.keys())
        self.winner = "TIE"
        # Comparing choices
        if "Rock" in choices_list and "Paper" in choices_list:
            self.winner = choices["Paper"]
        elif "Paper" in choices_list and "Scissor" in choices_list:
            self.winner = choices["Scissor"]
        elif "Scissor" in choices_list and "Rock" in choices_list:
            self.winner = choices["Rock"]

        # Changing the appearance of text on game to represent the winner, playing sound effects, increasing points and
        # increment round number
        if self.winner == "player":
            self.user_choice_text.color = 0, 1, 0
            self.computer_choice_text.color = 1, 0, 0
            self.you_win_sound.play()
            self.points["user"] += 1
            self.user_points.text = str(self.points["user"])
            self.current_round += 1
        elif self.winner == "computer":
            self.user_choice_text.color = 1, 0, 0
            self.computer_choice_text.color = 0, 1, 0
            self.you_lose_sound.play()
            self.points["computer"] += 1
            self.computer_points.text = str(self.points["computer"])
            self.current_round += 1
        else:
            self.tie_sound.play()

        Clock.schedule_once(self.start_round, 2)  # Start next round after 2 seconds
        return self.winner

    def set_round_text(self, delta_time):
        self.user_choice_text.color = 203/255, 158/255, 249/255
        self.computer_choice_text.color = 203/255, 158/255, 249/255
        self.round_on_screen.opacity = 1  # change the opacity of round number to 1 which is 0 when the game starts
        if self.current_round < 6:
            self.round_on_screen.text = f"ROUND {self.current_round}"
        elif self.current_round == 6:
            self.round_on_screen.text = "FINAL ROUND"
        else:
            self.round_on_screen.text = "TIE BREAKER"

    def start_round(self, delta_time=0):
        # Round will be played if the current_round is less than or equal to 6. And If the points of the user and the
        # computer are equal, tie breaker round will be played
        if self.current_round <= 6 or self.points["user"] == self.points["computer"]:
            # Play sound effect of current round and set the text of round in game
            Clock.schedule_once(lambda dt: self.round_sounds[self.current_round].play(), self.schedule_timings["rsp"])
            Clock.schedule_once(self.set_round_text, self.schedule_timings["rst"])
            # Enable the buttons and tell the user that it's his turn
            Clock.schedule_once(self.toggle_buttons_state, self.schedule_timings["rst"])
            Clock.schedule_once(partial(self.set_message, "It's your turn !!"), self.schedule_timings["rst"])
            # Scheduled timings will be changed after first round
            self.schedule_timings["rst"] = 0.3
            self.schedule_timings["rsp"] = 0
        else:  # After the sixth round or tie breaker round, tell the user who is the winner
            if self.points["user"] > self.points["computer"]:
                self.winner_sound.play()
                self.user_choice_text.color = 0, 1, 0
                self.computer_choice_text.color = 1, 0, 0
                self.user_choice_text.text = "WINNER"
                self.computer_choice_text.text = "LOSER"
            elif self.points["computer"] > self.points["user"]:
                self.loser_sound.play()
                self.user_choice_text.color = 1, 0, 0
                self.computer_choice_text.color = 0, 1, 0
                self.user_choice_text.text = "LOSER"
                self.computer_choice_text.text = "WINNER"
            # Enable and show the 'Play again' button
            self.play_again_button.disabled = False
            self.play_again_button.opacity = 1

    # This method will get the user's choice and computer's choice, and then compare them to get the winner by using the
    # get_winner() method
    def compare_choices(self, selection):
        options = {1: "Rock", 2: "Paper", 3: "Scissor"}
        user_choice = options[selection]
        self.user_choice_text.text = user_choice
        Clock.schedule_once(partial(self.set_message, "Computer's turn..."), 0.5)
        computer_choice = self.get_computer_choice(user_choice)
        Clock.schedule_once(partial(self.set_message, "", True, choice=computer_choice), 1.5)
        Clock.schedule_once(partial(self.get_winner, {user_choice: "player", computer_choice: "computer"}), 2)

    def play_again(self):  # method for 'Play again' button
        global main_game
        screen_manager.current = "Blank Screen"
        # reset points
        self.points["user"] = 0
        self.points["computer"] = 0
        # reset the game by removing current 'MainGame' screen and adding a new one
        screen_manager.remove_widget(main_game)
        main_game = MainGame(name="Main Game")
        main_game.user_name.text = name_of_user
        if cheats_screen.always_win_button.state == "down":
            main_game.always_win = True
        elif cheats_screen.always_lose_button.state == "down":
            main_game.always_lose = True
        screen_manager.add_widget(main_game)
        screen_manager.current = "Main Game"
        Clock.schedule_once(main_game.start_round, 1)

    # The two methods given below will set mute/unmute the music by changing their volume
    def mute_music(self):
        for sound in self.sounds_for_mute_unmute_stop:
            sound.volume = 0
        for sound in self.round_sounds.values():
            sound.volume = 0

    def unmute_music(self):
        if to_play_music:
            for sound in self.sounds_for_mute_unmute_stop:
                sound.volume = 1
            for sound in self.round_sounds.values():
                sound.volume = 1

    # This method will stop the music by changing their play state
    def stop_music(self):
        if to_play_music:
            main_game_music.stop()
            Sound.volume = 0
            for sound in self.sounds_for_mute_unmute_stop:
                if sound.state == "play":
                    sound.stop()
            for sound in self.round_sounds.values():
                if sound.state == "play":
                    sound.stop()

    def pause_game(self):  # method for pausing the game
        if self.game_playable:
            self.stop_music()
            self.mute_music()
            screen_manager.transition = NoTransition()
            screen_manager.current = "Pause Screen"

    # This method will be used by reset_cheats() method to set the clicks variable to 0
    def reset_clicks(self, delta_time):
        self.clicks = 0

    # This method will calculate the clicks of the user on the 'MainGame' screen. If the user clicks three times within
    # 0.5 seconds, all the cheats will be deactivated. Otherwise, it will reset the 'clicks' variable by using the above
    # method
    def reset_cheats(self):
        if self.clicks == 0:
            Clock.schedule_once(self.reset_clicks, 0.5)  # reset the clicks after 0.5 seconds
        self.clicks += 1
        if self.clicks == 3 and self.message.text == "It's your turn !!":
            self.always_win = False
            self.always_lose = False
            cheats_screen.always_win_button.state = "normal"
            cheats_screen.always_lose_button.state = "normal"


# This is actually a widget which will be shown when user clicks on 'exit.png' image of 'MainGame' screen
# It will show a prompt asking user if he/she is sure of getting back to 'MainMenu' screen
class ExitPrompt(Screen):
    click_sound = SoundLoader.load('Sounds/click.ogg')

    @staticmethod
    def go_to_main_menu():
        global main_game
        main_game.stop_music()
        main_game.mute_music()
        screen_manager.current = "Main Menu"
        # Remove 'MainGame' screen from screen manager and add it again to reset the game
        screen_manager.remove_widget(main_game)
        main_game = MainGame(name='Main Game')
        # Reset the points
        main_game.points["user"] = 0
        main_game.points["computer"] = 0
        screen_manager.add_widget(main_game)
        if to_play_music:
            Sound.volume = 1
            bg_music.play()
        main_game.game_playable = True

    def remove_prompt(self):
        # Reset the opacity of widgets to make them visible
        main_game.ids.background_image.opacity = 0.8
        main_game.ids.switch_to_home.opacity = 1
        main_game.ids.game_actions.opacity = 1
        main_game.ids.pause_game.opacity = 1
        main_game.play_again_button.disabled = False
        main_game.remove_widget(self)  # remove exit prompt from 'MainGame' screen
        main_game.game_playable = True


# This screen will be shown when user pauses the game
class PauseScreen(Screen):
    click_sound = SoundLoader.load("Sounds/click.ogg")

    @staticmethod
    def resume_game():
        if to_play_music:
            main_game.unmute_music()
            main_game_music.play()
        screen_manager.current = 'Main Game'
        screen_manager.transition = WipeTransition()

    # Following code is related to cheats
    top_button = ObjectProperty(None)  # hidden and disabled button
    bottom_button = ObjectProperty(None)  # hidden button

    clicks = 0

    # This method will be used by enable_top_button() and show_cheats() methods to set the clicks variable to 0
    def reset_clicks(self, delta_time):
        self.clicks = 0

    # If user clicks on the hidden bottom_button three times within 0.5 seconds, this method will enable the top_button
    def enable_top_button(self):
        if self.clicks == 0:
            Clock.schedule_once(self.reset_clicks, 0.5)
        self.clicks += 1
        if self.clicks == 3:
            self.top_button.disabled = False
            self.bottom_button.disabled = True

    # After the top_button is enabled by above method, clicking it three times within 0.5 seconds will reveal the cheats
    def show_cheats(self):
        if self.clicks == 0:
            Clock.schedule_once(self.reset_clicks, 0.5)
        self.clicks += 1
        if self.clicks == 3:
            self.top_button.disabled = True
            self.bottom_button.disabled = False
            screen_manager.current = "Cheats Screen"


# Cheats can be activated on this screen. There's a secret way to access this screen - Pause the game, triple tap on the
# bottom of the screen and then triple tap on the top of the screen; this will reveal this screen.
class CheatsScreen(Screen):
    always_win_button = ObjectProperty(None)
    always_lose_button = ObjectProperty(None)

    def toggle_cheats(self):
        if self.always_win_button.state == "normal":
            main_game.always_win = False
        elif self.always_win_button.state == "down":
            main_game.always_win = True

        if self.always_lose_button.state == "normal":
            main_game.always_lose = False
        elif self.always_lose_button.state == "down":
            main_game.always_lose = True


# This screen includes all the rules of the game. This screen also provides the user a hint for accessing the cheats.
class RulesScreen(Screen):
    click_sound = SoundLoader.load("Sounds/click.ogg")


# This screen includes the all the credits of the screen - The developer and all the websites which have provided the
# assets required for the game
class CreditsScreen(Screen):
    click_sound = SoundLoader.load("Sounds/click.ogg")


# This is the root widget of all the screens and widgets of the game
class RockPaperScissorApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.back_button)

    @staticmethod
    def back_button(window, key, *largs):  # handle back button click on android smartphone
        if key == 27:
            if screen_manager.current in ["Enter Name", "Rules Screen", "Credits Screen"]:
                screen_manager.current = "Main Menu"
            elif screen_manager.current == "Cheats Screen":
                screen_manager.current = "Pause Screen"
            elif screen_manager.current == "Main Game":
                main_game.show_exit_prompt()
            elif screen_manager.current == "Main Menu":
                stopTouchApp()

            return True

    def build(self):
        screen_manager.add_widget(MainMenu(name='Main Menu'))
        bg_music.play()
        return screen_manager


# Starting the game
if __name__ == '__main__':
    RockPaperScissorApp().run()
