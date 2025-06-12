import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from nptdms import TdmsFile
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pprint
import os

class TDMSViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TDMS Viewer with Paging")
        self.geometry("1000x700")

        self.tdms_file = None
        self.current_channel = None
        self.current_group = None
        self.page_size = 100
        self.current_page = 0

        self.create_widgets()

    def create_widgets(self):
        # Menu
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open TDMS File", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

        # Left panel
        left_frame = tk.Frame(self)
        left_frame.pack(side="left", fill="y", padx=5, pady=5)

        self.tree = ttk.Treeview(left_frame)
        self.tree.heading("#0", text="TDMS Structure", anchor='w')
        self.tree.pack(fill="both", expand=True)

        tk.Label(left_frame, text="Properties:").pack(anchor="w")
        self.prop_text = tk.Text(left_frame, height=12, width=40, state='disabled', bg='#f0f0f0')
        self.prop_text.pack(fill="both", expand=False)

        # Right panel
        right_paned = tk.PanedWindow(self, orient=tk.VERTICAL)
        right_paned.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # Table and navigation
        table_frame = tk.Frame(right_paned)
        self.table = ttk.Treeview(table_frame, columns=("Index", "Value"), show='headings')
        self.table.heading("Index", text="Index")
        self.table.heading("Value", text="Value")
        self.table.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        nav_frame = tk.Frame(table_frame)
        nav_frame.pack(fill="x", pady=2)

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

        right_paned.add(table_frame, stretch="always")

        # Plot
        plot_frame = tk.Frame(right_paned)
        self.fig, self.ax = plt.subplots(figsize=(7, 3))
        self.ax.set_title("Channel Data Plot")
        self.ax.set_xlabel("Index")
        self.ax.set_ylabel("Value")

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        right_paned.add(plot_frame, stretch="always")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("TDMS files", "*.tdms")])
        if not file_path:
            return

        try:
            self.tdms_file = TdmsFile.open(file_path)
            self.tree.delete(*self.tree.get_children())
            self.table.delete(*self.table.get_children())
            self.clear_properties()
            self.ax.clear()
            self.canvas.draw()
            self.build_tree(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open TDMS file:\n{e}")

    def build_tree(self, filepath):
        root_id = self.tree.insert("", "end", text=os.path.basename(filepath), open=True, tags=("file",))
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

        self.table.delete(*self.table.get_children())
        self.clear_properties()
        self.ax.clear()

        if "file" in item_tags:
            props = {
                "File": item_text,
                "Groups": len(self.tdms_file.groups()),
                "Channels": sum(len(g.channels()) for g in self.tdms_file.groups())
            }
            self.show_properties(props)

        elif "group" in item_tags:
            group = self.tdms_file[item_text]
            props = {
                "Group name": group.name,
                "Channels": len(group.channels()),
                "Properties": dict(group.properties)
            }
            self.show_properties(props)

        elif "channel" in item_tags:
            group_name = self.tree.item(parent_id, "text")
            self.current_group = group_name
            self.current_channel = self.tdms_file[group_name][item_text]
            self.current_page = 0

            self.show_properties({
                "Channel name": self.current_channel.name,
                "Data type": str(self.current_channel.data_type),
                "Data count": len(self.current_channel),
                "Properties": dict(self.current_channel.properties)
            })

            self.load_page()

    def load_page(self):
        if not self.current_channel:
            return

        self.table.delete(*self.table.get_children())
        self.ax.clear()

        total = len(self.current_channel)
        start = self.current_page * self.page_size
        end = min(start + self.page_size, total)
        data_slice = self.current_channel[start:end]

        for i, val in enumerate(data_slice, start=start):
            self.table.insert("", "end", values=(i, val))

        self.ax.plot(range(start, end), data_slice, marker='o', linestyle='-')
        self.ax.set_title(f"{self.current_group}/{self.current_channel.name}")
        self.ax.set_xlabel("Index")
        self.ax.set_ylabel("Value")
        self.ax.grid(True)
        self.canvas.draw()

        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        self.page_label.config(text=f"Page {self.current_page + 1} / {total_pages}")
        self.prev_btn.config(state="normal" if self.current_page > 0 else "disabled")
        self.next_btn.config(state="normal" if self.current_page < total_pages - 1 else "disabled")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page()

    def next_page(self):
        total_pages = (len(self.current_channel) + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.load_page()

    def jump_to_page(self):
        if not self.current_channel:
            messagebox.showinfo("No Channel Selected", "Please select a channel first.")
            return

        entry_value = self.page_entry.get()
        if not entry_value.strip():
            messagebox.showwarning("Missing Input", "Please enter a page number.")
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
            messagebox.showerror("Invalid Input", "Please enter a valid integer page number.")


    def show_properties(self, props):
        self.prop_text.configure(state='normal')
        self.prop_text.delete(1.0, tk.END)
        self.prop_text.insert(tk.END, pprint.pformat(props, indent=2))
        self.prop_text.configure(state='disabled')

    def clear_properties(self):
        self.prop_text.configure(state='normal')
        self.prop_text.delete(1.0, tk.END)
        self.prop_text.configure(state='disabled')


if __name__ == "__main__":
    app = TDMSViewer()
    app.mainloop()
