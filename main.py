# Rock Paper Scissors
# -- Created by Divyanshu Tiwari --

# Imports
from network import Network
from threading import Thread
from functools import partial
from random import choice as choose_randomly

from kivy.app import App
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.base import stopTouchApp
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.core.audio import SoundLoader, Sound
from kivy.uix.screenmanager import ScreenManager, Screen, WipeTransition, NoTransition


# Global Variables
screen_manager = ScreenManager(transition=NoTransition())
name_of_user = ""


# Loading screen is mainly made for Android where it will be shown while widgets and music of game is being
# loaded on background using another thread
class LoadingScreen(Screen):
    def __init__(self) -> None:
        super(LoadingScreen, self).__init__(name="Loading Screen")
        self.app = App.get_running_app()

        # This event will be triggered by the game on start after loading screen is added to the screen manager
        self.wait_for_loading_completion = Clock.create_trigger(self.wait_for_music, 1, True)

    def wait_for_music(self, delta_time=0) -> None:
        # Thread is not alive means loading of all the widgets and music is completed, so cancel the thread which
        # was waiting for the loading to be completed, go to main menu and start background music
        if not self.app.loading_thread.is_alive():
            self.wait_for_loading_completion.cancel()
            screen_manager.current = "Main Menu"
            screen_manager.transition = WipeTransition()
            self.app.bg_music.play()


# First screen of game: Main Menu
class MainMenu(Screen):
    def __init__(self) -> None:
        super(MainMenu, self).__init__(name="Main Menu")
        self.app = App.get_running_app()

    # This method will toggle the music of the game.
    def toggle_music(self) -> None:
        Sound.volume = 1 if Sound.volume == 0 else 0  # toggle the music by changing volume level

        # Toggle state of background music
        self.app.bg_music.stop() if self.app.bg_music.state == "play" else self.app.bg_music.play()

        # Change the source of image for representing the current state of music
        if self.ids.audio_switch_btn.source == "atlas://images/audio_on":
            self.ids.audio_switch_btn.source = "atlas://images/audio_off"
            self.app.music_allowed = False
        else:
            self.ids.audio_switch_btn.source = "atlas://images/audio_on"
            self.app.music_allowed = True


# This screen appears after "Play" button click of Main Menu: For getting name of the user
class EnterName(Screen):
    def __init__(self) -> None:
        super(EnterName, self).__init__(name="Enter Name")
        self.computer_game = screen_manager.get_screen("Computer Game")

    def validate_username(self) -> None:
        global name_of_user
        self.ids.username.text = self.ids.username.text.upper()  # capitalizing name
        if len(self.ids.username.text) > 12 or self.ids.username.text in [" ", "\t"]:  # prevent entering whitespace
            self.ids.username.text = self.ids.username.text[:len(self.ids.username.text) - 1]

        # If user has entered any name, store it else name will be "You"
        name_of_user = self.ids.username.text.title() if self.ids.username.text != "" else "You"
        self.computer_game.ids.user_name.text = name_of_user  # set name of user in computer game


