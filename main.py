import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
from dashboard_module import DashboardModule
from capture_module import CaptureModule
from item_data_manager import ItemDataManager
from process_module import ItemProcessor
from network_manager import NetworkManager, get_local_ip

import time
from datetime import datetime

# --- Global Configuration ---
# Set this IP to the IP address of the OTHER computer on your local network.
# You need to find this manually (e.g., using `ipconfig` on Windows, `ifconfig` on macOS/Linux).
OTHER_STORE_IP = "172.20.10.4" # <--- IMPORTANT: REPLACE THIS WITH THE ACTUAL IP OF THE OTHER MACHINE

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
        self.root.geometry("1000x600")  # Optional: set a window size

        # Create two main frames for left (scanner) and right (dashboard)
        self.left_frame = tk.Frame(root)
        self.left_frame.pack(side="left", fill="both", expand=True)

        self.right_frame = tk.Frame(root)
        self.right_frame.pack(side="right", fill="both", expand=True)

        # Left Side of UI
        self.camera_frame = tk.Frame(self.left_frame)
        self.camera_frame.pack(fill="x")

        self.video_label = tk.Label(self.camera_frame)
        self.video_label.pack()

        self.root.bind("<Configure>", self._on_resize)

        self.scan_button = tk.Button(self.left_frame, text="Scan Barcode", command=self.handle_scan)
        self.scan_button.pack()

        self.finish_button = tk.Button(self.left_frame, text="Finish Transaction", command=self.finish_transaction)
        self.finish_button.pack()

        # self.result_text = tk.Text(self.left_frame, height=10, width=50)
        # self.result_text.pack()

        self.log_frames = {}
        self.log_text_widgets = {}

        log_types = {
            "Scan Data": "scan",
            "Sent Network Data": "sent", # MODIFIED: Changed "send" to "sent" for consistency
            "Received Network Data": "received",
            "Price Adjustments/Decay": "process"
        }

        for title, log_type in log_types.items(): # ADDED: Loop to create multiple log feeds
            frame = tk.LabelFrame(self.right_frame, text=title, bd=2, relief="groove") # ADDED: LabelFrame for each feed
            frame.pack(fill="both", expand=True, padx=5, pady=2) # ADDED: Pack the frame
            
            text_widget = tk.Text(frame, height=5, width=60, state='normal', wrap='word', font=('Consolas', 9)) # ADDED: Text widget for log
            text_widget.pack(side="left", fill="both", expand=True) # ADDED: Pack text widget
            
            scrollbar = tk.Scrollbar(frame, command=text_widget.yview) # ADDED: Scrollbar for text widget
            scrollbar.pack(side="right", fill="y") # ADDED: Pack scrollbar
            text_widget.config(yscrollcommand=scrollbar.set) # ADDED: Configure scrollbar

            self.log_frames[log_type] = frame # ADDED: Store frame reference
            self.log_text_widgets[log_type] = text_widget # ADDED: Store text widget reference

        # ADDED: Pass the central logging function to modules
        self.item_data_manager = ItemDataManager(filepath=JSON_FILE, log_callback=self._log_message) # MODIFIED: Pass log_callback
        self.item_processor = ItemProcessor(item_data_manager=self.item_data_manager, log_callback=self._log_message) # MODIFIED: Pass log_callback
        
        # --- Module Instances ---
        self.capture_module = CaptureModule()
        # self.item_data_manager = ItemDataManager(filepath = JSON_FILE)
        # self.item_processor = ItemProcessor(item_data_manager = self.item_data_manager)
        self.network_manager = NetworkManager(
            item_data_manager = self.item_data_manager,
            is_this_store_server = is_this_store_server,
            other_store_ip = OTHER_STORE_IP,
            log_callback=self._log_message
        )

        # Right Side of UI
        self.dashboard = DashboardModule(self.right_frame, self.item_processor)
        self.dashboard.pack(fill="both", expand=True)

        # --- Application State ---
        self.transaction_barcodes = []
        self.last_hourly_check_time = time.time()
        self.last_daily_check_time = time.time()

        # Simulated intervals (in seconds)
        self.hourly_interval_simulated = 10
        self.daily_interval_simulated = 120

        # Start periodic tasks
        self.start_periodic_tasks()
        self.update_camera()
        self.start_dashboard_refresh()

        # Bind window close event to shutdown network manager
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def start_periodic_tasks(self):
        """ Schedules the hourly and daily tasks to run periodically. """
        self.check_hourly_tasks()
        self.check_daily_tasks()

    def check_hourly_tasks(self):
        """ Checks if the simulated hourly interval has passed and runs the task. """
        if time.time() - self.last_hourly_check_time >= self.hourly_interval_simulated:
            self.run_hourly_tasks()
        self.root.after(1000, self.check_hourly_tasks)

    def check_daily_tasks(self):
        """ Checks if the simulated daily interval has passed and runs the task. """
        if time.time() - self.last_daily_check_time >= self.daily_interval_simulated:
            self.run_daily_tasks()
        self.root.after(1000, self.check_daily_tasks)

    def run_hourly_tasks(self):
        """ Executes tasks that simulate hourly processes. """
        self._log_message("Simulating hourly process: Sending price updates to other store...", "sent")
        # Both client and server roles will send their prices
        self.network_manager.send_prices_to_other_store(self.last_hourly_check_time)
        self.last_hourly_check_time = time.time()

    def run_daily_tasks(self):
        """ Executes tasks that simulate daily processes. """
        self._log_message("Simulating daily process: Decaying prices of unsold items...", "process")
        self.item_processor.decay_prices(self.last_daily_check_time)
        self.dashboard.update_dashboard([])
        self.last_daily_check_time = time.time()

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

            self._log_message("\n".join(reversed(output_lines)), "scan")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during scan: {e}")
            self._log_message(f"Error during scan: {e}")

    def finish_transaction(self):
        """ Handles the 'Finish Transaction' button click event. """
        if not self.transaction_barcodes:
            messagebox.showinfo("Info", "No items bought in this transaction.")
            self._log_message("No items in current transaction.")
            return
        
        self._log_message("Processing transaction...", "scan")
        self.item_processor.process_pipeline(self.transaction_barcodes)
        self.dashboard.update_dashboard(self.transaction_barcodes)
        self.transaction_barcodes.clear()
        # self.result_text.delete('1.0', tk.END)
        self._log_message("Transaction processed. Ready for next transaction.", "scan")
        # self.result_text.insert(tk.END, "Transaction processed.\n")
        messagebox.showinfo("Transaction Complete", "Transaction processed successfully!")

    #update the image with live feed of the camera
    def update_camera(self):
        ret, frame = self.capture_module.camera.read()
        if ret:
            frame_height, frame_width = frame.shape[:2]
            frame_aspect_ratio = frame_width / frame_height

            # Get the current label dimensions
            label_width = self.video_label.winfo_width()
            label_height = self.video_label.winfo_height()

            if label_width == 1 and label_height == 1:
                # Default when widget hasn't been fully drawn yet
                label_width = 640
                label_height = 480

            label_aspect_ratio = label_width / label_height

            # Adjust image size to fit within the label while preserving aspect ratio
            if label_aspect_ratio > frame_aspect_ratio:
                new_height = label_height
                new_width = int(frame_aspect_ratio * new_height)
            else:
                new_width = label_width
                new_height = int(new_width / frame_aspect_ratio)

            resized_frame = cv2.resize(frame, (new_width, new_height))
            img_rgb = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_tk = ImageTk.PhotoImage(img_pil)

            self.video_label.imgtk = img_tk
            self.video_label.configure(image=img_tk)

        self.root.after(30, self.update_camera)


    def _log_message(self, message, log_type="scan"): # MODIFIED: Renamed to private, added log_type parameter
        """ Logs a message to the appropriate Tkinter text widget and console. """
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        full_message = f"{timestamp} {message}\n"

        target_widget = self.log_text_widgets.get(log_type) # ADDED: Get target widget based on log_type
        if target_widget: # ADDED: Check if widget exists
            target_widget.insert('1.0', full_message) # MODIFIED: Insert into specific widget
            num_lines = int(target_widget.index('end-1c').split('.')[0]) # MODIFIED: Count lines in specific widget
            if num_lines > 100: # Keep only the last 100 lines
                target_widget.delete('101.0', 'end') # MODIFIED: Delete from specific widget
            target_widget.see('1.0') # MODIFIED: Scroll specific widget to top
        else: # ADDED: Fallback for invalid log_type
            print(f"[{log_type.upper()} - ERROR] {full_message.strip()}")

        print(full_message.strip()) # Always print to console for debugging

    def _on_closing(self):
        """ Handles the window closing event to ensure proper shutdown. """
        print("Application closing. Shutting down network manager...")
        self.network_manager.shutdown()
        self.capture_module.camera.release()
        self.root.destroy()

    def start_dashboard_refresh(self):
        """ Periodically refresh dashboard to show price changes (e.g. decay). """
        self.dashboard.update_dashboard([])  # Pass empty list, no new transactions
        self.root.after(10000, self.start_dashboard_refresh)  # Refresh every 10 seconds

    def _on_resize(self, event):
        """Ensure video_label stays within 2/3 of the window height."""
        max_height = int(self.root.winfo_height() * 2 / 3)
        self.camera_frame.configure(height=max_height)
        self.camera_frame.pack_propagate(False)


# --- Main Application Entry Point ---
if __name__ == "__main__":
    # Determine if this instance is Store 1 or Store 2.
    # Set IS_THIS_STORE_SERVER = True for one computer (e.g., Store 1).
    # Set IS_THIS_STORE_SERVER = False for the other computer (e.g., Store 2).
    IS_THIS_STORE_SERVER = False # <--- IMPORTANT: SET THIS TO TRUE FOR ONE COMPUTER, FALSE FOR THE OTHER

    root = tk.Tk()
    app = DemandSyncApp(root, is_this_store_server = IS_THIS_STORE_SERVER)
    root.mainloop()
    

