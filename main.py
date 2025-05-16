from camera_module import capture_frame
from image_processing import preprocess_image
from barcode_scanner import scan_barcode

import cv2
import time

def main():
    print("Capturing image...")
    image = capture_frame()
    
    cv2.imshow("Captured Image", image)
    cv2.waitKey(2000)
    cv2.destroyAllWindows()

    print("Preprocessing image...")
    preprocessed = preprocess_image(image)

    print("Scanning barcode...")
    results = scan_barcode(preprocessed)
    if not results:
        print("No barcode detected.")
        return
    
    for barcode_data, barcode_type in results:
        print(f"Detected {barcode_type} barcode: {barcode_data}")

if __name__ == "__main__":
    while True:
        main()
        time.sleep(5)  # Wait for 5 seconds before capturing the next image