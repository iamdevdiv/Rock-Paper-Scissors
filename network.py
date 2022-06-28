from pickle import loads
from threading import Thread
from socket import socket, AF_INET, SOCK_STREAM, error as socket_error


# This class will be used by the client to communicate with the server
class Network:
    def __init__(self, player_name: str):
        self.client = socket(AF_INET, SOCK_STREAM)
        self.server = ""
        self.port = 0
        self.addr = (self.server, self.port)

        self.player_no = None
        self.player_name = player_name

        self.connection_thread = Thread(target=self.connect)
        self.connection_thread.start()  # start to connect with the server on initialization

    def get_player_no(self) -> int:
        return self.player_no

    def connect(self) -> None:
        try:
            self.client.connect(self.addr)
            # player_no is received from the server after the connection is successful
            self.player_no = self.client.recv(2048).decode()
            self.client.send(str.encode(self.player_name))  # send player name to the server
        except (ConnectionRefusedError, ConnectionResetError, OSError, socket_error):
            return None

    # Send a request to the server and receive response in the form of game object
    def send(self, data: str, delta_time=0) -> object:
        try:
            self.client.send(str.encode(data))
            return loads(self.client.recv(4096))
        except (socket_error, EOFError) as e:  # EOFError when data is still being received after disconnection
            print(e)
