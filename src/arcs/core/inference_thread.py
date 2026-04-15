import cv2
import os
import numpy as np
import torch
import time

from time import time as time_now
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
from ultralytics import YOLO
from queue import Queue, Empty
import threading

from arcs.utils.config_manager import load_env_config, load_json_config, load_model_path
from arcs.utils.image_processor import cv2_to_qimage, save_image_timed, cut_image, resize_image
from arcs.utils.data_processor import pixel_to_pulse

class InferenceThread(QThread):
    """
    
    """
    ui_signal = pyqtSignal(QImage, list)
    plc_command_signal = pyqtSignal(int, int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Load models
        cfg = load_json_config()

        first_model = cfg.get('yolo').get('first_model')
        self.first_model = YOLO(load_model_path(first_model))
        self.first_model_conf = cfg.get('yolo').get('first_model_conf')
        self.first_model_iou = cfg.get('yolo').get('first_model_iou')

        second_model = cfg.get('yolo').get('second_model')
        self.second_model = YOLO(load_model_path(second_model))
        self.second_model_conf = cfg.get('yolo').get('second_model_conf')
        self.second_model_iou = cfg.get('yolo').get('second_model_iou')
        
        # Check GPU availability
        self.device = 0 if torch.cuda.is_available() else 'cpu'
        if self.device == 0:
            print(f"GPU detected: {torch.cuda.get_device_name(0)}")
        else:
            print("GPU not available, using CPU")
        
        # Move models to GPU if available
        if self.device == 0:
            self.first_model.to(self.device)
            self.second_model.to(self.device)

        # Frame Queue
        self.frame_q = Queue(maxsize=1)
        self.frame_lock = threading.Lock()

        # Unidentifyed image saving
        self.save_dir = "data/no_match_img"
        self.max_save_count = 2000
        self.last_save_time = 0
        self.cooldown_seconds = 5

        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        self.current_save_count = len(os.listdir(self.save_dir))

        self.pixel_size = cfg.get('setting').get('pixel_mm')
        self.deadband_mm = cfg.get('setting').get('deadband_dist')
        self.mm_per_pulses_x = load_env_config().get('motor_mm_per_pulse_x')
        self.mm_per_pulses_y = load_env_config().get('motor_mm_per_pulse_y')

        self.is_detecting = False
        self.auto_control = False
        self.running = True
        self.last_crop = None
        self.display_mode = cfg.get('display').get('mode')
        self.first_inference_model = cfg.get('inference').get('first_inference_model') #"yolo_v11n"(目前無作用
        self.second_inference_model = cfg.get('inference').get('second_inference_model') #"cv2"

        self.threshold_value = cfg.get('cv2_setting').get('binary_threshold') #去除背景
        self.kernel_size = cfg.get('cv2_setting').get('kernel_size')          #去除雜訊
        self.white_b = cfg.get('cv2_setting').get('white_b')
        self.white_g = cfg.get('cv2_setting').get('white_g')
        self.white_r = cfg.get('cv2_setting').get('white_r')
        self.color_threshold = cfg.get('cv2_setting').get('color_threshold')  #容許偏差

    def submit_frame(self, frame):
        """Submit frame to processing queue. Drops old frames if queue is full."""
        with self.frame_lock:
            # Clear old frames and add new one
            if self.frame_q.full():
                try:
                    self.frame_q.get_nowait()
                except Empty:
                    pass
            self.frame_q.put(frame)

    def first_inference(self, frame) -> tuple:
        try:
            cx, cy = None, None
            results = self.first_model.predict(
                frame, 
                conf=self.first_model_conf, 
                iou=self.first_model_iou, 
                max_det=1, 
                verbose=False,
                device=self.device
            )
            res = results[0]
            if res.boxes:
                box = res.boxes[0]
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cx, cy = int((x1+x2)/2), int((y1+y2)/2)
            return cx, cy
        except Exception as e:
            print(f"First Infer Error: {e}")
            return None, None

    def second_inference(self, img):
        """
        **Return:** \n
        pt = [ [(x1, y1)] , [(x2, y2)] ] + Image  
        pt[0] = first_cross coordinates   
        pt[1] = second_cross coordinates  

        """
        try:
            # YOLOv11 Box or Pose
            if self.second_inference_model == "yolo_v11_box" or self.second_inference_model == "yolo_v11_pose":
                results = self.second_model.predict(
                    img, 
                    conf=self.second_model_conf, 
                    iou=self.second_model_iou, 
                    verbose=False,
                    device=self.device
                )
                res = results[0]

                first_points_list = []
                second_points_list = []

                # Using box:
                if self.second_inference_model == "yolo_v11_box":
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
                
                # Using pose:
                if self.second_inference_model == "yolo_v11_pose":
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

                # process results
                if not first_points_list or not second_points_list:
                    self.save_img(img)
                    return None, None, img
                else:
                    f_pt, s_pt = self.find_closest_points(first_points_list, second_points_list)
                    return f_pt, s_pt, img

            # CV2
            elif self.second_inference_model == "cv2":
                # BGR -> GRAY
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                # GRAY -> BINARY
                _, binary = cv2.threshold(gray, self.threshold_value, 255, cv2.THRESH_BINARY_INV)
                
                # Find Lines which Longer than {kernel_size} pixels
                h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (self.kernel_size, 1))
                v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, self.kernel_size))
                # Opening Operation
                h_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel)
                v_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel)

                # Find centroids
                h_num_labels, h_labels, h_stats, h_centroids = cv2.connectedComponentsWithStats(h_lines)
                v_num_labels, v_labels, v_stats, v_centroids = cv2.connectedComponentsWithStats(v_lines)

                # Find Center and color sample
                h_white_centroids = 0
                h_color_centroids = 0
                v_white_centroids = 0
                v_color_centroids = 0

                if h_num_labels == 3:
                    for i in range(1, h_num_labels):
                        mask_single_line = (h_labels == i).astype("uint8") * 255
                        b, g, r = cv2.mean(img, mask=mask_single_line)[:3]
                        if self.is_white(b, g, r):
                            h_white_centroids = h_centroids[i][1]
                        else:
                            h_color_centroids = h_centroids[i][1]
                    
                if v_num_labels == 3:
                    for i in range(1, v_num_labels):
                        mask_single_line = (v_labels == i).astype("uint8") * 255
                        b, g, r = cv2.mean(img, mask=mask_single_line)[:3]
                        if self.is_white(b, g, r):
                            v_white_centroids = v_centroids[i][0]
                        else:
                            v_color_centroids = v_centroids[i][0]

                f_pt = (int(v_white_centroids), int(h_white_centroids))
                s_pt = (int(v_color_centroids), int(h_color_centroids))

                if h_white_centroids == 0 or h_color_centroids == 0 or v_white_centroids == 0 or v_color_centroids == 0:
                    self.save_img(img)
                    f_pt, s_pt = None, None #if one of the coordinates is 0, means the detection fail, due to 1.num_labels is not 3, 2. cant match white color

                if self.display_mode == "zoom_in":
                    return_img = img
                elif self.display_mode == "cv2_gray":
                    return_img = gray
                elif self.display_mode == "cv2_binary":
                    return_img = binary
                elif self.display_mode == "cv2_horizon":
                    return_img = h_lines
                elif self.display_mode == "cv2_vertical":
                    return_img = v_lines
                else:
                    return_img = img

                return f_pt, s_pt, return_img

        except Exception as e:
            print(f"Second Infer Error: {e}")
            return None, None, img
    
    def save_img(self, img):
        current_time = time_now()
        if (current_time - self.last_save_time >= self.cooldown_seconds) and (self.current_save_count < self.max_save_count):
            success = save_image_timed(img, base_path="data/no_match_img")
            if success:
                self.last_save_time = current_time
                self.current_save_count += 1
                print(f"[Saved] (Total: {self.current_save_count}/2000)")
            else:
                print(f"[Save Error]")

    def find_closest_points(self, first_points_list, second_points_list):
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

    def is_white(self, b, g, r):
        current_color = np.array([b, g, r])
        white_bgr = np.array([self.white_b, self.white_g, self.white_r])
        distance = np.linalg.norm(current_color - white_bgr)
        #print(f"Sampled Color (BGR): {b}, {g}, {r}, Distance: {distance}")
        return distance < self.color_threshold

    def run(self):
        while self.running:
            # Try to get a frame from the queue
            try:
                frame = self.frame_q.get(timeout=0.1)
            except Empty:
                continue
            
            # first inference
            #h, w = frame.shape[:2]
            #small_frame = resize_image(frame, width=w//4, height=h//4)
            cx, cy = self.first_inference(frame)
            if cx is None or cy is None:
                continue
            #cx *= 4
            #cy *= 4
            
            # Cut image to 640x640
            img = cut_image(frame, cx, cy, size_x=640, size_y=640)
            # If not detecting, just send the image back to ui
            if not self.is_detecting:
                if self.display_mode == "close":
                    pass
                elif self.display_mode == "raw":
                    # Need to resize raw frame
                    frame = resize_image(frame, width=640, height=640)
                    q_img = cv2_to_qimage(frame)
                    self.ui_signal.emit(q_img, [])
                elif self.display_mode == "zoom_in":
                    q_img = cv2_to_qimage(img)
                    self.ui_signal.emit(q_img, [])
                continue
            
            # Second inference
            first_points, second_points, processed_img = self.second_inference(img)

            # If no points detected, send img back to ui
            if first_points is None or second_points is None:
                if self.display_mode == "close":
                    return_ui_img = None
                elif self.display_mode == "raw":
                    frame = resize_image(frame, width=640, height=640)
                    return_ui_img = cv2_to_qimage(frame)
                else:
                    return_ui_img = cv2_to_qimage(processed_img)

                self.ui_signal.emit(return_ui_img, [])
                continue
      
            # Send drawed image
            if self.is_detecting:
                cv2.circle(processed_img, first_points, 2, (255, 255, 255), -1)
                cv2.circle(processed_img, second_points, 2, (0, 0, 255), -1)

            if self.display_mode == "close":
                return_ui_img = None
            elif self.display_mode == "raw":
                frame = resize_image(frame, width=640, height=640)
                return_ui_img = cv2_to_qimage(frame)
            else:
                return_ui_img = cv2_to_qimage(processed_img)

            self.ui_signal.emit(return_ui_img, [first_points, second_points])

            # Send data to PLC if auto_control is enabled
            if self.auto_control:
                dx, dy, px, py = pixel_to_pulse(
                                    first_points, second_points, 
                                    self.pixel_size, 
                                    self.mm_per_pulses_x, 
                                    self.mm_per_pulses_y, 
                                    self.deadband_mm
                                )
                self.plc_command_signal.emit(dx, dy, px, py)

    def stop(self):
        self.running = False
        self.wait()




