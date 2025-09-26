#ChatServer.py
import socket
import threading
import pymysql

HOST = "0.0.0.0"
PORT = 2025

clients = []

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

def handle_client(conn, addr):
    print(f"[KẾT NỐI] {addr} đã kết nối")
    try:
        while True:
            header = conn.recv(1024).decode("utf-8")
            if not header:
                break

            parts = header.split("|")
            cmd = parts[0]

            # --- Đăng ký ---
            if cmd == "REGISTER":
                username, password = parts[1], parts[2]
                try:
                    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
                    db.commit()
                    conn.send("REGISTER_OK".encode("utf-8"))
                except:
                    conn.send("REGISTER_FAIL".encode("utf-8"))

            # --- Đăng nhập ---
            elif cmd == "LOGIN":
                username, password = parts[1], parts[2]
                cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
                result = cursor.fetchone()
                if result:
                    conn.send("LOGIN_OK".encode("utf-8"))
                else:
                    conn.send("LOGIN_FAIL".encode("utf-8"))

            # --- Chat text ---
            elif cmd == "MSG":
                sender, text = parts[1], parts[2]
                cursor.execute("INSERT INTO messages (sender, msg_type, content) VALUES (%s, 'TEXT', %s)", (sender, text))
                db.commit()
                broadcast(f"{sender}: {text}", conn)

            # --- Gửi ảnh ---
            elif cmd == "IMAGE":
                sender, filename, size = parts[1], parts[2], int(parts[3])
                data = b""
                while len(data) < size:
                    packet = conn.recv(4096)
                    if not packet:
                        break
                    data += packet
                cursor.execute(
                    "INSERT INTO messages (sender, msg_type, content, filename) VALUES (%s, 'IMAGE', %s, %s)",
                    (sender, data, filename)
                )
                db.commit()
                broadcast(f"{sender} đã gửi ảnh: {filename}", conn)

            # --- Gửi file ---
            elif cmd == "FILE":
                sender, filename, size = parts[1], parts[2], int(parts[3])
                data = b""
                while len(data) < size:
                    packet = conn.recv(4096)
                    if not packet:
                        break
                    data += packet
                cursor.execute(
                    "INSERT INTO messages (sender, msg_type, content, filename) VALUES (%s, 'FILE', %s, %s)",
                    (sender, data, filename)
                )
                db.commit()
                broadcast(f"{sender} đã gửi file: {filename}", conn)

    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        print(f"[NGẮT] {addr} đã thoát")
        if conn in clients:
            clients.remove(conn)
        conn.close()

def broadcast(message, sender_conn):
    for client in clients:
        if client != sender_conn:
            try:
                client.send(message.encode("utf-8"))
            except:
                clients.remove(client)

def start():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER] Đang lắng nghe trên {HOST}:{PORT}")
    while True:
        conn, addr = server.accept()
        clients.append(conn)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start()
