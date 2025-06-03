import json
from datetime import datetime

BLS_WEIGHT = 0.30
DEMAND_WEIGHT = 0.70

class ItemProcessor:
    def __init__(self, item_data_manager, log_callback=None):
        """
        Initializes the ItemProcessor.
        :param item_data_manager: An instance of ItemDataManager to manage item data.
        """
        self.item_data_manager = item_data_manager
        self.log_callback = log_callback if log_callback else self._default_log

    def _default_log(self, message, log_type="info"): # ADDED: Default logging method
        """Default logging if no callback is provided."""
        print(f"[{log_type.upper()}] {message}")

    def organize(self, items_list):
        """ Organizes a list of scanned barcodes into a dictionary with their respective quantities. """
        result = {}
        for barcode in items_list:
            if barcode not in result:
                result[barcode] = {"quantity": 0}
            result[barcode]["quantity"] += 1
        print(f"[ItemProcessor] Organized transaction: {result}")
        return result

    def adjust_price(self, item_count):
        """ Adjusts the price of the items based on the quantity bought and updates last_purchased/updated. """
        items_data = self.item_data_manager.items

        for barcode, details in item_count.items():
            if barcode in items_data:
                item = items_data[barcode]
                original_price = items_data[barcode]["current_price"]
                current_meter = item.get("meter", 0)
                new_meter = current_meter + details["quantity"]

                if "history" not in item or not item["history"]:
                    base_price = item.get("base_price", item.get("current_price", 0))
                    item["history"] = [round(base_price, 2)]

                while new_meter >= 5:
                    new_meter -= 5
                    # Increase demand_price by 1%
                    items_data[barcode]["demand_price"] *= 1.01
                    items_data[barcode]["current_price"] = (items_data[barcode]["base_price"] * BLS_WEIGHT) + (items_data[barcode]["demand_price"] * DEMAND_WEIGHT)
                    items_data[barcode]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                item["history"].append(round(item["current_price"], 2))
                item["meter"] = new_meter
                item["last_purchased"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.log_callback(f"Adjusted price for {barcode}. Old price: {original_price:.2f}, New price: {item['current_price']:.2f}", "process")

            else:
                print(f"[ItemProcessor] Warning: Barcode '{barcode}' not found in item data for price adjustment.")

        self.item_data_manager.save_items_to_json()

    def process_pipeline(self, items_list):
        """ Processes a list of scanned items (barcodes) through organization and price adjustment. """
        item_count = self.organize(items_list)
        self.adjust_price(item_count)

    def reset_history(self):
        """
        Clears the price history, prices, and meters for all items (locally)
        """
        items_data = self.item_data_manager.items

        for item in items_data.values():
            item["history"] = []
            item["current_price"] = item.get("base_price", item.get("current_price", 0))

        self.item_data_manager.save_items_to_json()
        print("Successfully reset item histories.")

    def decay_prices(self, since_timestamp):
        """ Decays the prices of items that have not been purchased in the last day and updates price history. """
        items_data = self.item_data_manager.items

        print("[ItemProcessor] Starting price decay process...")
        try:
            for barcode, details in items_data.items():
                if "last_purchased" in details and details["last_purchased"]:
                    try:
                        last_purchased = datetime.strptime(details["last_purchased"], "%Y-%m-%d %H:%M:%S")
                        # Check if it's been at least 1 day since last purchase
                        if last_purchased.timestamp() < since_timestamp:
                            if "demand_price" in details and "base_price" in details and "current_price" in details:
                                current_price = float(details["current_price"])
                                original_price = current_price
                                demand_price = float(details["demand_price"])
                                base_price = float(details["base_price"])

                                demand_price *= 0.9 # Decrease  demand price by 10%
                                if demand_price < base_price:
                                    demand_price = base_price # Don't decrease below base price
                                
                                current_price = (base_price * BLS_WEIGHT) + (demand_price * DEMAND_WEIGHT)

                                details["demand_price"] = demand_price
                                details["current_price"] = current_price
                                details["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                self.log_callback(f"Decayed price for {barcode}. Old price: {original_price:.2f}, Decayed price: {current_price:.2f}", "process")

                                # Append the new decayed price to history only if it changed
                                if "history" not in details or not isinstance(details["history"], list):
                                    details["history"] = []

                                if not details["history"] or details["history"][-1] != details["current_price"]:
                                    details["history"].append(details["current_price"])
                                else:
                                    print(f"[ItemProcessor] Price for {barcode} unchanged since last history entry; not appending.")
                    except ValueError:
                        print(f"[ItemProcessor] Warning: Could not parse 'last_purchased' date for barcode {barcode}.")
                else:
                    print(f"[ItemProcessor] Warning: 'last_purchased' not found or empty for barcode {barcode}. Skipping decay.")

            self.item_data_manager.save_items_to_json()
            self.log_callback("Price decay process completed.", "process")

        except Exception as e:
            print(f"[ItemProcessor] An error occurred during price decay: {e}")

