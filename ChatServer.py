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
groups = {}   # group_name -> [user1, user2, ...]
clients_lock = threading.Lock()

# --- KẾT NỐI DATABASE ---
db = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    database="chatpy",
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
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
    if len(parts) < 4:
        conn.sendall(b"REGISTER_FAIL\n")
        return

    username, password, b64_avatar = parts[1], parts[2], parts[3]
    avatar_filename = f"{username}.jpg"
    avatar_path = os.path.join(AVATAR_DIR, avatar_filename)

    try:
        if b64_avatar:
            with open(avatar_path, "wb") as f:
                f.write(base64.b64decode(b64_avatar))
        else:
            avatar_path = "avatars/default.jpg"

        cur = get_cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            conn.sendall(b"REGISTER_FAIL\n")
            return

        cur.execute("INSERT INTO users (username, password, avatar) VALUES (%s, %s, %s)",
                    (username, password, avatar_path))
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

            # gửi danh sách user
            send_user_list()

            # gửi danh sách nhóm cho user này
            user_groups = [g for g, mems in groups.items() if username in mems]
            if user_groups:
                conn.sendall(f"GROUP_LIST|{'|'.join(user_groups)}\n".encode("utf-8"))
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
            # ✅ loại trừ sender
            if c == conn:
                continue
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

    # Tìm target connection
    target_conn = None
    with clients_lock:
        for c, info in clients.items():
            if info["username"] == target:
                target_conn = c
                break

    if target_conn:
        # Chỉ gửi 1 lần PRIVATE
        try:
            target_conn.sendall(f"PRIVATE|{sender}|{text}\n".encode("utf-8"))
        except:
            pass

    # Lưu DB
    try:
        cur = get_cursor()
        cur.execute(
            "INSERT INTO messages (sender, receiver, msg_type, content) VALUES (%s,%s,'PRIVATE',%s)",
            (sender, target, text)
        )
        db.commit()
    except:
        pass

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
                    except Exception as e:
                        print("[BROADCAST IMG ERROR]", e)
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
            except Exception as e:
                print("[PRIVATE IMG ERROR]", e)


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
                    except Exception as e:
                        print("[BROADCAST FILE ERROR]", e)
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
            except Exception as e:
                print("[PRIVATE FILE ERROR]", e)


def handle_voice(parts, conn):
    if len(parts) < 4:
        return
    target, filename, b64_data = parts[1], parts[2], parts[3]
    sender = clients[conn]["username"]

    if target.upper() == "ALL":
        with clients_lock:
            for c in clients.keys():
                if c != conn:
                    try:
                        c.sendall(f"VOICE|{sender}|{filename}|{b64_data}\n".encode("utf-8"))
                    except Exception as e:
                        print("[BROADCAST VOICE ERROR]", e)
    else:
        target_conn = None
        with clients_lock:
            for c, info in clients.items():
                if info["username"] == target:
                    target_conn = c
                    break
        if target_conn:
            try:
                target_conn.sendall(f"VOICE|{sender}|{filename}|{b64_data}\n".encode("utf-8"))
            except Exception as e:
                print("[PRIVATE VOICE ERROR]", e)

def handle_call_request(parts, conn):
    # parts: ["CALL_REQUEST", target]
    if len(parts) < 2:
        return
    target = parts[1]
    sender = clients[conn]["username"]
    target_conn = None
    with clients_lock:
        for c, info in clients.items():
            if info["username"] == target:
                target_conn = c
                break
    if target_conn:
        try:
            target_conn.sendall(f"CALL_REQUEST|{sender}\n".encode("utf-8"))
        except:
            pass

def handle_call_accept(parts, conn):
    if len(parts) < 2:
        return
    target = parts[1]
    sender = clients[conn]["username"]
    target_conn = None
    with clients_lock:
        for c, info in clients.items():
            if info["username"] == target:
                target_conn = c
                break
    if target_conn:
        try:
            target_conn.sendall(f"CALL_ACCEPT|{sender}\n".encode("utf-8"))
        except:
            pass

def handle_call_stream(parts, conn):
    # parts: ["CALL_STREAM", target, b64data]
    if len(parts) < 3:
        return
    target = parts[1]
    b64 = parts[2]
    sender = clients[conn]["username"]
    target_conn = None
    with clients_lock:
        for c, info in clients.items():
            if info["username"] == target:
                target_conn = c
                break
    if target_conn:
        try:
            # forward: CALL_STREAM|sender|b64
            target_conn.sendall(f"CALL_STREAM|{sender}|{b64}\n".encode("utf-8"))
        except:
            pass

