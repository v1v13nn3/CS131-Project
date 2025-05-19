import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from capture_module import CaptureModule
import cv2
from fetch_module import FetchModule
from process_module import ProcessModule
from dashboard_module import DashboardModule

class DemandSync:
    def __init__(self, root):
        '''
        Main application loop that keeps time of all the app's processes

        while True:
            run main function -> main()
            simulate 1 hour by checking if 15 seconds have passed
                if yes then collect most recently updated items
                sync with other store
            simulate 1 day passing by checking id 360 seconds have passed
                if yes then decay the prices of items that have not been purchased in the last day
                make sure to not decrease bellow the base price
        '''

        '''
        This initializing function creates and runs the application window
        '''
        self.capMod = CaptureModule()
        self.processMod = ProcessModule()

        self.root = root
        self.root.title("DemandSync")
        self.root.geometry("1000x600")  # Optional: set a window size

        # Create two main frames for left (scanner) and right (dashboard)
        self.left_frame = tk.Frame(root)
        self.left_frame.pack(side="left", fill="both", expand=True)

        self.right_frame = tk.Frame(root)
        self.right_frame.pack(side="right", fill="both", expand=True)

        # --- LEFT: Scanning UI ---
        self.video_label = tk.Label(self.left_frame)
        self.video_label.pack()

        self.scan_button = tk.Button(self.left_frame, text="Scan Barcode", command=self.handle_scan)
        self.scan_button.pack()

        self.finish_button = tk.Button(self.left_frame, text="Finish Transaction", command=self.finish_transaction)
        self.finish_button.pack()

        self.result_text = tk.Text(self.left_frame, height=10, width=50)
        self.result_text.pack()

        # --- RIGHT: Dashboard UI ---
        self.dashboard = DashboardModule(self.right_frame)
        self.dashboard.pack(fill="both", expand=True)

        self.transaction = []
        #self.update_camera()


    def handle_scan(self):
        try:
            frame, results = self.capMod.capture_pipeline()

            # Convert frame to ImageTk and display
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_tk = ImageTk.PhotoImage(img_pil)
            self.video_label.imgtk = img_tk
            self.video_label.configure(image=img_tk)

            # Build the result string by iterating in reverse
            output_text = ""
            if not results:
                output_text = "No barcode found.\n"
            else:
                for barcode_data, barcode_type in reversed(results):
                    self.fetchMod = FetchModule()
                    name, price = self.fetchMod.fetch(barcode_data)
                    if name and price:
                        self.transaction.append(barcode_data)
                        output_text = f"Scanned {barcode_data}: {name} - ${round(price, 2)}\n" + output_text
                    else:
                        output_text = f"Item with barcode {barcode_data} not found.\n" + output_text
                    del self.fetchMod

            # Insert the complete output at the beginning
            self.result_text.insert('1.0', output_text)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def finish_transaction(self):
        if not self.transaction:
            messagebox.showinfo("Info", "No items bought.")
            return
        
        self.processMod.process_pipeline(self.transaction)

        self.dashboard.update_dashboard(self.transaction)
        
        # After processing, clear the transaction and result text
        self.transaction.clear()
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert(tk.END, "Transaction processed.\n")

    def update_camera(self):
        ret, frame = self.capMod.camera.read()
        if ret:
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_tk = ImageTk.PhotoImage(img_pil)
            self.video_label.imgtk = img_tk
            self.video_label.configure(image=img_tk)

        # Call this function again after 30ms
        self.root.after(30, self.update_camera)
        


if __name__ == "__main__":
    root = tk.Tk()
    app = DemandSync(root)
    root.mainloop()