# This screen appears after 'Start' button click of 'EnterName' screen: for selecting the computer or online mode
# for the game
class SelectMode(Screen):
    bg_image = ObjectProperty(None)
    back_button = ObjectProperty(None)
    select_mode_text = ObjectProperty(None)
    computer_mode = ObjectProperty(None)
    online_mode = ObjectProperty(None)
    waiting_text = ObjectProperty(None)
    cancel_search_info = ObjectProperty(None)
    cancel_button = ObjectProperty(None)
    no_wifi_img = ObjectProperty(None)

    def __init__(self) -> None:
        super(SelectMode, self).__init__(name="Select Mode")
        self.app = App.get_running_app()
        self.computer_game = screen_manager.get_screen("Computer Game")
        self.wait_for_player_event = Clock.create_trigger(self.set_waiting_text, 1, True)
        self.time_left = 31
        self.network = None

    def begin_game(self, game_mode: str) -> None:
        # Stop music
        self.app.bg_music.stop()
        self.computer_game.unmute_music()

        screen_manager.current = game_mode
        if self.app.music_allowed:
            self.app.main_game_music.play()

        # In online mode, rounds will be started and handled by OnlineGame object 
        if game_mode == "Computer Game":
            self.computer_game.start_round()

    def timer(self) -> int:
        self.time_left -= 1
        return self.time_left

    def show_no_wifi(self) -> None:  # the icon shown on connection lost or issue in connecting with the server
        self.no_wifi_img.opacity = 1
        self.waiting_text.opacity = 1
        self.cancel_search_info.opacity = 0

    def dim_the_background(self) -> None:
        self.back_button.opacity = 0.2
        self.computer_mode.opacity = 0.2
        self.bg_image.opacity = 0.2
        self.online_mode.opacity = 0.2
        self.select_mode_text.opacity = 0.2

        self.waiting_text.opacity = 1
        self.cancel_search_info.opacity = 1
        self.cancel_button.disabled = False

    def lit_the_background(self, delta_time=0) -> None:
        # If player has started searching again for an opponent after cancelling previous search or if one was not found
        # in previous search, then prevent lighting background by the scheduled lighting function
        if "Waiting" not in self.waiting_text.text or "Connecting" not in self.waiting_text.text:
            self.time_left = 31

            self.back_button.opacity = 1
            self.computer_mode.opacity = 1
            self.bg_image.opacity = 0.8
            self.select_mode_text.opacity = 1

            self.waiting_text.opacity = 0
            self.cancel_search_info.opacity = 0
            self.no_wifi_img.opacity = 0
            self.cancel_button.disabled = True

            self.waiting_text.text = "Connecting to server..."
            self.cancel_search_info.text = "(Touch anywhere to CANCEL)"

            self.online_mode.opacity = 1
            self.online_mode.disabled = False

    def set_waiting_text(self, delta_time=0) -> None:
        self.waiting_text.text = f"Waiting for an opponent... {self.timer()}"
        # OnlineGame object waits for an opponent and if internet connection is lost or something unexpected happen at
        # the server, this object is removed from the screen manager
        if "Online Game" not in screen_manager.screen_names:
            self.wait_for_player_event.cancel()
            self.waiting_text.text = "Connection lost !"
            self.cancel_search_info.text = ""
            Clock.schedule_once(self.lit_the_background, 3)
            self.show_no_wifi()
        elif self.time_left == 0:  # timeout, no player found
            self.waiting_text.text = "No player found !"
            self.cancel_search_info.text = "Ask your friend to join ;-)"
            Clock.schedule_once(self.lit_the_background, 3)
            self.disconnect(False)
        elif screen_manager.current == "Online Game":  # opponent is found, so stop setting waiting text
            self.wait_for_player_event.cancel()
            Clock.schedule_once(self.lit_the_background, 3)

    def connect(self, delta_time=0) -> None:
        global name_of_user
        self.network = Network(name_of_user)
        Clock.schedule_interval(self.check_connection, 0.1)

    def check_connection(self, delta_time=0) -> bool:
        if not self.network.connection_thread.is_alive():
            # Check for connection only if player didn't cancel the search which sets background image opacity to normal
            if self.bg_image.opacity == 0.2:
                # Unsuccessful connection returns None or ""
                if self.network.get_player_no() in [None, ""]:
                    self.waiting_text.text = "Couldn't connect to server !"
                    self.cancel_search_info.text = ""
                    self.show_no_wifi()
                    Clock.schedule_once(self.lit_the_background, 3)
                else:  # successful connection
                    self.wait_for_player_event()
                    game = self.network.send("get")
                    screen_manager.add_widget(OnlineGame(self.network, int(self.network.get_player_no()), game))
            return False  # stop scheduled interval (line 182)

    def disconnect(self, lit=True) -> None:
        self.wait_for_player_event.cancel()
        if lit:
            self.lit_the_background()

        if "Online Game" in screen_manager.screen_names:
            screen_manager.get_screen("Online Game").disconnect()