def handle_call_end(parts, conn):
    if len(parts) < 2:
        return
    target = parts[1]
    sender = clients[conn]["username"]
    target_conn = None
    with clients_lock:
        for c, info in clients.items():
            if info["username"] == target:
                target_conn = c
                break
    if target_conn:
        try:
            target_conn.sendall(f"CALL_END|{sender}\n".encode("utf-8"))
        except:
            pass

# ------------------- VIDEO CALL -------------------
def handle_video_request(parts, conn):
    # parts: ["VIDEO_REQUEST", target]
    if len(parts) < 2:
        return
    target = parts[1]
    sender = clients[conn]["username"]

    target_conn = None
    with clients_lock:
        for c, info in clients.items():
            if info["username"] == target:
                target_conn = c
                break

    if target_conn:
        try:
            target_conn.sendall(f"VIDEO_REQUEST|{sender}\n".encode("utf-8"))
        except:
            pass


def handle_video_accept(parts, conn):
    # parts: ["VIDEO_ACCEPT", target]
    if len(parts) < 2:
        return
    target = parts[1]
    sender = clients[conn]["username"]

    target_conn = None
    with clients_lock:
        for c, info in clients.items():
            if info["username"] == target:
                target_conn = c
                break

    if target_conn:
        try:
            target_conn.sendall(f"VIDEO_ACCEPT|{sender}\n".encode("utf-8"))
        except:
            pass


def handle_video_decline(parts, conn):
    if len(parts) < 2:
        return
    target = parts[1]
    sender = clients[conn]["username"]
    target_conn = None
    with clients_lock:
        for c, info in clients.items():
            if info["username"] == target:
                target_conn = c
                break
    if target_conn:
        try:
            target_conn.sendall(f"VIDEO_DECLINE|{sender}\n".encode("utf-8"))
        except:
            pass


def handle_video_stream(parts, conn):
    # parts: ["VIDEO_STREAM", target, b64_video, b64_audio]
    if len(parts) < 4:
        return
    target = parts[1]
    b64_video = parts[2]
    b64_audio = parts[3]
    sender = clients[conn]["username"]

    target_conn = None
    with clients_lock:
        for c, info in clients.items():
            if info["username"] == target:
                target_conn = c
                break

    if target_conn:
        try:
            target_conn.sendall(f"VIDEO_STREAM|{sender}|{b64_video}|{b64_audio}\n".encode("utf-8"))
        except:
            pass

def handle_video_end(parts, conn):
    if len(parts) < 2:
        return
    target = parts[1]
    sender = clients[conn]["username"]

    target_conn = None
    with clients_lock:
        for c, info in clients.items():
            if info["username"] == target:
                target_conn = c
                break

    if target_conn:
        try:
            target_conn.sendall(f"VIDEO_END|{sender}\n".encode("utf-8"))
        except:
            pass

# ------------------- GROUP CHAT -------------------
# --- Load groups từ DB khi khởi động ---
def load_groups_from_db():
    try:
        cur = get_cursor()
        cur.execute("SELECT name, members FROM `groups`")
        rows = cur.fetchall()
        for row in rows:
            name = row["name"]
            members = row["members"].split(",")
            groups[name] = members
        print(f"[INIT] Đã tải {len(groups)} nhóm từ database.")
    except Exception as e:
        print("[DB ERROR] Không thể load nhóm:", e)

load_groups_from_db()

def handle_group_create(parts, conn):
    if len(parts) < 3:
        conn.sendall("GROUP_CREATE_FAIL|Thiếu tên nhóm hoặc thành viên\n".encode("utf-8"))
        return

    group_name = parts[1]
    members_str = parts[2]
    members = members_str.split(",")  # ✅ tách danh sách đúng
    sender = clients[conn]["username"]

    # Đảm bảo người tạo nhóm cũng là thành viên
    if sender not in members:
        members.append(sender)

    # Thêm nhóm vào dictionary
    groups[group_name] = members
    print(f"[GROUP_CREATE] {sender} tạo nhóm {group_name} với: {members}")

    # --- Lưu vào DB ---
    try:
        cur = get_cursor()
        cur.execute("INSERT INTO `groups` (name, creator, members) VALUES (%s, %s, %s)",
                    (group_name, sender, ",".join(members)))
        db.commit()
        conn.sendall(f"GROUP_CREATE_OK|{group_name}\n".encode("utf-8"))
    except Exception as e:
        del groups[group_name]
        conn.sendall(f"GROUP_CREATE_FAIL|{e}\n".encode("utf-8"))
        print("[DB ERROR] Không thể lưu nhóm:", e)
        return

    # --- Gửi danh sách nhóm cập nhật cho tất cả thành viên ---
    with clients_lock:
        for c, info in clients.items():
            user_groups = [g for g, mems in groups.items() if info["username"] in mems]
            try:
                if user_groups:
                    c.sendall(f"GROUP_LIST|{'|'.join(user_groups)}\n".encode("utf-8"))
                else:
                    c.sendall("GROUP_LIST\n".encode("utf-8"))
            except:
                pass

