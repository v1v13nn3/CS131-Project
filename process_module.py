import json
from datetime import datetime

BLS_WEIGHT = 0.30
DEMAND_WEIGHT = 0.70

class ItemProcessor:
    def __init__(self, item_data_manager):
        """
        Initializes the ItemProcessor.
        :param item_data_manager: An instance of ItemDataManager to manage item data.
        """
        self.item_data_manager = item_data_manager

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
        items_data = self.item_data_manager.items # Get direct reference to the items dict

        for barcode, details in item_count.items():
            if barcode in items_data:
                current_meter = items_data[barcode].get("meter", 0)
                quantity = details.get("quantity", 0)
                new_meter = current_meter + quantity

                # Update the time the item was last purchased.
                items_data[barcode]["last_purchased"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                while (new_meter >= 5):
                    new_meter -= 5
                    # Increase demand_price by 1%
                    items_data[barcode]["demand_price"] *= 1.01
                    items_data[barcode]["current_price"] = (items_data[barcode]["base_price"] * BLS_WEIGHT) + (items_data[barcode]["demand_price"] * DEMAND_WEIGHT)
                    items_data[barcode]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                items_data[barcode]["meter"] = new_meter
            else:
                print(f"[ItemProcessor] Warning: Barcode '{barcode}' not found in item data for price adjustment.")

        self.item_data_manager.save_items_to_json()

    def decay_prices(self):
        """ Decays the prices of items that have not been purchased in the last day. """
        items_data = self.item_data_manager.items

        print("[ItemProcessor] Starting price decay process...")
        try:
            for barcode, details in items_data.items():
                if "last_purchased" in details and details["last_purchased"]:
                    try:
                        last_purchased = datetime.strptime(details["last_purchased"], "%Y-%m-%d %H:%M:%S")
                        # Check if it's been at least 1 day since last purchase
                        if (datetime.now() - last_purchased).days >= 1:
                            if "demand_price" in details and "base_price" in details and "current_price" in details:
                                current_price = float(details["current_price"])
                                demand_price = float(details["demand_price"])
                                base_price = float(details["base_price"])

                                demand_price *= 0.9 # Decrease  demand price by 10%
                                if demand_price < base_price:
                                    demand_price = base_price # Don't decrease below base price
                                
                                current_price = (base_price * BLS_WEIGHT) + (demand_price * DEMAND_WEIGHT)

                                details["demand_price"] = demand_price
                                details["current_price"] = current_price
                                details["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                print(f"[ItemProcessor] Decayed price for {barcode} to {current_price:.2f}")
                    except ValueError:
                        print(f"[ItemProcessor] Warning: Could not parse 'last_purchased' date for barcode {barcode}.")
                else:
                    print(f"[ItemProcessor] Warning: 'last_purchased' not found or empty for barcode {barcode}. Skipping decay.")

            self.item_data_manager.save_items_to_json()
            print("[ItemProcessor] Price decay process completed.")

        except Exception as e:
            print(f"[ItemProcessor] An error occurred during price decay: {e}")

    def process_pipeline(self, items_list):
        """ Processes a list of scanned items (barcodes) through organization and price adjustment. """
        item_count = self.organize(items_list)
        self.adjust_price(item_count)
