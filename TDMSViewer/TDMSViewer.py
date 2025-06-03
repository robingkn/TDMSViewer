import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from nptdms import TdmsFile
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pprint

class TDMSViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TDMS File Viewer with Properties Panel")
        self.geometry("1000x700")

        # Menu setup
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open TDMS File", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

        # Left frame contains tree + properties panel vertically stacked
        left_frame = tk.Frame(self)
        left_frame.pack(side="left", fill="y", padx=5, pady=5)

        # Treeview for TDMS structure
        self.tree = ttk.Treeview(left_frame)
        self.tree.heading("#0", text="TDMS Structure", anchor='w')
        self.tree.pack(fill="both", expand=True)

        # Properties panel (Text widget)
        prop_label = tk.Label(left_frame, text="Properties:")
        prop_label.pack(anchor="w")
        self.prop_text = tk.Text(left_frame, height=12, width=40, state='disabled', bg='#f0f0f0')
        self.prop_text.pack(fill="both", expand=False)

        # Right: PanedWindow (vertical) for table and plot
        right_paned = tk.PanedWindow(self, orient=tk.VERTICAL)
        right_paned.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # Table Frame
        table_frame = tk.Frame(right_paned)
        self.table = ttk.Treeview(table_frame, columns=("Index", "Value"), show='headings')
        self.table.heading("Index", text="Index")
        self.table.heading("Value", text="Value")
        self.table.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        right_paned.add(table_frame, stretch="always")

        # Plot Frame
        plot_frame = tk.Frame(right_paned)
        self.fig, self.ax = plt.subplots(figsize=(7, 3))
        self.ax.set_title("Channel Data Plot")
        self.ax.set_xlabel("Index")
        self.ax.set_ylabel("Value")

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        right_paned.add(plot_frame, stretch="always")

        # Bind tree selection event
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
            self.ax.set_title("Channel Data Plot")
            self.ax.set_xlabel("Index")
            self.ax.set_ylabel("Value")
            self.canvas.draw()
            self.build_tree(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open TDMS file:\n{e}")

    def build_tree(self, filepath):
        # Insert root node as file name
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

        # Clear previous data
        self.table.delete(*self.table.get_children())
        self.clear_properties()
        self.ax.clear()
        self.ax.set_title("Channel Data Plot")
        self.ax.set_xlabel("Index")
        self.ax.set_ylabel("Value")

        # If root node (file)
        if "file" in item_tags:
            # Show file properties
            props = {
                "File": item_text,
                "Number of groups": len(self.tdms_file.groups()),
                "Total channels": sum(len(g.channels()) for g in self.tdms_file.groups())
            }
            self.show_properties(props)

        # If group node
        elif "group" in item_tags:
            group = self.tdms_file[item_text]
            # Properties of group
            props = {
                "Group name": group.name,
                "Number of channels": len(group.channels()),
                "Properties": dict(group.properties)
            }
            self.show_properties(props)

        # If channel node
        elif "channel" in item_tags and parent_id:
            group_name = self.tree.item(parent_id, "text")
            channel_name = item_text
            channel = self.tdms_file[group_name][channel_name]

            # Show first 100 points in table
            preview = channel[:100]
            for i, val in enumerate(preview):
                self.table.insert("", "end", values=(i, val))

            # Plot data preview
            self.ax.plot(range(len(preview)), preview, marker='o', linestyle='-')
            self.ax.set_title(f"Plot: {group_name} / {channel_name}")
            self.ax.set_xlabel("Index")
            self.ax.set_ylabel("Value")
            self.ax.grid(True)
            self.canvas.draw()

            # Show channel properties
            props = {
                "Channel name": channel.name,
                "Data type": str(channel.data_type),
                "Data count": len(channel),
                "Properties": dict(channel.properties)
            }
            self.show_properties(props)

    def show_properties(self, props):
        self.prop_text.configure(state='normal')
        self.prop_text.delete(1.0, tk.END)
        pretty_props = pprint.pformat(props, indent=2)
        self.prop_text.insert(tk.END, pretty_props)
        self.prop_text.configure(state='disabled')

    def clear_properties(self):
        self.prop_text.configure(state='normal')
        self.prop_text.delete(1.0, tk.END)
        self.prop_text.configure(state='disabled')

if __name__ == "__main__":
    app = TDMSViewer()
    app.mainloop()
