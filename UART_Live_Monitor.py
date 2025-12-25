import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import threading
import sv_ttk

BAUD_RATE = 115200

class UARTMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("UART Log Monitor")
        self.root.geometry("750x600")

        # Set the modern theme
        sv_ttk.set_theme("dark")

        # Serial variables
        self.ser = None
        self.listening = False
        self.thread = None
        
        # This variable is linked to the Entry box in the UI
        self.search_var = tk.StringVar(value="") 

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill="both", expand=True)

        # --- Header ---
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="ew")
        ttk.Label(header_frame, text="UART Port Monitor", font=("Segoe UI", 18, "bold")).pack(side="left")
        
        # --- Configuration Panel ---
        settings_frame = ttk.LabelFrame(main_frame, text="Connection & Search Settings", padding=15)
        settings_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))

        # COM Port
        ttk.Label(settings_frame, text="Port:").grid(row=0, column=0, sticky="w", padx=5)
        self.combobox = ttk.Combobox(settings_frame, values=self.get_com_ports(), state="readonly", width=12)
        self.combobox.grid(row=0, column=1, padx=5, sticky="w")
        if self.combobox["values"]:
            self.combobox.current(0)

        # Dynamic Search Entry
        ttk.Label(settings_frame, text="Search Text:").grid(row=0, column=2, sticky="w", padx=(15, 5))
        self.search_entry = ttk.Entry(settings_frame, textvariable=self.search_var, width=25)
        self.search_entry.grid(row=0, column=3, padx=5, sticky="w")

        # Control Button
        self.button = ttk.Button(settings_frame, text="Start Listening", style="Accent.TButton", command=self.toggle_listening)
        self.button.grid(row=0, column=4, padx=15, sticky="w")

        # --- Status Area ---
        status_frame = ttk.Frame(main_frame, padding=(0, 5))
        status_frame.grid(row=2, column=0, columnspan=3, sticky="ew")

        self.status_label = ttk.Label(status_frame, text="Status: IDLE", font=("Segoe UI", 10, "italic"))
        self.status_label.pack(side="left")

        self.canvas = tk.Canvas(status_frame, width=16, height=16, bg="#1c1c1c", highlightthickness=0)
        self.canvas.pack(side="right", padx=10)
        self.circle = self.canvas.create_oval(2, 2, 14, 14, fill="#555555", outline="")

        # --- Log Output ---
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=3, column=0, columnspan=3, sticky="nsew")
        main_frame.rowconfigure(3, weight=1)
        main_frame.columnconfigure(0, weight=1)

        self.text = tk.Text(
            log_frame, wrap="word", font=("Consolas", 10), 
            bg="#2b2b2b", fg="#ffffff", insertbackground="white", 
            padx=10, pady=10, borderwidth=0
        )
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.text.config(state="disabled")

    def get_com_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def toggle_listening(self):
        if not self.listening:
            if not self.combobox.get():
                self.update_status("No COM port selected", "#555555")
                return
            
            self.listening = True
            self.button.config(text="Stop Listening")
            
            # Clear logs for new session
            self.text.config(state="normal")
            self.text.delete("1.0", tk.END)
            self.text.config(state="disabled")
            
            # Capture the current UI text to look for
            user_query = self.search_var.get()
            self.update_status(f"Scanning for '{user_query}'...", "#f1c40f") # Yellow (Searching)
            
            self.thread = threading.Thread(target=self.read_uart, args=(user_query,), daemon=True)
            self.thread.start()
        else:
            self.stop_listening()

    def stop_listening(self):
        self.listening = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.button.config(text="Start Listening")
        self.update_status("Stopped", "#555555")

    def read_uart(self, target_string):
        try:
            self.ser = serial.Serial(self.combobox.get(), BAUD_RATE, timeout=1)
            while self.listening:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode(errors="ignore").strip()
                    if line:
                        self.append_log(line)
                        # Case-insensitive search of UI text within the log line
                        if target_string and target_string.lower() in line.lower():
                            self.root.after(0, self.update_status, f"FOUND: {target_string}", "#107c10") # Green
            self.ser.close()
        except Exception as e:
            self.root.after(0, self.update_status, f"Error: {e}", "#555555")

    def update_status(self, text, color):
        self.status_label.config(text=f"Status: {text}")
        self.canvas.itemconfig(self.circle, fill=color)

    def append_log(self, message):
        self.text.config(state="normal")
        self.text.insert(tk.END, message + "\n")
        self.text.see(tk.END)
        self.text.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = UARTMonitorApp(root)
    root.mainloop()