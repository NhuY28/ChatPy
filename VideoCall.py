# VideoCall.py
import threading
import cv2
import base64
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import numpy as np
import sounddevice as sd
import queue

class VideoCall:
    def __init__(self, client, target_user, parent=None, samplerate=16000, blocksize=1024):
        self.client = client
        self.target_user = target_user
        self.parent = parent
        self.is_calling = False
        self.cap = None

        # audio
        self.samplerate = samplerate
        self.channels = 1
        self.blocksize = blocksize
        self._play_queue = queue.Queue()

    def start(self):
        self.is_calling = True
        self.win = tk.Toplevel(self.parent)
        self.win.title(f"🎥 Video call: {self.target_user}")
        self.win.geometry("680x560")
        self.win.resizable(False, False)

        self.video_label = tk.Label(self.win)
        self.video_label.pack(pady=10)

        tk.Button(self.win, text="Kết thúc", bg="red", fg="white",
                  font=("Arial", 12, "bold"), command=self.end).pack(pady=10)

        # Khởi động webcam
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Lỗi", "Không mở được camera!")
            self.end()
            return

        # Bắt đầu thu âm và gửi
        threading.Thread(target=self._record_loop, daemon=True).start()

        # Bắt đầu phát audio
        threading.Thread(target=self._play_loop, daemon=True).start()

        # Bắt đầu gửi video frame
        threading.Thread(target=self._send_video, daemon=True).start()

    # --- Thu âm và lưu vào hàng đợi gửi ---
    def _record_loop(self):
        def callback(indata, frames, time_, status):
            if not self.is_calling:
                raise sd.CallbackStop()
            # Mỗi block âm thanh sẽ được tạm giữ, gửi kèm mỗi khung hình
            self._last_audio = base64.b64encode(indata.astype(np.float32).tobytes()).decode("utf-8")

        self._last_audio = ""
        with sd.InputStream(samplerate=self.samplerate,
                            channels=self.channels,
                            dtype='float32',
                            blocksize=self.blocksize,
                            callback=callback):
            while self.is_calling:
                sd.sleep(50)

    # --- Gửi video + âm thanh ---
    def _send_video(self):
        while self.is_calling and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.resize(frame, (320, 240))
            _, buffer = cv2.imencode('.jpg', frame)
            b64_video = base64.b64encode(buffer).decode('utf-8')

            b64_audio = getattr(self, "_last_audio", "")

            try:
                self.client.send(f"VIDEO_STREAM|{self.target_user}|{b64_video}|{b64_audio}\n")
            except Exception as e:
                print("send video error:", e)
                break

            # Hiển thị video local
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(Image.fromarray(img))
            self.video_label.config(image=img)
            self.video_label.image = img

            self.win.after(50)

    # --- Nhận video + audio từ người kia ---
    def receive_video(self, b64_video, b64_audio):
        try:
            # Xử lý video
            frame_data = base64.b64decode(b64_video)
            np_arr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = ImageTk.PhotoImage(Image.fromarray(frame))
                self.video_label.config(image=frame)
                self.video_label.image = frame

            # Xử lý audio
            if b64_audio:
                audio_bytes = base64.b64decode(b64_audio)
                audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
                audio_array = audio_array.reshape(-1, self.channels)
                self._play_queue.put(audio_array)
        except Exception as e:
            print("receive video error:", e)

    # --- Phát lại âm thanh ---
    def _play_loop(self):
        try:
            with sd.OutputStream(samplerate=self.samplerate,
                                 channels=self.channels,
                                 dtype='float32') as stream:
                while self.is_calling:
                    try:
                        audio = self._play_queue.get(timeout=0.1)
                        stream.write(audio)
                    except queue.Empty:
                        continue
        except Exception as e:
            print("play loop error:", e)

    # --- Kết thúc ---
    def end(self):
        self.is_calling = False
        if self.cap:
            self.cap.release()
        try:
            self.client.send(f"VIDEO_END|{self.target_user}\n")
        except:
            pass
        if hasattr(self, "win"):
            self.win.destroy()
