# chat_client.py
import socket
import threading

class ChatClient:
    def __init__(self, host="127.0.0.1", port=2020):
        self.host = host
        self.port = port
        self.sock = None
        self.running = False
        self.on_message = None  # callback khi nhận tin nhắn

    def connect(self):
        """Kết nối đến server"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.running = True

        # Thread nhận tin nhắn
        thread = threading.Thread(target=self.receive_loop, daemon=True)
        thread.start()

    def login(self, username, password):
        self.send(f"LOGIN|{username}|{password}")

    def register(self, username, password):
        self.send(f"REGISTER|{username}|{password}")

    def send_message(self, text):
        self.send(f"MSG|{text}")

    def send(self, message: str):
        """Gửi tin nhắn đến server"""
        if self.sock and self.running:
            self.sock.send(message.encode("utf-8"))

    def receive_loop(self):
        """Luồng nhận tin nhắn"""
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
        """Đóng kết nối"""
        self.running = False
        if self.sock:
            self.sock.close()