# This screen appears if the player chooses computer mode on the 'SelectMode' screen
class ComputerGame(Screen):
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

    def __init__(self) -> None:
        super(ComputerGame, self).__init__(name="Computer Game")
        self.app = App.get_running_app()
        self.rock_clicked_sound = SoundLoader.load("Sounds/rock.ogg")
        self.paper_clicked_sound = SoundLoader.load("Sounds/paper.ogg")
        self.scissor_clicked_sound = SoundLoader.load("Sounds/scissor.ogg")
        self.you_win_sound = SoundLoader.load("Sounds/you_win.ogg")
        self.you_lose_sound = SoundLoader.load("Sounds/you_lose.ogg")
        self.winner_sound = SoundLoader.load("Sounds/winner.ogg")
        self.loser_sound = SoundLoader.load("Sounds/loser.ogg")
        self.tie_sound = SoundLoader.load("Sounds/tie.ogg")
        self.tie_breaker_sound = SoundLoader.load("Sounds/tie_breaker.ogg")
        self.round_one_sound = SoundLoader.load("Sounds/round_1.ogg")
        self.round_two_sound = SoundLoader.load("Sounds/round_2.ogg")
        self.round_three_sound = SoundLoader.load("Sounds/round_3.ogg")
        self.round_four_sound = SoundLoader.load("Sounds/round_4.ogg")
        self.round_five_sound = SoundLoader.load("Sounds/round_5.ogg")
        self.final_round_sound = SoundLoader.load("Sounds/final_round.ogg")

        self.round_sounds = {1: self.round_one_sound, 2: self.round_two_sound, 3: self.round_three_sound,
                             4: self.round_four_sound, 5: self.round_five_sound, 6: self.final_round_sound, 7:
                                 self.tie_breaker_sound}
        self.sounds_for_mute_unmute_stop = [self.app.click_sound, self.rock_clicked_sound, self.paper_clicked_sound,
                                            self.scissor_clicked_sound, self.you_win_sound, self.you_lose_sound,
                                            self.winner_sound, self.loser_sound, self.tie_sound, self.tie_breaker_sound]

        self.points = {"user": 0, "computer": 0}
        self.current_round = 1
        self.winner = ""
        self.schedule_timings = {"rst": 2.0, "rsp": 1.7}  # rst: round_start_time, rsp: round_sound_play
        self.game_playable = True

        # Cheats related variables
        self.always_win = False
        self.always_lose = False
        self.clicks = 0

    def show_exit_prompt(self) -> None:
        if self.game_playable:
            # Lower the opacity of all the widgets
            self.ids.background_image.opacity = 0.4
            self.ids.switch_to_home.opacity = 0.4
            self.ids.game_actions.opacity = 0.4
            self.ids.pause_game.opacity = 0.4

            self.play_again_button.disabled = True
            self.game_playable = False
            self.add_widget(ExitPrompt())

    def set_message(self, text: str, set_computer_choice=False, choice="", delta_time=0) -> None:
        self.message.text = text
        if text == "It's your turn !!":
            self.user_choice_text.text = ""
            self.computer_choice_text.text = ""
        if set_computer_choice:
            self.computer_choice_text.text = choice

    def enable_buttons(self, delta_time=0) -> None:
        self.select_rock.disabled = False
        self.select_rock.opacity = 1
        self.select_paper.disabled = False
        self.select_paper.opacity = 1
        self.select_scissor.disabled = False
        self.select_scissor.opacity = 1

    def disable_buttons(self, delta_time=0) -> None:
        self.select_rock.disabled = True
        self.select_rock.opacity = 0.7
        self.select_paper.disabled = True
        self.select_paper.opacity = 0.7
        self.select_scissor.disabled = True
        self.select_scissor.opacity = 0.7

    # This method will get the choice of computer. If any cheat is activated, choice will be based on that cheat,
    # otherwise choice will be random.
    def get_computer_choice(self, user_choice: str) -> str:
        choices = ["Rock", "Paper", "Scissor"]
        choices_for_win = {"Rock": "Scissor", "Paper": "Rock", "Scissor": "Paper"}
        choices_for_lose = {"Rock": "Paper", "Paper": "Scissor", "Scissor": "Rock"}

        if self.always_win:
            return choices_for_win[user_choice]
        elif self.always_lose:
            return choices_for_lose[user_choice]
        else:
            return choose_randomly(choices)

    def set_computer_choice(self, choice: str) -> None:
        self.computer_choice_text.text = choice

    # This method will compare the choices of player and computer and then return the winner
    def get_winner(self, choices: dict, delta_time=0) -> str:
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

    def set_round_text(self, delta_time=0) -> None:
        self.user_choice_text.color = 203/255, 158/255, 249/255
        self.computer_choice_text.color = 203/255, 158/255, 249/255
        self.round_on_screen.opacity = 1  # change the opacity of round number to 1 which is 0 when the game starts
        if self.current_round < 6:
            self.round_on_screen.text = f"ROUND {self.current_round}"
        elif self.current_round == 6:
            self.round_on_screen.text = "FINAL ROUND"
        else:
            self.round_on_screen.text = "TIEBREAKER"

    def start_round(self, delta_time=0) -> None:
        # Round will be played if the current_round is less than or equal to 6. And If the points of the user and the
        # computer are equal, tiebreaker round will be played
        if self.current_round <= 6 or self.points["user"] == self.points["computer"]:
            # Play sound effect of current round and set the text of round in game
            Clock.schedule_once(lambda dt: self.round_sounds[self.current_round].play(), self.schedule_timings["rsp"])
            Clock.schedule_once(self.set_round_text, self.schedule_timings["rst"])
            # Enable the buttons and tell the user that it's his turn
            Clock.schedule_once(self.enable_buttons, self.schedule_timings["rst"])
            Clock.schedule_once(partial(self.set_message, "It's your turn !!"), self.schedule_timings["rst"])
            # Scheduled timings will be changed after first round
            self.schedule_timings["rst"] = 0.3
            self.schedule_timings["rsp"] = 0
        else:  # After the sixth round or tiebreaker round, tell the user who is the winner
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
    def compare_choices(self, selection: int) -> None:
        options = {1: "Rock", 2: "Paper", 3: "Scissor"}
        user_choice = options[selection]
        self.user_choice_text.text = user_choice
        Clock.schedule_once(partial(self.set_message, "Computer's turn..."), 0.5)
        computer_choice = self.get_computer_choice(user_choice)
        Clock.schedule_once(partial(self.set_message, "", True, computer_choice), 1.5)
        Clock.schedule_once(partial(self.get_winner, {user_choice: "player", computer_choice: "computer"}), 2)

    def play_again(self) -> None:  # method for 'Play again' button
        # reset the game and restart from round 1
        self.reset_game()
        self.start_round()

    # Below two methods will set mute/unmute the music by changing their volume
    def mute_music(self) -> None:
        for sound in self.sounds_for_mute_unmute_stop:
            sound.volume = 0
        for sound in self.round_sounds.values():
            sound.volume = 0

    def unmute_music(self) -> None:
        if self.app.music_allowed:
            Sound.volume = 1
            for sound in self.sounds_for_mute_unmute_stop:
                sound.volume = 1
            for sound in self.round_sounds.values():
                sound.volume = 1

    # This method will stop the music by changing their play state
    def stop_music(self) -> None:
        if self.app.music_allowed:
            self.app.main_game_music.stop()
            Sound.volume = 0
            for sound in self.sounds_for_mute_unmute_stop:
                if sound.state == "play":
                    sound.stop()
            for sound in self.round_sounds.values():
                if sound.state == "play":
                    sound.stop()

    def pause_game(self) -> None:  # method for pausing the game
        if self.game_playable:
            self.stop_music()
            self.mute_music()
            screen_manager.transition = NoTransition()
            screen_manager.current = "Pause Screen"

    # This method will be used by reset_cheats() method to set the clicks variable to 0
    def reset_clicks(self, delta_time=0) -> None:
        self.clicks = 0

    # This method will calculate the clicks of the user on the 'ComputerGame' screen. If the user clicks three times
    # within 0.5 seconds, all the cheats will be deactivated. Otherwise, it will reset the 'clicks' variable by using
    # the above method
    def reset_cheats(self) -> None:
        cheats_screen = screen_manager.get_screen("Cheats Screen")
        if self.clicks == 0:
            Clock.schedule_once(self.reset_clicks, 0.5)  # reset the clicks after 0.5 seconds
        self.clicks += 1
        if self.clicks == 3 and self.message.text == "It's your turn !!":
            self.always_win = False
            self.always_lose = False
            cheats_screen.always_win_button.state = "normal"
            cheats_screen.always_lose_button.state = "normal"

    def reset_game(self) -> None:  # reset game is used when player chooses to play again
        self.points["user"] = self.points["computer"] = 0
        self.user_points.text = self.computer_points.text = "0"

        self.user_choice_text.text = ""
        self.computer_choice_text.text = ""

        self.play_again_button.opacity = 0
        self.play_again_button.disabled = True

        self.current_round = 1
        self.message.text = "Game starting..."
        self.round_on_screen.opacity = 0
        self.round_on_screen.text = f"ROUND {self.current_round}"


