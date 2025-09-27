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
        self.on_message = None

    def connect(self):
        if self.sock:
            return
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.running = True
        thread = threading.Thread(target=self.receive_loop, daemon=True)
        thread.start()

    def register(self, username, password, avatar_path):
        if avatar_path and os.path.exists(avatar_path):
            filename = os.path.basename(avatar_path)
            with open(avatar_path, "rb") as f:
                data = f.read()
            header = f"REGISTER|{username}|{password}|{filename}|{len(data)}\n"
            self.send(header)
            self.sock.sendall(data)
        else:
            self.send(f"REGISTER|{username}|{password}|default.png|0\n")

    def login(self, username, password):
        self.send(f"LOGIN|{username}|{password}\n")

    def send_message(self, username, text):
        self.send(f"MSG|{username}|{text}\n")

    def send_image(self, username, filepath):
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            data = f.read()
        header = f"IMAGE|{username}|{filename}|{len(data)}\n"
        self.send(header)
        self.sock.sendall(data)

    def send_file(self, username, filepath):
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            data = f.read()
        header = f"FILE|{username}|{filename}|{len(data)}\n"
        self.send(header)
        self.sock.sendall(data)

    def send(self, message: str):
        if self.sock and self.running:
            self.sock.send(message.encode("utf-8"))

    def receive_loop(self):
        buffer = ""
        while self.running:
            try:
                data = self.sock.recv(1024).decode("utf-8")
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    msg, buffer = buffer.split("\n", 1)
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
