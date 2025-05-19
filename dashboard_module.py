import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import os

class DashboardModule(tk.Frame):
    def __init__(self, parent, json_path="items.json", max_items=5):
        super().__init__(parent)
        self.json_path = json_path
        self.max_items = max_items

        self.recent_frame = ttk.LabelFrame(self, text="Recently Bought Items")
        self.recent_frame.pack(fill='x', padx=10, pady=10)

        self.graph_frame = ttk.LabelFrame(self, text="Top Item Price Trends")
        self.graph_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.recent_labels = []
        for _ in range(self.max_items):
            lbl = ttk.Label(self.recent_frame, text="Waiting for data...")
            lbl.pack(anchor="w")
            self.recent_labels.append(lbl)

        self.figure, self.ax = plt.subplots(figsize=(5, 3))
        self.canvas = FigureCanvasTkAgg(self.figure, self.graph_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

    def update_dashboard(self, transaction_barcodes):
        """
        Updates both the text and graph sections of the dashboard.
        """
        if not os.path.exists(self.json_path):
            return

        with open(self.json_path, 'r') as f:
            items = json.load(f)

        # Show recent items
        recent_barcodes = transaction_barcodes[-self.max_items:]
        for i, barcode in enumerate(reversed(recent_barcodes)):
            if barcode in items:
                name = items[barcode]["item_name"]
                base = items[barcode]["base_price"]
                current = items[barcode]["current_price"]
                trend = self.get_trend_icon(current, base)
                change = round(((current - base) / base) * 100, 2)
                self.recent_labels[i].configure(text=f"{name} {trend} +{change}%")
            else:
                self.recent_labels[i].configure(text=f"{barcode} - Unknown")

        # Graph most bought items
        sorted_items = sorted(items.items(), key=lambda x: x[1].get("meter", 0), reverse=True)
        top_items = sorted_items[:min(5, len(sorted_items))]

        self.ax.clear()
        for barcode, item in top_items:
            if "history" in item:
                self.ax.plot(item["history"], label=item["item_name"])
        self.ax.set_title("Price Trends")
        self.ax.set_ylabel("Price")
        self.ax.legend()
        self.canvas.draw()

    def get_trend_icon(self, current, base):
        if current > base:
            return "🔼"
        elif current < base:
            return "🔽"
        else:
            return "➖"
