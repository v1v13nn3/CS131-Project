import zmq
import json
import socket
import threading
import time

# Configuration for Network Communication
STORE_1_LISTEN_PORT = "5556" # Port for Store 1 to listen on (PULL socket binds here)
STORE_2_LISTEN_PORT = "5557" # Port for Store 2 to listen on (PULL socket binds here)

class NetworkManager:
    def __init__(self, item_data_manager, is_this_store_server = False, other_store_ip = None, log_callback = None):
        """
        Initializes the NetworkManager for bidirectional PUSH/PULL communication.
        :param item_data_manager: An instance of ItemDataManager to get/set item data.
        :param is_this_store_server: True if this instance is Store 1 (binds to STORE_1_LISTEN_PORT),
                                     False if it is Store 2 (binds to STORE_2_LISTEN_PORT).
        :param other_store_ip: The IP address of the other store. Required for PUSH socket to connect.
        """
        self.context = zmq.Context()
        self.item_data_manager = item_data_manager
        self.is_this_store_server = is_this_store_server
        self.running = True
        self.receiver_thread = None
        self.other_store_ip = other_store_ip
        self.log_callback = log_callback if log_callback else self._defailt_log

        if not self.other_store_ip:
            raise ValueError("other_store_ip must be provided for network communication.")

        self.setup_sockets()

    def _default_log(self, message, log_type="info"):
        """Default logging if no callback is provided."""
        print(f"[{log_type.upper()}] {message}")

    def setup_sockets(self):
        """ Sets up the PUSH and PULL sockets based on the store's role. """
        if self.is_this_store_server:
            self.my_listen_port = STORE_1_LISTEN_PORT
            self.other_store_connect_port = STORE_2_LISTEN_PORT
        else:
            self.my_listen_port = STORE_2_LISTEN_PORT
            self.other_store_connect_port = STORE_1_LISTEN_PORT

        # Setup PULL socket (for receiving messages from the other store)
        self.pull_socket = self.context.socket(zmq.PULL)
        try:
            self.pull_socket.bind(f"tcp://*:{self.my_listen_port}")
            self.log_callback(f"PULL socket bound to tcp://*:{self.my_listen_port} (Receiving from other store)", "received")
            self.receiver_thread = threading.Thread(target = self.receive_loop, daemon = True)
            self.receiver_thread.start()
        except zmq.error.ZMQError as e:
            print(f"[NetworkManager] Error binding PULL socket: {e}")
            self.pull_socket.close()
            self.context.term()
            self.running = False
            return

        # Setup PUSH socket (for sending messages to the other store)
        self.push_socket = self.context.socket(zmq.PUSH)
        try:
            # Connect to the other store's PULL socket
            self.push_socket.connect(f"tcp://{self.other_store_ip}:{self.other_store_connect_port}")
            self.log_callback(f" PUSH socket connected to tcp://{self.other_store_ip}:{self.other_store_connect_port} (Sending to other store)", "sent")
            self.push_socket.send_string("Hello this is store 1")
        except zmq.error.ZMQError as e:
            print(f"[NetworkManager] Error connecting PUSH socket: {e}")
            self.push_socket.close()
            self.pull_socket.close()
            self.context.term()
            self.running = False


    def receive_loop(self):
        """ Loop to receive messages on the PULL socket. """
        self.pull_socket.RCVTIMEO = 100 # milliseconds
        while self.running:
            try:
                message = self.pull_socket.recv_string()
                self.log_callback(f"Received price update -> {message}", "received")
                received_prices = json.loads(message)
                self.log_callback("[NetworkManager] Processing received prices...", "received")

                self.item_data_manager.update_prices_from_sync(received_prices)

            except zmq.error.Again:
                pass
            except zmq.error.ZMQError as e:
                if self.running:
                    print(f"[NetworkManager] ZMQ Error in receive loop: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"[NetworkManager] JSON Decode Error in received message: {e}")
            except Exception as e:
                print(f"[NetworkManager] Unexpected error in receive loop: {e}")
            time.sleep(0.01)

    def send_prices_to_other_store(self, last_sync_time):
        """
        Sends the current prices to the other store using the PUSH socket.
        Only sends items updated since last_sync_time.
        :param last_sync_time: A float timestamp (e.g., from time.time()) representing the last sync time.
        """
        if not self.running:
            print("[NetworkManager] Not running, cannot send prices.")
            return

        try:
            prices = self.item_data_manager.get_recently_updated_items_for_sync(last_sync_time)
            if prices:
                msg = json.dumps(prices)
                self.push_socket.send_string(msg)
                self.log_callback(f"Sent price update for {len(prices)} items -> {msg}", "sent")
            else:
                self.log_callback("No recent item updates to send.", "sent")
        except zmq.error.ZMQError as e:
            print(f"[NetworkManager] Error sending prices: {e}")
        except Exception as e:
            print(f"[NetworkManager] Unexpected error during send: {e}")

    def shutdown(self):
        """Shuts down ZeroMQ sockets and context."""
        print("[NetworkManager] Shutting down...")
        self.running = False
        if self.receiver_thread and self.receiver_thread.is_alive():
            self.receiver_thread.join(timeout = 1) # Give thread a moment to finish

        if self.push_socket:
            self.push_socket.close()
        if self.pull_socket:
            self.pull_socket.close()
        self.context.term()
        print("[NetworkManager] Shut down complete.")

# Helper function to get local IP (useful for identifying your own machine)
def get_local_ip():
    """Attempts to get the local IP address of the current machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except socket.gaierror:
        return "127.0.0.1"
    except Exception:
        return "127.0.0.1"
