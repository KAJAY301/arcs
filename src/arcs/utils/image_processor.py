import cv2
import os
import numpy as np

from datetime import datetime
from PyQt5.QtGui import QImage



def qimage_to_cv2(q_img):
    q_img = q_img.convertToFormat(QImage.Format_RGB888)
    width = q_img.width()
    height = q_img.height()
    ptr = q_img.bits()
    ptr.setsize(height * width * 3)
    arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 3))
    #cv_img = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    return arr.copy()

def cv2_to_qimage(cv_img):
    #cv_img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    h, w, ch = cv_img.shape
    bytes_per_line = ch * w
    return QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()

def save_image_timed(img, base_path="data/collected_samples/no_detection"):
    """
    save image, name: yymmddHHMMSS.jpg
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