import socket
import threading

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
        threading.Thread(target=self.receive_loop, daemon=True).start()

    def register(self, username, password, avatar_path="avatars/default.jpg"):
        self.send(f"REGISTER|{username}|{password}\n")

    def login(self, username, password):
        self.send(f"LOGIN|{username}|{password}\n")

    def send_message(self, text):
        self.send(f"MSG|{text}\n")

    def send_private_message(self, target, text):
        self.send(f"PRIVATE|{target}|{text}\n")

    def send(self, message):
        if self.sock and self.running:
            try:
                self.sock.sendall(message.encode("utf-8"))
            except:
                self.close()

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
            try: self.sock.close()
            except: pass
            self.sock = None
