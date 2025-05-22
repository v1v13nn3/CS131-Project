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
            item = self.items[barcode]

            current_meter = item.get("meter", 0)
            new_meter = current_meter + details["quantity"]

            if "history" not in item or not item["history"]:
                base_price = item.get("base_price", item.get("current_price", 0))
                item["history"] = [round(base_price, 2)]

            while new_meter >= 5:
                new_meter -= 5
                item["current_price"] *= 1.1

            item["current_price"] = round(item["current_price"], 2)

            item["history"].append(item["current_price"])

            item["meter"] = new_meter

        try:
            with open(self.filepath, "w") as file:
                json.dump(self.items, file, indent=4)
            print(f"Successfully updated items in {self.filepath}.")
        except IOError:
            print(f"Error writing to file {self.filepath}.")

    def process_pipeline(self, items):
        """
        Processes the items and returns the organized result.
        """
        item_count = self.organize(items)
        self.adjust_price(item_count)

    def reset_history(self):
        """
        Clears the price history, prices, and meters for all items (locally)
        """
        for item in self.items.values():
            item["history"] = []
            item["current_price"] = item["base_price"]
            item["meter"] = 0

        try:
            with open(self.filepath, "w") as file:
                json.dump(self.items, file, indent=4)
            print("Successfully reset item histories.")
        except IOError:
            print(f"Error writing to file {self.filepath}.")