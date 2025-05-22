import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import os
from PIL import Image, ImageTk


class DashboardModule(tk.Frame):
    def __init__(self, parent, process_module, json_path="items.json", max_items=5):
        super().__init__(parent)
        self.process_module = process_module
        self.recent_barcodes = []  # This keeps a running log
        self.icon_up = ImageTk.PhotoImage(Image.open("icons/up_arrow.png").resize((16, 16)))
        self.icon_down = ImageTk.PhotoImage(Image.open("icons/down_arrow.png").resize((16, 16)))
        self.icon_same = ImageTk.PhotoImage(Image.open("icons/no_change.png").resize((16, 16)))

        self.json_path = json_path
        self.max_items = max_items

        self.recent_frame = ttk.LabelFrame(self, text="Recently Bought Items")
        self.recent_frame.pack(fill='x', padx=10, pady=10)

        self.graph_frame = ttk.LabelFrame(self, text="Top Item Price Trends")
        self.graph_frame.pack(fill='both', expand=True, padx=10, pady=10)

        #Reset values button
        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(pady=5)

        reset_button = ttk.Button(self.button_frame, text="Reset History", command=self.reset_history)
        reset_button.pack()

        self.recent_labels = []
        for _ in range(self.max_items):
            frame = tk.Frame(self.recent_frame)
            frame.pack(anchor="w", pady=2)

            icon_label = tk.Label(frame)  # Image holder
            icon_label.pack(side="left")

            text_label = ttk.Label(frame, text="Waiting for data...")
            text_label.pack(side="left")

            self.recent_labels.append((icon_label, text_label))

        self.figure, self.ax = plt.subplots(figsize=(5, 3))
        self.canvas = FigureCanvasTkAgg(self.figure, self.graph_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self.load_existing_data()

    def update_dashboard(self, transaction_barcodes):
        if not os.path.exists(self.json_path):
            # Clear UI if data doesn't exist
            self.clear_dashboard_ui("No data available.")
            return

        with open(self.json_path, 'r') as f:
            items = json.load(f)

        self.recent_barcodes.extend(transaction_barcodes)

        # remove duplicates, keep most recent instance
        seen = {}
        for barcode in reversed(self.recent_barcodes):
            if barcode in items and barcode not in seen:
                seen[barcode] = {
                    "name": items[barcode]["item_name"],
                    "current_price": items[barcode]["current_price"],
                    "base_price": items[barcode]["base_price"],
                    "meter": items[barcode].get("meter", 0),
                }

 
        sorted_items = sorted(
            items.items(),
            key=lambda x: x[1].get("total_bought", 0),
            reverse=True
        )
        
        if not sorted_items:
            self.clear_dashboard_ui("No items to display.")
            return

        top_items = sorted_items[:5]

        self.ax.clear()
        

        for idx, (barcode, item) in enumerate(top_items):
            name = item.get("item_name", f"Item {idx}")
            history = item.get("history", [])

            if len(history) >= 2:
                self.ax.plot(
                    list(range(len(history))),
                    history,
                    label=name,
                    linewidth=2,
                    marker='o'
                )
            elif len(history) == 1:
                # Show flat line if only one data point
                self.ax.plot([0, 1], [history[0], history[0]], label=name, linewidth=2, marker='o')

        self.ax.set_xticks([])  # Can adjust ticks for num of days
        self.ax.set_title("Top 5 Most Bought Items – Price Trend")
        self.ax.set_ylabel("Current Price")
        self.ax.set_xlabel("Change in Price")
        self.ax.legend()
        self.ax.grid(True)
        self.canvas.draw()

        # Update recent label UI
        for i, (icon_label, text_label) in enumerate(self.recent_labels):
            if i < len(top_items):
                barcode, data = top_items[i]
                name = data["item_name"]
                current = data["current_price"]
                base = data["base_price"]
                history = data.get("history", [])

                # Calculate delta relative to base price
                delta = current - base

                # Determine previous price for arrow comparison
                if len(history) >= 2:
                    prev_price = history[-2]
                else:
                    prev_price = base

                # Get arrow icon based on comparison to previous price
                icon = self.get_trend_icon_image(current, prev_price)

                icon_label.config(image=icon)
                icon_label.image = icon
                text_label.config(text=f"{name}  {delta:+.2f}")
            else:
                icon_label.config(image="")
                text_label.config(text="Waiting for data...")


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
            self.recent_barcodes.clear()  # Clear recent barcodes list 
            self.update_dashboard([])  # Refresh dashboard
            tk.messagebox.showinfo("Reset Done", "All item histories and prices have been reset.")

    def load_existing_data(self):
        if not os.path.exists(self.json_path):
            return
        
        with open(self.json_path, 'r') as f:
            items = json.load(f)

        # Filter items with non-empty history
        items_with_history = {k: v for k, v in items.items() if v.get("history")}

        # Sort by total_bought or any other metric you prefer (fall back to items with history)
        sorted_items = sorted(
            items_with_history.items(),
            key=lambda x: x[1].get("total_bought", 0),
            reverse=True
        )

        # Limit to max_items
        top_items = sorted_items[:self.max_items]

        # Update recent_barcodes with those top item barcodes
        self.recent_barcodes = [barcode for barcode, _ in top_items]

        # Call the dashboard update with these barcodes to update UI
        self.update_dashboard(self.recent_barcodes)

    def clear_dashboard_ui(self, message="Waiting for data..."):
        self.ax.clear()
        self.ax.set_title("Top 5 Most Bought Items – Price Trend")
        self.ax.set_ylabel("Current Price")
        self.ax.set_xlabel("Change in Price")
        self.ax.grid(True)
        self.canvas.draw()

        for icon_label, text_label in self.recent_labels:
            icon_label.config(image="")
            text_label.config(text=message)

        self.summary_label.config(text="Market Trend: --", foreground="black")
