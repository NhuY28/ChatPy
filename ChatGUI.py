import os
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from ChatClient import ChatClient


class ChatGUI:
    def __init__(self, root=None):
        # Nếu root không truyền vào => tạo Tk() chính
        self.is_main = False
        if root is None:
            self.root = tk.Tk()
            self.is_main = True
        else:
            self.root = tk.Toplevel(root)

        self.root.title("ChatPy - Đăng nhập/Đăng ký")
        self.root.geometry("600x500")
        self.root.config(bg="#f5f5f5")

        self.client = ChatClient()
        self.username = None
        self.avatar_path = None


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

        # Label chứa avatar (mặc định là icon folder/camera)
        self.avatar_image = ImageTk.PhotoImage(Image.open("folder.png").resize((20, 20)))
        self.avatar_label = tk.Label(self.avatar_frame, image=self.avatar_image, bg="#f5f5f5", cursor="hand2")
        self.avatar_label.pack()

        # Bind click để chọn ảnh
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
        tk.Label(frame_confirm,  image=self.icon_pass, font=("Arial", 14), bg="#f5f5f5").pack(side="left", padx=5)
        self.entry_confirm = tk.Entry(frame_confirm, font=("Arial", 16), show="*")
        self.entry_confirm.pack(side="left", fill="x", expand=True)

        # Button đăng ký
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
        avatar = self.avatar_path if self.avatar_path else "default.png"

        self.client.connect()
        self.client.on_message = self.handle_server_message
        self.client.register(user, pw, avatar)


    def choose_avatar(self):
        file = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if file:
            img = Image.open(file).resize((90, 90))
            self.avatar_image = ImageTk.PhotoImage(img)
            self.avatar_label.config(image=self.avatar_image)
            self.avatar_path = file   # Lưu đường dẫn để dùng khi đăng ký



    # ------------------- ĐĂNG NHẬP -------------------
    def show_login(self):
        self.clear_window()

        lbl_title = tk.Label(self.root, text="ĐĂNG NHẬP",
                             font=("Arial", 18, "bold"), bg="#f5f5f5", fg="#333")
        lbl_title.pack(pady=20)

        # Username
        frame_user = tk.Frame(self.root, bg="#f5f5f5")
        frame_user.pack(pady=10, padx=40, fill="x")
        tk.Label(frame_user, image=self.icon_user, bg="#f5f5f5").pack(side="left", padx=5)
        self.login_user = tk.Entry(frame_user, font=("Arial", 12))
        self.login_user.pack(side="left", fill="x", expand=True)

        # Password
        frame_pass = tk.Frame(self.root, bg="#f5f5f5")
        frame_pass.pack(pady=10, padx=40, fill="x")
        tk.Label(frame_pass, image=self.icon_pass, bg="#f5f5f5").pack(side="left", padx=5)
        self.login_pass = tk.Entry(frame_pass, font=("Arial", 12), show="*")
        self.login_pass.pack(side="left", fill="x", expand=True)

        # Button đăng nhập
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

        # Hiển thị avatar user (nếu có)
        if self.avatar_path and os.path.exists(self.avatar_path):
            img = Image.open(self.avatar_path).resize((50, 50))
            self.chat_avatar = ImageTk.PhotoImage(img)
            tk.Label(self.root, image=self.chat_avatar).pack(pady=5)

        self.text_area = tk.Text(self.root, state="disabled",
                                 wrap="word", bg="white")
        self.text_area.pack(padx=10, pady=10, fill="both", expand=True)

        frame_bottom = tk.Frame(self.root)
        frame_bottom.pack(fill="x", padx=10, pady=5)

        self.entry_msg = tk.Entry(frame_bottom, font=("Arial", 12))
        self.entry_msg.pack(side="left", fill="x", expand=True, padx=5)

        btn_send = tk.Button(frame_bottom, text="Gửi", command=self.send_message,
                             bg="#6a5acd", fg="white")
        btn_send.pack(side="left", padx=5)

        btn_img = tk.Button(frame_bottom, text="📷 Ảnh", command=self.send_image)
        btn_img.pack(side="left", padx=5)

        btn_file = tk.Button(frame_bottom, text="📂 File", command=self.send_file)
        btn_file.pack(side="left", padx=5)

    def send_message(self):
        text = self.entry_msg.get()
        if text.strip():
            self.client.send_message(self.username, text)
            self.entry_msg.delete(0, tk.END)

    def send_image(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])
        if filepath:
            self.client.send_image(self.username, filepath)

    def send_file(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            self.client.send_file(self.username, filepath)

    def show_message(self, msg):
        self.text_area.config(state="normal")
        self.text_area.insert("end", msg + "\n")
        self.text_area.config(state="disabled")
        self.text_area.see("end")

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
                self.avatar_path = parts[1]   # lấy avatar từ DB
            self.root.after(0, lambda: [
                messagebox.showinfo("Thành công", "Đăng nhập thành công!"),
                self.show_chat()
            ])
        elif msg == "LOGIN_FAIL":
            self.root.after(0, lambda: messagebox.showerror("Lỗi", "Sai tài khoản hoặc mật khẩu!"))

        else:
            self.root.after(0, lambda: self.show_message(msg))


    # ------------------- TIỆN ÍCH -------------------
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    ChatGUI()
