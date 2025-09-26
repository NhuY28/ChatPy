import tkinter as tk
from tkinter import messagebox, filedialog
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

        self.show_register()

        if self.is_main:
            self.root.mainloop()

    # ------------------- ĐĂNG KÝ -------------------
    def show_register(self):
        self.clear_window()

        lbl_title = tk.Label(self.root, text="TẠO TÀI KHOẢN",
                             font=("Arial", 16, "bold"), bg="#f5f5f5")
        lbl_title.pack(pady=20)

        self.entry_user = tk.Entry(self.root, font=("Arial", 12))
        self.entry_user.pack(pady=10)

        self.entry_pass = tk.Entry(self.root, font=("Arial", 12), show="*")
        self.entry_pass.pack(pady=10)

        self.entry_confirm = tk.Entry(self.root, font=("Arial", 12), show="*")
        self.entry_confirm.pack(pady=10)

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
        self.client.connect()
        self.client.on_message = self.handle_server_message
        self.client.register(user, pw)

    # ------------------- ĐĂNG NHẬP -------------------
    def show_login(self):
        self.clear_window()

        lbl_title = tk.Label(self.root, text="ĐĂNG NHẬP",
                             font=("Arial", 16, "bold"), bg="#f5f5f5")
        lbl_title.pack(pady=20)

        self.login_user = tk.Entry(self.root, font=("Arial", 12))
        self.login_user.pack(pady=10)

        self.login_pass = tk.Entry(self.root, font=("Arial", 12), show="*")
        self.login_pass.pack(pady=10)

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

        elif msg == "LOGIN_OK":
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
