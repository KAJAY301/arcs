import os
import cv2
import sys
import shutil
import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QApplication

from arcs.utils.config_manager import load_model_path, load_json_config
from arcs.utils.image_processor import qimage_to_cv2
from arcs.core.inference_thread import InferenceThread

class FirstModelResult():
    def __init__(self, img_dir):
        self.cfg = load_json_config()
        inf_cfg = self.cfg.get("inference", {})
        first_model = inf_cfg.get("first_model")
        self.model_path = load_model_path(first_model)

        self.img_dir = img_dir
        self.output_dir = os.path.join("test", "model_result")
        self.prepare_output_directory()
        self.is_detecting = True

        self.image_extensions = ('.jpg')
        self.image_files = [f for f in os.listdir(img_dir) if f.lower().endswith(self.image_extensions)]
        self.image_files.sort()
        self.current_index = 0

        if not self.image_files:
            print(f"Error: No images found in {img_dir}")
            sys.exit(1)

        self.infer_thread = InferenceThread(
            model_path = self.model_path,
            conf_thresh = inf_cfg.get("conf_threshold"),
            iou_thresh = inf_cfg.get("iou_threshold"),
            display_size = (600, 600)#unused
        )

        self.infer_thread.result_ready.connect(self.mark_inference_result, Qt.QueuedConnection)
        self.infer_thread.start()

        self.process_next_image()

    def prepare_output_directory(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
            print(f"Removed existing directory: {self.output_dir}")
        os.makedirs(self.output_dir)
        print(f"Created directory: {self.output_dir}")

    def process_next_image(self):
        if self.current_index < len(self.image_files):
            filename = self.image_files[self.current_index]
            full_path = os.path.join(self.img_dir, filename)
            
            self.current_frame = cv2.imread(full_path)
            if self.current_frame is not None:
                print(f"Processing ({self.current_index + 1}/{len(self.image_files)}): {filename}")
                self.infer_thread.submit_frame(self.current_frame)
            else:
                print(f"Skip (Read Error): {filename}")
                self.current_index += 1
                self.process_next_image()
        else:
            print("--- All images processed. ---")
            self.finish_all()

    def mark_inference_result(self, data, q_img):
        filename = self.image_files[self.current_index]

        w_pt = data.get('white')
        c_pt = data.get('color')

        draw_img = qimage_to_cv2(q_img)

        if w_pt and c_pt:
            dx = (c_pt[0] - w_pt[0])
            dy = (c_pt[1] - w_pt[1])
            w = (300, 300)
            c = (int(300 + 2 * dx), int(300 + 2 * dy))

            cv2.circle(draw_img, w, 2, (255, 255, 255), -1)
            cv2.circle(draw_img, c, 2, (0, 0, 255), -1)

            print(f"  Result -> White: {w_pt}, Color: {c_pt}, Offset: ({dx}, {dy})")
        else:
            print(f"  Warning: Target not found in {filename}")
            
        save_path = os.path.join(self.output_dir, f"res_{filename}")
        cv2.imwrite(save_path, draw_img)

        self.current_index += 1
        self.process_next_image()
            
    def finish_all(self):
        self.infer_thread.stop()
        QApplication.instance().quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    img_directory = "test/test_img"
    test_node = FirstModelResult(img_directory)
    
    sys.exit(app.exec_())