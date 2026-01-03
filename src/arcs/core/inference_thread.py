import numpy as np
import cv2

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
from ultralytics import YOLO
from queue import Queue, Empty

class InferenceThread(QThread):
    """
    rerurn dict{color_cross, white_cross} and QImage
    """
    result_ready = pyqtSignal(dict, QImage)

    def __init__(self, model_path, conf_thresh, iou_thresh, display_size, parent=None):
        super().__init__(parent)
        self.model = None
        try:
            self.model = YOLO(model_path)
        except Exception as e:
            print(f"Model Load Error: {e}")
        
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

    def run(self):
        while self.running:
            try:
                frame = self.frame_q.get(timeout=0.1)
            except Empty:
                continue
            
            white_points_list = []
            color_points_list = []
            white_points = None
            color_points = None
            q_img = None
            
            if self.model:
                try:
                    results = self.model.predict(
                        frame, 
                        conf=self.conf, 
                        iou=self.iou, 
                        #verbose=False
                    )
                    res = results[0]
                    # 1. collect points
                    # When using box:
                    
                    if res.boxes:
                        for box in res.boxes:
                            cls_id = int(box.cls[0])
                            label = res.names[cls_id].lower()
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            cx, cy = int((x1+x2)/2), int((y1+y2)/2)
                            #cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2) #draw rectangle
                            if "white_cross" in label:
                                white_points_list.append((cx, cy))
                            elif "color_cross" in label:
                                color_points_list.append((cx, cy))
                    
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
                            if "white_cross" in label:
                                white_points_list.append((cx, cy))
                            elif "color_cross" in label:
                                color_points_list.append((cx, cy))
                    """
                    # Find Closest Two Point
                    if not white_points_list or not color_points_list:
                        white_points = None
                        color_points = None
                    else:
                        best_pair = (None, None)
                        min_dist = float('inf')
                        for w in white_points_list:
                            for c in color_points_list:
                                dist = np.linalg.norm(np.array(w) - np.array(c))
                                if dist < min_dist:
                                    min_dist = dist
                                    best_pair = (w, c)

                        max_dist_pixels = 2000 #2000*pixel_mm = 70mm
                        if min_dist > max_dist_pixels:
                            white_points = None
                            color_points = None
                        else:
                            white_points = best_pair[0]
                            color_points = best_pair[1]

                    # image resize
                    ref_cx, ref_cy = frame.shape[1]//2, frame.shape[0]//2
                    if white_points: ref_cx, ref_cy = white_points
                    elif color_points: ref_cx, ref_cy = color_points

                    size_x = 300 
                    size_y = 300
                    x1c, x2c = max(0, ref_cx - size_x), min(frame.shape[1], ref_cx + size_x)
                    y1c, y2c = max(0, ref_cy - size_y), min(frame.shape[0], ref_cy + size_y)

                    crop = frame[y1c:y2c, x1c:x2c]
                    if crop.size > 0:
                        # Resize
                        crop_resized = cv2.resize(crop, self.display_size)
                        # BGR to RGB for Qt
                        crop_rgb = cv2.cvtColor(crop_resized, cv2.COLOR_BGR2RGB)
                        h, w, ch = crop_rgb.shape
                        bytes_per_line = ch * w
    
                        q_img = QImage(crop_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
                        self.last_crop = q_img

                except Exception as e:
                    print(f"Infer Error: {e}")

            # 3. return result to UI
            data = {"white": white_points, "color": color_points}
            # use last image if dont have new result
            img_to_send = q_img if q_img is not None else (self.last_crop if self.last_crop else QImage())
            self.result_ready.emit(data, img_to_send)
    
    def stop(self):
        self.running = False
        self.wait()