def handle_group_msg(parts, conn):
    # Cú pháp client gửi: GROUP_MSG|group_name|text
    if len(parts) < 3:
        conn.sendall("ERR|Sai cú pháp GROUP_MSG\n".encode())
        return

    group_name = parts[1]
    text = parts[2]
    sender = clients[conn]["username"]

    if group_name not in groups:
        conn.sendall(f"ERR|Nhóm {group_name} không tồn tại\n".encode("utf-8"))
        return

    # --- Lưu tin nhắn vào DB ---
    try:
        cur = get_cursor()
        cur.execute("INSERT INTO group_messages (group_name, sender, message) VALUES (%s, %s, %s)",
                    (group_name, sender, text))
        db.commit()
    except Exception as e:
        print("[DB ERROR] Không thể lưu tin nhắn nhóm:", e)

    # --- Gửi tin nhắn cho tất cả thành viên trong nhóm ---
    with clients_lock:
        for c, info in clients.items():
            if info["username"] in groups[group_name]:
                # ❌ Không gửi lại cho chính người gửi
                if info["username"] == sender:
                    continue
                try:
                    c.sendall(f"GROUP_MSG|{group_name}|{sender}|{text}\n".encode("utf-8"))
                except:
                    pass

def handle_group_leave(parts, conn):
    if len(parts) < 2:
        conn.sendall("GROUP_LEAVE_FAIL|Thiếu tên nhóm\n".encode())
        return

    group_name = parts[1]
    username = clients[conn]["username"]

    if group_name not in groups:
        conn.sendall(f"GROUP_LEAVE_FAIL|Nhóm {group_name} không tồn tại\n".encode())
        return

    if username not in groups[group_name]:
        conn.sendall(f"GROUP_LEAVE_FAIL|Bạn không ở trong nhóm {group_name}\n".encode())
        return

    # Xóa khỏi danh sách thành viên
    groups[group_name].remove(username)

    # Cập nhật DB
    try:
        cur = get_cursor()
        cur.execute("UPDATE `groups` SET members=%s WHERE name=%s",
                    (",".join(groups[group_name]), group_name))
        db.commit()
    except Exception as e:
        conn.sendall(f"GROUP_LEAVE_FAIL|{e}\n".encode())
        return

    # ✅ Gửi thông báo rời nhóm cho người dùng
    conn.sendall(f"GROUP_LEAVE_OK|{group_name}|{username}\n".encode())

    # ✅ Gửi danh sách nhóm còn lại cho user
    user_groups = [g for g, mems in groups.items() if username in mems]
    conn.sendall(f"GROUP_LIST|{'|'.join(user_groups)}\n".encode("utf-8"))

    # ✅ Nếu nhóm vẫn còn thành viên, thông báo cho các thành viên còn lại
    if groups[group_name]:
        with clients_lock:
            for c, info in clients.items():
                if info["username"] in groups[group_name]:
                    try:
                        c.sendall(f"GROUP_INFO|{group_name}|{username} đã rời nhóm\n".encode("utf-8"))
                    except:
                        pass
    else:
        # ✅ Nếu nhóm trống -> xóa nhóm khỏi DB và bộ nhớ
        try:
            cur = get_cursor()
            cur.execute("DELETE FROM `groups` WHERE name=%s", (group_name,))
            db.commit()
        except:
            pass
        del groups[group_name]

        # 🔔 Gửi thông báo cho tất cả client để xóa nhóm khỏi giao diện
        with clients_lock:
            for c in clients.keys():
                try:
                    c.sendall(f"GROUP_DELETE|{group_name}\n".encode("utf-8"))
                except:
                    pass

