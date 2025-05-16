from pyzbar.pyzbar import decode
import cv2

def scan_barcode(image):
    barcodes = decode(image)
    results = []
    for barcode in barcodes:
        barcode_data = barcode.data.decode("utf-8")
        barcode_type = barcode.type
        results.append((barcode_data, barcode_type))
    return results