# This screen will be shown when user clicks on 'exit.png' image of 'ComputerGame' screen
# It will show a prompt asking user if he/she is sure of getting back to 'MainMenu' screen
class ExitPrompt(Screen):
    def __init__(self) -> None:
        super(ExitPrompt, self).__init__(name="Exit Prompt")
        self.app = App.get_running_app()
        self.computer_game = screen_manager.get_screen("Computer Game")

    def go_to_main_menu(self) -> None:
        # cancel scheduled tasks of the previous game
        for event in Clock.get_events():
            if "Computer Game" in str(event):
                event.cancel()

        # stop the music and change the screen to 'Main Menu'
        self.computer_game.stop_music()
        screen_manager.current = "Main Menu"

        # Remove exit prompt from the computer game screen, disable the buttons and reset everything
        self.remove_prompt(True)
        self.computer_game.disable_buttons()
        self.computer_game.schedule_timings = {"rst": 2.0, "rsp": 1.7}
        self.computer_game.reset_game()

        if self.app.music_allowed:  # play background music if sound is not muted
            Sound.volume = 1
            self.app.bg_music.play()

    def remove_prompt(self, remove_online_game=False) -> None:
        # Reset the opacity of widgets to make them visible
        self.computer_game.ids.pause_game.opacity = 1
        self.computer_game.play_again_button.disabled = False

        for game_name in ["Computer Game", "Online Game"]:
            if game_name in screen_manager.screen_names:
                game = screen_manager.get_screen(game_name)
                game.ids.background_image.opacity = 0.8
                game.ids.switch_to_home.opacity = 1
                game.ids.game_actions.opacity = 1
                game.remove_widget(self)  # remove exit prompt from the screen
                game.game_playable = True
                # remove online game only when player clicks on "Yes"
                if game_name == "Online Game" and remove_online_game:
                    game.check_winner_event.cancel()
                    game.exit_event.cancel()
                    game.disconnect("Main Menu")


