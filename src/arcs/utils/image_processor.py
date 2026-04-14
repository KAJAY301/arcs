import cv2
import os
import numpy as np

from datetime import datetime
from PyQt5.QtGui import QImage

def qimage_to_cv2(q_img):
    """
    Convert from QImage to an OpenCV image
    """
    q_img = q_img.convertToFormat(QImage.Format_RGB888)
    width = q_img.width()
    height = q_img.height()
    ptr = q_img.bits()
    ptr.setsize(height * width * 3)
    arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 3))
    return arr.copy()

def cv2_to_qimage(cv_img):
    """
    Convert from an OpenCV image to QImage
    """
    if len(cv_img.shape) == 3:
        h, w, ch = cv_img.shape
    else:
        h, w = cv_img.shape
        ch = 1

    bytes_per_line = ch * w

    if ch == 3:
        return QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
    
    elif ch == 1:
        return QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_Grayscale8).copy()

def save_image_timed(img, base_path):
    """
    Save image\n
    name: yymmddHHMMSS.jpg
    """
    try:
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        timestamp = datetime.now().strftime("%y%m%d%H%M%S")
        filename = f"{timestamp}.jpg"
        full_path = os.path.join(base_path, filename)

        bgr_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        success = cv2.imwrite(full_path, bgr_img)
        
        if success:
            return True
        else:
            return False

    except:
        return False
    
def cut_image(img, cx, cy, size_x, size_y):
    """ Cut image around center (cx, cy) with size (size_x, size_y)\n
    If the cut area goes beyond the image borders, pad with white."""
    size_x = size_x // 2
    size_y = size_y // 2
    x1, x2 = int(cx - size_x), int(cx + size_x)
    y1, y2 = int(cy - size_y), int(cy + size_y)

    top, bottom, left, right = 0, 0, 0, 0
    h, w = img.shape[:2]
    if x1 < 0:
        left = abs(x1)
        x1 = 0
    if x2 > w:
        right = x2 - w
        x2 = w
    if y1 < 0:
        top = abs(y1)
        y1 = 0
    if y2 > h:
        bottom = y2 - h
        y2 = h

    crop = img[y1:y2, x1:x2]

    # Padding
    crop_padded = cv2.copyMakeBorder(
        crop, top, bottom, left, right, 
        cv2.BORDER_CONSTANT, value=(255, 255, 255)
    )

    # BGR to RGB for Qt
    #crop_rgb = cv2.cvtColor(crop_padded, cv2.COLOR_BGR2RGB)

    return crop_padded

def resize_image(img, width, height):
    """Resize image to fit within (width, height) while maintaining aspect ratio.
    If the image is smaller than the target size, it will be scaled up."""
    h, w = img.shape[:2]
    scale_w = width / w
    scale_h = height / h
    scale = min(scale_w, scale_h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    # if not fast enouth, use small_img = image[::2, ::2]
    return resized




