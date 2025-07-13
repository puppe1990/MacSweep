#!/usr/bin/env python3
"""Simple Tkinter GUI for MacSweep"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from macsweep import FileScanner, CleanupEngine


class MacSweepGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MacSweep GUI")
        self.scanner = FileScanner()
        self.engine = CleanupEngine()
        self.scan_results = {}
        self.category_order = []

        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        path_label = ttk.Label(frame, text="Directory:")
        path_label.grid(row=0, column=0, sticky=tk.W)
        self.path_var = tk.StringVar(value=os.path.expanduser("~"))
        path_entry = ttk.Entry(frame, textvariable=self.path_var, width=40)
        path_entry.grid(row=0, column=1, sticky=tk.W)
        browse_btn = ttk.Button(frame, text="Browse", command=self.browse_path)
        browse_btn.grid(row=0, column=2, padx=5)

        depth_label = ttk.Label(frame, text="Depth:")
        depth_label.grid(row=1, column=0, sticky=tk.W)
        self.depth_var = tk.IntVar(value=3)
        depth_spin = ttk.Spinbox(frame, from_=1, to=10, textvariable=self.depth_var, width=5)
        depth_spin.grid(row=1, column=1, sticky=tk.W)

        self.dry_var = tk.BooleanVar()
        dry_check = ttk.Checkbutton(frame, text="Dry run", variable=self.dry_var)
        dry_check.grid(row=1, column=2, sticky=tk.W)

        scan_btn = ttk.Button(frame, text="Scan", command=self.scan)
        scan_btn.grid(row=2, column=0, pady=5, sticky=tk.W)

        self.listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, width=50, height=10)
        self.listbox.grid(row=3, column=0, columnspan=3, pady=5, sticky=tk.W+tk.E)

        clean_btn = ttk.Button(frame, text="Clean Selected", command=self.clean)
        clean_btn.grid(row=4, column=0, pady=5, sticky=tk.W)

        self.status_var = tk.StringVar()
        status_label = ttk.Label(frame, textvariable=self.status_var)
        status_label.grid(row=5, column=0, columnspan=3, sticky=tk.W)

    def browse_path(self):
        path = filedialog.askdirectory(initialdir=self.path_var.get())
        if path:
            self.path_var.set(path)

    def scan(self):
        path = self.path_var.get()
        if not os.path.isdir(path):
            messagebox.showerror("Error", "Selected path is not a directory")
            return

        self.status_var.set("Scanning...")
        self.root.update()
        self.scan_results = self.scanner.scan_directory(path, self.depth_var.get(), show_progress=False)
        self.status_var.set("Scan complete")

        self.listbox.delete(0, tk.END)
        self.category_order = []
        for category, files in self.scan_results.items():
            if not files:
                continue
            size = sum(s for _, s, _ in files)
            text = f"{category} ({len(files)} files, {self.engine.format_size(size)})"
            self.listbox.insert(tk.END, text)
            self.category_order.append(category)

    def clean(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo("MacSweep", "No categories selected")
            return
        selected_files = []
        total_size = 0
        for idx in selection:
            category = self.category_order[idx]
            for path, size, _ in self.scan_results[category]:
                selected_files.append(path)
                total_size += size

        confirm = messagebox.askyesno(
            "Confirm Cleanup",
            f"Remove {len(selected_files)} files?\nTotal size: {self.engine.format_size(total_size)}"
        )
        if not confirm:
            return

        self.engine.set_dry_run(self.dry_var.get())
        files_removed, bytes_freed = self.engine.cleanup_files(selected_files)
        messagebox.showinfo(
            "MacSweep",
            f"Cleanup complete.\nFiles removed: {files_removed}\nSpace freed: {self.engine.format_size(bytes_freed)}"
        )
        self.scan_results = {}
        self.listbox.delete(0, tk.END)
        self.status_var.set("Ready")


def main():
    root = tk.Tk()
    app = MacSweepGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
