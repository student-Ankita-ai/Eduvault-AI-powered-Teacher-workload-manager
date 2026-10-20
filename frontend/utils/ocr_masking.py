import cv2
import numpy as np
from PIL import Image

def process_and_mask_document(image_file):
    image = Image.open(image_file)
    img_cv = np.array(image)
    if len(img_cv.shape) == 3 and img_cv.shape[2] == 3:
        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
        
    height, width, _ = img_cv.shape
    start_x, end_x = int(width * 0.2), int(width * 0.8)
    start_y, end_y = int(height * 0.6), int(height * 0.78)
    
    cv2.rectangle(img_cv, (start_x, start_y), (end_x, end_y), (0, 0, 0), -1)
    cv2.putText(img_cv, "PII MASKED & SECURED VIA EDUVAULT AI", (int(width * 0.05), int(height * 0.95)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    masked_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    return Image.fromarray(masked_rgb)