# This screen will be shown when user pauses the game
class PauseScreen(Screen):
    # Following code is related to cheats
    top_button = ObjectProperty(None)  # hidden and disabled button
    bottom_button = ObjectProperty(None)  # hidden button

    def __init__(self) -> None:
        super(PauseScreen, self).__init__(name="Pause Screen")
        self.app = App.get_running_app()
        self.computer_game = screen_manager.get_screen("Computer Game")
        self.clicks = 0

    def resume_game(self) -> None:
        screen_manager.current = "Computer Game"
        if self.app.music_allowed:
            self.computer_game.unmute_music()
            self.app.main_game_music.play()
        screen_manager.transition = WipeTransition()

    # This method will be used by enable_top_button() and show_cheats() methods to set the clicks variable to 0
    def reset_clicks(self, delta_time=0) -> None:
        self.clicks = 0

    # If user clicks on the hidden bottom_button three times within 0.5 seconds, this method will enable the top_button
    def enable_top_button(self) -> None:
        if self.clicks == 0:
            Clock.schedule_once(self.reset_clicks, 0.5)
        self.clicks += 1
        if self.clicks == 3:
            self.top_button.disabled = False
            self.bottom_button.disabled = True

    # After the top_button is enabled by above method, clicking it three times within 0.5 seconds will reveal the cheats
    def show_cheats(self) -> None:
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

    def __init__(self) -> None:
        super(CheatsScreen, self).__init__(name="Cheats Screen")
        self.computer_game = screen_manager.get_screen("Computer Game")

    def toggle_cheats(self) -> None:
        if self.always_win_button.state == "normal":
            self.computer_game.always_win = False
        elif self.always_win_button.state == "down":
            self.computer_game.always_win = True

        if self.always_lose_button.state == "normal":
            self.computer_game.always_lose = False
        elif self.always_lose_button.state == "down":
            self.computer_game.always_lose = True


