# === ui_app.py ===
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
from camera_module import capture_frame
from image_processing import preprocess_image
from barcode_scanner import scan_barcode
# from data_sender import send_data_to_cloud

class BarcodeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Jetson Nano Barcode Scanner")

        self.video_label = tk.Label(root)
        self.video_label.pack()

        self.scan_button = tk.Button(root, text="Scan Barcode", command=self.scan_barcode)
        self.scan_button.pack()

        self.finish_button = tk.Button(root, text="Finish Transaction", command=self.finish_transaction)
        self.finish_button.pack()

        self.result_text = tk.Text(root, height=10, width=50)
        self.result_text.pack()

        self.transaction = {}

    def scan_barcode(self):
        frame = capture_frame()
        processed = preprocess_image(frame)
        results = scan_barcode(processed)

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_tk = ImageTk.PhotoImage(image=img_pil)

        self.video_label.imgtk = img_tk
        self.video_label.configure(image=img_tk)

        if not results:
            messagebox.showinfo("Result", "No barcode found.")
            return

        for barcode_data, barcode_type in results:
            self.transaction[barcode_data] = self.transaction.get(barcode_data, 0) + 1
            self.result_text.insert(tk.END, f"Scanned {barcode_type}: {barcode_data}\n")

    def finish_transaction(self):
        if not self.transaction:
            messagebox.showinfo("Info", "No items to send.")
            return

        # try:
        #     status, response = send_data_to_cloud(self.transaction, "https://your-cloud-endpoint.com/api/barcode")
        #     messagebox.showinfo("Success", f"Transaction sent. Status: {status}")
        #     self.transaction.clear()
        #     self.result_text.insert(tk.END, "Transaction complete.\n")
        # except Exception as e:
        #     messagebox.showerror("Error", f"Failed to send data: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BarcodeApp(root)
    root.mainloop()
