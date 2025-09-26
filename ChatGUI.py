import tkinter as tk
from tkinter import messagebox

class ChatGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Signup Form")
        self.root.geometry("600x500")
        self.root.config(bg="#f5f5f5")

        self.show_register()
        self.root.mainloop()

    def show_register(self):
        self.clear_window()

        # --- Title ---
        lbl_title = tk.Label(self.root, text="TẠO TÀI KHOẢN", font=("Arial", 16, "bold"), bg="#f5f5f5")
        lbl_title.pack(pady=20)

        # Load icons (nếu có file ảnh)
        try:
            self.icon_user = tk.PhotoImage(file="username.png").subsample(20, 20)
            self.icon_pass = tk.PhotoImage(file="password.png").subsample(20, 20)
        except:
            self.icon_user = None
            self.icon_pass = None

        # --- Username field ---
        frame_user = tk.Frame(self.root, bg="white", highlightthickness=1, highlightbackground="#ccc")
        frame_user.pack(pady=10, padx=40, fill="x")

        lbl_user = tk.Label(frame_user, text="Tên đăng nhập", font=("Arial", 9), bg="white", anchor="w")
        lbl_user.pack(fill="x", padx=8, pady=(4,0))

        inner_user = tk.Frame(frame_user, bg="white")
        inner_user.pack(fill="x", padx=5, pady=5)

        if self.icon_user:
            lbl_icon = tk.Label(inner_user, image=self.icon_user, bg="white")
            lbl_icon.pack(side="left", padx=5)

        self.entry_user = tk.Entry(inner_user, font=("Arial", 12), bd=0, bg="white")
        self.entry_user.pack(side="left", fill="x", expand=True, padx=5)

        # --- Password field ---
        frame_pass = tk.Frame(self.root, bg="white", highlightthickness=1, highlightbackground="#ccc")
        frame_pass.pack(pady=10, padx=40, fill="x")

        lbl_pass = tk.Label(frame_pass, text="Mật khẩu", font=("Arial", 9), bg="white", anchor="w")
        lbl_pass.pack(fill="x", padx=8, pady=(4,0))

        inner_pass = tk.Frame(frame_pass, bg="white")
        inner_pass.pack(fill="x", padx=5, pady=5)

        if self.icon_pass:
            lbl_icon = tk.Label(inner_pass, image=self.icon_pass, bg="white")
            lbl_icon.pack(side="left", padx=5)

        self.entry_pass = tk.Entry(inner_pass, font=("Arial", 12), bd=0, bg="white", show="*")
        self.entry_pass.pack(side="left", fill="x", expand=True, padx=5)

        # --- Confirm Password field ---
        frame_confirm = tk.Frame(self.root, bg="white", highlightthickness=1, highlightbackground="#ccc")
        frame_confirm.pack(pady=10, padx=40, fill="x")

        lbl_confirm = tk.Label(frame_confirm, text="Xác nhận mật khẩu", font=("Arial", 9), bg="white", anchor="w")
        lbl_confirm.pack(fill="x", padx=8, pady=(4,0))

        inner_confirm = tk.Frame(frame_confirm, bg="white")
        inner_confirm.pack(fill="x", padx=5, pady=5)

        if self.icon_pass:
            lbl_icon = tk.Label(inner_confirm, image=self.icon_pass, bg="white")
            lbl_icon.pack(side="left", padx=5)

        self.entry_confirm = tk.Entry(inner_confirm, font=("Arial", 12), bd=0, bg="white", show="*")
        self.entry_confirm.pack(side="left", fill="x", expand=True, padx=5)

        # --- Button ---
        btn_register = tk.Button(self.root, text="Đăng ký", bg="#6a5acd", fg="white",
                                 font=("Arial", 12, "bold"), relief="flat", padx=20, pady=10)
        btn_register.pack(pady=20)

        # --- Link ---
        lbl_login = tk.Label(self.root, text="Bạn đã có tài khoản? Đăng nhập ngay",
                             fg="red", bg="#f5f5f5", cursor="hand2", font=("Arial", 10, "underline"))
        lbl_login.pack()
        lbl_login.bind("<Button-1>", lambda e: self.show_login())

# Login Form
    def show_login(self):
        self.clear_window()

        lbl_title = tk.Label(self.root, text="ĐĂNG NHẬP", font=("Arial", 16, "bold"), bg="#f5f5f5")
        lbl_title.pack(pady=20)

        # Username field
        frame_user = tk.Frame(self.root, bg="white", highlightthickness=1, highlightbackground="#ccc")
        frame_user.pack(pady=10, padx=40, fill="x")

        lbl_user = tk.Label(frame_user, text="Tên đăng nhập", font=("Arial", 9), bg="white", anchor="w")
        lbl_user.pack(fill="x", padx=8, pady=(4,0))

        inner_user = tk.Frame(frame_user, bg="white")
        inner_user.pack(fill="x", padx=5, pady=5)

        if self.icon_user:
            lbl_icon = tk.Label(inner_user, image=self.icon_user, bg="white")
            lbl_icon.pack(side="left", padx=5)

        self.login_user = tk.Entry(inner_user, font=("Arial", 12), bd=0, bg="white")
        self.login_user.pack(side="left", fill="x", expand=True, padx=5)

        # Password field
        frame_pass = tk.Frame(self.root, bg="white", highlightthickness=1, highlightbackground="#ccc")
        frame_pass.pack(pady=10, padx=40, fill="x")

        lbl_pass = tk.Label(frame_pass, text="Mật khẩu", font=("Arial", 9), bg="white", anchor="w")
        lbl_pass.pack(fill="x", padx=8, pady=(4,0))

        inner_pass = tk.Frame(frame_pass, bg="white")
        inner_pass.pack(fill="x", padx=5, pady=5)

        if self.icon_pass:
            lbl_icon = tk.Label(inner_pass, image=self.icon_pass, bg="white")
            lbl_icon.pack(side="left", padx=5)

        self.login_pass = tk.Entry(inner_pass, font=("Arial", 12), bd=0, bg="white", show="*")
        self.login_pass.pack(side="left", fill="x", expand=True, padx=5)

        # Button
        btn_login = tk.Button(self.root, text="Đăng nhập", bg="#228B22", fg="white",
                              font=("Arial", 12, "bold"), relief="flat", padx=20, pady=10)
        btn_login.pack(pady=20)

        # Link
        lbl_register = tk.Label(self.root, text="Chưa có tài khoản? Đăng ký ngay",
                                fg="blue", bg="#f5f5f5", cursor="hand2", font=("Arial", 10, "underline"))
        lbl_register.pack()
        lbl_register.bind("<Button-1>", lambda e: self.show_register())

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    ChatGUI()