# This screen appears if the player chooses computer mode on the 'SelectMode' screen
class OnlineGame(Screen):
    user_name = ObjectProperty(None)
    opponent_name = ObjectProperty(None)
    round_on_screen = ObjectProperty(None)
    select_rock = ObjectProperty(None)
    select_paper = ObjectProperty(None)
    select_scissor = ObjectProperty(None)
    user_points = ObjectProperty(None)
    user_choice_text = ObjectProperty(None)
    opponent_points = ObjectProperty(None)
    opponent_choice_text = ObjectProperty(None)
    message = ObjectProperty(None)
    play_again_button = ObjectProperty(None)

    def __init__(self, network, player_no, game) -> None:
        super(OnlineGame, self).__init__(name="Online Game")
        self.app = App.get_running_app()
        self.select_mode = screen_manager.get_screen("Select Mode")
        self.computer_game = screen_manager.get_screen("Computer Game")

        # use computer game sounds to prevent loading them again
        self.rock_clicked_sound = self.computer_game.rock_clicked_sound
        self.paper_clicked_sound = self.computer_game.paper_clicked_sound
        self.scissor_clicked_sound = self.computer_game.scissor_clicked_sound
        self.round_sounds = self.computer_game.round_sounds
        self.winner_sound = self.computer_game.winner_sound
        self.loser_sound = self.computer_game.loser_sound
        self.you_win_sound = self.computer_game.you_win_sound
        self.you_lose_sound = self.computer_game.you_lose_sound
        self.tie_sound = self.computer_game.tie_sound

        self.network = network
        self.player_no = player_no
        self.game = game

        self.game_playable = True
        self.user_name.text = name_of_user
        self.play_again_prompt = None

        self.move_to_game_event = Clock.schedule_interval(self.move_to_game, 0.1)  # triggered while waiting for
        # opponent
        self.check_winner_event = Clock.create_trigger(self.check_for_winner, 0.1, True)  # triggered after every round
        self.exit_event = Clock.create_trigger(self.exit_game, 0.1, True)  # triggered after game completion
        self.keep_getting_game = Clock.create_trigger(self.get_game, 0.1, True)  # triggered between rounds

    # This method will keep updating self.game when there is a break of 2 seconds before starting next round
    def get_game(self, delta_time=0) -> None:
        self.game = self.network.send("get")

    def play_round_sound(self, delta_time=0) -> None:
        try:
            if self.game.connected():
                self.round_sounds[self.game.current_round].play()
        except AttributeError:
            pass

    def reset_message_and_points(self, delta_time=0) -> None:
        self.message.text = ""
        self.user_points.text = self.opponent_points.text = "0"

    def exit_game(self, delta_time=0) -> None:
        self.game = self.network.send("get")

        try:
            exit_time_left = int(self.game.exit_time)
            if exit_time_left <= 5:  # disable play again button when only 5 seconds are left
                self.disable_play_again_button()

            if exit_time_left > 1:
                self.message.text = f"Exiting in {self.game.exit_time} seconds..."
            elif exit_time_left == 1:
                self.message.text = f"Exiting in {self.game.exit_time} second..."
            else:  # exit the game
                self.exit_event.cancel()
                self.disconnect()

            # If opponent requests to play again, show the play again prompt
            if self.game.play_again[1 - self.player_no]:
                self.show_prompt("again")

            # If play again request is accepted, restart the game
            if self.game.completed is False and self.game.connected():
                self.exit_event.cancel()
                self.disable_play_again_button()
                self.message.text = "Restarting game..."
                Clock.schedule_once(self.reset_message_and_points, 2)
                self.start_round()
            # If play again request is declined, show it to the player
            elif self.play_again_button.opacity == 1 and self.play_again_button.disabled and \
                    not self.game.play_again[self.player_no] and self.game.connected():
                self.play_again_button.font_size = dp(25)
                self.play_again_button.text = "Request declined !"
                # Button still won't work until its text is not set to "Play again" (line 682)
                self.play_again_button.disabled = False
                self.play_again_button.background_down = ""
                if exit_time_left > 10:
                    Clock.schedule_once(self.enable_play_again_button, 5)  # enable play again button after 5 seconds

            # If the opponent disconnects, remove play again button and play again prompt if available
            if not self.game.connected():
                self.disable_play_again_button()
                if self.play_again_prompt is not None:
                    self.play_again_prompt.decline_request()  # declining the request removes the play again prompt

        except AttributeError:  # connection error
            self.exit_event.cancel()
            self.disconnection_aftermath()

    # This method is used to show exit prompt and play again prompt
    def show_prompt(self, prompt: str) -> None:
        if self.game_playable:
            # Lower the opacity of all the widgets
            self.ids.background_image.opacity = 0.4
            self.ids.switch_to_home.opacity = 0.4
            self.ids.game_actions.opacity = 0.4

            self.game_playable = False
            if prompt == "exit":
                self.add_widget(ExitPrompt())
            elif prompt == "again":
                self.play_again_prompt = PlayAgainPrompt(self.opponent_name.text)
                self.add_widget(self.play_again_prompt)

    def enable_buttons(self, delta_time=0) -> None:
        self.keep_getting_game.cancel()
        try:
            if self.game.connected():
                self.select_rock.disabled = False
                self.select_rock.opacity = 1
                self.select_paper.disabled = False
                self.select_paper.opacity = 1
                self.select_scissor.disabled = False
                self.select_scissor.opacity = 1
        except AttributeError:
            pass

    def disable_buttons(self, delta_time=0) -> None:
        self.select_rock.disabled = True
        self.select_rock.opacity = 0.7
        self.select_paper.disabled = True
        self.select_paper.opacity = 0.7
        self.select_scissor.disabled = True
        self.select_scissor.opacity = 0.7

    def enable_play_again_button(self, delta_time=0) -> None:
        if self.game.completed:
            self.play_again_button.font_size = dp(30)
            self.play_again_button.disabled = False
            self.play_again_button.text = "Play again"
            self.play_again_button.opacity = 1
            self.play_again_button.background_down = "atlas://data/images/defaulttheme/button_pressed"

    def disable_play_again_button(self) -> None:
        self.play_again_button.disabled = True
        self.play_again_button.opacity = 0
        self.play_again_button.text = "Play again"

    def set_round_text(self, delta_time=0) -> None:
        try:
            if self.game.connected():
                self.user_choice_text.color = 203/255, 158/255, 249/255
                self.opponent_choice_text.color = 203/255, 158/255, 249/255
                # change the opacity of round number to 1 which is 0 when the game starts
                self.round_on_screen.opacity = 1
                if self.game.current_round < 6:
                    self.round_on_screen.text = f"ROUND {self.game.current_round}"
                elif self.game.current_round == 6:
                    self.round_on_screen.text = "FINAL ROUND"
                else:
                    self.round_on_screen.text = "TIEBREAKER"
        except AttributeError:
            pass

    @staticmethod
    def show_result(winner: ObjectProperty, loser: ObjectProperty, sound: Sound, final_result: bool,
                    delta_time=0) -> None:
        winner.color = 0, 1, 0
        loser.color = 1, 0, 0
        sound.play()
        if final_result:
            winner.text = "WINNER"
            loser.text = "LOSER"

    def move_to_game(self, delta_time=0) -> None:  # wait for an opponent and move to game when found
        self.game = self.network.send("get")
        try:
            if self.game.connected() and self.game.names[1 - self.player_no] != "":
                self.move_to_game_event.cancel()
                self.app.begin_sound.play()
                opponent_name = self.game.names[1 - self.player_no]
                self.opponent_name.text = opponent_name if opponent_name != "You" else "Opponent"
                self.select_mode.begin_game("Online Game")
                self.start_round()
        except AttributeError:  # connection error
            self.move_to_game_event.cancel()
            self.disconnect()

    def start_round(self, delta_time=0) -> None:
        # Round will be played if the current_round is less than or equal to 6. And If the points of the both the
        # players are equal, tiebreaker round will be played
        if self.game.current_round <= 6 or self.game.points[self.player_no] == self.game.points[1 - self.player_no]:
            # Play sound effect of current round and set the text of round in game
            Clock.schedule_once(self.play_round_sound, 2)
            Clock.schedule_once(self.set_round_text, 2)

            Clock.schedule_once(partial(self.network.send, "reset"), 2)  # send reset request to the server
            Clock.schedule_once(self.check_winner_event, 2)  # start checking for winner
        else:  # After the sixth round or tiebreaker round, tell the user who is the winner
            if self.game.points[self.player_no] > self.game.points[1 - self.player_no]:
                Clock.schedule_once(partial(self.show_result, self.user_choice_text, self.opponent_choice_text,
                                            self.winner_sound, True), 1.5)
            elif self.game.points[1 - self.player_no] > self.game.points[self.player_no]:
                Clock.schedule_once(partial(self.show_result, self.opponent_choice_text, self.user_choice_text,
                                            self.loser_sound, True), 1.5)

            self.enable_play_again_button()
            self.check_winner_event.cancel()
            self.exit_event()

    def check_for_winner(self, delta_time=0) -> None:
        self.game = self.network.send("get")

        try:
            my_move = self.game.get_player_move(self.player_no)
            opponent_move = self.game.get_player_move(1 - self.player_no)

            # If both players have selected their move, determine the winner
            if self.game.both_went() and self.game.connected():
                self.disable_buttons()

                self.user_choice_text.text = my_move
                self.opponent_choice_text.text = opponent_move

                winner = self.game.get_winner()
                if winner is None:
                    self.user_choice_text.color = self.opponent_choice_text.color = 1, 0, 0
                    self.user_choice_text.text = self.opponent_choice_text.text = "Timeout"
                    self.check_winner_event.cancel()
                    Clock.schedule_once(partial(self.disconnect, "Select Mode"), 3)
                    return
                elif winner == 0:
                    if self.player_no == 0:
                        self.show_result(self.user_choice_text, self.opponent_choice_text, self.you_win_sound, False)
                        self.user_points.text = str(self.game.points[self.player_no])
                    else:
                        self.show_result(self.opponent_choice_text, self.user_choice_text, self.you_lose_sound, False)
                        self.opponent_points.text = str(self.game.points[1 - self.player_no])
                elif winner == 1:
                    if self.player_no == 1:
                        self.show_result(self.user_choice_text, self.opponent_choice_text, self.you_win_sound, False)
                        self.user_points.text = str(self.game.points[self.player_no])
                    else:
                        self.show_result(self.opponent_choice_text, self.user_choice_text, self.you_lose_sound, False)
                        self.opponent_points.text = str(self.game.points[1 - self.player_no])
                else:
                    self.tie_sound.play()

                self.check_winner_event.cancel()
                self.keep_getting_game()
                self.start_round()

            # If both players have not selected their move, show text based on some conditions
            elif self.game.connected():
                if self.game.players_went[self.player_no]:
                    self.user_choice_text.text = my_move
                else:
                    self.user_choice_text.text = f"Waiting... {self.game.time_left[self.player_no]}"
                    if "down" not in [self.select_rock.state, self.select_paper.state, self.select_scissor.state]:
                        self.enable_buttons()

                if self.game.players_went[1 - self.player_no]:
                    self.opponent_choice_text.text = "Locked in"
                else:
                    self.opponent_choice_text.text = f"Waiting... {self.game.time_left[1 - self.player_no]}"

            # If one of the players has disconnected, make the connected player winner
            else:
                self.disable_buttons()
                self.user_choice_text.color = 0, 1, 0
                self.user_choice_text.text = "WINNER"
                self.winner_sound.play()
                self.opponent_choice_text.color = 1, 0, 0
                self.opponent_choice_text.text = "Left"

                self.check_winner_event.cancel()
                self.exit_event()
        except AttributeError:  # connection error
            self.check_winner_event.cancel()
            self.disconnection_aftermath()

    def disconnect(self, screen="Select Mode", delta_time=0) -> None:
        if screen_manager.current == "Online Game":
            screen_manager.current = screen
        self.network.send("disconnect")
        if "Online Game" in screen_manager.screen_names:
            screen_manager.remove_widget(screen_manager.get_screen("Online Game"))

    def disconnection_aftermath(self):  # when the opponent disconnects
        self.disable_buttons()
        self.disable_play_again_button()
        self.user_choice_text.text = self.opponent_choice_text.text = ""
        self.message.text = "Connection lost !"


