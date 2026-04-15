import tkinter as tk
from tkinter import scrolledtext, ttk
import subprocess
import threading
import multiprocessing
import sys
import os
import queue
import hashlib
import time
import io
import traceback
import importlib

# =====================================================================
# --- CONFIGURATION ---
# =====================================================================
TARGET_MODULE = "main"                 # File name: main.py
TARGET_FUNCTION = "main"               # Function: def main(ThreadNum, fetch_url):
DEFAULT_THREADS = 3                    
MAX_THREADS = 50                       
DEFAULT_DELAY = 1.0                    
DEFAULT_URL = "https://www.thebluealliance.com/api/v3" # <--- AUTO-POPULATED URL
DEBUG_MODE = True                      
AUTO_INPUT_VALUE = "b"                 
REQUIREMENTS_FILE = "requirements.txt" 
REQUIREMENTS_CACHE = ".req_hash"       
# =====================================================================

class InfiniteInput:
    def __init__(self, value):
        self.value = f"{value}\n"
    def readline(self): return self.value
    def read(self, size=-1): return self.value
    def __iter__(self): return self
    def __next__(self): return self.value

class QueueWriter:
    def __init__(self, q, worker_id):
        self.q = q
        self.worker_id = worker_id

    def write(self, message):
        if message:
            out = message if message.endswith('\n') else message + '\n'
            self.q.put((self.worker_id, out))

    def flush(self):
        pass

def worker_proxy(func_name, worker_id, fetch_url, log_queue, debug_on):
    sys.stdin = InfiniteInput(AUTO_INPUT_VALUE)
    sys.stdout = QueueWriter(log_queue, worker_id)
    sys.stderr = sys.stdout

    try:
        module = importlib.import_module(TARGET_MODULE)
        importlib.reload(module) 
        
        if hasattr(module, func_name):
            script_func = getattr(module, func_name)
            script_func(worker_id, fetch_url) 
        else:
            if debug_on:
                log_queue.put((worker_id, f"[System] Error: '{func_name}' not found.\n"))
        
        log_queue.put((worker_id, f"[Worker {worker_id}] Task Completed.\n"))
        
    except Exception:
        error_msg = traceback.format_exc() if debug_on else str(sys.exc_info()[1])
        log_queue.put((worker_id, f"[Worker {worker_id}] CRASHED:\n{error_msg}\n"))

class TerminalGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FRC Scouting Instance Manager")
        
        self.log_queue = multiprocessing.Queue()
        self.active_processes = []
        self.terminals = {}
        self.is_aborting = False
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- UI SETUP ---
        control_frame = tk.Frame(root, bg='#2d2d2d', pady=10, padx=15)
        control_frame.pack(fill='x')

        # Left side controls
        tk.Label(control_frame, text="Instances:", bg='#2d2d2d', fg='white', font=('Segoe UI', 9, 'bold')).pack(side='left')
        self.thread_var = tk.IntVar(value=DEFAULT_THREADS)
        ttk.Spinbox(control_frame, from_=1, to=MAX_THREADS, textvariable=self.thread_var, width=5).pack(side='left', padx=5)

        tk.Label(control_frame, text="Delay (s):", bg='#2d2d2d', fg='white', font=('Segoe UI', 9, 'bold')).pack(side='left', padx=(10, 0))
        self.delay_var = tk.DoubleVar(value=DEFAULT_DELAY)
        ttk.Spinbox(control_frame, from_=0.0, to=60.0, increment=0.5, textvariable=self.delay_var, width=5).pack(side='left', padx=5)

        self.start_btn = tk.Button(control_frame, text="LAUNCH ALL", command=self.start_initialization, 
                                  bg='#28a745', fg='white', relief='flat', padx=20, font=('Consolas', 10, 'bold'))
        self.start_btn.pack(side='left', padx=15)

        self.abort_btn = tk.Button(control_frame, text="ABORT ALL", command=self.abort_all, 
                                  bg='#d11a2a', fg='white', relief='flat', padx=20, font=('Consolas', 10, 'bold'), state='disabled')
        self.abort_btn.pack(side='left')

        # Right side Fetch URL input
        url_frame = tk.Frame(control_frame, bg='#2d2d2d')
        url_frame.pack(side='right', padx=10)
        
        tk.Label(url_frame, text="Fetch URL:", bg='#2d2d2d', fg='white', font=('Segoe UI', 9, 'bold')).pack(side='left', padx=5)
        self.url_entry = tk.Entry(url_frame, width=35, font=('Consolas', 10))
        self.url_entry.insert(0, DEFAULT_URL) # Auto-populates from config
        self.url_entry.pack(side='left', padx=5)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)

        self.update_ui_from_queue()

    def add_terminal(self, worker_id):
        tab = tk.Frame(self.notebook)
        text_area = scrolledtext.ScrolledText(tab, state='disabled', bg='#121212', fg='#00ff00', 
                                              font=('Consolas', 10), tabs=(40,), undo=False)
        text_area.pack(expand=True, fill='both')
        self.notebook.add(tab, text=f"Thread {worker_id}")
        self.terminals[worker_id] = text_area

    def raw_insert(self, worker_id, text):
        widget = self.terminals.get(worker_id)
        if not widget: return
        widget.configure(state='normal')
        widget.insert(tk.END, text)
        widget.configure(state='disabled')
        widget.see(tk.END)

    def update_ui_from_queue(self):
        try:
            while True:
                worker_id, message = self.log_queue.get_nowait()
                self.raw_insert(worker_id, message)
        except queue.Empty: pass
        self.root.after(50, self.update_ui_from_queue)

    def abort_all(self):
        self.is_aborting = True
        count = 0
        for p in self.active_processes:
            if p.is_alive():
                p.kill()
                count += 1
        
        self.active_processes = []
        self.abort_btn.config(state='disabled')
        self.start_btn.config(state='normal')
        
        for wid in self.terminals:
            self.raw_insert(wid, f"\n[SYSTEM] KILLED {count} active processes.\n")

    def start_initialization(self):
        self.is_aborting = False
        current_url = self.url_entry.get()
        
        for tab in self.notebook.tabs(): self.notebook.forget(tab)
        self.terminals.clear()
        self.active_processes = []
        
        self.start_btn.config(state='disabled')
        self.abort_btn.config(state='normal')
        
        def init_sequence():
            if os.path.exists(REQUIREMENTS_FILE):
                with open(REQUIREMENTS_FILE, 'rb') as f:
                    curr_hash = hashlib.md5(f.read()).hexdigest()
                if not os.path.exists(REQUIREMENTS_CACHE) or open(REQUIREMENTS_CACHE).read() != curr_hash:
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE])
                    with open(REQUIREMENTS_CACHE, 'w') as f: f.write(curr_hash)
            
            num_instances = self.thread_var.get()
            delay = self.delay_var.get()
            
            for i in range(0, num_instances):
                if self.is_aborting: break
                
                self.root.after(0, self.add_terminal, i)
                p = multiprocessing.Process(
                    target=worker_proxy, 
                    args=(TARGET_FUNCTION, i, current_url, self.log_queue, DEBUG_MODE), 
                    daemon=True
                )
                p.start()
                self.active_processes.append(p)
                if i < (num_instances - 1): time.sleep(delay)

            self.root.after(0, lambda: self.start_btn.config(state='normal'))

        threading.Thread(target=init_sequence, daemon=True).start()

    def on_closing(self):
        self.abort_all()
        self.root.destroy()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    root = tk.Tk()
    root.geometry("1200x800")
    style = ttk.Style()
    style.theme_use('clam')
    app = TerminalGUI(root)
    root.mainloop()