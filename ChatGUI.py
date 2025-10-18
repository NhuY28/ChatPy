# ChatGUI.py
import os
import tkinter as tk
import base64
from pathlib import Path
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw
from ChatClient import ChatClient


class ChatGUI:
    def __init__(self, root=None):
        if root is None:
            self.root = tk.Tk()
            self.is_main = True
        else:
            self.root = tk.Toplevel(root)
            self.is_main = False

        self.root.title("ChatPy - Đăng nhập/Đăng ký")
        self.root.geometry("900x550")
        self.root.config(bg="#f5f5f5")

        self.client = ChatClient()
        self.username = None
        self.avatar_path = None
        self.user_avatars = {}    # dict username -> avatar_path
        self.current_users = []   # latest user list from server
        self.pending_users = []   # if update arrives before UI created
        self.current_chat_user = None

        # Quản lý nhiều khung chat
        self.chat_frames = {}     # username -> Frame
        self.unread_count = {}    # username -> số tin chưa đọc

        # --- Load icon ---
        # Ensure these files exist or replace with your own icons
        self.icon_user = ImageTk.PhotoImage(Image.open("username.png").resize((20, 20)))
        self.icon_pass = ImageTk.PhotoImage(Image.open("password.png").resize((20, 20)))
        self.icon_folder = ImageTk.PhotoImage(Image.open("folder.png").resize((20, 20)))

        self.show_register()

        if self.is_main:
            self.root.mainloop()

    # ------------------- ĐĂNG KÝ -------------------
    def show_register(self):
        self.clear_window()

        lbl_title = tk.Label(self.root, text="TẠO TÀI KHOẢN",
                             font=("Arial", 18, "bold"), bg="#f5f5f5", fg="#333")
        lbl_title.pack(pady=20)

        # --- Avatar ---
        self.avatar_frame = tk.Frame(self.root, bg="#f5f5f5")
        self.avatar_frame.pack(pady=10)

        self.avatar_image = ImageTk.PhotoImage(Image.open("folder.png").resize((40, 40)))
        self.avatar_label = tk.Label(self.avatar_frame, image=self.avatar_image, bg="#f5f5f5", cursor="hand2")
        self.avatar_label.pack()
        self.avatar_label.bind("<Button-1>", lambda e: self.choose_avatar())

        # Username
        frame_user = tk.Frame(self.root, bg="#f5f5f5")
        frame_user.pack(pady=10, padx=40, fill="x")
        tk.Label(frame_user, image=self.icon_user, bg="#f5f5f5").pack(side="left", padx=5)
        self.entry_user = tk.Entry(frame_user, font=("Arial", 16))
        self.entry_user.pack(side="left", fill="x", expand=True)

        # Password
        frame_pass = tk.Frame(self.root, bg="#f5f5f5")
        frame_pass.pack(pady=10, padx=40, fill="x")
        tk.Label(frame_pass, image=self.icon_pass, bg="#f5f5f5").pack(side="left", padx=5)
        self.entry_pass = tk.Entry(frame_pass, font=("Arial", 16), show="*")
        self.entry_pass.pack(side="left", fill="x", expand=True)

        # Confirm password
        frame_confirm = tk.Frame(self.root, bg="#f5f5f5")
        frame_confirm.pack(pady=10, padx=40, fill="x")
        tk.Label(frame_confirm, image=self.icon_pass, bg="#f5f5f5").pack(side="left", padx=5)
        self.entry_confirm = tk.Entry(frame_confirm, font=("Arial", 16), show="*")
        self.entry_confirm.pack(side="left", fill="x", expand=True)

        btn_register = tk.Button(self.root, text="Đăng ký", bg="#6a5acd", fg="white",
                                 font=("Arial", 12, "bold"), command=self.do_register)
        btn_register.pack(pady=20)

        lbl_login = tk.Label(self.root, text="Bạn đã có tài khoản? Đăng nhập ngay",
                             fg="red", bg="#f5f5f5", cursor="hand2", font=("Arial", 10, "underline"))
        lbl_login.pack()
        lbl_login.bind("<Button-1>", lambda e: self.show_login())

    def do_register(self):
        user = self.entry_user.get()
        pw = self.entry_pass.get()
        cf = self.entry_confirm.get()
        if pw != cf:
            messagebox.showerror("Lỗi", "Mật khẩu không khớp!")
            return
        avatar = self.avatar_path if self.avatar_path else "avatars/default.jpg"

        # connect and register
        self.client.connect()
        self.client.on_message = self.handle_server_message
        # original ChatClient.register expects "REGISTER|user|pw\n"
        self.client.register(user, pw, avatar)

    def choose_avatar(self):
        file = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if file:
            img = Image.open(file).resize((90, 90))
            self.avatar_image = ImageTk.PhotoImage(img)
            self.avatar_label.config(image=self.avatar_image)
            self.avatar_path = file

    # ------------------- ĐĂNG NHẬP -------------------
    def show_login(self):
        self.clear_window()

        lbl_title = tk.Label(self.root, text="ĐĂNG NHẬP",
                             font=("Arial", 18, "bold"), bg="#f5f5f5", fg="#333")
        lbl_title.pack(pady=20)

        frame_user = tk.Frame(self.root, bg="#f5f5f5")
        frame_user.pack(pady=10, padx=40, fill="x")
        tk.Label(frame_user, image=self.icon_user, bg="#f5f5f5").pack(side="left", padx=5)
        self.login_user = tk.Entry(frame_user, font=("Arial", 14))
        self.login_user.pack(side="left", fill="x", expand=True)

        frame_pass = tk.Frame(self.root, bg="#f5f5f5")
        frame_pass.pack(pady=10, padx=40, fill="x")
        tk.Label(frame_pass, image=self.icon_pass, bg="#f5f5f5").pack(side="left", padx=5)
        self.login_pass = tk.Entry(frame_pass, font=("Arial", 14), show="*")
        self.login_pass.pack(side="left", fill="x", expand=True)

        btn_login = tk.Button(self.root, text="Đăng nhập", bg="#228B22", fg="white",
                              font=("Arial", 12, "bold"), command=self.do_login)
        btn_login.pack(pady=20)

        lbl_register = tk.Label(self.root, text="Chưa có tài khoản? Đăng ký ngay",
                                fg="blue", bg="#f5f5f5", cursor="hand2", font=("Arial", 10, "underline"))
        lbl_register.pack()
        lbl_register.bind("<Button-1>", lambda e: self.show_register())

    def do_login(self):
        user = self.login_user.get()
        pw = self.login_pass.get()
        self.client.connect()
        self.username = user
        self.client.on_message = self.handle_server_message
        self.client.login(user, pw)

    # ------------------- CỬA SỔ CHAT -------------------
    def show_chat(self, chat_frame=None):
        self.clear_window()
        self.root.title(f"ChatPy - {self.username}")

        main_frame = tk.Frame(self.root, bg="#f5f5f5")
        main_frame.pack(fill="both", expand=True)

        # --- Khung danh sách user online (bên trái) ---
        self.user_frame = tk.Frame(main_frame, width=150, bg="#e0e0e0")
        self.user_frame.pack(side="left", fill="y")
        self.user_frame.pack_propagate(False)  # không cho co giãn theo widget con

        tk.Label(self.user_frame, text="👥 Online", bg="#e0e0e0",
                 font=("Arial", 12, "bold")).pack(pady=5)

        # Container chứa danh sách user
        self.user_list_container = tk.Frame(self.user_frame, bg="#e0e0e0")
        self.user_list_container.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Khung trò chuyện (bên phải) ---
        self.chat_frame = tk.Frame(main_frame, bg="#f5f5f5")
        self.chat_frame.pack(side="right", fill="both", expand=True)

        # Header khung chat (hiển thị tên và avatar user đang chat)
        self.chat_header = tk.Frame(self.chat_frame, bg="#ddd", height=50)
        self.chat_header.pack(fill="x")
        self.chat_header.pack_propagate(False)

        self.chat_header_avatar = tk.Label(self.chat_header, bg="#ddd")
        self.chat_header_avatar.pack(side="left", padx=10)

        self.chat_header_name = tk.Label(self.chat_header, text="Chọn người để chat",
                                         font=("Arial", 12, "bold"), bg="#ddd", anchor="w")
        self.chat_header_name.pack(side="left", padx=5)

        # --- Khung hiển thị tin nhắn ---
        chat_display = tk.Frame(self.chat_frame, bg="#f5f5f5")
        chat_display.pack(fill="both", expand=True)

        self.chat_canvas = tk.Canvas(chat_display, bg="#f5f5f5", highlightthickness=0)
        self.chat_scrollbar = tk.Scrollbar(chat_display, orient="vertical", command=self.chat_canvas.yview)
        self.chat_canvas.configure(yscrollcommand=self.chat_scrollbar.set)

        self.chat_canvas.pack(side="left", fill="both", expand=True)
        self.chat_scrollbar.pack(side="right", fill="y")

        self.chat_inner = tk.Frame(self.chat_canvas, bg="#f5f5f5")

        # Gán ID để có thể config lại width sau này
        self.chat_window = self.chat_canvas.create_window((0, 0), window=self.chat_inner, anchor="nw")

        # Khi canvas thay đổi kích thước, cập nhật width cho chat_inner
        def resize_inner(event):
            self.chat_canvas.itemconfig(self.chat_window, width=event.width)

        self.chat_canvas.bind("<Configure>", resize_inner)

        self.chat_inner.bind(
            "<Configure>",
            lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        )

        # --- Khung nhập tin nhắn ---
        frame_bottom = tk.Frame(self.chat_frame, bg="#ddd", height=45)
        frame_bottom.pack(fill="x", side="bottom")
        frame_bottom.pack_propagate(False)

        self.entry_msg = tk.Entry(frame_bottom, font=("Arial", 12))
        self.entry_msg.pack(side="left", fill="x", expand=True, padx=5, ipady=3)

        btn_send = tk.Button(frame_bottom, text="Gửi", command=self.send_message,
                             bg="#6a5acd", fg="white")
        btn_send.pack(side="left", padx=5)

        btn_img = tk.Button(frame_bottom, text="📷 Ảnh", command=self.send_image)
        btn_img.pack(side="left", padx=5)

        btn_file = tk.Button(frame_bottom, text="📂 File", command=self.send_file)
        btn_file.pack(side="left", padx=5)



        # Nếu đã nhận danh sách user trước đó thì hiển thị luôn
        if self.pending_users:
            self.update_user_list(self.pending_users)
            self.pending_users = []

    # ------------------- Cập nhật danh sách user online -------------------
    def update_user_list(self, users):
        self.current_users = users

        # If UI not ready yet -> store pending
        if not hasattr(self, "user_list_container"):
            self.pending_users = users
            return

        # Clear and render
        for widget in self.user_list_container.winfo_children():
            widget.destroy()

        for u in users:
            if u == self.username:
                continue

            frame = tk.Frame(self.user_list_container, bg="#e0e0e0", pady=5)
            frame.pack(fill="x", padx=5, pady=2)

            avatar_path = self.user_avatars.get(u, "avatars/default.jpg")
            avatar_img = self.create_circle_avatar(avatar_path, size=36)
            lbl_avatar = tk.Label(frame, image=avatar_img, bg="#e0e0e0")
            lbl_avatar.image = avatar_img
            lbl_avatar.pack(side="left", padx=8)

            lbl_name = tk.Label(frame, text=u, bg="#e0e0e0", font=("Arial", 11))
            lbl_name.pack(side="left", padx=6)

            # Badge số tin nhắn chưa đọc
            count = self.unread_count.get(u, 0)
            if count > 0:
                lbl_notify = tk.Label(frame, text=str(count), fg="white", bg="red", font=("Arial", 9, "bold"))
                lbl_notify.pack(side="right", padx=5)

            # Bind click to the whole row
            frame.bind("<Button-1>", lambda e, user=u: self.select_chat_user(user))
            lbl_avatar.bind("<Button-1>", lambda e, user=u: self.select_chat_user(user))
            lbl_name.bind("<Button-1>", lambda e, user=u: self.select_chat_user(user))

    # ------------------- Chọn người để chat -------------------
    def select_chat_user(self, user):
        self.current_chat_user = user
        self.root.title(f"ChatPy - {self.username} (chat với {user})")

        # Cập nhật header: avatar + tên user
        avatar_path = self.user_avatars.get(user, "avatars/default.jpg")
        avatar_img = self.create_circle_avatar(avatar_path, size=36)
        self.chat_header_avatar.config(image=avatar_img)
        self.chat_header_avatar.image = avatar_img
        self.chat_header_name.config(text=user)

        # Ẩn tất cả frame cũ
        for f in self.chat_frames.values():
            f.pack_forget()

        # Tạo frame mới nếu chưa có
        if user not in self.chat_frames:
            frame = tk.Frame(self.chat_inner, bg="#f5f5f5")
            frame.pack(fill="both", expand=True)
            self.chat_frames[user] = frame
        else:
            self.chat_frames[user].pack(fill="both", expand=True)

        self.messages_frame = self.chat_frames[user]

        # Reset tin nhắn chưa đọc
        self.unread_count[user] = 0
        self.update_user_list(self.current_users)

    # ------------------- Gửi tin nhắn -------------------
    def send_message(self):
        text = self.entry_msg.get().strip()
        if not text:
            return

        if self.current_chat_user:
            # send private message to the selected user
            try:
                self.client.send_private_message(self.current_chat_user, text)
            except Exception:
                # Nếu ChatClient không hỗ trợ send_private_message thì bỏ qua luôn
                pass

            # show locally in the correct chat frame
            self.show_message(self.username, text, self.avatar_path, target_user=self.current_chat_user)

        else:
            # no selected user -> broadcast (if supported)
            try:
                self.client.send_message(text)
            except Exception:
                try:
                    self.client.send(f"MSG|{self.username}|{text}\n")
                except Exception:
                    pass
            # Show in ALL frame
            self.show_message(self.username, text, self.avatar_path, target_user="ALL")

        self.entry_msg.delete(0, tk.END)

    def send_image(self):
        filepath = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])
        if not filepath:
            return

        # đọc file và encode base64
        with open(filepath, "rb") as f:
            data = f.read()
        b64_data = base64.b64encode(data).decode("utf-8")

        target = self.current_chat_user if self.current_chat_user else "ALL"
        try:
            self.client.send(f"IMG|{target}|{Path(filepath).name}|{b64_data}\n")
        except Exception:
            pass

        # hiển thị local luôn
        self.show_image_message(self.username, filepath, target_user=target)

    def show_image_message(self, sender, filepath, target_user=None):
        if target_user is None:
            target_user = sender  # luôn tạo frame theo sender

        # Tạo frame nếu chưa có
        if target_user not in self.chat_frames:
            frame = tk.Frame(self.chat_inner, bg="#f5f5f5")
            frame.pack_forget()  # ẩn đi
            self.chat_frames[target_user] = frame
        frame = self.chat_frames[target_user]

        # Load avatar
        avatar_img = self.create_circle_avatar(
            self.user_avatars.get(sender, "avatars/default.jpg") if sender != self.username else self.avatar_path,
            size=36
        )

        # Outer frame
        outer_frame = tk.Frame(frame, bg="#f5f5f5")
        outer_frame.pack(fill="x", pady=5, padx=10)

        msg_container = tk.Frame(outer_frame, bg="#f5f5f5")
        msg_container.pack(anchor="w" if sender != self.username else "e")

        lbl_avatar = tk.Label(msg_container, image=avatar_img, bg="#f5f5f5")
        lbl_avatar.image = avatar_img
        lbl_avatar.pack(side="left" if sender != self.username else "right", padx=5)

        try:
            img = Image.open(filepath)
            img.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(img)
        except Exception:
            lbl = tk.Label(msg_container, text=f"[Ảnh lỗi: {os.path.basename(filepath)}]", bg="#f0f0f0")
            lbl.pack(side="left")
            return

        lbl_img = tk.Label(msg_container, image=photo, bg="#f0f0f0", cursor="hand2", bd=1, relief="solid")
        lbl_img.image = photo
        lbl_img.pack(side="left" if sender != self.username else "right")
        lbl_img.bind("<Button-1>", lambda e: self.show_full_image(filepath))

        # Luôn update canvas, nếu người nhận đang chat mới cuộn xuống cuối
        self.chat_canvas.update_idletasks()
        if self.current_chat_user == sender:
            self.chat_canvas.yview_moveto(1.0)
        else:
            self.unread_count[sender] = self.unread_count.get(sender, 0) + 1
            self.root.after(0, lambda: self.update_user_list(self.current_users))

    def show_full_image(self, filepath):
        if not os.path.exists(filepath):
            return
        top = tk.Toplevel(self.root)
        top.title("Xem ảnh")
        img = Image.open(filepath)
        photo = ImageTk.PhotoImage(img)
        lbl = tk.Label(top, image=photo)
        lbl.image = photo
        lbl.pack()
    def send_file(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            target = self.current_chat_user if self.current_chat_user else "ALL"
            try:
                self.client.send_file(target, filepath)
            except Exception:
                try:
                    self.client.send(f"FILE|{target}|{os.path.basename(filepath)}\n")
                except Exception:
                    pass
            self.show_message(self.username, f"Đã gửi file: {os.path.basename(filepath)}", self.avatar_path, target_user=target)

    # ------------------- Avatar hình tròn -------------------
    def create_circle_avatar(self, path, size=40):
        if not os.path.exists(path):
            img = Image.new("RGB", (size, size), color="#cccccc")
        else:
            img = Image.open(path).resize((size, size))
        # ensure alpha channel
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        return ImageTk.PhotoImage(img)

    # ------------------- Hiển thị tin nhắn -------------------
    def show_message(self, sender, msg, avatar_path=None, target_user=None):
        if not target_user:
            target_user = self.current_chat_user or "ALL"

        # Tạo frame cho conversation nếu chưa có
        if target_user not in self.chat_frames:
            frame = tk.Frame(self.chat_inner, bg="#f5f5f5")
            frame.pack(fill="both", expand=True)
            self.chat_frames[target_user] = frame

        frame = self.chat_frames[target_user]

        if getattr(self, "messages_frame", None) is frame:
            if not frame.winfo_ismapped():
                frame.pack(fill="both", expand=True)

        # Load avatar
        if avatar_path and os.path.exists(avatar_path):
            avatar_img = self.create_circle_avatar(avatar_path, size=36)
        else:
            avatar_img = self.create_circle_avatar("avatars/default.jpg", size=36)

        # Outer frame cho mỗi tin nhắn
        outer_frame = tk.Frame(frame, bg="#f5f5f5")
        outer_frame.pack(fill="x", pady=5, padx=10)

        # Container cho avatar + bong bóng tin nhắn
        msg_container = tk.Frame(outer_frame, bg="#f5f5f5")
        if sender == self.username:
            msg_container.pack(anchor="e")
        else:
            msg_container.pack(anchor="w")

        # Avatar
        lbl_avatar = tk.Label(msg_container, image=avatar_img, bg="#f5f5f5")
        lbl_avatar.image = avatar_img
        if sender == self.username:
            lbl_avatar.pack(side="right", padx=5)
        else:
            lbl_avatar.pack(side="left", padx=5)

        # Bong bóng tin nhắn
        lbl_msg = tk.Label(
            msg_container,
            text=msg,
            bg="#d1ffd6" if sender == self.username else "#f0f0f0",
            wraplength=400,
            justify="right" if sender == self.username else "left",
            padx=10, pady=6,
            relief="solid", bd=1
        )
        if sender == self.username:
            lbl_msg.pack(side="right")
        else:
            lbl_msg.pack(side="left")

        # Tự cuộn xuống cuối
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    # ------------------- Server trả về -------------------
    def handle_server_message(self, msg):
        # This handler assumes server sends plain strings like:
        # REGISTER_OK, REGISTER_FAIL, LOGIN_OK|avatar_path, LOGIN_FAIL
        # USER_LIST|user1|user2|...
        # PRIVATE|sender|text
        # MSG|sender|text   (broadcast)
        # adapt to your server protocol accordingly

        if msg == "REGISTER_OK":
            self.root.after(0, lambda: [
                messagebox.showinfo("Thành công", "Đăng ký thành công!"),
                self.show_login()
            ])
            return
        if msg == "REGISTER_FAIL":
            self.root.after(0, lambda: messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại!"))
            return

        if msg.startswith("LOGIN_OK"):
            parts = msg.split("|")
            avatar = parts[1] if len(parts) > 1 else "avatars/default.jpg"
            self.avatar_path = avatar
            self.user_avatars[self.username] = avatar   # cập nhật avatar chính mình
            self.root.after(0, self.show_chat)
            return
        if msg == "LOGIN_FAIL":
            self.root.after(0, lambda: messagebox.showerror("Lỗi", "Sai tài khoản hoặc mật khẩu!"))
            return

        if msg.startswith("PRIVATE|"):
            try:
                _, sender, text = msg.split("|", 2)
            except ValueError:
                return  # malformed message, bỏ qua

            # Tạo frame nếu chưa có, nhưng không pack
            if sender not in self.chat_frames:
                frame = tk.Frame(self.chat_inner, bg="#f5f5f5")
                self.chat_frames[sender] = frame
            else:
                frame = self.chat_frames[sender]

            # Lưu message vào frame
            outer_frame = tk.Frame(frame, bg="#f5f5f5")
            outer_frame.pack(fill="x", pady=5, padx=10)
            msg_container = tk.Frame(outer_frame, bg="#f5f5f5")
            msg_container.pack(anchor="w")
            avatar_img = self.create_circle_avatar(self.user_avatars.get(sender, "avatars/default.jpg"), size=36)
            lbl_avatar = tk.Label(msg_container, image=avatar_img, bg="#f5f5f5")
            lbl_avatar.image = avatar_img
            lbl_avatar.pack(side="left", padx=5)
            lbl_msg = tk.Label(
                msg_container,
                text=text,
                bg="#f0f0f0",
                wraplength=400,
                justify="left",
                padx=10, pady=6,
                relief="solid", bd=1
            )
            lbl_msg.pack(side="left")

            # Nếu frame chưa mở, chỉ tăng unread_count
            if self.current_chat_user != sender:
                self.unread_count[sender] = self.unread_count.get(sender, 0) + 1
                self.root.after(0, lambda: self.update_user_list(self.current_users))

        if msg.startswith("MSG|"):
            # broadcast message to ALL
            try:
                _, sender, text = msg.split("|", 2)
            except ValueError:
                self.root.after(0, lambda: self.show_message("Server", msg))
                return
            self.root.after(0, lambda: self.show_message(sender, text, self.user_avatars.get(sender), target_user="ALL"))
            return

        if msg.startswith("USER_LIST|"):
            parts = msg.split("|")[1:]
            users = []
            for p in parts:
                if ":" in p:
                    uname, avatar = p.split(":", 1)
                    users.append(uname)
                    self.user_avatars[uname] = avatar
                else:
                    users.append(p)
                    if p not in self.user_avatars:
                        self.user_avatars[p] = "avatars/default.jpg"
            self.root.after(0, lambda: self.update_user_list(users))
            return

        if msg.startswith("IMG|"):
            try:
                _, sender, filename, b64_data = msg.split("|", 3)
            except ValueError:
                return

            save_dir = Path("downloads")
            save_dir.mkdir(exist_ok=True)
            save_path = save_dir / filename

            data = base64.b64decode(b64_data)
            with open(save_path, "wb") as f:
                f.write(data)

            def show_img():
                # tạo frame nếu chưa có
                if sender not in self.chat_frames:
                    frame = tk.Frame(self.chat_inner, bg="#f5f5f5")
                    self.chat_frames[sender] = frame
                    if self.current_chat_user == sender:
                        frame.pack(fill="both", expand=True)
                else:
                    frame = self.chat_frames[sender]
                    if self.current_chat_user == sender:
                        frame.pack(fill="both", expand=True)

                # **Use the saved local path here, not the original filepath**
                self.show_image_message(sender, save_path, target_user=sender)

            self.root.after(0, show_img)

        if msg.startswith("FILE|"):
            try:
                _, sender, filename, b64_data = msg.split("|", 3)
            except ValueError:
                return

            # Lưu vào bộ nhớ tạm
            if not hasattr(self, "pending_files"):
                self.pending_files = {}
            self.pending_files[(sender, filename)] = b64_data

            def show_file():
                # Container cho message
                outer_frame = tk.Frame(self.chat_frames.get(sender, self.chat_inner), bg="#f5f5f5")
                outer_frame.pack(fill="x", pady=5, padx=10)

                msg_container = tk.Frame(outer_frame, bg="#f5f5f5")
                msg_container.pack(anchor="w")

                # Avatar
                avatar_img = self.create_circle_avatar(self.user_avatars.get(sender, "avatars/default.jpg"), size=36)
                lbl_avatar = tk.Label(msg_container, image=avatar_img, bg="#f5f5f5")
                lbl_avatar.image = avatar_img
                lbl_avatar.pack(side="left", padx=5)

                # Nút tải xuống
                def download_file():
                    save_dir = Path("downloads")
                    save_dir.mkdir(exist_ok=True)
                    save_path = save_dir / filename
                    data = base64.b64decode(self.pending_files[(sender, filename)])
                    with open(save_path, "wb") as f:
                        f.write(data)
                    messagebox.showinfo("Download", f"File {filename} đã lưu tại {save_path}")

                btn_file = tk.Button(
                    msg_container,
                    text=f"📂 {filename} (Tải xuống)",
                    command=download_file,
                    relief="flat",
                    bg="#e6e6e6"
                )
                btn_file.pack(side="left")

            self.root.after(0, show_file)

    # fallback: show raw server text in an "ALL" conversation (or server frame)
        # self.root.after(0, lambda: self.show_message("Server", msg, target_user="ALL"))

    # ------------------- Tiện ích -------------------
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # optional helper to gracefully close client socket if GUI is closed
    def close(self):
        try:
            self.client.close()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    ChatGUI()