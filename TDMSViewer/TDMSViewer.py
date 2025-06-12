import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from nptdms import TdmsFile
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pprint

class TDMSViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TDMS File Viewer")
        self.geometry("1000x700")

        self.page_size = 100
        self.current_page = 0
        self.current_channel = None

        # Menu
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open TDMS File", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

        # Main content frames
        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True)

        # Left: Tree + Properties
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side="left", fill="y", padx=5, pady=5)

        self.tree = ttk.Treeview(left_frame)
        self.tree.heading("#0", text="TDMS Structure", anchor='w')
        self.tree.pack(fill="both", expand=True)

        tk.Label(left_frame, text="Properties:").pack(anchor="w")
        self.prop_text = tk.Text(left_frame, height=12, width=40, state='disabled', bg='#f0f0f0')
        self.prop_text.pack(fill="both", expand=False)

        # Right: Paned window (table + plot)
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True)

        right_paned = tk.PanedWindow(right_frame, orient=tk.VERTICAL)
        right_paned.pack(fill="both", expand=True, padx=5, pady=5)

        # Table Frame
        table_frame = tk.Frame(right_paned)
        self.table = ttk.Treeview(table_frame, columns=("Index", "Value"), show='headings')
        self.table.heading("Index", text="Index")
        self.table.heading("Value", text="Value")
        self.table.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        right_paned.add(table_frame)

        # Plot Frame
        self.plot_frame = tk.Frame(right_paned)
        self.fig, self.ax = plt.subplots(figsize=(7, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.ax.set_title("Channel Data Plot")
        self.ax.set_xlabel("Index")
        self.ax.set_ylabel("Value")
        right_paned.add(self.plot_frame)

        # Navigation Frame (FIXED BOTTOM)
        nav_frame = tk.Frame(self)
        nav_frame.pack(fill="x", pady=5)

        self.prev_btn = tk.Button(nav_frame, text="<", command=self.prev_page)
        self.prev_btn.pack(side="left", padx=2)

        self.page_label = tk.Label(nav_frame, text="Page 1")
        self.page_label.pack(side="left", padx=5)

        self.page_entry = tk.Entry(nav_frame, width=5)
        self.page_entry.pack(side="left")

        self.go_btn = tk.Button(nav_frame, text="Go", command=self.jump_to_page)
        self.go_btn.pack(side="left", padx=2)

        self.next_btn = tk.Button(nav_frame, text=">", command=self.next_page)
        self.next_btn.pack(side="left", padx=2)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tdms_file = None

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("TDMS files", "*.tdms")])
        if not file_path:
            return
        try:
            self.tdms_file = TdmsFile.read(file_path)
            self.tree.delete(*self.tree.get_children())
            self.table.delete(*self.table.get_children())
            self.clear_properties()
            self.ax.clear()
            self.canvas.draw()
            self.build_tree(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open TDMS file:\n{e}")

    def build_tree(self, filepath):
        root_id = self.tree.insert("", "end", text=filepath, open=True, tags=("file",))
        for group in self.tdms_file.groups():
            group_id = self.tree.insert(root_id, "end", text=group.name, open=True, tags=("group",))
            for channel in group.channels():
                self.tree.insert(group_id, "end", text=channel.name, tags=("channel",))

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item_id = selected[0]
        item_text = self.tree.item(item_id, "text")
        item_tags = self.tree.item(item_id, "tags")
        parent_id = self.tree.parent(item_id)

        self.clear_properties()
        self.table.delete(*self.table.get_children())
        self.ax.clear()

        if "file" in item_tags:
            props = {
                "File": item_text,
                "Groups": len(self.tdms_file.groups()),
                "Total Channels": sum(len(g.channels()) for g in self.tdms_file.groups())
            }
            self.show_properties(props)

        elif "group" in item_tags:
            group = self.tdms_file[item_text]
            props = {
                "Group": group.name,
                "Channels": len(group.channels()),
                "Properties": dict(group.properties)
            }
            self.show_properties(props)

        elif "channel" in item_tags:
            group_name = self.tree.item(parent_id, "text")
            channel_name = item_text
            self.current_channel = self.tdms_file[group_name][channel_name]
            self.current_page = 0
            self.load_page()

            props = {
                "Channel": channel_name,
                "Data type": str(self.current_channel.data_type),
                "Length": len(self.current_channel),
                "Properties": dict(self.current_channel.properties)
            }
            self.show_properties(props)

    def load_page(self):
        if self.current_channel is None:
            return

        total_length = len(self.current_channel)
        start = self.current_page * self.page_size
        end = min(start + self.page_size, total_length)

        self.table.delete(*self.table.get_children())
        preview = self.current_channel[start:end]

        for i, val in enumerate(preview, start=start):
            self.table.insert("", "end", values=(i, val))

        self.ax.clear()
        self.ax.plot(range(start, end), preview, marker='o', linestyle='-')
        self.ax.set_title(f"Page {self.current_page + 1}")
        self.ax.set_xlabel("Index")
        self.ax.set_ylabel("Value")
        self.ax.grid(True)
        self.canvas.draw()

        total_pages = (total_length + self.page_size - 1) // self.page_size
        self.page_label.config(text=f"Page {self.current_page + 1} of {total_pages}")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page()

    def next_page(self):
        if not self.current_channel:
            return
        total_pages = (len(self.current_channel) + self.page_size - 1) // self.page_size
        if self.current_page + 1 < total_pages:
            self.current_page += 1
            self.load_page()

    def jump_to_page(self):
        if not self.current_channel:
            messagebox.showinfo("No Channel", "Select a channel first.")
            return

        entry_value = self.page_entry.get()
        if not entry_value.strip():
            messagebox.showwarning("Input Missing", "Enter a page number.")
            return

        try:
            page = int(entry_value) - 1
            total_pages = (len(self.current_channel) + self.page_size - 1) // self.page_size
            if 0 <= page < total_pages:
                self.current_page = page
                self.load_page()
            else:
                messagebox.showwarning("Out of Range", f"Enter a page between 1 and {total_pages}")
        except ValueError:
            messagebox.showerror("Invalid Input", "Enter a valid integer.")

    def show_properties(self, props):
        self.prop_text.config(state='normal')
        self.prop_text.delete(1.0, tk.END)
        self.prop_text.insert(tk.END, pprint.pformat(props, indent=2))
        self.prop_text.config(state='disabled')

    def clear_properties(self):
        self.prop_text.config(state='normal')
        self.prop_text.delete(1.0, tk.END)
        self.prop_text.config(state='disabled')

if __name__ == "__main__":
    app = TDMSViewer()
    app.mainloop()
