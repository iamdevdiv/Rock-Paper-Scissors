from time import time


# This class will be used by the server to create game, manipulate it based on the requests of the clients and send it
# to the players
class MainGame:
    def __init__(self, game_id) -> None:
        # These attributes will never be changed
        self.game_id = game_id
        self.names = ["", ""]

        # These attributes are based on the actions of the player
        self.ready = [False, False]  # index is the player number, True when player is connected
        self.players_went = [False, False]  # True when players have selected their move (line 47)
        self.play_again = [False, False]  # True based on which player wants to play again

        # These attributes are gameplay related
        self.current_round = 1  # incremented when a player wins a round
        self.points = [0, 0]   # same as above
        self.moves = ["", ""]  # the server uses play() method to set these moves which are selected by the player

        # These attributes are timer related
        self.start_time = None  # used by server to show timers to the players
        # Index is the player number. Players have to select their moves within this time. Stopped when a player selects
        # his/her move
        self.time_left = [15, 15]
        # Same exit timer will be showed to both players, started when game is completed or a player disconnects
        self.exit_time = 0

        # These attributes are used in conditions by the server
        self.started = False  # True when game is started
        self.completed = False  # True when game is completed or one of the players has disconnected
        # used to prevent giving points twice to the winner because requests are made by both clients/players
        self.give_points = False
        self.reset_matches = True  # used to reset match_made variable of the server

    def set_start_time(self) -> None:  # set start time which is used for the timers
        self.start_time = time()

    # Used by the clients/players to get their moves
    def get_player_move(self, player_no: int) -> str:
        return self.moves[player_no]

    # Used by the server to set moves on being selected by the players
    def play(self, player: int, move: str) -> int:
        self.moves[player] = move.title()
        self.players_went[player] = True
        if self.both_went():
            return self.get_winner()
        return -1  # when both players have not selected their move yet

    # Following two methods are used by both the clients and server in conditions
    def connected(self) -> bool:
        return self.ready[0] and self.ready[1]

    def both_went(self) -> bool:
        return self.players_went[0] and self.players_went[1]

    # Used by server to determine the winner
    def get_winner(self) -> int:
        p1 = self.moves[0].title()
        p2 = self.moves[1].title()

        winner = -1
        if p1 == p2 == "Timeout":  # winner is None when both players timeout
            winner = None
        elif p1 == "Timeout":
            winner = 1
        elif p2 == "Timeout":
            winner = 0
        elif p1 == "Rock" and p2 == "Scissor":
            winner = 0
        elif p1 == "Scissor" and p2 == "Rock":
            winner = 1
        elif p1 == "Paper" and p2 == "Rock":
            winner = 0
        elif p1 == "Rock" and p2 == "Paper":
            winner = 1
        elif p1 == "Scissor" and p2 == "Paper":
            winner = 0
        elif p1 == "Paper" and p2 == "Scissor":
            winner = 1

        return winner

    def reset(self) -> None:  # reset attributes after every round
        self.play_again = [False, False]
        self.completed = False
        self.give_points = True
        self.moves = ["", ""]
        self.players_went = [False, False]
        self.start_time = time()
        self.time_left = [15, 15]
