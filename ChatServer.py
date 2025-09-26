import socket
import threading
import mysql.connector

HOST = "0.0.0.0"
PORT = 2025

clients = []

# --- KẾT NỐI DATABASE ---
db = mysql.connector.connect(
    host="localhost",
    user="root",        # mặc định của XAMPP
    password="",        # để trống nếu chưa đặt mật khẩu MySQL
    database="chatpy"
)
cursor = db.cursor()

def handle_client(conn, addr):
    print(f"[KẾT NỐI] {addr} đã kết nối")
    try:
        while True:
            msg = conn.recv(1024).decode("utf-8")
            if not msg:
                break

            print(f"{addr}: {msg}")

            parts = msg.split("|")
            cmd = parts[0]

            # --- Xử lý đăng ký ---
            if cmd == "REGISTER":
                username, password = parts[1], parts[2]
                try:
                    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
                    db.commit()
                    conn.send("REGISTER_OK".encode("utf-8"))
                except:
                    conn.send("REGISTER_FAIL".encode("utf-8"))

            # --- Xử lý đăng nhập ---
            elif cmd == "LOGIN":
                username, password = parts[1], parts[2]
                cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
                result = cursor.fetchone()
                if result:
                    conn.send("LOGIN_OK".encode("utf-8"))
                else:
                    conn.send("LOGIN_FAIL".encode("utf-8"))

            # --- Chat bình thường ---
            elif cmd == "MSG":
                text = parts[1]
                broadcast(f"{addr}: {text}", conn)

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
