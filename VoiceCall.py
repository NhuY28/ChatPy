# VoiceCall.py
import threading
import sounddevice as sd
import numpy as np
import base64
import tkinter as tk
from tkinter import messagebox

class VoiceCall:
    def __init__(self, client, target_user, parent=None, samplerate=16000, blocksize=1024):
        """
        client: ChatClient instance
        target_user: username to call
        parent: parent tk window (optional) để hiện popup
        """
        self.client = client
        self.target_user = target_user
        self.parent = parent
        self.samplerate = samplerate
        self.channels = 1
        self.blocksize = blocksize
        self.is_calling = False
        self._stream = None

    def start(self):
        """Mở cửa sổ gọi và bắt đầu thu âm + gửi"""
        if not self.target_user:
            messagebox.showwarning("Gọi thoại", "Chưa chọn người để gọi!", parent=self.parent)
            return

        self.is_calling = True
        self.win = tk.Toplevel(self.parent) if self.parent else tk.Toplevel()
        self.win.title(f"📞 Gọi: {self.target_user}")
        self.win.geometry("300x160")
        self.win.resizable(False, False)

        lbl = tk.Label(self.win, text=f"📞 Đang gọi {self.target_user}...", font=("Arial", 12))
        lbl.pack(pady=16)

        btn_end = tk.Button(self.win, text="Kết thúc", bg="#f44336", fg="white",
                            font=("Arial", 11, "bold"), width=12, command=self.end)
        btn_end.pack(pady=8)

        # Khởi chạy luồng thu âm
        self._t_record = threading.Thread(target=self._record_loop, daemon=True)
        self._t_record.start()

    def _record_loop(self):
        """Ghi và gửi từng block bằng float32 little-endian"""
        try:
            def callback(indata, frames, time_, status):
                if not self.is_calling:
                    raise sd.CallbackStop()
                # indata là float32 shaped (frames, channels)
                try:
                    # encode raw bytes then base64
                    b = indata.astype(np.float32).tobytes()
                    b64 = base64.b64encode(b).decode("utf-8")
                    # gửi: CALL_STREAM|target|b64\n
                    # client.send_call_stream method (sẽ thêm ở ChatClient)
                    try:
                        self.client.send_call_stream(self.target_user, b64)
                    except Exception:
                        # fall back generic send
                        self.client.send(f"CALL_STREAM|{self.target_user}|{b64}<END>\n")
                except Exception as e:
                    print("voice send error:", e)

            with sd.InputStream(samplerate=self.samplerate, channels=self.channels,
                                dtype='float32', blocksize=self.blocksize, callback=callback):
                while self.is_calling:
                    sd.sleep(100)
        except Exception as e:
            print("record loop error:", e)
            # tự dừng khi lỗi
            self.is_calling = False

    def receive_audio(self, b64_data):
        """Phát dữ liệu nhận về (được gọi bởi ChatGUI khi nhận CALL_STREAM từ server)."""
        try:
            audio_bytes = base64.b64decode(b64_data)
            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
            # sounddevice: play non-blocking
            sd.play(audio_array, self.samplerate)
        except Exception as e:
            print("play error:", e)

    def end(self):
        """Kết thúc cuộc gọi"""
        self.is_calling = False
        try:
            self.win.destroy()
        except Exception:
            pass
        # optionally send end notification (not required)
        try:
            self.client.send(f"CALL_END|{self.target_user}\n")
        except Exception:
            pass
