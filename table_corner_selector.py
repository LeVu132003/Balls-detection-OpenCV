import cv2
import numpy as np
import json
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Billiard Table Corner Selection Tool")
    parser.add_argument("--input_file", type=str, default="input.jpg", help="Path to input image (billiard table)")
    parser.add_argument("--output_file", type=str, default="output.jpg", help="Path to save output image with marked corners")
    parser.add_argument("--json_file", type=str, default="table.json", help="Path to save JSON file containing corner coordinates")
    return parser.parse_args()

def drag_points(image, points):
    dragging_idx = None

    def mouse_callback(event, x, y, flags, param):
        nonlocal dragging_idx
        if event == cv2.EVENT_LBUTTONDOWN:
            for i, (px, py) in enumerate(points):
                if abs(x - px) < 15 and abs(y - py) < 15:
                    dragging_idx = i
        elif event == cv2.EVENT_LBUTTONUP:
            dragging_idx = None
        elif event == cv2.EVENT_MOUSEMOVE and dragging_idx is not None:
            points[dragging_idx] = [x, y]

    clone = image.copy()
    cv2.namedWindow("Set Table Corners")
    cv2.setMouseCallback("Set Table Corners", mouse_callback)

    while True:
        disp = clone.copy()
        for idx, (px, py) in enumerate(points):
            cv2.circle(disp, (px, py), 8, (0, 255, 0), -1)
            cv2.putText(disp, f"{idx+1}", (px+10, py-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        cv2.polylines(disp, [np.array(points, np.int32).reshape((-1,1,2))], isClosed=True, color=(255,0,255), thickness=2)
        cv2.putText(disp, "Drag corners. Press ENTER to save. ESC to cancel.", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
        cv2.imshow("Set Table Corners", disp)
        key = cv2.waitKey(1)
        if key in [13, 10]:  # ENTER
            break
        elif key == 27:  # ESC
            cv2.destroyWindow("Set Table Corners")
            return None
    cv2.destroyWindow("Set Table Corners")
    return points

def main():
    args = parse_args()

    img = cv2.imread(args.input_file)
    if img is None:
        print(f"Image not found: {args.input_file}")
        return

    h, w = img.shape[:2]
    # Default points: 4 corners close to the image border
    default_points = [
        [int(w*0.05), int(h*0.05)],
        [int(w*0.95), int(h*0.05)],
        [int(w*0.95), int(h*0.95)],
        [int(w*0.05), int(h*0.95)]
    ]
    points = drag_points(img, default_points)
    if points is None:
        print("Operation cancelled.")
        return

    # Save coordinates to JSON
    data = {"table_corners": points}
    with open(args.json_file, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Corners saved to {args.json_file}")

    # Draw corners on the image and save it
    img_marked = img.copy()
    for idx, (px, py) in enumerate(points):
        cv2.circle(img_marked, (px, py), 8, (0, 255, 0), -1)
        cv2.putText(img_marked, f"{idx+1}", (px+10, py-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
    cv2.polylines(img_marked, [np.array(points, np.int32).reshape((-1,1,2))], isClosed=True, color=(255,0,255), thickness=2)
    cv2.imwrite(args.output_file, img_marked)
    print(f"Marked image saved to {args.output_file}")

if __name__ == "__main__":
    main()