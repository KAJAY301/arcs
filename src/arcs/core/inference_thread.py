import numpy as np
import cv2

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
from ultralytics import YOLO
from queue import Queue, Empty

from arcs.utils.image_processor import cv2_to_qimage

class InferenceThread(QThread):
    """
    
    """
    result_ready = pyqtSignal(dict, QImage)

    def __init__(self, first_model_path, second_model_path, conf_thresh, iou_thresh, display_size, parent=None):
        super().__init__(parent)

        self.first_model = YOLO(first_model_path)
        self.second_model = YOLO(second_model_path)
        self.conf = conf_thresh
        self.iou = iou_thresh
        self.frame_q = Queue(maxsize=2)
        self.display_size = display_size
        self.running = True
        self.last_crop = None

    def submit_frame(self, frame):
        if self.frame_q.full():
            try: self.frame_q.get_nowait()
            except: pass
        self.frame_q.put(frame)

    def first_inference(self, frame):
        try:
            cx, cy = None, None
            results = self.first_model.predict(
                frame, 
                conf=self.conf, 
                iou=self.iou, 
                max_det=1, 
                #verbose=False
            )
            res = results[0]
            if res.boxes:
                box = res.boxes[0]
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cx, cy = int((x1+x2)/2), int((y1+y2)/2)
            return cx, cy
        except Exception as e:
            print(f"First Infer Error: {e}")

    def second_inference(self, img):
        """
        **Return:** \n
        pt = [ [(x1, y1)] , [(x2, y2)] ] \n
        pt.lengh = 2 \n
        pt[0] = first_cross coordinates \n 
        pt[1] = second_cross coordinates \n
        """
        try:
            results = self.first_model.predict(
                img, 
                conf=self.conf, 
                iou=self.iou, 
                #verbose=False
            )
            res = results[0]
            first_points_list = []
            second_points_list = []
            # When using box:
            if res.boxes:
                for box in res.boxes:
                    cls_id = int(box.cls[0])
                    label = res.names[cls_id].lower()
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    cx, cy = int((x1+x2)/2), int((y1+y2)/2)
                    #cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2) #draw rectangle
                    if "first_cross" in label:
                        first_points_list.append((cx, cy))
                    elif "second_cross" in label:
                        second_points_list.append((cx, cy))
            # When using pose:
            """
            if res.keypoints:
                for i, box in enumerate(res.boxes):
                    cls_id = int(box.cls[0])
                    label = res.names[cls_id].lower()
                    kpts = res.keypoints.xy[i]
                    cx, cy = kpts[0].cpu().numpy()
                    cx = int(cx)
                    cy = int(cy)
                    if "first_cross" in label:
                        first_points_list.append((cx, cy))
                    elif "second_cross" in label:
                        second_points_list.append((cx, cy))
            """
            return first_points_list, second_points_list


        except Exception as e:
            print(f"Second Infer Error: {e}")

    def cut_img(self, img, cx, cy, size_x, size_y):
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
        crop_rgb = cv2.cvtColor(crop_padded, cv2.COLOR_BGR2RGB)
        """
        #cv2 to QImage
        h, w, ch = crop_rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(crop_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
        self.last_crop = q_img
        """
        return crop_rgb
    
    def find_cores_points(self, first_points_list, second_points_list):
        if not first_points_list or not second_points_list:
            return None, None
        
        else:
            best_pair = (None, None)
            min_dist = float('inf')
            for w in first_points_list:
                for c in second_points_list:
                    dist = np.linalg.norm(np.array(w) - np.array(c))
                    if dist < min_dist:
                        min_dist = dist
                        best_pair = (w, c)

            max_dist_pixels = 2000 #2000*pixel_mm = 70mm
            if min_dist > max_dist_pixels:
                return None, None
            else:
                return best_pair[0], best_pair[1]

    def run(self):
        while self.running:
            try:
                frame = self.frame_q.get(timeout=0.1)
            except Empty:
                continue
            
            cx, cy = self.first_inference(frame)
            img = self.cut_img(frame, cx, cy, size_x=640, size_y=640)
            coordinate = self.second_inference(img)
            first_points_list = coordinate[0]
            second_points_list = coordinate[1]
            f_pt, s_pt = self.find_cores_points(first_points_list, second_points_list)
            data = {"first": f_pt, "color": s_pt}

            q_img = cv2_to_qimage(img)
            self.last_crop = q_img

            img_to_send = q_img if q_img is not None else (self.last_crop if self.last_crop else QImage())
            self.result_ready.emit(data, img_to_send)
    
    def stop(self):
        self.running = False
        self.wait()




