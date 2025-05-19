import json

class ProcessModule:
    def __init__ (self):
        self.filepath = "items.json"
        self.items = {}

        try:
            with open(self.filepath, "r") as file:
                self.items = json.load(file)
                print(f"Successfuly loaded items from {self.filepath}.")
        except FileNotFoundError:
            print(f"File {self.filepath} not found.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file {self.filepath}.")

    def organize(self, items):
        """
        Organizes the items into a dictionary with their respective quantities.
        """
        result = {}
        for barcode in items:
            if barcode not in result: 
                result[barcode] = {"quantity": 0}
            result[barcode]["quantity"] += 1
        print(result)
        return result

    def adjust_price(self, item_count):
        """
        Adjusts the price of the items based on the quantity bought.
        """
        for barcode, details in item_count.items():
            current_meter = self.items[barcode]["meter"]
            new_meter = current_meter + details["quantity"]
            
            while (new_meter >= 5):
                new_meter -= 5
                # Increase price by 10%
                self.items[barcode]["current_price"] *= 1.1
            
            self.items[barcode]["meter"] = new_meter

        try: 
            with open(self.filepath, "w") as file:
                json.dump(self.items, file, indent = 4)
            print(f"Successfully updated items in {self.filepath}.")
        except IOError:
            print(f"Error writing to file {self.filepath}.")

    def process_pipeline(self, items):
        """
        Processes the items and returns the organized result.
        """
        item_count = self.organize(items)
        self.adjust_price(item_count)