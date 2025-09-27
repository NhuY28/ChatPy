# ChatServer.py
import socket
import threading
import pymysql
import os

HOST = "0.0.0.0"
PORT = 2025
AVATAR_DIR = "avatars"

if not os.path.exists(AVATAR_DIR):
    os.makedirs(AVATAR_DIR)

clients = []
clients_lock = threading.Lock()

# --- KẾT NỐI DATABASE ---
db = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    database="chatpy",
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor
)
cursor = db.cursor()

def broadcast(message, sender_conn):
    with clients_lock:
        for client in clients.copy():
            if client != sender_conn:
                try:
                    client.send((message + "\n").encode("utf-8"))
                except:
                    clients.remove(client)

def handle_client(conn, addr):
    print(f"[KẾT NỐI] {addr} đã kết nối")
    with clients_lock:
        clients.append(conn)
    try:
        conn.settimeout(20)
        buffer = ""
        while True:
            try:
                data = conn.recv(1024).decode("utf-8")
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    header, buffer = buffer.split("\n", 1)
                    parts = header.strip().split("|")
                    cmd = parts[0]

                    # --- Đăng ký ---
                    if cmd == "REGISTER":
                        username, password = parts[1], parts[2]
                        filename, size = parts[3], int(parts[4])

                        avatar_data = b""
                        remaining = size
                        while remaining > 0:
                            packet = conn.recv(min(4096, remaining))
                            if not packet:
                                break
                            avatar_data += packet
                            remaining -= len(packet)

                        if size > 0 and len(avatar_data) < size:
                            print(f"[LỖI] Nhận avatar không đầy đủ từ {addr}")
                            conn.send("REGISTER_FAIL\n".encode("utf-8"))
                            continue

                        avatar_path = os.path.join(AVATAR_DIR, filename) if size > 0 else "default.png"
                        if size > 0:
                            with open(avatar_path, "wb") as f:
                                f.write(avatar_data)

                        try:
                            cursor.execute(
                                "INSERT INTO users (username, password, avatar) VALUES (%s, %s, %s)",
                                (username, password, avatar_path)
                            )
                            db.commit()
                            conn.send("REGISTER_OK\n".encode("utf-8"))
                        except Exception as e:
                            print("Đăng ký lỗi:", e)
                            conn.send("REGISTER_FAIL\n".encode("utf-8"))

                    # --- Đăng nhập ---
                    elif cmd == "LOGIN":
                        username, password = parts[1], parts[2]
                        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
                        result = cursor.fetchone()
                        if result:
                            conn.send(f"LOGIN_OK|{result['avatar']}\n".encode("utf-8"))
                        else:
                            conn.send("LOGIN_FAIL\n".encode("utf-8"))

                    # --- Chat text ---
                    elif cmd == "MSG":
                        sender, text = parts[1], parts[2]
                        cursor.execute("INSERT INTO messages (sender, msg_type, content) VALUES (%s, 'TEXT', %s)", (sender, text))
                        db.commit()
                        broadcast(f"{sender}: {text}", conn)

                    # --- Gửi ảnh ---
                    elif cmd == "IMAGE":
                        sender, filename, size = parts[1], parts[2], int(parts[3])
                        img_data = b""
                        remaining = size
                        while remaining > 0:
                            packet = conn.recv(min(4096, remaining))
                            if not packet:
                                break
                            img_data += packet
                            remaining -= len(packet)
                        cursor.execute(
                            "INSERT INTO messages (sender, msg_type, content, filename) VALUES (%s, 'IMAGE', %s, %s)",
                            (sender, img_data, filename)
                        )
                        db.commit()
                        broadcast(f"{sender} đã gửi ảnh: {filename}", conn)

                    # --- Gửi file ---
                    elif cmd == "FILE":
                        sender, filename, size = parts[1], parts[2], int(parts[3])
                        file_data = b""
                        remaining = size
                        while remaining > 0:
                            packet = conn.recv(min(4096, remaining))
                            if not packet:
                                break
                            file_data += packet
                            remaining -= len(packet)
                        cursor.execute(
                            "INSERT INTO messages (sender, msg_type, content, filename) VALUES (%s, 'FILE', %s, %s)",
                            (sender, file_data, filename)
                        )
                        db.commit()
                        broadcast(f"{sender} đã gửi file: {filename}", conn)
            except socket.timeout:
                continue
    except Exception as e:
        print(f"[LỖI] {addr}: {e}")
    finally:
        print(f"[NGẮT] {addr} đã thoát")
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        conn.close()

def start():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER] Đang lắng nghe trên {HOST}:{PORT}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start()
