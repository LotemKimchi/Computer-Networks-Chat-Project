import socket
import threading
import queue
import tkinter as tk
from tkinter import messagebox

HOST_DEFAULT = "127.0.0.1"
PORT_DEFAULT = 5000


class ChatGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Socket Chat Client")

        self.sock = None
        self.q = queue.Queue()

        # Top row: name/host/port/connect
        top = tk.Frame(root)
        top.pack(fill="x", padx=8, pady=6)

        tk.Label(top, text="Name:").pack(side="left")
        self.name_var = tk.StringVar()
        tk.Entry(top, textvariable=self.name_var, width=14).pack(side="left", padx=4)

        tk.Label(top, text="Host:").pack(side="left")
        self.host_var = tk.StringVar(value=HOST_DEFAULT)
        tk.Entry(top, textvariable=self.host_var, width=14).pack(side="left", padx=4)

        tk.Label(top, text="Port:").pack(side="left")
        self.port_var = tk.StringVar(value=str(PORT_DEFAULT))
        tk.Entry(top, textvariable=self.port_var, width=6).pack(side="left", padx=4)

        self.btn_connect = tk.Button(top, text="Connect", command=self.connect)
        self.btn_connect.pack(side="left", padx=6)

        # Chat controls
        controls = tk.Frame(root)
        controls.pack(fill="x", padx=8, pady=4)

        tk.Label(controls, text="Chat with:").pack(side="left")
        self.target_var = tk.StringVar()
        tk.Entry(controls, textvariable=self.target_var, width=18).pack(side="left", padx=4)

        tk.Button(controls, text="Start Chat", command=self.start_chat).pack(side="left", padx=4)
        tk.Button(controls, text="End Chat", command=self.end_chat).pack(side="left", padx=4)

        # Log
        self.log = tk.Text(root, height=18, state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True, padx=8, pady=6)

        # Bottom: message entry
        bottom = tk.Frame(root)
        bottom.pack(fill="x", padx=8, pady=6)

        self.msg_var = tk.StringVar()
        entry = tk.Entry(bottom, textvariable=self.msg_var)
        entry.pack(side="left", fill="x", expand=True, padx=4)
        entry.bind("<Return>", lambda e: self.send_msg())

        tk.Button(bottom, text="Send", command=self.send_msg).pack(side="left", padx=4)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(100, self.pump_queue)

    def append(self, text: str):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def send_line(self, text: str):
        if not self.sock:
            return
        try:
            self.sock.sendall((text + "\n").encode("utf-8"))
        except OSError:
            self.append("[INFO] send failed")

    def connect(self):
        if self.sock:
            return

        name = self.name_var.get().strip()
        host = self.host_var.get().strip()
        try:
            port = int(self.port_var.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Port must be a number")
            return

        if not name:
            messagebox.showerror("Error", "Name is required")
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, port))
        except Exception as e:
            self.sock = None
            messagebox.showerror("Error", f"Connect failed: {e}")
            return

        self.btn_connect.config(state="disabled", text="Connected")
        self.append(f"[INFO] Connected to {host}:{port} as {name}")

        # Start receiver thread
        threading.Thread(target=self.recv_loop, daemon=True).start()

        # Login
        self.send_line(f"HELLO {name}")

    def recv_loop(self):
        f = self.sock.makefile("r", encoding="utf-8", newline="\n")
        try:
            for line in f:
                self.q.put(line.strip())
        except Exception:
            pass
        finally:
            self.q.put("[INFO] Disconnected")

    def pump_queue(self):
        try:
            while True:
                msg = self.q.get_nowait()
                self.append(msg)
        except queue.Empty:
            pass
        self.root.after(100, self.pump_queue)

    def start_chat(self):
        target = self.target_var.get().strip()
        if not target:
            messagebox.showerror("Error", "Target name is required")
            return
        self.send_line(f"CHAT {target}")

    def end_chat(self):
        self.send_line("END")

    def send_msg(self):
        text = self.msg_var.get().strip()
        if not text:
            return
        self.send_line(f"MSG {text}")
        self.msg_var.set("")

    def on_close(self):
        try:
            if self.sock:
                try:
                    self.send_line("QUIT")
                except Exception:
                    pass
                self.sock.close()
        except Exception:
            pass
        self.root.destroy()


def main():
    root = tk.Tk()
    ChatGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
