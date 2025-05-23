import json
from datetime import datetime
import requests

from api_BLS import get_bls_data

BLS_WEIGHT = 0.30
DEMAND_WEIGHT = 0.70

class ItemDataManager:
    def __init__(self, filepath="items.json"):
        self.get_bls_data = get_bls_data

        self.filepath = filepath
        self.items = {}
        self._load_items()
        self.load_bls_data()

    def _load_items(self):
        """ Loads item data from the JSON file. """
        try:
            with open(self.filepath, "r") as file:
                self.items = json.load(file)
                print(f"[ItemDataManager] Successfully loaded items from {self.filepath}.")
        except FileNotFoundError:
            print(f"[ItemDataManager] File {self.filepath} not found. Starting with empty items.")
            self.items = {}
        except json.JSONDecodeError:
            print(f"[ItemDataManager] Error decoding JSON from file {self.filepath}. Starting with empty items.")
            self.items = {}

    def load_bls_data(self):
        """ Loads the average pricing data from the Beureau of Labor Statistics (BLS) API. """
        # Gather sersies IDs from the items
        print(f"[ItemDataManager] Loading BLS data...")
        series_ids = []
        for barcode in self.items:
            series_ids.append(self.items[barcode].get("series_id"))

        avg_prices = self.get_bls_data(series_ids)

        for index, barcode in enumerate(self.items):
            self.items[barcode]["base_price"] = avg_prices[index]
            self.items[barcode]["current_price"] = (self.items[barcode]["base_price"] * BLS_WEIGHT) + (self.items[barcode]["demand_price"] * DEMAND_WEIGHT)

        self.save_items_to_json()

    def save_items_to_json(self):
        """ Saves the current item data to the JSON file. """
        try:
            with open(self.filepath, "w") as file:
                json.dump(self.items, file, indent=4)
            print(f"[ItemDataManager] Successfully saved updated items to {self.filepath}.")
        except IOError as e:
            print(f"[ItemDataManager] Error writing to file {self.filepath}: {e}")

    def get_item_details(self, barcode):
        """ Fetches the item details (name and current_price) from the items dictionary using the barcode. """
        if barcode in self.items:
            item = self.items[barcode]
            return item.get("item_name"), item.get("current_price")
        else:
            print(f"[ItemDataManager] Item with barcode {barcode} not found.")
            return None, None

    def get_all_prices_for_sync(self):
        """ Returns a dictionary of all item prices suitable for syncing. """
        prices = {}
        for item_id, info in self.items.items():
            prices[item_id] = {"current_price": info.get("current_price")}
        return prices
    
    def get_recently_updated_items_for_sync(self, since_timestamp):
        """
        Returns a dictionary of items that have been updated since the given timestamp,
        formatted for syncing (item_id: {"current_price": price}).
        :param since_timestamp: A float timestamp (e.g., from time.time()) representing the last sync time.
        """

###########################################################from here
    for index, (item_id, info) in enumerate(self.items.items()):
        try:
            response = requests.get("https://aloft.pythonanywhere.com/submit", params={
                "insertStore": "1",
                "searchStore": "0",
                "storename": "STORE1",
                "storeIP": "1.1.1",
                "storeCo": "USA",
                "itemname": f"xyz_{index}",
                "password": "password"
            })
            response.raise_for_status()
            #print(f"Submitted item")
        except requests.RequestException as e:
            print(f"Error submitting item {index} to Flask")
###############################to here
            
        recently_updated_prices = {}
        for item_id, info in self.items.items():
            last_updated_str = info.get("last_updated")
            if last_updated_str:
                try:
                    # Convert string timestamp to datetime object
                    last_updated_dt = datetime.strptime(last_updated_str, "%Y-%m-%d %H:%M:%S")
                    # Convert datetime object to Unix timestamp for comparison
                    last_updated_unix = last_updated_dt.timestamp()

                    if last_updated_unix >= since_timestamp:
                        recently_updated_prices[item_id] = {"current_price": info.get("current_price")}
                except ValueError:
                    print(f"[ItemDataManager] Warning: Could not parse 'last_updated' date for barcode {item_id}.")
        return recently_updated_prices

    def update_prices_from_sync(self, synced_prices):
        """ Updates local item prices based on received synced prices. """
        updated_count = 0
        for barcode, data in synced_prices.items():
            if barcode in self.items and "current_price" in data:
                if data["current_price"] > self.items[barcode]["current_price"]:
                    self.items[barcode]["current_price"] = data["current_price"]
                    updated_count += 1
            elif barcode not in self.items:
                print(f"[ItemDataManager] New item {barcode} is not in local data.")
        if updated_count > 0:
            self.save_items_to_json()
            print(f"[ItemDataManager] Updated {updated_count} prices from sync.")
        else:
            print("[ItemDataManager] No prices updated from sync.")