# This screen will be shown when the opponent requests to play again
# It will show a prompt asking user if he/she accepts or decline the opponent's request
class PlayAgainPrompt(Screen):
    request_msg = ObjectProperty(None)

    def __init__(self, opponent_name) -> None:
        super(PlayAgainPrompt, self).__init__()
        self.request_msg.text = f"{opponent_name} wants to play again"
        self.online_game = screen_manager.get_screen("Online Game")

    def remove_prompt(self) -> None:
        self.online_game.ids.background_image.opacity = 0.8
        self.online_game.ids.switch_to_home.opacity = 1
        self.online_game.ids.game_actions.opacity = 1

        self.online_game.game_playable = True
        self.online_game.play_again_prompt = None
        self.online_game.remove_widget(self)

    def decline_request(self) -> None:
        self.remove_prompt()
        self.online_game.network.send("decline")

    def accept_request(self) -> None:
        self.remove_prompt()
        self.online_game.network.send("accept")


# This screen includes all the rules of the game. This screen also provides the user a hint for accessing the cheats.
class RulesScreen(Screen):
    def __init__(self) -> None:
        super(RulesScreen, self).__init__(name="Rules Screen")


# This screen includes the all the credits of the screen - The developer and all the websites which have provided the
# assets required for the game
class CreditsScreen(Screen):
    def __init__(self) -> None:
        super(CreditsScreen, self).__init__(name="Credits Screen")


