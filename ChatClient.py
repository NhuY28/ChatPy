import socket
import threading
import base64, os, hashlib

class ChatClient:
    def __init__(self, host="192.168.56.1", port=2025):
        self.host = host
        self.port = port
        self.sock = None
        self.running = False
        self.on_message = None  # callback: msg từ server
        # -------------------------------
        self.group_unread_count = {}  # {group_name: số tin nhắn chưa đọc}
        self.open_groups = set()      # nhóm đang mở
        self.received_msg_ids = set() # tránh tăng count trùng

    # ====================== CONNECT ======================
    def connect(self):
        if self.sock:
            return
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.running = True
        threading.Thread(target=self.receive_loop, daemon=True).start()

    # ====================== ACCOUNT ======================
    def register(self, username, password, avatar_path="avatars/default.jpg"):
        if os.path.exists(avatar_path):
            with open(avatar_path, "rb") as f:
                b64_avatar = base64.b64encode(f.read()).decode("utf-8")
        else:
            b64_avatar = ""
        self.send(f"REGISTER|{username}|{password}|{b64_avatar}\n")

    def login(self, username, password):
        self.send(f"LOGIN|{username}|{password}\n")

    # ====================== MESSAGE ======================
    def send_message(self, text):
        self.send(f"MSG|{text}\n")

    def send_private_message(self, target, text):
        self.send(f"PRIVATE|{target}|{text}\n")

    # ====================== FILE / IMAGE / VOICE ======================
    def send_file(self, target, filepath):
        self._send_file_generic("FILE", target, filepath)

    def send_image(self, target, filepath):
        self._send_file_generic("IMG", target, filepath)

    def send_voice(self, target, filepath):
        self._send_file_generic("VOICE", target, filepath)

    def _send_file_generic(self, cmd, target, filepath):
        try:
            with open(filepath, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")
            filename = os.path.basename(filepath)
            self.send(f"{cmd}|{target}|{filename}|{b64_data}\n")
        except Exception as e:
            print(f"[{cmd} ERROR]", e)

    # ====================== GROUP CHAT ======================
    def send_group_create(self, group_name, members):
        msg = f"GROUP_CREATE|{group_name}|{','.join(members)}\n"
        self.send(msg)

    def send_group_message(self, group_name, text):
        self.send(f"GROUP_MSG|{group_name}|{text}\n")

    def send_group_image(self, group_name, filepath):
        self._send_file_generic("GROUP_IMG", group_name, filepath)

    def send_group_file(self, group_name, filepath):
        self._send_file_generic("GROUP_FILE", group_name, filepath)

    def send_group_voice(self, group_name, filepath):
        self._send_file_generic("GROUP_VOICE", group_name, filepath)

    def send_group_leave(self, group_name):
        self.send(f"GROUP_LEAVE|{group_name}\n")

    # ====================== CALL ======================
    def send_call_request(self, target):
        self.send(f"CALL_REQUEST|{target}\n")

    def send_call_accept(self, target):
        self.send(f"CALL_ACCEPT|{target}\n")

    def send_call_stream(self, target, b64_chunk):
        self.send(f"CALL_STREAM|{target}|{b64_chunk}\n")

    def send_call_end(self, target):
        self.send(f"CALL_END|{target}\n")

    # ====================== GROUP OPEN / UNREAD ======================
    def open_group(self, group_name):
        """Mở nhóm, reset unread count"""
        self.open_groups.add(group_name)
        self.group_unread_count[group_name] = 0

    def close_group(self, group_name):
        """Đóng nhóm"""
        if group_name in self.open_groups:
            self.open_groups.remove(group_name)

    def get_unread_count(self, group_name):
        return self.group_unread_count.get(group_name, 0)

    # ====================== CORE SOCKET ======================
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
                chunk = self.sock.recv(65536)
                if not chunk:
                    break

                try:
                    text = chunk.decode("utf-8")
                except UnicodeDecodeError:
                    continue

                buffer += text
                if "\n" not in buffer:
                    continue

                while "\n" in buffer:
                    msg, buffer = buffer.split("\n", 1)
                    msg = msg.strip()
                    if not msg:
                        continue
                    self.handle_incoming(msg)
            except Exception as e:
                print("[RECV ERROR]", e)
                break
        self.running = False

    # ====================== HANDLE INCOMING ======================
    def handle_incoming(self, msg):
        """
        Xử lý message từ server trước khi gửi GUI.
        Tăng group_unread_count chỉ khi message mới, nhóm đóng.
        """
        parts = msg.split("|")
        cmd = parts[0]

        # Các message nhóm
        group_cmds = ("GROUP_MSG", "GROUP_IMG", "GROUP_FILE", "GROUP_VOICE")
        if cmd in group_cmds:
            group_name = parts[1]
            # Tạo id đơn giản để tránh trùng lặp (hash msg)
            msg_id = hashlib.md5(msg.encode("utf-8")).hexdigest()
            if msg_id not in self.received_msg_ids:
                self.received_msg_ids.add(msg_id)
                if group_name not in self.open_groups:
                    self.group_unread_count[group_name] = self.group_unread_count.get(group_name, 0) + 1

        # gửi tới GUI / callback
        if self.on_message:
            self.on_message(msg)

    def close(self):
        self.running = False
        if self.sock:
            try: self.sock.close()
            except: pass
            self.sock = None
