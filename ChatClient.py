# ChatClient.py
import socket
import threading
import os


class ChatClient:
    def __init__(self, host="127.0.0.1", port=2025):
        self.host = host
        self.port = port
        self.sock = None
        self.running = False
        self.on_message = None  # callback khi nhận tin nhắn

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.running = True
        thread = threading.Thread(target=self.receive_loop, daemon=True)
        thread.start()

    def register(self, username, password, avatar):
        self.send(f"REGISTER|{username}|{password}|{avatar}")

    def login(self, username, password):
        self.send(f"LOGIN|{username}|{password}")


    def send_message(self, username, text):
        self.send(f"MSG|{username}|{text}")

    def send_image(self, username, filepath):
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            data = f.read()
        header = f"IMAGE|{username}|{filename}|{len(data)}"
        self.send(header)
        self.sock.sendall(data)

    def send_file(self, username, filepath):
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            data = f.read()
        header = f"FILE|{username}|{filename}|{len(data)}"
        self.send(header)
        self.sock.sendall(data)

    def send(self, message: str):
        if self.sock and self.running:
            self.sock.send(message.encode("utf-8"))

    def receive_loop(self):
        while self.running:
            try:
                msg = self.sock.recv(1024).decode("utf-8")
                if not msg:
                    break
                if self.on_message:
                    self.on_message(msg)
            except:
                break
        self.running = False

    def close(self):
        self.running = False
        if self.sock:
            self.sock.close()
            self.sock = None
