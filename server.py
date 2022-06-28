from time import time
from pickle import dumps
from online_game import MainGame
from _thread import start_new_thread
from socket import socket, AF_INET, SOCK_STREAM, error as socket_error

server = ""  # IP address
port = 0  # ufw allow <port>

s = socket(AF_INET, SOCK_STREAM)

try:
    s.bind((server, port))
except socket_error as e:
    print(e)

s.listen()
print("Server started !")

games = {}  # game_id: MainGame object
game_id = 1
match_made = [False, False]  # index is the player number, True when player is connected


# Started by start_new_thread function when a client/player connects to server
def threaded_client(conn: socket, player_no: int, key: int) -> None:
    global match_made

    conn.send(str.encode(str(player_no)))  # send player number to the connected player
    games[key].names[player_no] = conn.recv(2048).decode()  # receive and set name of the player

    while True:
        game = games[key]
        try:
            data = conn.recv(4096).decode()  # continuously receive data from the client

            if not data or data == "disconnect":  # when the client disconnects or wants to disconnect
                disconnection_aftermath(game, key, player_no, conn)
                break
            else:
                if data.lower() == "reset" and game.connected():  # when next round is about to be started
                    game.reset()
                elif data.lower() == "again":  # when the player wants to play again
                    game.play_again[player_no] = True
                elif data.lower() == "decline":  # when the player declines to play again
                    game.play_again[1 - player_no] = False
                elif data.lower() == "accept":  # when the player accepts to play again
                    game.current_round = 1
                    game.points = [0, 0]
                    game.started = False
                    game.reset()
                #  When the player selects his/her move           or no move is selected within 15 seconds
                elif data.lower() in ["rock", "paper", "scissor"] or game.time_left[player_no] <= 0:
                    if data.lower() in ["rock", "paper", "scissor"]:
                        game.play(player_no, data)
                    else:
                        game.play(player_no, "timeout")

                    winner = game.get_winner()
                    # If there's no tie or timeout from both players and points are not already given
                    if winner != -1 and winner is not None and game.give_points:
                        game.current_round += 1
                        game.points[winner] += 1
                        game.give_points = False

                # 15 seconds timer for the players to select their move
                if game.start_time is not None and game.completed is False:
                    if game.moves[0] == "":  # stop the timer when the player selects his/her move
                        game.time_left[0] = 15 - int(time() - game.start_time)
                    if game.moves[1] == "":
                        game.time_left[1] = 15 - int(time() - game.start_time)

                # Set start_time after completion of all the rounds for the exit timer
                # CONDITIONS:
                # 1. game is not completed
                # and
                # 2. one of the players have won the sixth round (moves are not reset after sixth round)
                # or
                # 2. there was a tie and the seventh round is completed (points are not equal after tiebreaker round)
                # NOTE: game.current_round is incremented by one after getting the winner of previous round, that's why
                # it will be compared with its incremented value
                if not game.completed and \
                        ((game.current_round == 7 and game.moves[0] != "" and game.moves[1] != "") or
                         (game.current_round == 8 and game.points[0] != game.points[1])):
                    game.completed = True
                    game.set_start_time()
                if game.completed:  # start exit timer when the game completes
                    game.exit_time = 30 - int(time() - game.start_time)

                conn.sendall(dumps(game))

                # Game will start when both players connect hence the value of the 'started' property
                # It will be used to decrement the value of game_id if the second player of a game disconnects
                # immediately after connecting and the game didn't start (line 138)
                if game.started is False and game.connected():
                    game.started = True
        except ConnectionResetError:  # when the game is closed forcefully
            disconnection_aftermath(game, key, player_no, conn)
            break


# This function will be executed when a client/player disconnects
def disconnection_aftermath(game: MainGame, key: int, player_no: int, conn: socket) -> None:
    game.ready[player_no] = False  # the player is not ready for the game if he/she disconnects, obviously
    conn.close()
    print(f"Player {player_no + 1} of game {key} has disconnected !")

    # Set start_time for the exit timer for the other player who was playing with the disconnected player
    # Game is completed instantly if one of the players of the game disconnects
    if game.ready[1 - player_no] and not game.completed:
        game.set_start_time()
        game.completed = True

    global match_made
    # If both players have disconnected, delete the game (MainGame object)
    if game.ready == [False, False]:
        print("Closing game", key)
        del games[key]

        # If there was only one player connected [True, False] who was waiting for an opponent [True, True] and has now
        # disconnected, then reset match_made to [False, False]
        if match_made == [True, False] and game.reset_matches:
            match_made = [False, False]

    # If player(s) of any game disconnect(s) and a new player is not waiting for his/her opponent [True, False], then
    # reset match_made to [False, False]
    # game.reset_matches is set to False for preventing its reset again after the disconnection of second player of the
    # same game
    if match_made != [True, False]:
        if game.reset_matches or game.ready == [False, False]:
            match_made = [False, False]
            game.reset_matches = False

    # If player 1 is connected to a game waiting for his/her opponent, and player 2 connects and disconnects
    # immediately before the game is started, decrement game_id and set match_made to [True, False] which got reset to
    # [False, False] when the opponent player connected (line 166)
    # This helps player 1 to find his/her opponent for his/her game_id without searching for player again
    if game.ready == [True, False] and game.started is False:
        global game_id
        game_id -= 1
        match_made = [True, False]


while True:
    new_conn, addr = s.accept()
    print("Connected to:", addr)

    new_player_no = 0
    if match_made[0] is False:  # no first player is connected so create a new game
        print("Creating a new game...")
        games[game_id] = MainGame(game_id)
        games[game_id].ready[new_player_no] = True
        match_made[0] = True
        print(f"Player {new_player_no + 1} of game {game_id} is ready !")
    else:  # first player is connected so add the second player to the game
        new_player_no = 1
        games[game_id].ready[new_player_no] = True
        print(f"Player {new_player_no + 1} of game {game_id} is ready !")
        print(f"Starting game {game_id}...")

    start_new_thread(threaded_client, (new_conn, new_player_no, game_id))

    # If second player is added to a game, increment game_id for the next player and reset match_made
    if new_player_no == 1:
        game_id += 1
        match_made = [False, False]
