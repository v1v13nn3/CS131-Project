import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import os
from PIL import Image, ImageTk


class DashboardModule(tk.Frame):
    def __init__(self, parent, process_module, json_path="items.json", max_items=5):
        super().__init__(parent)
        self.process_module = process_module
        self.recent_barcodes = []
        self.icon_up = ImageTk.PhotoImage(Image.open("icons/up_arrow.png").resize((16, 16)))
        self.icon_down = ImageTk.PhotoImage(Image.open("icons/down_arrow.png").resize((16, 16)))
        self.icon_same = ImageTk.PhotoImage(Image.open("icons/no_change.png").resize((16, 16)))

        self.json_path = json_path
        self.max_items = max_items

        self.recent_frame = ttk.LabelFrame(self, text="Recently Bought Items")
        self.recent_frame.pack(fill='x', padx=10, pady=10)

        self.graph_frame = ttk.LabelFrame(self, text="Top Item Price Trends")
        self.graph_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(pady=5)
        reset_button = ttk.Button(self.button_frame, text="Reset History", command=self.reset_history)
        reset_button.pack()

        # Add column headers
        header_frame = tk.Frame(self.recent_frame)
        header_frame.pack(anchor="w", pady=(0, 5))
        tk.Label(header_frame, text="", width=2).pack(side="left")  # icon spacer
        tk.Label(header_frame, text="Name", width=13, anchor="w").pack(side="left")
        tk.Label(header_frame, text="Current Price", width=18, anchor="w").pack(side="left")
        tk.Label(header_frame, text="Δ (Change)", width=20, anchor="w").pack(side="left")

        self.recent_labels = []
        for _ in range(self.max_items):
            frame = tk.Frame(self.recent_frame)
            frame.pack(anchor="w", pady=2)

            icon_label = tk.Label(frame, width=2)
            icon_label.pack(side="left")

            name_label = ttk.Label(frame, width=25, anchor="w")
            name_label.pack(side="left")

            price_label = ttk.Label(frame, width=15, anchor="w")
            price_label.pack(side="left")

            delta_label = ttk.Label(frame, width=10, anchor="w")
            delta_label.pack(side="left")

            self.recent_labels.append((icon_label, name_label, price_label, delta_label))

        self.figure, self.ax = plt.subplots(figsize=(5, 3))
        self.canvas = FigureCanvasTkAgg(self.figure, self.graph_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self.load_existing_data()

    def update_dashboard(self, transaction_barcodes):
        if not os.path.exists(self.json_path):
            self.clear_dashboard_ui("No data available.")
            return

        with open(self.json_path, 'r') as f:
            items = json.load(f)

        self.recent_barcodes.extend(transaction_barcodes)

        seen = {}
        for barcode in reversed(self.recent_barcodes):
            if barcode in items and barcode not in seen:
                seen[barcode] = items[barcode]

        recent_items = list(seen.items())[:self.max_items]

        # Update graph with top items
        sorted_items = sorted(items.items(), key=lambda x: x[1].get("total_bought", 0), reverse=True)
        top_items = sorted_items[:5]

        self.ax.clear()
        for idx, (barcode, item) in enumerate(top_items):
            name = item.get("item_name", f"Item {idx}")
            history = item.get("history", [])[-10:]  # Last 10 entries

            if len(history) >= 2:
                self.ax.plot(range(len(history)), history, label=name, linewidth=2, marker='o')
            elif len(history) == 1:
                self.ax.plot([0, 1], [history[0], history[0]], label=name, linewidth=2, marker='o')

        self.ax.set_xticks([])
        self.ax.set_title("Top 5 Most Bought Items – Price Trend")
        self.ax.set_ylabel("Current Price")
        self.ax.set_xlabel("Change in Price")
        self.ax.legend()
        self.ax.grid(True)
        self.canvas.draw()

        for i, (icon_label, name_label, price_label, delta_label) in enumerate(self.recent_labels):
            if i < len(recent_items):
                barcode, data = recent_items[i]
                name = data.get("item_name", "Unknown")
                current = data.get("current_price", 0.0)
                base = data.get("base_price", 0.0)
                history = data.get("history", [])
                delta = current - base
                prev_price = history[-2] if len(history) >= 2 else base
                icon = self.get_trend_icon_image(current, prev_price)

                icon_label.config(image=icon)
                icon_label.image = icon
                name_label.config(text=name)
                price_label.config(text=f"${current:.2f}")
                delta_label.config(text=f"{delta:+.2f}")
            else:
                icon_label.config(image="")
                name_label.config(text="Waiting for data...")
                price_label.config(text="")
                delta_label.config(text="")

    def get_trend_icon_image(self, current, base):
        if current > base:
            return self.icon_up
        elif current < base:
            return self.icon_down
        else:
            return self.icon_same

    def reset_history(self):
        confirm = tk.messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all item histories?")
        if confirm:
            self.process_module.reset_history()
            self.recent_barcodes.clear()
            self.update_dashboard([])
            tk.messagebox.showinfo("Reset Done", "All item histories and prices have been reset.")

    def load_existing_data(self):
        if not os.path.exists(self.json_path):
            return

        with open(self.json_path, 'r') as f:
            items = json.load(f)

        items_with_history = {k: v for k, v in items.items() if v.get("history")}
        sorted_items = sorted(items_with_history.items(), key=lambda x: x[1].get("total_bought", 0), reverse=True)
        top_items = sorted_items[:self.max_items]
        self.recent_barcodes = [barcode for barcode, _ in top_items]
        self.update_dashboard(self.recent_barcodes)

    def clear_dashboard_ui(self, message="Waiting for data..."):
        self.ax.clear()
        self.ax.set_title("Most Bought Items – Price Trend")
        self.ax.set_ylabel("Current Price")
        self.ax.set_xlabel("Change in Price")
        self.ax.grid(True)
        self.canvas.draw()

        for icon_label, name_label, price_label, delta_label in self.recent_labels:
            icon_label.config(image="")
            name_label.config(text=message)
            price_label.config(text="")
            delta_label.config(text="")
