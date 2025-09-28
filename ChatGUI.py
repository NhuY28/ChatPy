import os
import tkinter as tk
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

        # --- Load icon ---
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

        self.client.connect()
        self.client.on_message = self.handle_server_message
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
            # --- Header ---
        self.header_label = tk.Label(chat_frame, text="Chọn người để chat",
                                     font=("Arial", 12, "bold"), bg="#ddd", anchor="w")
        self.header_label.pack(fill="x")

        # Danh sách user online (left)
        self.user_frame = tk.Frame(main_frame, width=200, bg="#e0e0e0")
        self.user_frame.pack(side="left", fill="y")
        tk.Label(self.user_frame, text="Online", bg="#e0e0e0",
                 font=("Arial", 12, "bold")).pack(pady=5)

        # Container chứa các user online (dynamic)
        self.user_list_container = tk.Frame(self.user_frame, bg="#e0e0e0")
        self.user_list_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Khung chat (right)
        chat_frame = tk.Frame(main_frame, bg="#f5f5f5")
        chat_frame.pack(side="right", fill="both", expand=True)

        self.chat_canvas = tk.Canvas(chat_frame, bg="#f5f5f5", highlightthickness=0)
        self.chat_scrollbar = tk.Scrollbar(chat_frame, orient="vertical", command=self.chat_canvas.yview)
        self.chat_canvas.configure(yscrollcommand=self.chat_scrollbar.set)

        self.chat_scrollbar.pack(side="right", fill="y")
        self.chat_canvas.pack(side="left", fill="both", expand=True)

        self.chat_inner = tk.Frame(self.chat_canvas, bg="#f5f5f5")
        self.chat_canvas.create_window((0, 0), window=self.chat_inner, anchor="nw")
        self.chat_inner.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))

        # Frame chứa tin nhắn
        self.messages_frame = tk.Frame(self.chat_inner, bg="#f5f5f5")
        self.messages_frame.pack(fill="both", expand=True)

        # Ô nhập tin nhắn ở dưới cùng
        frame_bottom = tk.Frame(self.root, bg="#ddd")
        frame_bottom.pack(fill="x", padx=5, pady=5)

        self.entry_msg = tk.Entry(frame_bottom, font=("Arial", 12))
        self.entry_msg.pack(side="left", fill="x", expand=True, padx=5)

        btn_send = tk.Button(frame_bottom, text="Gửi", command=self.send_message, bg="#6a5acd", fg="white")
        btn_send.pack(side="left", padx=5)

        btn_img = tk.Button(frame_bottom, text="📷 Ảnh", command=self.send_image)
        btn_img.pack(side="left", padx=5)

        btn_file = tk.Button(frame_bottom, text="📂 File", command=self.send_file)
        btn_file.pack(side="left", padx=5)

        # nếu có pending_users (server đã gửi trước đó), render bây giờ
        if self.pending_users:
            self.update_user_list(self.pending_users)
            self.pending_users = []

    # ------------------- Cập nhật danh sách user online -------------------
    def update_user_list(self, users):
        # lưu luôn danh sách hiện tại
        self.current_users = users

        # Nếu UI chưa tạo (user_list_container chưa tồn tại) -> lưu pending và return
        if not hasattr(self, "user_list_container"):
            self.pending_users = users
            return

        # Xóa cũ rồi render lại
        for widget in self.user_list_container.winfo_children():
            widget.destroy()

        for u in users:
            if u == self.username:
                continue  # Không hiển thị chính mình

            frame = tk.Frame(self.user_list_container, bg="#e0e0e0", pady=5)
            frame.pack(fill="x", padx=5, pady=2)

            avatar_path = self.user_avatars.get(u, "avatars/default.jpg")
            avatar_img = self.create_circle_avatar(avatar_path, size=36)
            lbl_avatar = tk.Label(frame, image=avatar_img, bg="#e0e0e0")
            lbl_avatar.image = avatar_img
            lbl_avatar.pack(side="left", padx=8)

            lbl_name = tk.Label(frame, text=u, bg="#e0e0e0", font=("Arial", 11))
            lbl_name.pack(side="left", padx=6)

            # Khi nhấn vào user thì chọn chat với họ
            frame.bind("<Button-1>", lambda e, user=u: self.select_chat_user(user))
            lbl_avatar.bind("<Button-1>", lambda e, user=u: self.select_chat_user(user))
            lbl_name.bind("<Button-1>", lambda e, user=u: self.select_chat_user(user))

    # ------------------- Chọn người để chat -------------------
    def select_chat_user(self, user):
        self.current_chat_user = user
        self.root.title(f"ChatPy - {self.username} (chat với {user})")
        self.header_label.config(text=f"{user} - Đang hoạt động")


    # ------------------- Gửi tin nhắn -------------------
    def send_message(self):
        text = self.entry_msg.get().strip()
        if not text:
            return

        # Nếu có chat riêng
        if self.current_chat_user:
            self.client.send_private_message(self.current_chat_user, text)
        else:
            self.client.send_message("ALL", text)

        self.show_message(self.username, text, self.avatar_path)
        self.entry_msg.delete(0, tk.END)



    def send_image(self):
        filepath = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])
        if filepath:
            target = self.current_chat_user if self.current_chat_user else self.username
            self.client.send_image(target, filepath)
            self.show_message(self.username, f"Đã gửi ảnh: {os.path.basename(filepath)}", self.avatar_path)

    def send_file(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            target = self.current_chat_user if self.current_chat_user else self.username
            self.client.send_file(target, filepath)
            self.show_message(self.username, f"Đã gửi file: {os.path.basename(filepath)}", self.avatar_path)

    # ------------------- Avatar hình tròn -------------------
    def create_circle_avatar(self, path, size=40):
        if not os.path.exists(path):
            img = Image.new("RGB", (size, size), color="#cccccc")
        else:
            img = Image.open(path).resize((size, size))
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        return ImageTk.PhotoImage(img)

    # ------------------- Hiển thị tin nhắn -------------------
    def show_message(self, sender, msg, avatar_path=None):
        # Nếu messages_frame chưa khởi tạo (chưa vào chat) thì bỏ qua
        if not hasattr(self, "messages_frame"):
            return

        outer_frame = tk.Frame(self.messages_frame, bg="#f5f5f5")
        outer_frame.pack(fill="x", pady=5)

        msg_frame = tk.Frame(outer_frame, bg="#f5f5f5")

        # Avatar
        if avatar_path and os.path.exists(avatar_path):
            avatar_img = self.create_circle_avatar(avatar_path, size=40)
        else:
            avatar_img = self.create_circle_avatar("avatars/default.jpg", size=40)

        lbl_avatar = tk.Label(msg_frame, image=avatar_img, bg="#f5f5f5")
        lbl_avatar.image = avatar_img

        # Bong bóng
        bubble_color = "#d1ffd6" if sender == self.username else "#f0f0f0"
        lbl_msg = tk.Label(
            msg_frame, text=msg, bg=bubble_color, wraplength=500,
            justify="left", padx=10, pady=5, relief="solid", bd=1
        )

        lbl_name = tk.Label(msg_frame, text=sender, font=("Arial", 9, "bold"), bg="#f5f5f5")

        if sender == self.username:
            lbl_name.pack(anchor="e")
            lbl_msg.pack(side="right", padx=5)
            lbl_avatar.pack(side="right")
            msg_frame.pack(anchor="e", padx=10)
        else:
            lbl_name.pack(anchor="w")
            lbl_avatar.pack(side="left")
            lbl_msg.pack(side="left", padx=5)
            msg_frame.pack(anchor="w", padx=10)

        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    # ------------------- Server trả về -------------------
    def handle_server_message(self, msg):
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
            self.root.after(0, self.show_chat)
            return
        if msg == "LOGIN_FAIL":
            self.root.after(0, lambda: messagebox.showerror("Lỗi", "Sai tài khoản hoặc mật khẩu!"))
            return

        if msg.startswith("MSG|"):
            _, sender, text = msg.split("|", 2)
            self.root.after(0, lambda: self.show_message(sender, text, self.user_avatars.get(sender)))
            return

        if msg.startswith("USER_LIST|"):
            parts = msg.split("|")[1:]
            self.root.after(0, lambda: self.update_user_list(parts))
            return


        # fallback: show raw server text
        self.root.after(0, lambda: self.show_message("Server", msg))

    # ------------------- Tiện ích -------------------
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    ChatGUI()
