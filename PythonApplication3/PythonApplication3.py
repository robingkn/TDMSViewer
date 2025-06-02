import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from nptdms import TdmsFile
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class TDMSViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TDMS File Viewer with Plot")
        self.geometry("900x700")

        # Menu
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open TDMS File", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

        # Left: Treeview for TDMS structure
        self.tree = ttk.Treeview(self)
        self.tree.heading("#0", text="TDMS Structure", anchor='w')
        self.tree.pack(side="left", fill="y", padx=5, pady=5)

        # Right frame for table + plot
        right_frame = tk.Frame(self)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # Table to show data values
        self.table = ttk.Treeview(right_frame, columns=("Index", "Value"), show='headings', height=10)
        self.table.heading("Index", text="Index")
        self.table.heading("Value", text="Value")
        self.table.pack(fill="x")

        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Matplotlib figure for plotting
        self.fig, self.ax = plt.subplots(figsize=(7, 3))
        self.ax.set_title("Channel Data Plot")
        self.ax.set_xlabel("Index")
        self.ax.set_ylabel("Value")

        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("TDMS files", "*.tdms")])
        if not file_path:
            return

        try:
            self.tdms_file = TdmsFile.read(file_path)
            self.tree.delete(*self.tree.get_children())
            self.table.delete(*self.table.get_children())
            self.ax.clear()
            self.ax.set_title("Channel Data Plot")
            self.ax.set_xlabel("Index")
            self.ax.set_ylabel("Value")
            self.canvas.draw()
            self.build_tree()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open TDMS file:\n{e}")

    def build_tree(self):
        for group in self.tdms_file.groups():
            group_id = self.tree.insert("", "end", text=group.name, open=True)
            for channel in group.channels():
                ch_id = self.tree.insert(group_id, "end", text=channel.name)
                self.tree.item(ch_id, tags=("channel",))
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        parent = self.tree.parent(selected[0])

        if parent:  # selected item is a channel
            group_name = self.tree.item(parent)["text"]
            channel_name = item["text"]
            try:
                channel = self.tdms_file[group_name][channel_name]
                self.table.delete(*self.table.get_children())
                preview = channel[:100]  # show first 100 points
                for i, val in enumerate(preview):
                    self.table.insert("", "end", values=(i, val))

                # Plot the preview data
                self.ax.clear()
                self.ax.plot(range(len(preview)), preview, marker='o', linestyle='-')
                self.ax.set_title(f"Plot: {group_name} / {channel_name}")
                self.ax.set_xlabel("Index")
                self.ax.set_ylabel("Value")
                self.ax.grid(True)
                self.canvas.draw()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read channel: {e}")
        else:
            self.table.delete(*self.table.get_children())
            self.ax.clear()
            self.ax.set_title("Channel Data Plot")
            self.ax.set_xlabel("Index")
            self.ax.set_ylabel("Value")
            self.canvas.draw()

if __name__ == "__main__":
    app = TDMSViewer()
    app.mainloop()
