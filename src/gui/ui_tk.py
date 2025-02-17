import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import List, Callable


class LiveTranscriptionUI:
    def __init__(self, start_callback: Callable[[], None] = None, stop_callback: Callable[[], None] = None):
        self.root = tk.Tk()
        self.root.title("SmartLog AI")
        self.root.geometry("800x600")

        self.start_callback = start_callback
        self.stop_callback = stop_callback

        self.text_area = scrolledtext.ScrolledText(self.root, height=20, width=80, wrap=tk.WORD, state=tk.DISABLED)
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.keyword_label = tk.Label(self.root, text="Keywords: ", font=("Arial", 12))
        self.keyword_label.pack(padx=10, pady=5)

        # Buttons for start/stop
        button_frame = tk.Frame(self.root)
        button_frame.pack(padx=10, pady=5)

        self.start_button = tk.Button(button_frame, text="Start Capture", command=self.on_start)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(button_frame, text="Stop Capture", command=self.on_stop)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # User Guidance Placeholders
        self.instructions_label = tk.Label(self.root, text="Note-Taking Instructions (Future Feature):")
        self.instructions_label.pack(padx=10, pady=2)

        self.instructions_entry = ttk.Entry(self.root, width=50)
        self.instructions_entry.pack(padx=10, pady=2)

        self.style_label = tk.Label(self.root, text="Note-Taking Style:")
        self.style_label.pack(padx=10, pady=2)

        self.style_combo = ttk.Combobox(self.root, values=["Keywords Only", "Short Summary", "Detailed Keywords"], state="readonly")
        self.style_combo.pack(padx=10, pady=2)
        self.style_combo.set("Keywords Only")

    def on_start(self):
        if self.start_callback:
            self.start_callback()

    def on_stop(self):
        if self.stop_callback:
            self.stop_callback()

    def update_display(self, transcription: str, keywords: List[str]):
        self.root.after(0, self._update_text_area, transcription)
        self.root.after(0, self._update_keyword_label, keywords)

    def _update_text_area(self, transcription: str):
        try:
            self.text_area.config(state=tk.NORMAL)
            self.text_area.insert(tk.END, transcription + "\n")
            self.text_area.see(tk.END)
            self.text_area.config(state=tk.DISABLED)
        except tk.TclError:
            pass

    def _update_keyword_label(self, keywords: List[str]):
        try:
            if keywords:
                self.keyword_label.config(text="Keywords: " + ", ".join(keywords))
            else:
                self.keyword_label.config(text="Keywords: ")
        except tk.TclError:
            pass

    def run(self):
        self.root.mainloop()
