import cv2
from matplotlib.pyplot import gray
import numpy as np
import os
import glob
import json
import sys
import argparse

TABLE_CORNERS_FILE = "table_corners.json"

def get_ball_number(b, g, r, brightness, detect_cue_ball=False):
    """
    Xác định số thứ tự bi dựa trên màu BGR và độ sáng trung bình
    
    Args:
        b, g, r: Giá trị màu BGR (0-255)
        brightness: Độ sáng trung bình (0-255)
        detect_cue_ball: Có phát hiện bi 16 (cue ball) hay không
    
    Returns:
        int: Số thứ tự bi (1-15 hoặc 16 nếu detect_cue_ball=True), hoặc 0 nếu không khớp
    """

    # Danh sách các pattern bi (không bao gồm cue ball)
    base_patterns = [
        # Bi 1: Màu vàng sáng
        (1, lambda b,g,r,br: 20<=b<=90 and 150<=g<=230 and 150<=r<=230 and 140<=br<=190),
        
        # Bi 2: Màu xanh dương
        (2, lambda b,g,r,br: 140<=b<=190 and 80<=g<=120 and 10<=r<=45 and 70<=br<=110),
        
        # Bi 3: Màu đỏ
        (3, lambda b,g,r,br: 30<=b<=100 and 25<=g<=90 and 110<=r<=255 and 70<=br<=140),
        
        # Bi 4: Màu hồng
        (4, lambda b,g,r,br: 155<=b<=170 and 90<=g<=100 and 200<=r<=240 and 130<=br<=150),
        
        # Bi 5: Màu cam
        (5, lambda b,g,r,br: 30<=b<=95 and 80<=g<=145 and 160<=r<=225 and 100<=br<=160),
        
        # Bi 6: Màu xanh lá đậm
        (6, lambda b,g,r,br: 80<=b<=120 and 100<=g<=150 and 15<=r<=45 and 75<=br<=110),
        
        # Bi 7: Màu xanh lá nhạt
        (7, lambda b,g,r,br: 55<=b<=125 and 70<=g<=140 and 65<=r<=135 and 75<=br<=125),
        
        # Bi 8: Màu xanh đậm
        (8, lambda b,g,r,br: 75<=b<=110 and 55<=g<=90 and 25<=r<=55 and 50<=br<=80),
        
        # Bi 9: Màu vàng nhạt
        (9, lambda b,g,r,br: 80<=b<=135 and 165<=g<=205 and 160<=r<=230 and 165<=br<=200),
        
        # Bi 10: Màu xanh dương nhạt
        (10, lambda b, g, r, br: 170 <= b <= 210 and 120 <= g <= 160 and 65 <= r <= 105 and 115 <= br <= 145),
        
        # Bi 11: Màu đỏ viền trắng 
        (11, lambda b,g,r,br: 95<=b<=115 and 95<=g<=105 and 210<=r<=230 and 125<=br<=150),

        # Bi 12: Màu hồng viền trắng
        (12, lambda b, g, r, br: 169 <= b <= 209 and 122 <= g <= 162 and 201 <= r <= 241 and 151 <= br <= 191),

        # Bi 13: Màu cam viền trắng
        (13, lambda b, g, r, br: 87 <= b <= 127 and 135 <= g <= 175 and 204 <= r <= 244 and 149 <= br <= 189),
        
        # Bi 14: Màu xanh lá viền trắng
        (14, lambda b, g, r, br: 117 <= b <= 157 and 136 <= g <= 176 and 65 <= r <= 105 and 110 <= br <= 150),

        # Bi 15: Màu tím viền trắng
        (15, lambda b, g, r, br: 91 <= b <= 131 and 117 <= g <= 157 and 149 <= r <= 189 and 124 <= br <= 164),
    ]
    
    # Tạo danh sách patterns cuối cùng
    ball_patterns = base_patterns.copy()
    
    # Chỉ thêm cue ball nếu được yêu cầu
    if detect_cue_ball:
        ball_patterns.append((16, lambda b,g,r,br: 160<=b<=255 and 160<=g<=255 and 160<=r<=255 and 160<=br<=255))

    for ball_num, pattern_func in ball_patterns:
        if pattern_func(b, g, r, brightness):
            return ball_num
    
    return 0