# This is the root widget of all the screens and widgets of the game
class RockPaperScissorApp(App):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        Window.bind(on_keyboard=self.back_button)

        Sound.volume = 1
        self.music_allowed = True
        self.bg_music = None
        self.main_game_music = None

        self.begin_sound = SoundLoader.load("Sounds/begin.ogg")
        self.click_sound = SoundLoader.load("Sounds/click.ogg")
        self.loading_thread = Thread(target=self.load)

    @staticmethod
    def back_button(window, key, *args) -> bool:  # handle back button click on android smartphone
        if key == 27:
            if screen_manager.current in ["Enter Name", "Rules Screen", "Credits Screen"]:
                screen_manager.current = "Main Menu"
            elif screen_manager.current == "Select Mode":
                screen_manager.current = "Enter Name"
            elif screen_manager.current == "Cheats Screen":
                screen_manager.current = "Pause Screen"
            elif screen_manager.current == "Computer Game":
                screen_manager.get_screen("Computer Game").show_exit_prompt()
            elif screen_manager.current == "Main Menu":
                stopTouchApp()

            return True

    def on_start(self) -> None:  # start loading thread
        self.loading_thread.start()
        screen_manager.get_screen("Loading Screen").wait_for_loading_completion()

    def on_pause(self) -> bool:
        if screen_manager.current in ["Computer Game", "Cheats Screen"]:
            screen_manager.get_screen("Computer Game").pause_game()
        return True

    def load(self) -> None:  # this method will be executed in another thread while loading screen is shown
        self.bg_music = SoundLoader.load("Sounds/bg.ogg")
        self.bg_music.loop = True
        self.main_game_music = SoundLoader.load("Sounds/main_game.ogg")
        self.main_game_music.loop = True

        screen_manager.add_widget(MainMenu())
        screen_manager.add_widget(RulesScreen())
        screen_manager.add_widget(CreditsScreen())
        screen_manager.add_widget(ComputerGame())
        screen_manager.add_widget(EnterName())
        screen_manager.add_widget(SelectMode())
        screen_manager.add_widget(PauseScreen())
        screen_manager.add_widget(CheatsScreen())

    def build(self) -> ScreenManager:
        screen_manager.add_widget(LoadingScreen())
        return screen_manager


# Starting the game
if __name__ == "__main__":
    RockPaperScissorApp().run()
