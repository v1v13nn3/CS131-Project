import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2

from capture_module import CaptureModule
from item_data_manager import ItemDataManager
from process_module import ItemProcessor
from network_manager import NetworkManager, get_local_ip

import time
from datetime import datetime

# --- Global Configuration ---
# Set this IP to the IP address of the OTHER computer on your local network.
# You need to find this manually (e.g., using `ipconfig` on Windows, `ifconfig` on macOS/Linux).
OTHER_STORE_IP = """ TODO: Fill in IP adress """ # <--- IMPORTANT: REPLACE THIS WITH THE ACTUAL IP OF THE OTHER MACHINE

JSON_FILE = "items.json" # Path to your item data file

# --- Application Class ---
class DemandSyncApp:
    def __init__(self, root, is_this_store_server = False):
        """
        Initializes the DemandSync application.
        :param root: The Tkinter root window.
        :param is_this_store_server: Set to True if this instance is Store 1 (binds to 5556, connects to 5557),
                                     False if it is Store 2 (binds to 5557, connects to 5556).
        """
        self.root = root
        self.root.title(f"DemandSync (Store {'1' if is_this_store_server else '2'}) - My IP: {get_local_ip()}")

        # --- Module Instances ---
        self.capture_module = CaptureModule()
        self.item_data_manager = ItemDataManager(filepath = JSON_FILE)
        self.item_processor = ItemProcessor(item_data_manager = self.item_data_manager)
        self.network_manager = NetworkManager(
            item_data_manager = self.item_data_manager,
            is_this_store_server = is_this_store_server,
            other_store_ip = OTHER_STORE_IP
        )

        # --- UI Elements ---
        self.video_label = tk.Label(root)
        self.video_label.pack(pady = 10)

        self.scan_button = tk.Button(root, text = "Scan Barcode", command = self.handle_scan)
        self.scan_button.pack(pady = 5)

        self.finish_button = tk.Button(root, text = "Finish Transaction", command = self.finish_transaction)
        self.finish_button.pack(pady = 5)

        self.result_text = tk.Text(root, height = 10, width = 50, state = 'normal')
        self.result_text.pack(pady = 10)

        # --- Application State ---
        self.transaction_barcodes = []
        self.last_hourly_check_time = time.time()
        self.last_daily_check_time = time.time()

        # Simulated intervals (in seconds)
        self.hourly_interval_simulated = 5
        self.daily_interval_simulated = 12

        # Start periodic tasks
        self.start_periodic_tasks()

        # Bind window close event to shutdown network manager
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def start_periodic_tasks(self):
        """ Schedules the hourly and daily tasks to run periodically. """
        self.check_hourly_tasks()
        self.check_daily_tasks()

    def check_hourly_tasks(self):
        """ Checks if the simulated hourly interval has passed and runs the task. """
        if time.time() - self.last_hourly_check_time >= self.hourly_interval_simulated:
            self.last_hourly_check_time = time.time()
            self.run_hourly_tasks()
        self.root.after(1000, self.check_hourly_tasks)

    def check_daily_tasks(self):
        """ Checks if the simulated daily interval has passed and runs the task. """
        if time.time() - self.last_daily_check_time >= self.daily_interval_simulated:
            self.last_daily_check_time = time.time()
            self.run_daily_tasks()
        self.root.after(1000, self.check_daily_tasks)

    def run_hourly_tasks(self):
        """ Executes tasks that simulate hourly processes. """
        self.log_message("Simulating hourly process: Sending price updates to other store...")
        # Both client and server roles will send their prices
        self.network_manager.send_prices_to_other_store()

    def run_daily_tasks(self):
        """ Executes tasks that simulate daily processes. """
        self.log_message("Simulating daily process: Decaying prices of unsold items...")
        self.item_processor.decay_prices()

    def handle_scan(self):
        """ Handles the 'Scan Barcode' button click event. """
        try:
            frame, results = self.capture_module.capture_pipeline()

            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_tk = ImageTk.PhotoImage(img_pil)
            self.video_label.imgtk = img_tk
            self.video_label.configure(image = img_tk)

            output_lines = []
            if not results:
                output_lines.append("No barcode found.")
            else:
                for barcode_data, barcode_type in results:
                    name, price = self.item_data_manager.get_item_details(barcode_data)
                    if name and price is not None:
                        self.transaction_barcodes.append(barcode_data)
                        output_lines.append(f"Scanned {barcode_data}: {name} - ${round(price, 2)}")
                    else:
                        output_lines.append(f"Item with barcode {barcode_data} not found.")

            self.log_message("\n".join(reversed(output_lines)))

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during scan: {e}")
            self.log_message(f"Error during scan: {e}")

    def finish_transaction(self):
        """ Handles the 'Finish Transaction' button click event. """
        if not self.transaction_barcodes:
            messagebox.showinfo("Info", "No items bought in this transaction.")
            self.log_message("No items in current transaction.")
            return

        self.log_message("Processing transaction...")
        self.item_processor.process_pipeline(self.transaction_barcodes)

        self.transaction_barcodes.clear()
        self.log_message("Transaction processed. Ready for next transaction.")
        messagebox.showinfo("Transaction Complete", "Transaction processed successfully!")

    def log_message(self, message):
        """ Logs a message to the Tkinter text widget and console. """
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        full_message = f"{timestamp} {message}\n"
        self.result_text.insert('1.0', full_message)
        num_lines = int(self.result_text.index('end-1c').split('.')[0])
        if num_lines > 100:
            self.result_text.delete('101.0', 'end')
        self.result_text.see('1.0')
        print(full_message.strip())

    def _on_closing(self):
        """ Handles the window closing event to ensure proper shutdown. """
        print("Application closing. Shutting down network manager...")
        self.network_manager.shutdown()
        self.capture_module.__del__()
        self.root.destroy()

# --- Main Application Entry Point ---
if __name__ == "__main__":
    # Determine if this instance is Store 1 or Store 2.
    # Set IS_THIS_STORE_SERVER = True for one computer (e.g., Store 1).
    # Set IS_THIS_STORE_SERVER = False for the other computer (e.g., Store 2).
    IS_THIS_STORE_SERVER = """ TODO: Fill in True or False """ # <--- IMPORTANT: SET THIS TO TRUE FOR ONE COMPUTER, FALSE FOR THE OTHER

    root = tk.Tk()
    app = DemandSyncApp(root, is_this_store_server = IS_THIS_STORE_SERVER)
    root.mainloop()
