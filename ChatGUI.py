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

        self.root.title("ChatPy - Đăng nhập/Đăng ký")
        self.root.geometry("800x500")
        self.root.config(bg="#f5f5f5")

        self.client = ChatClient()
        self.username = None
        self.avatar_path = None
        self.user_avatars = {}

        # --- Load icon ảnh ---
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

        # --- AVATAR ---
        self.avatar_frame = tk.Frame(self.root, bg="#f5f5f5")
        self.avatar_frame.pack(pady=10)

        self.avatar_image = ImageTk.PhotoImage(Image.open("folder.png").resize((20, 20)))
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
        tk.Label(frame_confirm, image=self.icon_pass, font=("Arial", 14), bg="#f5f5f5").pack(side="left", padx=5)
        self.entry_confirm = tk.Entry(frame_confirm, font=("Arial", 16), show="*")
        self.entry_confirm.pack(side="left", fill="x", expand=True)

        btn_register = tk.Button(self.root, text="Đăng ký", bg="#6a5acd", fg="white",
                                 font=("Arial", 12, "bold"),
                                 command=self.do_register)
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
        self.login_user = tk.Entry(frame_user, font=("Arial", 12))
        self.login_user.pack(side="left", fill="x", expand=True)

        frame_pass = tk.Frame(self.root, bg="#f5f5f5")
        frame_pass.pack(pady=10, padx=40, fill="x")
        tk.Label(frame_pass, image=self.icon_pass, bg="#f5f5f5").pack(side="left", padx=5)
        self.login_pass = tk.Entry(frame_pass, font=("Arial", 12), show="*")
        self.login_pass.pack(side="left", fill="x", expand=True)

        btn_login = tk.Button(self.root, text="Đăng nhập", bg="#228B22", fg="white",
                              font=("Arial", 12, "bold"),
                              command=self.do_login)
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
    def show_chat(self):
        self.clear_window()
        self.root.title(f"ChatPy - {self.username}")

        main_frame = tk.Frame(self.root, bg="#f5f5f5")
        main_frame.pack(fill="both", expand=True)

        # Danh sách user online
        self.user_frame = tk.Frame(main_frame, width=180, bg="#e0e0e0")
        self.user_frame.pack(side="left", fill="y", padx=5, pady=5)
        tk.Label(self.user_frame, text="Online", bg="#e0e0e0", font=("Arial", 12, "bold")).pack(pady=5)
        self.user_listbox = tk.Listbox(self.user_frame)
        self.user_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Khung chat chính
        chat_frame = tk.Frame(main_frame, bg="#f5f5f5")
        chat_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

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

        # Ô nhập tin nhắn
        frame_bottom = tk.Frame(self.root)
        frame_bottom.pack(fill="x", padx=5, pady=5)

        self.entry_msg = tk.Entry(frame_bottom, font=("Arial", 12))
        self.entry_msg.pack(side="left", fill="x", expand=True, padx=5)

        btn_send = tk.Button(frame_bottom, text="Gửi", command=self.send_message,
                             bg="#6a5acd", fg="white")
        btn_send.pack(side="left", padx=5)

        btn_img = tk.Button(frame_bottom, text="📷 Ảnh", command=self.send_image)
        btn_img.pack(side="left", padx=5)

        btn_file = tk.Button(frame_bottom, text="📂 File", command=self.send_file)
        btn_file.pack(side="left", padx=5)

    # ------------------- Gửi tin nhắn -------------------
    def send_message(self):
        text = self.entry_msg.get()
        if text.strip():
            self.client.send_message(self.username, text)
            self.show_message(self.username, text, self.avatar_path)
            self.entry_msg.delete(0, tk.END)

    def send_image(self):
        filepath = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])
        if filepath:
            self.client.send_image(self.username, filepath)
            self.show_message(self.username, f"Đã gửi ảnh: {os.path.basename(filepath)}", self.avatar_path)

    def send_file(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            self.client.send_file(self.username, filepath)
            self.show_message(self.username, f"Đã gửi file: {os.path.basename(filepath)}", self.avatar_path)

    # ------------------- Tạo avatar hình tròn -------------------
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
        # Frame bọc ngang đủ width
        outer_frame = tk.Frame(self.messages_frame, bg="#f5f5f5")
        outer_frame.pack(fill="x", pady=10)

        # Frame chứa avatar + bong bóng
        msg_frame = tk.Frame(outer_frame, bg="#f5f5f5")

        if avatar_path and os.path.exists(avatar_path):
            avatar_img = self.create_circle_avatar(avatar_path, size=40)
        else:
            avatar_img = self.create_circle_avatar("avatars/default.jpg", size=40)

        lbl_avatar = tk.Label(msg_frame, image=avatar_img, bg="#f5f5f5")
        lbl_avatar.image = avatar_img

        if sender == self.username:
            # Tin nhắn của mình (căn phải)
            lbl_msg = tk.Label(msg_frame, text=msg, bg="#d1ffd6", wraplength=300,
                               justify="left", padx=10, pady=5, relief="solid", bd=1)
            lbl_msg.pack(side="right", padx=5)
            lbl_avatar.pack(side="right")
            lbl_name = tk.Label(msg_frame, text=sender, font=("Arial", 9, "bold"), bg="#f5f5f5")
            lbl_name.pack(anchor="e")
            msg_frame.pack(anchor="e", padx=20)

        else:
            # Tin nhắn người khác (căn trái)
            lbl_msg = tk.Label(msg_frame, text=msg, bg="#f0f0f0", wraplength=300,
                               justify="left", padx=10, pady=5, relief="solid", bd=1)
            lbl_avatar.pack(side="left")
            lbl_msg.pack(side="left", padx=5)
            lbl_name = tk.Label(msg_frame, text=sender, font=("Arial", 9, "bold"), bg="#f5f5f5")
            lbl_name.pack(anchor="w")
            msg_frame.pack(anchor="w", padx=20)

        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    # ------------------- XỬ LÝ SERVER TRẢ VỀ -------------------
    def handle_server_message(self, msg):
        if msg == "REGISTER_OK":
            self.root.after(0, lambda: [
                messagebox.showinfo("Thành công", "Đăng ký thành công!"),
                self.show_login()
            ])
        elif msg == "REGISTER_FAIL":
            self.root.after(0, lambda: messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại!"))

        elif msg.startswith("LOGIN_OK"):
            parts = msg.split("|")
            if len(parts) > 1:
                self.avatar_path = parts[1]
                self.user_avatars[self.username] = self.avatar_path
            self.root.after(0, lambda: [
                messagebox.showinfo("Thành công", "Đăng nhập thành công!"),
                self.show_chat()
            ])
        elif msg.startswith("MSG|"):
            parts = msg.split("|", 2)
            if len(parts) == 3:
                sender, content = parts[1], parts[2]
                avatar = self.user_avatars.get(sender, "avatars/default.jpg")
                self.root.after(0, lambda: self.show_message(sender, content, avatar))
        elif msg.startswith("USER_AVATAR|"):
            parts = msg.split("|")
            if len(parts) == 3:
                self.user_avatars[parts[1]] = parts[2]
        else:
            self.root.after(0, lambda: self.show_message("Server", msg))

    # ------------------- TIỆN ÍCH -------------------
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    ChatGUI()
