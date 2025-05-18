import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from capture_module import CaptureModule
import cv2

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
        self.root = root
        self.root.title("DemandSync")

        self.video_label = tk.Label(root)
        self.video_label.pack()
        
        self.capMod = CaptureModule()
        self.scan_button = tk.Button(root, text = "Scan Barcode", command = self.handle_scan)
        self.scan_button.pack()

        self.result_text = tk.Text(root, height=10, width=50)
        self.result_text.pack()

        self.transaction = {}

    def handle_scan(self):
        try:
            frame, results = self.capMod.capture_pipeline()

            # Convert frame to ImageTk and display
            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_tk = ImageTk.PhotoImage(img_pil)
            self.video_label.imgtk = img_tk
            self.video_label.configure(image=img_tk)

            # Display results
            # self.result_text.delete('1.0', tk.END)
            if not results:
                self.result_text.insert(tk.END, "No barcode found.\n")
            else:
                for barcode_data, barcode_type in results:
                    self.result_text.insert(tk.END, f"{barcode_type}: {barcode_data}\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = DemandSync(root)
    root.mainloop()