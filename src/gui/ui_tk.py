import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import List, Dict, Callable, Optional, Any, Union


class LiveTranscriptionUI:
    def __init__(
        self,
        start_callback: Optional[Callable[[], None]] = None,
        stop_callback: Optional[Callable[[], None]] = None,
    ):
        self.root = tk.Tk()
        self.root.title("SmartLog AI")
        self.root.geometry("800x600")

        self.start_callback: Optional[Callable[[], Any]] = start_callback
        self.stop_callback: Optional[Callable[[], Any]] = stop_callback

        self.text_area = scrolledtext.ScrolledText(
            self.root, height=20, width=80, wrap=tk.WORD, state=tk.DISABLED
        )
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Create frame for summary display
        self.summary_frame = tk.Frame(self.root)
        self.summary_frame.pack(padx=10, pady=5, fill=tk.X)

        # Initialize summary category labels
        self.summary_labels = {}

        # Create the initial keyword label for backwards compatibility
        self.keyword_label = tk.Label(
            self.summary_frame, text="Keywords: ", font=("Arial", 12)
        )
        self.keyword_label.pack(padx=10, pady=5, anchor=tk.W)
        self.summary_labels["keywords"] = self.keyword_label

        # Buttons for start/stop
        button_frame = tk.Frame(self.root)
        button_frame.pack(padx=10, pady=5)

        self.start_button = tk.Button(
            button_frame, text="Start Capture", command=self.on_start
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(
            button_frame, text="Stop Capture", command=self.on_stop
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # User Guidance Placeholders
        self.instructions_label = tk.Label(
            self.root, text="Note-Taking Instructions (Future Feature):"
        )
        self.instructions_label.pack(padx=10, pady=2)

        self.instructions_entry = ttk.Entry(self.root, width=50)
        self.instructions_entry.pack(padx=10, pady=2)

        self.style_label = tk.Label(self.root, text="Note-Taking Style:")
        self.style_label.pack(padx=10, pady=2)

        self.style_combo = ttk.Combobox(
            self.root,
            values=["Basic", "Detailed", "Comprehensive"],
            state="readonly",
        )
        self.style_combo.pack(padx=10, pady=2)
        self.style_combo.set("Basic")

    def on_start(self):
        if self.start_callback:
            self.start_callback()

    def on_stop(self):
        if self.stop_callback:
            self.stop_callback()

    def update_display(
        self, transcription: str, summary: Union[List[str], Dict[str, List[str]]]
    ):
        """Update the display with transcription and summary data."""
        # Enable text area for editing
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, transcription)
        self.text_area.config(state=tk.DISABLED)

        # Handle both legacy list format and new dict format
        if isinstance(summary, list):
            # Legacy format - just keywords
            self.keyword_label.config(text=f"Keywords: {', '.join(summary)}")
        elif isinstance(summary, dict):
            # New structured format - create or update labels for each category
            for category, items in summary.items():
                category_title = category.capitalize()
                display_text = f"{category_title}: {', '.join(items)}"

                # Create label if it doesn't exist
                if category not in self.summary_labels:
                    self.summary_labels[category] = tk.Label(
                        self.summary_frame,
                        text=display_text,
                        font=("Arial", 12),
                        anchor=tk.W,
                        justify=tk.LEFT,
                    )
                    self.summary_labels[category].pack(
                        padx=10, pady=2, anchor=tk.W, fill=tk.X
                    )
                else:
                    # Update existing label
                    self.summary_labels[category].config(text=display_text)

    def run(self):
        self.root.mainloop()
