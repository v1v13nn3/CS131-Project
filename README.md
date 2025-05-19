# CS131-Project
To launch app run `python3 main.py`

Main Timing Pipeline
```
if __name == "__main__":
	while True:
		# run main function -> main()
		# simulate 1 hour by checking if 15 seconds have passed
			# if yes then collect most recently updated items
			# sync with other store
		# simulate 1 day passing by checking id 360 seconds have passed
			# if yes then decay the prices of items that have not been purchased in the last day by 10%
			# make sure to not decrease bellow the base price
```

Iterated Barcode Capture Piepeline
```
def main():
	# Capture barcode image
	# Pre-process image
	# Scan barcode
	# Process Transaction data
		# Get quantity of each item
		# For every 5 items bought raise price by 1%

			# Update current item price, last-price-change timestamp, and last-purchase-date timestamp
```

Items.json Structure
```
{
	"0000": {
		"item_name": "apple",
		"base_price": "0.30",
		"current_price": "0.50",
		"last_purchased": "00:00:00",
		"last_updated": "00:00:00",
        	"meter": "0"
}
```
