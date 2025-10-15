#!/usr/bin/env python3
"""
Interactive position selector
- Show an image using OpenCV
- Let user drag rectangles (click-drag)
- After releasing mouse, prompt in terminal for class name (e.g., ball number)
- Compute rectangle center in image coords
- If a table corners JSON is provided, compute perspective transform and map center to table coords
- Compute normalized coords (0-1) relative to table size (or image size)
- Save results to JSON matching the requested format

Usage:
  python3 positions-selector.py --image 3.jpg --table-corners table_input.json --output 3-output.json

"""

import cv2
import argparse
import json
import numpy as np
import os

# Globals for mouse callback
refPt = []
drawing = False
current_image = None
clone_image = None
# rects now holds point annotations: {"pt": (x,y), "class": str}
rects = []
current_mouse = None


def click_and_drag(event, x, y, flags, param):
    """Handle single-click: add a point annotation at click location and prompt for class."""
    global current_image, clone_image, rects
    if event == cv2.EVENT_LBUTTONDOWN:
        # Record point
        pt = (x, y)
        rects.append({"pt": pt, "class": ''})
        # Prompt user for class/name in terminal
        class_name = input('Enter class/name for clicked point (or press Enter to skip): ').strip()
        if class_name:
            rects[-1]['class'] = class_name
        redraw_annotations()
        cv2.imshow('image', clone_image)


def load_table_transform(tc_file):
    try:
        with open(tc_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'table_corners' in data and len(data['table_corners']) == 4:
                corners = np.array(data['table_corners'], dtype=np.float32)
                widthA = np.linalg.norm(corners[1] - corners[0])
                widthB = np.linalg.norm(corners[2] - corners[3])
                maxWidth = int(max(widthA, widthB))
                heightA = np.linalg.norm(corners[3] - corners[0])
                heightB = np.linalg.norm(corners[2] - corners[1])
                maxHeight = int(max(heightA, heightB))
                dst = np.array([[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype=np.float32)
                M = cv2.getPerspectiveTransform(corners, dst)
                return M, (maxWidth, maxHeight)
            else:
                print('Table corners file format invalid. Expected key "table_corners" with 4 points.')
    except FileNotFoundError:
        print(f"Table corners file '{tc_file}' not found.")
    except Exception as e:
        print('Failed to load table corners:', e)
    return None, None


def redraw_annotations():
    """Redraw clone_image from current_image and all rectangles in `rects`."""
    global clone_image, current_image, rects
    if current_image is None:
        return
    clone_image = current_image.copy()
    for r in rects:
        pt = tuple(r['pt'])
        # draw small circle at point
        cv2.circle(clone_image, pt, 6, (0, 255, 0), -1)
        cls = r.get('class')
        if cls:
            text_pos = (pt[0] + 8, pt[1] + 4)
            cv2.putText(clone_image, str(cls), text_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)


def main():
    global current_image, clone_image
    parser = argparse.ArgumentParser(description='Interactive bounding-box selector that outputs table-normalized coordinates')
    parser.add_argument('--image', '-i', required=True, help='Input image path')
    parser.add_argument('--table-corners', '-t', help='JSON file containing table_corners (optional)')
    parser.add_argument('--output', '-o', default='positions.json', help='Output JSON file')

    args = parser.parse_args()

    if not os.path.isfile(args.image):
        print('Image not found:', args.image)
        return

    img = cv2.imread(args.image)
    if img is None:
        print('Failed to read image:', args.image)
        return

    current_image = img
    clone_image = img.copy()

    transform_M = None
    table_size = None
    if args.table_corners:
        transform_M, table_size = load_table_transform(args.table_corners)
        if transform_M is not None:
            print('Loaded table corners. Table size:', table_size)

    cv2.namedWindow('image', cv2.WINDOW_NORMAL)
    cv2.setMouseCallback('image', click_and_drag)

    print('Instructions:')
    print('- Drag mouse to draw a rectangle; after release, enter class/name in terminal.')
    print("- Press 's' to save and exit, 'q' or ESC to quit without saving.")

    while True:
        # Show image; if currently drawing, render a temporary rectangle for feedback
        if drawing and current_mouse is not None and refPt:
            img_to_show = clone_image.copy()
            cv2.rectangle(img_to_show, refPt[0], current_mouse, (0, 255, 0), 2)
            cv2.imshow('image', img_to_show)
        else:
            cv2.imshow('image', clone_image)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            print('Exiting without saving.')
            break
        elif key == ord('u'):
            # undo last rectangle
            if rects:
                removed = rects.pop()
                print('Undid last rectangle:', removed.get('class', ''))
                redraw_annotations()
                cv2.imshow('image', clone_image)
            else:
                print('No rectangles to undo.')
        elif key == ord('s'):
            # Build JSON
            output = {}
            balls = []
            # If transform not provided, use image dims for normalization
            if table_size is not None:
                W, H = table_size
            else:
                H, W = img.shape[:2]
            for r in rects:
                cx, cy = r['pt']
                # Map to table coords if available
                if transform_M is not None:
                    src_pt = np.array([[[cx, cy]]], dtype=np.float32)
                    dst_pt = cv2.perspectiveTransform(src_pt, transform_M)[0][0]
                    tx, ty = int(dst_pt[0]), int(dst_pt[1])
                else:
                    tx, ty = int(cx), int(cy)
                x_norm = round(tx / W, 6) if W > 0 else 0.0
                y_norm = round(ty / H, 6) if H > 0 else 0.0
                entry = {
                    'number': int(r['class']) if isinstance(r.get('class'), str) and r['class'].isdigit() else r.get('class'),
                    'x': tx,
                    'y': ty,
                    'x_norm': x_norm,
                    'y_norm': y_norm
                }
                balls.append(entry)

            output['balls'] = balls
            if table_size is not None:
                output['table_size'] = {'width': int(table_size[0]), 'height': int(table_size[1])}
            # Save
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print('Saved to', args.output)
            break

    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
