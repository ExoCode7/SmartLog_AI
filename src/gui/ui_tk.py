import tkinter as tk


class MinimalUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SmartLog AI - MVP")

        self.label = tk.Label(self.root, text="Welcome to SmartLog AI MVP Phase 1!")
        self.label.pack(padx=10, pady=10)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MinimalUI()
    app.run()
