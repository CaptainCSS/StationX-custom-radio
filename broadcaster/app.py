import tkinter as tk
from tkinter import ttk, messagebox
import pyaudio
import socketio
import threading
import numpy as np

# Audio settings
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

class BroadcasterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Radio Broadcaster")
        self.root.geometry("500x500")

        self.sio = socketio.Client()
        self.p = pyaudio.PyAudio()
        self.is_streaming = False
        self.stream_thread = None

        self.music_stream = None
        self.mic_stream = None

        self.active_requests = {}

        self.setup_ui()
        self.setup_socketio()
        
        self.setup_requests_window()
        
        # DUMMY TEST DATA
        self.root.after(2000, self.inject_dummy_request)

    def inject_dummy_request(self):
        dummy = {
            'id': 999,
            'username': 'Test User',
            'time': '12:00 PM',
            'song': 'Test Song',
            'artist': 'Test Artist'
        }
        self.render_request(dummy)

    def get_input_devices(self):
        info = self.p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        devices = []
        for i in range(0, numdevices):
            if (self.p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                name = self.p.get_device_info_by_host_api_device_index(0, i).get('name')
                devices.append(f"{i}: {name}")
        return devices

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')

        pads = {'padx': 10, 'pady': 10}

        # Connection Frame
        conn_frame = ttk.LabelFrame(self.root, text="Server Connection")
        conn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(conn_frame, text="Server URL:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.server_url = tk.StringVar(value="http://localhost:3000")
        ttk.Entry(conn_frame, textvariable=self.server_url, width=30).grid(row=0, column=1, padx=5, pady=5)

        self.btn_connect = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.btn_connect.grid(row=0, column=2, padx=5, pady=5)

        # Devices Frame
        dev_frame = ttk.LabelFrame(self.root, text="Audio Devices")
        dev_frame.pack(fill="x", padx=10, pady=10)

        devices = self.get_input_devices()

        ttk.Label(dev_frame, text="Music Source:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.music_device = ttk.Combobox(dev_frame, values=devices, state="readonly", width=40)
        self.music_device.grid(row=0, column=1, padx=5, pady=5)
        if devices: self.music_device.current(0)

        ttk.Label(dev_frame, text="Mic Source:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.mic_device = ttk.Combobox(dev_frame, values=devices, state="readonly", width=40)
        self.mic_device.grid(row=1, column=1, padx=5, pady=5)
        if devices: self.mic_device.current(0)

        # Controls Frame
        ctrl_frame = ttk.LabelFrame(self.root, text="Streaming Controls")
        ctrl_frame.pack(fill="x", padx=10, pady=10)

        self.stream_mode = tk.StringVar(value="both")
        ttk.Radiobutton(ctrl_frame, text="Music Only", variable=self.stream_mode, value="music").grid(row=0, column=0, padx=5, pady=5)
        ttk.Radiobutton(ctrl_frame, text="Mic Only", variable=self.stream_mode, value="mic").grid(row=0, column=1, padx=5, pady=5)
        ttk.Radiobutton(ctrl_frame, text="Both", variable=self.stream_mode, value="both").grid(row=0, column=2, padx=5, pady=5)

        self.btn_stream = ttk.Button(ctrl_frame, text="Start Streaming", command=self.toggle_stream, state="disabled")
        self.btn_stream.grid(row=1, column=0, columnspan=3, pady=10)

        # Metadata Frame
        meta_frame = ttk.LabelFrame(self.root, text="Metadata Updates")
        meta_frame.pack(fill="x", padx=10, pady=10)

        # PIN DISPLAY
        self.pin_var = tk.StringVar(value="PIN: ----")
        ttk.Label(meta_frame, textvariable=self.pin_var, font=('TkDefaultFont', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 10))

        ttk.Label(meta_frame, text="Song Title:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.song_title = tk.StringVar(value="Live Radio Stream")
        ttk.Entry(meta_frame, textvariable=self.song_title, width=40).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(meta_frame, text="DJ Notes:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.dj_notes = tk.StringVar(value="Welcome to the stream!")
        ttk.Entry(meta_frame, textvariable=self.dj_notes, width=40).grid(row=2, column=1, padx=5, pady=5)

        self.btn_update_meta = ttk.Button(meta_frame, text="Update Metadata", command=self.update_metadata, state="disabled")
        self.btn_update_meta.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.btn_requests = ttk.Button(meta_frame, text="Show Song Requests", command=self.show_requests_window)
        self.btn_requests.grid(row=4, column=0, columnspan=2, pady=(0, 10))

        # Status Bar
        self.status = tk.StringVar(value="Disconnected")
        ttk.Label(self.root, textvariable=self.status, relief="sunken", anchor="w").pack(fill="x", side="bottom")

    def setup_socketio(self):
        @self.sio.event
        def connect():
            self.root.after(0, self.on_connected)

        @self.sio.event
        def disconnect():
            self.root.after(0, self.on_disconnected)
            
        @self.sio.event
        def connect_error(data):
            self.root.after(0, lambda: messagebox.showerror("Connection Error", "Could not connect to server"))
            
        @self.sio.on('server_pin')
        def on_server_pin(data):
            pin = data.get('pin', '----')
            self.root.after(0, lambda: self.pin_var.set(f"ADMIN PIN: {pin}"))

        @self.sio.on('all_requests')
        def on_all_requests(data):
            print(f"DEBUG: all_requests received {data}")
            self.root.after(0, self.clear_all_requests_ui)
            for req in data:
                print(f"DEBUG: queuing render for {req}")
                self.root.after(0, self.render_request, req)

        @self.sio.on('new_request')
        def on_new_request(data):
            print(f"DEBUG: new_request received {data}")
            self.root.after(0, self.render_request, data)

        @self.sio.on('request_removed')
        def on_request_removed(req_id):
            self.root.after(0, lambda i=req_id: self.remove_request_ui(i))

    def show_requests_window(self):
        if hasattr(self, 'requests_window') and self.requests_window.winfo_exists():
            self.requests_window.deiconify()
            self.requests_window.lift()
        else:
            self.setup_requests_window()

    def setup_requests_window(self):
        if hasattr(self, 'requests_window') and self.requests_window.winfo_exists():
            return
            
        self.requests_window = tk.Toplevel(self.root)
        self.requests_window.title("Song Requests")
        self.requests_window.geometry("400x500")
        self.requests_window.configure(bg="#2f3136")
        self.requests_window.protocol("WM_DELETE_WINDOW", self.requests_window.withdraw)

        self.req_canvas = tk.Canvas(self.requests_window, bg="#2f3136", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.requests_window, orient="vertical", command=self.req_canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.req_canvas, bg="#2f3136")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.req_canvas.configure(
                scrollregion=self.req_canvas.bbox("all")
            )
        )

        canvas_window = self.req_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        def configure_canvas_width(e):
            self.req_canvas.itemconfig(canvas_window, width=e.width)
        self.req_canvas.bind("<Configure>", configure_canvas_width)

        self.req_canvas.configure(yscrollcommand=scrollbar.set)

        self.req_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event):
            self.req_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.requests_window.bind_all("<MouseWheel>", _on_mousewheel)

    def render_request(self, req_data):
        print(f"DEBUG: Rendering request {req_data}")
        
        if not hasattr(self, 'scrollable_frame') or not self.scrollable_frame.winfo_exists():
            self.setup_requests_window()
            
        req_id = req_data['id']
        if req_id in self.active_requests:
            return

        frame = tk.Frame(self.scrollable_frame, bg="#36393f")
        frame.pack(fill="x", pady=2, padx=5)
        
        header_frame = tk.Frame(frame, bg="#36393f")
        header_frame.pack(fill="x")
        
        username_lbl = tk.Label(header_frame, text=req_data['username'], font=("Arial", 10, "bold"), fg="#ffffff", bg="#36393f")
        username_lbl.pack(side="left")
        
        time_lbl = tk.Label(header_frame, text=req_data['time'], font=("Arial", 8), fg="#72767d", bg="#36393f")
        time_lbl.pack(side="left", padx=5)
        
        def mark_used(rid=req_id):
            if self.sio.connected:
                self.sio.emit('remove_request', {'id': rid})
            else:
                self.remove_request_ui(rid)
            
        chk_btn = tk.Button(header_frame, text="✓", font=("Arial", 12, "bold"), fg="#43b581", bg="#36393f", activebackground="#36393f", activeforeground="#3ca374", borderwidth=0, cursor="hand2", command=mark_used)
        chk_btn.pack(side="right")
        
        content_text = f"Requested: {req_data['song']}"
        if req_data.get('artist'):
            content_text += f" by {req_data['artist']}"
            
        content_lbl = tk.Label(frame, text=content_text, font=("Arial", 10), fg="#dcddde", bg="#36393f", justify="left")
        content_lbl.pack(side="left", anchor="w", pady=(2, 0))
        
        self.active_requests[req_id] = frame

    def remove_request_ui(self, req_id):
        if req_id in self.active_requests:
            self.active_requests[req_id].destroy()
            del self.active_requests[req_id]
            
    def clear_all_requests_ui(self):
        for frame in self.active_requests.values():
            frame.destroy()
        self.active_requests.clear()

    def on_connected(self):
        self.status.set(f"Connected to {self.server_url.get()}")
        self.btn_connect.config(text="Disconnect")
        self.btn_stream.config(state="normal")
        self.btn_update_meta.config(state="normal")
        self.sio.emit('get_server_pin')
        self.update_metadata()

    def on_disconnected(self):
        self.status.set("Disconnected")
        self.btn_connect.config(text="Connect")
        self.btn_stream.config(state="disabled")
        self.btn_update_meta.config(state="disabled")
        self.pin_var.set("PIN: ----")
        if self.is_streaming:
            self.toggle_stream()

    def toggle_connection(self):
        if self.sio.connected:
            self.sio.disconnect()
        else:
            try:
                self.sio.connect(self.server_url.get())
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def update_metadata(self):
        if self.sio.connected:
            pin = self.pin_var.get().replace("ADMIN PIN: ", "").replace("PIN: ", "").strip()
            self.sio.emit('update_metadata', {
                'pin': pin,
                'title': self.song_title.get(),
                'notes': self.dj_notes.get()
            })

    def open_streams(self):
        try:
            music_idx = int(self.music_device.get().split(':')[0])
            mic_idx = int(self.mic_device.get().split(':')[0])

            self.music_stream = self.p.open(format=FORMAT,
                                            channels=CHANNELS,
                                            rate=RATE,
                                            input=True,
                                            input_device_index=music_idx,
                                            frames_per_buffer=CHUNK)

            self.mic_stream = self.p.open(format=FORMAT,
                                          channels=CHANNELS,
                                          rate=RATE,
                                          input=True,
                                          input_device_index=mic_idx,
                                          frames_per_buffer=CHUNK)
            return True
        except Exception as e:
            messagebox.showerror("Audio Error", f"Could not open audio streams: {e}")
            return False

    def close_streams(self):
        if self.music_stream:
            self.music_stream.stop_stream()
            self.music_stream.close()
            self.music_stream = None
        if self.mic_stream:
            self.mic_stream.stop_stream()
            self.mic_stream.close()
            self.mic_stream = None

    def audio_capture_loop(self):
        while self.is_streaming and self.sio.connected:
            try:
                mode = self.stream_mode.get()

                # Read raw bytes
                if mode in ['music', 'both']:
                    music_bytes = self.music_stream.read(CHUNK, exception_on_overflow=False)
                    music_data = np.frombuffer(music_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                else:
                    music_data = np.zeros(CHUNK, dtype=np.float32)

                if mode in ['mic', 'both']:
                    mic_bytes = self.mic_stream.read(CHUNK, exception_on_overflow=False)
                    mic_data = np.frombuffer(mic_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                else:
                    mic_data = np.zeros(CHUNK, dtype=np.float32)

                # Mix
                if mode == 'both':
                    # Simple average mixing
                    mixed_data = (music_data + mic_data) / 2.0
                elif mode == 'music':
                    mixed_data = music_data
                else:
                    mixed_data = mic_data

                # Send float32 bytes over socket
                self.sio.emit('audio_stream', mixed_data.tobytes())

            except Exception as e:
                print(f"Streaming error: {e}")
                break

        self.root.after(0, self.stop_streaming_ui)

    def stop_streaming_ui(self):
        if self.is_streaming:
            self.is_streaming = False
            self.btn_stream.config(text="Start Streaming")
            self.status.set("Streaming stopped")
            self.close_streams()

    def toggle_stream(self):
        if not self.is_streaming:
            if self.open_streams():
                self.is_streaming = True
                self.btn_stream.config(text="Stop Streaming")
                self.status.set("Streaming live...")
                self.stream_thread = threading.Thread(target=self.audio_capture_loop, daemon=True)
                self.stream_thread.start()
        else:
            self.is_streaming = False
            # The thread will exit because is_streaming is False
            self.btn_stream.config(text="Start Streaming")
            self.status.set("Streaming stopped")
            self.close_streams()

    def on_closing(self):
        self.is_streaming = False
        if self.sio.connected:
            self.sio.disconnect()
        self.close_streams()
        self.p.terminate()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = BroadcasterApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
