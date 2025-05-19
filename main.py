import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from capture_module import CaptureModule
import cv2
from fetch_module import FetchModule
from process_module import ProcessModule
import zmq
import json

import time
# CHANGE THE PORTS BASED ON IP ADDRESSES OF THE NANO'S
PORT_SEND = "5556"   # server -> client
PORT_RECV = "5557"   # client -> server
JSON_FILE = "items.json"

# Helper to load just current_price values
def load_prices(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return {item_id: {"current_price": info["current_price"]}
            for item_id, info in data.items()}

# Method to send and receive prices
def sendPrices():
    # Set up ZeroMQ context and sockets
    context = zmq.Context()
    socket_send = context.socket(zmq.PAIR)
    socket_recv = context.socket(zmq.PAIR)

    socket_send.bind(f"tcp://*:{PORT_SEND}")
    socket_recv.bind(f"tcp://*:{PORT_RECV}")

    # Send JSON of current prices to client
    prices = load_prices(JSON_FILE)
    msg = json.dumps(prices)
    socket_send.send_string(msg)
    print(f"[Server] sent -> {msg}")

    # Receive one response from client
    reply = socket_recv.recv_string()
    print(f"[Server] recv <- {reply}")

    # Clean up
    socket_send.close()
    socket_recv.close()
    context.term()




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

        self.video_label = tk.Label(root)
        self.video_label.pack()
        
        self.scan_button = tk.Button(root, text = "Scan Barcode", command = self.handle_scan)
        self.scan_button.pack()

        self.finish_button = tk.Button(root, text="Finish Transaction", command=self.finish_transaction)
        self.finish_button.pack()

        self.result_text = tk.Text(root, height=10, width=50)
        self.result_text.pack()

        self.transaction = []


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
        
        # After processing, clear the transaction and result text
        self.transaction.clear()
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert(tk.END, "Transaction processed.\n")
        
if __name__ == "__main__":
    root = tk.Tk()
    app = DemandSync(root)
    root.mainloop()