def detect_circles(image_path, annotated_output_path, json_output_path, detect_cue_ball=False):
    """
    Phát hiện các vật thể hình tròn (bi và lỗ) trên bàn bi-a
    
    Args:
        image_path: Đường dẫn đến ảnh đầu vào
        annotated_output_path: Đường dẫn lưu ảnh đã chú thích
        json_output_path: Đường dẫn lưu file JSON với tọa độ các bi
        detect_cue_ball: Có phát hiện bi 16 (cue ball) hay không
    """
    # Đọc ảnh
    img = cv2.imread(image_path)
    if img is None:
        print(f"Không thể đọc ảnh từ {image_path}")
        return
    
    # Tạo bản sao để vẽ
    output = img.copy()

    # Load table corners and compute perspective transform to table coordinate system
    table_corners = None
    transform_M = None
    table_size = None
    try:
        with open(TABLE_CORNERS_FILE, 'r', encoding='utf-8') as f:
            tc = json.load(f)
            # Expecting structure { "table_corners": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] }
            if 'table_corners' in tc and len(tc['table_corners']) == 4:
                table_corners = np.array(tc['table_corners'], dtype=np.float32)
                # We'll map these to a rectangular table coordinate system with origin at top-left
                # Compute width and height from corners (take max of opposing edges)
                widthA = np.linalg.norm(table_corners[1] - table_corners[0])
                widthB = np.linalg.norm(table_corners[2] - table_corners[3])
                maxWidth = int(max(widthA, widthB))

                heightA = np.linalg.norm(table_corners[3] - table_corners[0])
                heightB = np.linalg.norm(table_corners[2] - table_corners[1])
                maxHeight = int(max(heightA, heightB))

                table_size = (maxWidth, maxHeight)

                dst = np.array([[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype=np.float32)
                transform_M = cv2.getPerspectiveTransform(table_corners, dst)
            else:
                print(f"Warning: '{TABLE_CORNERS_FILE}' not in expected format. Falling back to image coordinates.")
    except FileNotFoundError:
        print(f"Warning: '{TABLE_CORNERS_FILE}' not found. Falling back to image coordinates.")
    except Exception as e:
        print(f"Warning: failed to load '{TABLE_CORNERS_FILE}': {e}. Falling back to image coordinates.")
    
    # Tách các kênh màu để bảo toàn thông tin màu sắc
    b, g, r = cv2.split(img)
    
    # Chuyển sang ảnh xám nhưng với trọng số tối ưu để giữ lại chi tiết
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Tạo ảnh tổng hợp từ các kênh màu để phát hiện hình tròn tốt hơn
    # Sử dụng kênh có contrast cao nhất
    combined = np.maximum(np.maximum(r, g), b)

    # Phát hiện tất cả các hình tròn từ ảnh tổng hợp
    circles = cv2.HoughCircles(
        combined,
        cv2.HOUGH_GRADIENT,
        dp=1.0,
        minDist=15,  # 15
        param1=200,  # 200
        param2=15,   # 15
        minRadius=8, # 8
        maxRadius=13 # 13
    )
    
    detected_balls = []
    hole_count = 0
    
    # Xử lý tất cả các hình tròn được phát hiện
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for circle in circles[0, :]:
            center = (circle[0], circle[1])
            radius = circle[2]
            
            # Kiểm tra ROI cho màu sắc
            roi = img[max(0, circle[1]-radius):min(img.shape[0], circle[1]+radius),
                     max(0, circle[0]-radius):min(img.shape[1], circle[0]+radius)]
            
            # Kiểm tra ROI cho độ sáng
            roi_gray = gray[max(0, circle[1]-radius):min(gray.shape[0], circle[1]+radius),
                           max(0, circle[0]-radius):min(gray.shape[1], circle[0]+radius)]
            
            if roi.size > 0 and roi_gray.size > 0:
                avg_color = np.mean(roi)
                avg_intensity = np.mean(roi_gray)
                
                # Lấy thông tin màu sắc chi tiết của ROI
                avg_bgr = np.mean(roi, axis=(0, 1))  # Trung bình B, G, R
                b_avg, g_avg, r_avg = avg_bgr
                
                # Phân loại dựa trên kích thước và màu sắc
                if 8 <= radius <= 12 and avg_color > 50:  # Bi lớn và có màu
                    # Kiểm tra nếu bi màu trắng (giá trị BGR cao và cân bằng)
                    # is_white = (b_avg > 180 and g_avg > 180 and r_avg > 180 and 
                            #    abs(b_avg - g_avg) < 30 and abs(g_avg - r_avg) < 30 and abs(b_avg - r_avg) < 30)
                    
                    # if not is_white:  # Chỉ xử lý bi không phải màu trắng
                        # Sử dụng hàm get_ball_number để xác định số bi
                        ball_number = get_ball_number(int(b_avg), int(g_avg), int(r_avg), int(avg_intensity), detect_cue_ball)
                        
                        # Lưu thông tin bi với số thứ tự
                        if (ball_number > 0):
                            ball_info = {
                                'center': center,
                                'radius': radius,
                                'bgr': (b_avg, g_avg, r_avg),
                                'brightness': avg_intensity,
                                'number': ball_number
                            }
                            detected_balls.append(ball_info)
                elif radius <= 6 and avg_intensity < 50:  # Lỗ nhỏ và tối màu
                    hole_count += 1
    
    # In thông tin và vẽ tất cả các hình tròn được phát hiện
    for i, ball in enumerate(detected_balls, 1):
        center = ball['center']
        radius = ball['radius']
        b_avg, g_avg, r_avg = ball['bgr']
        ball_number = ball['number']
        
        # In thông tin màu sắc và số bi ra màn hình
        # If we have a perspective transform, map the center to table coordinates
        if transform_M is not None:
            src_pt = np.array([[[center[0], center[1]]]], dtype=np.float32)
            dst_pt = cv2.perspectiveTransform(src_pt, transform_M)[0][0]
            table_x, table_y = int(dst_pt[0]), int(dst_pt[1])
            coord_text = f"({table_x}, {table_y})"
            print(f"Bi số {ball_number if ball_number > 0 else 'Không xác định'}:")
            print(f"  Tọa độ (bàn): {coord_text}")
        else:
            print(f"Bi số {ball_number if ball_number > 0 else 'Không xác định'}:")
            print(f"  Tọa độ (ảnh): ({center[0]}, {center[1]})")
        print(f"  Bán kính: {radius}")
        print(f"  Màu BGR: B={b_avg:.1f}, G={g_avg:.1f}, R={r_avg:.1f}")
        print(f"  Màu RGB: R={r_avg:.1f}, G={g_avg:.1f}, B={b_avg:.1f}")
        print(f"  Độ sáng trung bình: {ball['brightness']:.1f}")
        if ball_number > 0:
            print(f"  Số bi được xác định: {ball_number}")
        else:
            print(f"  Không xác định được số bi")
        print("-" * 40)
        
        # Vẽ border hình tròn màu đen xung quanh vật thể
        cv2.circle(output, center, radius, (0, 0, 0), 3)  # Border đen dày 3px
        cv2.circle(output, center, 2, (0, 0, 0), 3)  # Tâm màu đen
        
        # Hiển thị số bi và tọa độ (hiển thị toạ độ bàn nếu có)
        if ball_number > 0:
            cv2.putText(output, f'Ball {ball_number}', 
                      (center[0] - 25, center[1] - radius - 10),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.4, (60, 60, 60), 1)  # Text màu xám nhạt
            # Hiển thị tọa độ bên phải viên bi
            if transform_M is not None:
                cv2.putText(output, coord_text, 
                          (center[0] + radius + 8, center[1] + 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.35, (60, 60, 60), 1)
            else:
                cv2.putText(output, f'({center[0]},{center[1]})', 
                          (center[0] + radius + 8, center[1] + 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.35, (60, 60, 60), 1)  # Text màu xám nhạt
        else:
            cv2.putText(output, f'Ball ?', 
                      (center[0] - 15, center[1] - radius - 10),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.4, (60, 60, 60), 1)  # Text màu xám nhạt
            # Hiển thị tọa độ bên phải viên bi cho bi không xác định được số
            if transform_M is not None:
                cv2.putText(output, coord_text, 
                          (center[0] + radius + 8, center[1] + 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.35, (60, 60, 60), 1)
            else:
                cv2.putText(output, f'({center[0]},{center[1]})', 
                          (center[0] + radius + 8, center[1] + 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.35, (60, 60, 60), 1)  # Text màu xám nhạt
    
    # Đếm số hình tròn được phát hiện
    ball_count = len(detected_balls)
    
    # Thêm thông tin tổng quan
    info_text = f'Circles: {ball_count} | Holes: {hole_count} | Total: {ball_count + hole_count}'
    cv2.putText(output, info_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Lưu ảnh kết quả đã chú thích
    cv2.imwrite(annotated_output_path, output)
    
    # Tạo dữ liệu JSON với tọa độ các bi
    balls_data = []
    for ball in detected_balls:
        # Map to table coordinates if transform available
        cx, cy = ball['center']
        if transform_M is not None:
            src_pt = np.array([[[cx, cy]]], dtype=np.float32)
            dst_pt = cv2.perspectiveTransform(src_pt, transform_M)[0][0]
            tx, ty = int(dst_pt[0]), int(dst_pt[1])
        else:
            tx, ty = int(cx), int(cy)

        # Determine normalization base (table size if available, otherwise image size)
        if table_size is not None:
            norm_w, norm_h = table_size[0], table_size[1]
        else:
            norm_w, norm_h = img.shape[1], img.shape[0]

        # Avoid division by zero
        x_norm = float(tx) / float(norm_w) if norm_w > 0 else 0.0
        y_norm = float(ty) / float(norm_h) if norm_h > 0 else 0.0

        ball_data = {
            "number": int(ball['number']),
            "x": tx,
            "y": ty,
            "x_norm": round(x_norm, 6),
            "y_norm": round(y_norm, 6)
        }
        balls_data.append(ball_data)
    
    # Tạo cấu trúc JSON cuối cùng
    json_data = {
        "balls": balls_data
    }
    # If we computed table size, include it so consumers know coordinate space
    if table_size is not None:
        json_data['table_size'] = {"width": int(table_size[0]), "height": int(table_size[1])}
    
    # Lưu file JSON
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    # In tổng kết
    print("=" * 50)
    print(f"KET QUA PHAT HIEN:")
    print(f"Tổng số bi phát hiện: {ball_count}")
    print(f"Ảnh đã chú thích được lưu tại: {annotated_output_path}")
    print(f"File JSON tọa độ được lưu tại: {json_output_path}")
    print("=" * 50)
    
    return json_data

if __name__ == "__main__":
    # Thiết lập argument parser
    parser = argparse.ArgumentParser(description='Phát hiện và phân loại bi bi-a trong ảnh')
    parser.add_argument('input_path', nargs='?', default='input', 
                       help='Đường dẫn đến file ảnh hoặc thư mục chứa ảnh (mặc định: input)')
    parser.add_argument('--cue-ball', action='store_true', 
                       help='Phát hiện bi 16 (cue ball - bi trắng)')
    
    args = parser.parse_args()
    
    # Xác định input source
    input_path = args.input_path
    detect_cue_ball = args.cue_ball
    
    if os.path.isfile(input_path):
        # Input là một file đơn lẻ
        image_files = [input_path]
    elif os.path.isdir(input_path):
        # Input là một folder
        input_folder = input_path
        image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tiff']
        image_files = []
        
        for extension in image_extensions:
            image_files.extend(glob.glob(os.path.join(input_folder, extension)))
            image_files.extend(glob.glob(os.path.join(input_folder, extension.upper())))
    else:
        print(f"Đường dẫn '{input_path}' không tồn tại!")
        print("Sử dụng: python main.py [đường_dẫn_file_hoặc_folder] [--cue-ball]")
        exit(1)
    
    if not image_files:
        print("Không tìm thấy file ảnh nào!")
        exit(1)
    
    # Tạo folder output nếu chưa tồn tại
    output_annotated_folder = "output/annotated"
    output_position_folder = "output/position"
    
    if not os.path.exists(output_annotated_folder):
        os.makedirs(output_annotated_folder)
    
    if not os.path.exists(output_position_folder):
        os.makedirs(output_position_folder)
    
    print(f"Tìm thấy {len(image_files)} file ảnh")
    print("=" * 60)
    
    # Xử lý từng ảnh
    for i, image_path in enumerate(image_files, 1):
        # Lấy tên file không có đường dẫn
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        
        # Tạo đường dẫn output
        annotated_output_path = os.path.join(output_annotated_folder, filename)
        json_output_path = os.path.join(output_position_folder, f"{name}.json")
        
        print(f"Đang xử lý ảnh {i}/{len(image_files)}: {filename}")
        print("-" * 40)
        
        # Gọi hàm detect circles
        result = detect_circles(image_path, annotated_output_path, json_output_path, detect_cue_ball)
        
        print(f"Số bi được phát hiện: {len(result['balls'])}")
        print("=" * 60)
    
    print("Hoàn thành xử lý tất cả ảnh!")
    print(f"Ảnh đã chú thích được lưu trong: {output_annotated_folder}")
    print(f"File JSON tọa độ được lưu trong: {output_position_folder}")
    if detect_cue_ball:
        print("✅ Đã bao gồm phát hiện bi 16 (cue ball)")
    else:
        print("ℹ️  Chỉ phát hiện bi 1-15 (sử dụng --cue-ball để bao gồm bi 16)")