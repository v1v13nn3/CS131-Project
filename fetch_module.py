import json

class FetchModule:
    def __init__ (self):
        filepath = "items.json"
        self.items = {}

        try:
            with open(filepath, "r") as file:
                self.items = json.load(file)
                print(f"Successfuly loaded items from {filepath}.")
        except FileNotFoundError:
            print(f"File {filepath} not found.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file {filepath}.")
    
    def __del__(self):
        self.items.clear()

    def fetch(self, barcode):
        """
        Fetches the item details from the items dictionary using the barcode.
        """
        if barcode in self.items:
            return [self.items[barcode]["item_name"], self.items[barcode]["current_price"]]
        else:
            print(f"Item with barcode {barcode} not found.")
            return None