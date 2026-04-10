import cv2
import time
import numpy as np

#global variables
threshold_value = 52 #去除背景
kernel_size = 40 #去除雜訊

white_bgr = np.array([26, 39, 42])
color_threshold = 10
#color_bgr = np.array([10, 10, 30])

def is_white(b, g, r):
    current_color = np.array([b, g, r])
    distance = np.linalg.norm(current_color - white_bgr)
    #print(f"Sampled Color (BGR): {b}, {g}, {r}, Distance: {distance}")
    return distance < color_threshold


def find_cross_center_gray(image):
    # BGR -> GRAY
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # GRAY -> BINARY
    _, binary = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY_INV)
    
    # Find Lines which Longer than {kernel_size} pixels
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_size))
    # Opening Operation
    h_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel)
    v_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel)

    # Find centroids
    h_num_labels, h_labels, h_stats, h_centroids = cv2.connectedComponentsWithStats(h_lines)
    v_num_labels, v_labels, v_stats, v_centroids = cv2.connectedComponentsWithStats(v_lines)

    # Find Distances and color sample
    h_distances = 0
    v_distances = 0

    if h_num_labels == 3:
        h_white_centroids = 0
        h_color_centroids = 0
        for i in range(1, h_num_labels):
            mask_single_line = (h_labels == i).astype("uint8") * 255
            b, g, r = cv2.mean(image, mask=mask_single_line)[:3]
            if is_white(b, g, r):
                h_white_centroids = h_centroids[i][1]
            else:
                h_color_centroids = h_centroids[i][1]
        h_distances = int(h_white_centroids) - int(h_color_centroids)
        
    if v_num_labels == 3:
        v_white_centroids = 0
        v_color_centroids = 0
        for i in range(1, v_num_labels):
            mask_single_line = (v_labels == i).astype("uint8") * 255
            b, g, r = cv2.mean(image, mask=mask_single_line)[:3]
            if is_white(b, g, r):
                v_white_centroids = v_centroids[i][0]
            else:
                v_color_centroids = v_centroids[i][0]
        v_distances = int(v_white_centroids) - int(v_color_centroids)


    #cv2.imshow('Binary Image', binary)
    #cv2.imshow('Horizontal Lines', h_lines)
    #cv2.imshow('Vertical Lines', v_lines)
    results = [h_distances, v_distances]
    return results

def find_cross_center_hsv(image):
    # BGR -> HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # HSV -> BINARY
    white_lower_hsv = np.array([10, 0, 26])
    white_upper_hsv = np.array([60, 255, 58])
    white_binary = cv2.inRange(hsv, white_lower_hsv, white_upper_hsv)

    color_lower_hsv = np.array([0, 140, 0])
    color_upper_hsv = np.array([179, 255, 255])
    color_binary = cv2.inRange(hsv, color_lower_hsv, color_upper_hsv)

    #black_lower_hsv = np.array([0, 0, 0])
    #black_upper_hsv = np.array([179, 255, 255])
    #black_binary = cv2.inRange(hsv, black_lower_hsv, black_upper_hsv)

    # Find Lines which Longer than {kernel_size} pixels
    kernel_size = 30
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_size))

    # Opening Operation
    white_h_lines = cv2.morphologyEx(white_binary, cv2.MORPH_OPEN, h_kernel)
    white_v_lines = cv2.morphologyEx(white_binary, cv2.MORPH_OPEN, v_kernel)
    color_h_lines = cv2.morphologyEx(color_binary, cv2.MORPH_OPEN, h_kernel)
    color_v_lines = cv2.morphologyEx(color_binary, cv2.MORPH_OPEN, v_kernel)

    #cv2.imshow('white_binary', white_binary)
    #cv2.imshow('white_h_lines', white_h_lines)
    #cv2.imshow('color_h_lines', color_h_lines)
    #cv2.imshow('white_v_lines', white_v_lines)
    #cv2.imshow('color_v_lines', color_v_lines)
    # Find Intersections
    white_joints = cv2.bitwise_and(white_h_lines, white_v_lines)
    color_joints = cv2.bitwise_and(color_h_lines, color_v_lines)

    # return how many points, their coordinates
    white_num_labels, labels, stats, white_centroids = cv2.connectedComponentsWithStats(white_joints)
    color_num_labels, labels, stats, color_centroids = cv2.connectedComponentsWithStats(color_joints)

    white_results = []
    color_results = []
    for i in range(1, white_num_labels):
        x, y = white_centroids[i]
        white_results.append((int(x), int(y)))
        #print(f"偵測到白色十字中心: {int(x)}, {int(y)}")
    for i in range(1, color_num_labels):
        x, y = color_centroids[i]
        color_results.append((int(x), int(y)))
        #print(f"偵測到彩色十字中心: {int(x)}, {int(y)}")
    
    return [white_results, color_results]

def find_cross_center_bgr(image):
    # BGR -> BINARY
    white_lower_bgr = np.array([10, 10, 0])
    white_upper_bgr = np.array([70, 70, 50])
    white = cv2.inRange(image, white_lower_bgr, white_upper_bgr)

    color_lower_bgr = np.array([0, 0, 40])
    color_upper_bgr = np.array([40, 40, 100])
    color = cv2.inRange(image, color_lower_bgr, color_upper_bgr)
    
    # Find Lines which Longer than {kernel_size} pixels
    kernel_size = 40
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_size))

    # Opening Operation
    white_h_lines = cv2.morphologyEx(white, cv2.MORPH_OPEN, h_kernel)
    white_v_lines = cv2.morphologyEx(white, cv2.MORPH_OPEN, v_kernel)
    
    color_h_lines = cv2.morphologyEx(color, cv2.MORPH_OPEN, h_kernel)
    color_v_lines = cv2.morphologyEx(color, cv2.MORPH_OPEN, v_kernel)

    # Find Intersections
    white_joints = cv2.bitwise_and(white_h_lines, white_v_lines)
    color_joints = cv2.bitwise_and(color_h_lines, color_v_lines)

    # return how many points, their coordinates
    white_num_labels, labels, stats, white_centroids = cv2.connectedComponentsWithStats(white_joints)
    color_num_labels, labels, stats, color_centroids = cv2.connectedComponentsWithStats(color_joints)

    white_results = []
    color_results = []
    for i in range(1, white_num_labels):
        x, y = white_centroids[i]
        white_results.append((int(x), int(y)))
        print(f"偵測到白色十字中心: {int(x)}, {int(y)}")
    for i in range(1, color_num_labels):
        x, y = color_centroids[i]
        color_results.append((int(x), int(y)))
        print(f"偵測到彩色十字中心: {int(x)}, {int(y)}")
    return white_joints, color_joints


def main():
    img = cv2.imread(r'D:\program\Film Printing\test\640img\260113152046.jpg')
    #img = cv2.imread(r'D:\program\Film Printing\test\640img\260113155140.jpg')
    #img = cv2.imread(r'D:\program\Film Printing\test\640img\260113151951.jpg')#上下
    start_time = time.perf_counter()

    res = find_cross_center_gray(img)

    end_time = time.perf_counter()
    print(f"處理時間: {end_time - start_time:.4f} 秒")
    print(res)



    """for center in res[0]:
        print(f"第一色十字中心: {center}")
    for center in res[1]:
        print(f"第二色十字中心: {center}")"""
    
    cv2.imshow('Raw Image', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()