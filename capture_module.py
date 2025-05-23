import cv2
from pyzbar.pyzbar import decode

class CaptureModule:
    def __init__ (self, camera_index = 0):
        self.camera_index = camera_index
        self.camera = cv2.VideoCapture(camera_index)
        if not self.camera.isOpened():
            raise IOError("Cannot open camera!")
        
    def __del__(self):
        if self.camera.isOpened():
            self.camera.release()
        
    def capture_frame(self):
        result, frame = self.camera.read()
        if not result:
            raise IOError("Failed to capture image!")
        return frame
    
    def preprocess_image(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh
    
    def scan_barcode(self, pre_processed_frame):
        barcodes = decode(pre_processed_frame)
        results = []
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            barcode_type = barcode.type
            results.append((barcode_data, barcode_type))
        return results
    
    def capture_pipeline(self):
        frame = self.capture_frame()
        pre_processed_frame = self.preprocess_image(frame)
        results = self.scan_barcode(pre_processed_frame)
        return frame, results
        
        
    
    
        
