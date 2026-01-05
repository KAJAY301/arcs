import cv2
import numpy as np
from PyQt5.QtGui import QImage



def qimage_to_cv2(q_img):
    q_img = q_img.convertToFormat(QImage.Format_RGB888)
    width = q_img.width()
    height = q_img.height()
    ptr = q_img.bits()
    ptr.setsize(height * width * 3)
    arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 3))
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

def cv2_to_qimage(cv_img):
    #cv_img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    h, w, ch = cv_img.shape
    bytes_per_line = ch * w
    return QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()