def handle_group_image(parts, conn):
    if len(parts) < 4:
        return
    group_name, filename, b64_data = parts[1], parts[2], parts[3]
    sender = clients[conn]["username"]

    if group_name not in groups:
        conn.sendall(f"ERR|Nhóm {group_name} không tồn tại\n".encode())
        return

    with clients_lock:
        for c, info in clients.items():
            if info["username"] in groups[group_name]:
                tag = "GROUP_IMG_SELF" if info["username"] == sender else "GROUP_IMG"
                try:
                    c.sendall(f"{tag}|{group_name}|{sender}|{filename}|{b64_data}\n".encode("utf-8"))
                except Exception as e:
                    print("[GROUP_IMG ERROR]", e)
def handle_group_file(parts, conn):
    if len(parts) < 4:
        return
    group_name, filename, b64_data = parts[1], parts[2], parts[3]
    sender = clients[conn]["username"]

    if group_name not in groups:
        conn.sendall(f"ERR|Nhóm {group_name} không tồn tại\n".encode())
        return

    with clients_lock:
        for c, info in clients.items():
            if info["username"] in groups[group_name]:
                tag = "GROUP_FILE_SELF" if info["username"] == sender else "GROUP_FILE"
                try:
                    c.sendall(f"{tag}|{group_name}|{sender}|{filename}|{b64_data}\n".encode("utf-8"))
                except Exception as e:
                    print("[GROUP_FILE ERROR]", e)
def handle_group_voice(parts, conn):
    if len(parts) < 4:
        return
    group_name, filename, b64_data = parts[1], parts[2], parts[3]
    sender = clients[conn]["username"]

    if group_name not in groups:
        conn.sendall(f"ERR|Nhóm {group_name} không tồn tại\n".encode())
        return

    with clients_lock:
        for c, info in clients.items():
            if info["username"] in groups[group_name]:
                tag = "GROUP_VOICE_SELF" if info["username"] == sender else "GROUP_VOICE"
                try:
                    c.sendall(f"{tag}|{group_name}|{sender}|{filename}|{b64_data}\n".encode("utf-8"))
                except Exception as e:
                    print("[GROUP_VOICE ERROR]", e)

# ------------------- XỬ LÝ CLIENT -------------------
def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr}")
    buffer = ""
    try:
        while True:
            # 👇 tăng kích thước nhận
            data = conn.recv(65536)
            if not data:
                break

            # 👇 thêm try/except ở đây
            try:
                buffer += data.decode("utf-8", errors="ignore")
            except UnicodeDecodeError:
                # nếu dữ liệu base64 bị cắt giữa chừng -> đợi thêm
                continue

            if "\n" not in buffer:
                continue

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                # Chỉ tách 2 phần đầu để giữ nguyên base64 (cho tất cả loại lệnh)
                if line.startswith(("GROUP_IMG|", "GROUP_FILE|", "GROUP_VOICE|")):
                    parts = line.split("|", 4)
                elif line.startswith(("IMG|", "FILE|", "VOICE|")):
                    parts = line.split("|", 3)
                else:
                    parts = line.split("|")

                if len(parts) == 0 or parts[0] == "":
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
                elif cmd == "VOICE":
                    handle_voice(parts, conn)
                elif cmd == "CALL_REQUEST":
                    handle_call_request(parts, conn)
                elif cmd == "CALL_ACCEPT":
                    handle_call_accept(parts, conn)
                elif cmd == "CALL_STREAM":
                    handle_call_stream(parts, conn)
                elif cmd == "CALL_END":
                    handle_call_end(parts, conn)
                elif cmd == "VIDEO_REQUEST":
                    handle_video_request(parts, conn)
                elif cmd == "VIDEO_ACCEPT":
                    handle_video_accept(parts, conn)
                elif cmd == "VIDEO_DECLINE":
                    handle_video_decline(parts, conn)
                elif cmd == "VIDEO_STREAM":
                    handle_video_stream(parts, conn)
                elif cmd == "VIDEO_END":
                    handle_video_end(parts, conn)
                elif cmd == "GROUP_CREATE":
                    handle_group_create(parts, conn)
                elif cmd == "GROUP_MSG":
                    handle_group_msg(parts, conn)
                elif cmd == "GROUP_LEAVE":
                    handle_group_leave(parts, conn)
                elif cmd == "GROUP_IMG":
                    handle_group_image(parts, conn)
                elif cmd == "GROUP_FILE":
                    handle_group_file(parts, conn)
                elif cmd == "GROUP_VOICE":
                    handle_group_voice(parts, conn)
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
