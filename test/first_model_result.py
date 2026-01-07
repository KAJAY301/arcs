import os
import cv2
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication

from arcs.utils.image_processor import cv2_to_qimage
from arcs.utils.config_manager import load_model_path, load_json_config
from arcs.core.inference_thread import InferenceThread

def run_test():
    # 使用 QApplication 管理物件生命週期，但不一定要跑 exec_()
    app = QApplication(sys.argv)
    cfg = load_json_config()
    inf_cfg = cfg.get("inference", {})
    
    # 讀取模型路徑 (請確保 config 裡有 first_model 這個 key)
    model_path = load_model_path(inf_cfg.get("first_model") or inf_cfg.get("model"))
    
    img_dir = "test/test_img"
    output_dir = "test/first_model_result"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 初始化推論引擎 (這裡我們不需要 Start Thread，直接調用它的方法)
    tester = InferenceThread(
        first_model_path=model_path,
        second_model_path=model_path, 
        conf_thresh=inf_cfg.get("conf_threshold"),
        iou_thresh=inf_cfg.get("iou_threshold"),
        display_size=(640, 640)
    )

    image_files = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.png', '.bmp'))]
    image_files.sort()
    total = len(image_files)
    
    print(f"Starting batch process: {total} images found.")

    for idx, img_name in enumerate(image_files):
        full_path = os.path.join(img_dir, img_name)
        frame = cv2.imread(full_path)
        
        if frame is not None:
            # 1. 執行第一階段 (直接呼叫方法，這會阻塞直到完成)
            cx, cy = tester.first_inference(frame)
            
            if cx is not None and cy is not None:
                # 2. 執行裁切
                crop_rgb = tester.cut_img(frame, cx, cy, size_x=640, size_y=640)
                
                # 3. 存檔 (將 RGB 轉回 BGR 才能正確用 cv2 儲存)
                save_path = os.path.join(output_dir, f"{idx+154}.jpg")
                crop_bgr = cv2.cvtColor(crop_rgb, cv2.COLOR_RGB2BGR)
                cv2.imwrite(save_path, crop_rgb)
                
                print(f"[{idx+1}/{total}] Processed: {img_name} (Center: {cx}, {cy})")
            else:
                print(f"[{idx+1}/{total}] Failed: {img_name} - No target detected.")
        else:
            print(f"[{idx+1}/{total}] Skip: {img_name} - Read error.")

    print("\nAll tasks completed. System shutting down...")
    
    # 完成後直接退出
    QCoreApplication.quit()
    sys.exit(0)

if __name__ == "__main__":
    run_test()