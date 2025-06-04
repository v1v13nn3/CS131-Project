# CS131-Project
### Before Runnning... fill in TODO's <br />
Computer 1: <br />
```
main.py -> Line 17 -> IP of Computer 2
	-> Line 167 -> True
```
Computer 2: <br />
```
main.py -> Line 17 -> IP of Computer 1
	-> Line 167 -> False 
```
   
To launch app run `python3 main.py`

Main Timing Pipeline
```
while True:
	# run main function -> main()
	# simulate 1 hour by checking if 30 seconds have passed
		# if yes then collect most recently updated items
		# sync with other store
	# simulate 1 day passing by checking id 60 seconds have passed
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
"0001": {
	"item_name": "apple (1 lb.)",
	"base_price": 1.315,
	"demand_price": 1.315,
	"current_price": 1.315,
	"last_purchased": "2025-05-22 19:51:15",
	"last_updated": "2025-05-23 12:54:46",
	"meter": 1,
	"series_id": "APU0000711111",
	"history": [
		1.315
	]
},
```
