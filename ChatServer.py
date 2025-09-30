# ChatServer.py
import socket
import threading
import pymysql
import os
import base64

HOST = "0.0.0.0"
PORT = 2025
AVATAR_DIR = "avatars"

if not os.path.exists(AVATAR_DIR):
    os.makedirs(AVATAR_DIR)

# clients: dict {conn: {"username": str, "avatar": str}}
clients = {}
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

def get_cursor():
    return db.cursor()

# ------------------- GỬI DANH SÁCH USER ONLINE -------------------
def send_user_list():
    with clients_lock:
        users = [f"{info['username']}:{info['avatar']}" for info in clients.values()]
        msg = "USER_LIST|" + "|".join(users) + "\n"
        for c in clients.keys():
            try:
                c.sendall(msg.encode("utf-8"))
            except:
                pass

# ------------------- REGISTER -------------------
def handle_register(parts, conn):
    if len(parts) < 3:
        conn.sendall(b"REGISTER_FAIL\n")
        return

    username, password = parts[1], parts[2]
    try:
        cur = get_cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            conn.sendall(b"REGISTER_FAIL\n")
            return

        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        db.commit()
        conn.sendall(b"REGISTER_OK\n")
    except Exception as e:
        conn.sendall(f"ERR|{e}\n".encode("utf-8"))

# ------------------- LOGIN -------------------
def handle_login(parts, conn):
    if len(parts) < 3:
        conn.sendall(b"LOGIN_FAIL\n")
        return
    username, password = parts[1], parts[2]

    try:
        cur = get_cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cur.fetchone()
        if user:
            avatar_path = user.get("avatar") or "avatars/default.jpg"
            with clients_lock:
                clients[conn] = {"username": username, "avatar": avatar_path}
            conn.sendall(f"LOGIN_OK|{avatar_path}\n".encode("utf-8"))
            send_user_list()
        else:
            conn.sendall(b"LOGIN_FAIL\n")
    except Exception as e:
        conn.sendall(f"ERR|{e}\n".encode("utf-8"))

# ------------------- BROADCAST MESSAGE -------------------
def handle_msg(parts, conn):
    if len(parts) < 2:
        return
    text = parts[1]
    sender = clients[conn]["username"]

    with clients_lock:
        for c in clients.keys():
            try:
                c.sendall(f"MSG|{sender}|{text}\n".encode("utf-8"))
            except:
                pass

    try:
        cur = get_cursor()
        cur.execute(
            "INSERT INTO messages (sender, receiver, msg_type, content) VALUES (%s,%s,'PUBLIC',%s)",
            (sender, None, text)
        )
        db.commit()
    except:
        pass

# ------------------- PRIVATE MESSAGE -------------------
def handle_private(parts, conn):
    if len(parts) < 3:
        return
    target, text = parts[1], parts[2]
    sender = clients[conn]["username"]

    target_conn = None
    with clients_lock:
        for c, info in clients.items():
            if info["username"] == target:
                target_conn = c
                break

    if target_conn:
        try:
            target_conn.sendall(f"PRIVATE|{sender}|{text}\n".encode("utf-8"))
        except:
            pass

        # lưu vào DB
        try:
            cur = get_cursor()
            cur.execute(
                "INSERT INTO messages (sender, receiver, msg_type, content) VALUES (%s,%s,'PRIVATE',%s)",
                (sender, target, text)
            )
            db.commit()
        except:
            pass
    else:
        conn.sendall(f"ERR|User {target} not online\n".encode("utf-8"))

# ------------------- IMAGE -------------------
def handle_image(parts, conn):
    if len(parts) < 4:
        return
    target, filename, b64_data = parts[1], parts[2], parts[3]
    sender = clients[conn]["username"]

    if target.upper() == "ALL":
        # broadcast
        with clients_lock:
            for c in clients.keys():
                if c != conn:
                    try:
                        c.sendall(f"IMG|{sender}|{filename}|{b64_data}\n".encode("utf-8"))
                    except:
                        pass
    else:
        # private
        target_conn = None
        with clients_lock:
            for c, info in clients.items():
                if info["username"] == target:
                    target_conn = c
                    break
        if target_conn:
            try:
                target_conn.sendall(f"IMG|{sender}|{filename}|{b64_data}\n".encode("utf-8"))
            except:
                pass

def handle_file(parts, conn):
    if len(parts) < 4:
        return
    target, filename, b64_data = parts[1], parts[2], parts[3]
    sender = clients[conn]["username"]

    if target.upper() == "ALL":
        with clients_lock:
            for c in clients.keys():
                if c != conn:
                    try:
                        c.sendall(f"FILE|{sender}|{filename}|{b64_data}\n".encode("utf-8"))
                    except:
                        pass
    else:
        target_conn = None
        with clients_lock:
            for c, info in clients.items():
                if info["username"] == target:
                    target_conn = c
                    break
        if target_conn:
            try:
                target_conn.sendall(f"FILE|{sender}|{filename}|{b64_data}\n".encode("utf-8"))
            except:
                pass

# ------------------- XỬ LÝ CLIENT -------------------
def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr}")
    buffer = ""
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buffer += data.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                parts = line.strip().split("|")
                if not parts:
                    continue
                cmd = parts[0].upper()
                if cmd == "REGISTER":
                    handle_register(parts, conn)
                elif cmd == "LOGIN":
                    handle_login(parts, conn)
                elif cmd == "MSG":
                    handle_msg(parts, conn)
                elif cmd == "PRIVATE":
                    handle_private(parts, conn)
                elif cmd == "IMG":
                    handle_image(parts, conn)
                elif cmd == "FILE":
                    handle_file(parts, conn)
                else:
                    conn.sendall(f"ERR|Unknown command {cmd}\n".encode("utf-8"))
    except Exception as e:
        print("[ERROR]", e)
    finally:
        with clients_lock:
            if conn in clients:
                print(f"[DISCONNECT] {clients[conn]['username']} left.")
                del clients[conn]
                send_user_list()
        conn.close()

# ------------------- KHỞI ĐỘNG SERVER -------------------
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[STARTED] Server running on {HOST}:{PORT}")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()
