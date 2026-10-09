import json
import os
import socket
import subprocess
import threading
import time
from tkinter import *
from tkinter import ttk, messagebox, filedialog

CONFIG_FILE = "config.json"


def default_config():
    return {
        "selected_server": "Server 1",
        "servers": [
            {"name": "Server 1", "host": "127.0.0.1", "port": 26000},
            {"name": "Server 2", "host": "127.0.0.1", "port": 26001},
        ],
        "username": "Player1",
        "game_path": "",
        "last_server": "127.0.0.1",
        "last_port": 26000,
    }


def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(default_config())
        return default_config()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        default = default_config()
        default.update(data)

        if "servers" not in data or not isinstance(data["servers"], list):
            default["servers"] = default_config()["servers"]

        return default
    except Exception:
        save_config(default_config())
        return default_config()


def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def check_server(host, port, timeout=2.5):
    start = time.perf_counter()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)

    try:
        sock.connect((host, int(port)))
        latency = round((time.perf_counter() - start) * 1000, 2)
        return {
            "status": "online",
            "latency_ms": latency,
            "message": f"Server online ({latency} ms)",
        }
    except Exception as e:
        return {
            "status": "offline",
            "latency_ms": 0,
            "message": f"Server offline: {str(e)}",
        }
    finally:
        sock.close()


def launch_game(game_path):
    if not game_path or not os.path.exists(game_path):
        messagebox.showerror("Error", "Path game tidak valid atau belum diisi.")
        return

    try:
        subprocess.Popen([game_path], shell=True)
        messagebox.showinfo("Berhasil", "Game berhasil dijalankan.")
    except Exception as e:
        messagebox.showerror("Error", f"Gagal menjalankan game: {e}")


class PinkMSLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("PinkMS 10 Launcher")
        self.root.geometry("700x520")
        self.root.resizable(False, False)

        self.config = load_config()
        self.server_list = self.config["servers"]

        self.username_var = StringVar(value=self.config.get("username", "Player1"))
        self.game_path_var = StringVar(value=self.config.get("game_path", ""))
        self.server_name_var = StringVar(value=self.config.get("selected_server", "Server 1"))
        self.server_host_var = StringVar(value=self.config.get("last_server", "127.0.0.1"))
        self.server_port_var = StringVar(value=str(self.config.get("last_port", 26000)))
        self.status_var = StringVar(value="Status: Belum dicek")

        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="PinkMS 10 Game Launcher", font=("Arial", 16, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 12)
        )

        ttk.Label(main, text="Username").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(main, textvariable=self.username_var, width=28).grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(main, text="Game Path").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(main, textvariable=self.game_path_var, width=28).grid(row=2, column=1, sticky="w", padx=5, pady=5)
        ttk.Button(main, text="Pilih Game", command=self.select_game_path).grid(row=2, column=2, sticky="w", padx=5, pady=5)

        ttk.Label(main, text="Host").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(main, textvariable=self.server_host_var, width=28).grid(row=3, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(main, text="Port").grid(row=3, column=2, sticky="w", pady=5)
        ttk.Entry(main, textvariable=self.server_port_var, width=12).grid(row=3, column=3, sticky="w", padx=5, pady=5)

        ttk.Label(main, text="Daftar Server").grid(row=4, column=0, sticky="w", pady=(12, 5))

        self.server_box = Listbox(main, height=8, width=40)
        self.server_box.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        self.refresh_server_list()

        ttk.Button(main, text="Tambah Server", command=self.add_server).grid(row=5, column=2, sticky="n", padx=5, pady=5)
        ttk.Button(main, text="Hapus Server", command=self.delete_server).grid(row=6, column=2, sticky="n", padx=5, pady=5)
        ttk.Button(main, text="Pilih Server", command=self.select_server_from_list).grid(row=7, column=2, sticky="n", padx=5, pady=5)

        ttk.Button(main, text="Cek Koneksi", command=self.check_connection_async).grid(row=8, column=0, sticky="ew", padx=5, pady=10)
        ttk.Button(main, text="Jalankan Game", command=self.launch_game_button).grid(row=8, column=1, sticky="ew", padx=5, pady=10)
        ttk.Button(main, text="Simpan Konfigurasi", command=self.save_settings).grid(row=8, column=2, columnspan=2, sticky="ew", padx=5, pady=10)

        ttk.Label(main, textvariable=self.status_var, font=("Arial", 10, "bold"), foreground="darkblue").grid(
            row=9, column=0, columnspan=4, sticky="w", pady=(8, 0)
        )

    def refresh_server_list(self):
        self.server_box.delete(0, END)
        for server in self.server_list:
            label = f"{server['name']} - {server['host']}:{server['port']}"
            self.server_box.insert(END, label)

    def add_server(self):
        name = f"Server {len(self.server_list) + 1}"
        host = self.server_host_var.get().strip()
        port = self.server_port_var.get().strip()

        if not host or not port:
            messagebox.showwarning("Warning", "Host dan port harus diisi.")
            return

        try:
            port = int(port)
        except ValueError:
            messagebox.showwarning("Warning", "Port harus angka.")
            return

        self.server_list.append({"name": name, "host": host, "port": port})
        self.refresh_server_list()
        self.server_name_var.set(name)

    def delete_server(self):
        selected_index = self.server_box.curselection()
        if not selected_index:
            messagebox.showwarning("Warning", "Pilih server terlebih dahulu.")
            return

        idx = selected_index[0]
        if idx < len(self.server_list):
            del self.server_list[idx]
            self.refresh_server_list()

    def select_server_from_list(self):
        selected_index = self.server_box.curselection()
        if not selected_index:
            messagebox.showwarning("Warning", "Pilih server dari daftar.")
            return

        idx = selected_index[0]
        if idx < len(self.server_list):
            server = self.server_list[idx]
            self.server_name_var.set(server["name"])
            self.server_host_var.set(server["host"])
            self.server_port_var.set(str(server["port"]))
            self.status_var.set(f"Status: server dipilih -> {server['name']}")

    def select_game_path(self):
        path = filedialog.askopenfilename(
            title="Pilih file game",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")],
        )
        if path:
            self.game_path_var.set(path)

    def save_settings(self):
        username = self.username_var.get().strip()
        game_path = self.game_path_var.get().strip()
        host = self.server_host_var.get().strip()
        port = self.server_port_var.get().strip()

        if not host:
            messagebox.showwarning("Warning", "Host tidak boleh kosong.")
            return

        try:
            port_int = int(port)
        except ValueError:
            messagebox.showwarning("Warning", "Port harus angka.")
            return

        data = {
            "username": username or "Player1",
            "game_path": game_path,
            "selected_server": self.server_name_var.get(),
            "servers": self.server_list,
            "last_server": host,
            "last_port": port_int,
        }

        save_config(data)
        self.config = data
        self.status_var.set("Status: Konfigurasi berhasil disimpan.")
        messagebox.showinfo("Sukses", "Konfigurasi berhasil disimpan.")

    def check_connection_async(self):
        host = self.server_host_var.get().strip()
        port = self.server_port_var.get().strip()

        if not host or not port:
            self.status_var.set("Status: Host dan port harus diisi.")
            return

        self.status_var.set("Status: Mengecek koneksi...")
        threading.Thread(target=self.check_connection_worker, args=(host, port), daemon=True).start()

    def check_connection_worker(self, host, port):
        result = check_server(host, port)
        if result["status"] == "online":
            msg = f"Status: SERVER ONLINE | Latency: {result['latency_ms']} ms"
        else:
            msg = f"Status: SERVER OFFLINE | {result['message']}"

        self.root.after(0, lambda: self.status_var.set(msg))

    def launch_game_button(self):
        launch_game(self.game_path_var.get().strip())


if __name__ == "__main__":
    root = Tk()
    app = PinkMSLauncher(root)
    root.mainloop()
