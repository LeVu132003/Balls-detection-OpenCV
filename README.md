# 🎱 Hệ thống phát hiện và so khớp bi bi-a

Hệ thống tự động phát hiện, phân loại và so khớp mẫu các viên bi trên bàn bi-a sử dụng OpenCV.

## 📋 Tổng quan công cụ

Dự án bao gồm 4 công cụ chính:

1. **main.py** - Phát hiện bi tự động từ ảnh
2. **table_corner_selector.py** - Chọn 4 góc bàn bi-a thủ công
3. **positions-selector.py** - Đánh dấu vị trí bi thủ công
4. **compare_positions.py** - So khớp shot với patterns

---

## 🚀 Cài đặt nhanh

```bash
# Cài đặt thư viện
pip install opencv-python numpy matplotlib

# Tạo thư mục cần thiết
mkdir -p input output/annotated output/position patterns/position shots
```

---

## 📖 Hướng dẫn sử dụng

### 1️⃣ Phát hiện bi tự động (`main.py`)

**Mục đích**: Tự động phát hiện các viên bi trong ảnh và xuất kết quả.

#### Cách dùng:

```bash
# Bước 1: Đặt ảnh vào thư mục input/
cp your_image.jpg input/

# Bước 2: Chạy phát hiện
python main.py

# Hoặc phát hiện 1 ảnh cụ thể
python main.py input/1.jpg

# Bao gồm bi 16 (cue ball)
python main.py --cue-ball
```

#### Kết quả:
- `output/annotated/` - Ảnh có chú thích (border, số bi, tọa độ)
- `output/position/` - File JSON chứa tọa độ các bi

#### Ví dụ JSON output:
```json
{
  "balls": [
    {
      "number": 1,
      "x": 181,
      "y": 64,
      "x_norm": 0.123973,
      "y_norm": 0.087912
    }
  ],
  "table_size": {
    "width": 1460,
    "height": 728
  }
}
```

---

### 2️⃣ Chọn góc bàn (`table_corner_selector.py`)

**Mục đích**: Xác định 4 góc bàn bi-a bằng cách kéo thả để chuyển đổi tọa độ sang hệ tọa độ bàn.

#### Cách dùng:

```bash
python table_corner_selector.py \
  --input_file input/table.jpg \
  --output_file table_marked.jpg \
  --json_file table_corners.json
```

#### Hướng dẫn trong giao diện:
1. Kéo các điểm xanh để điều chỉnh vị trí 4 góc
2. Nhấn `ENTER` để lưu
3. Nhấn `ESC` để hủy

#### Tham số:
| Tham số | Mặc định | Mô tả |
|---------|----------|-------|
| `--input_file` | `input.jpg` | Ảnh đầu vào |
| `--output_file` | `output.jpg` | Ảnh có đánh dấu góc |
| `--json_file` | `table.json` | File JSON lưu tọa độ góc |

#### Kết quả JSON:
```json
{
  "table_corners": [
    [532, 257],   // Góc trên trái
    [1992, 257],  // Góc trên phải
    [1989, 984],  // Góc dưới phải
    [532, 985]    // Góc dưới trái
  ]
}
```

---

### 3️⃣ Đánh dấu vị trí bi (`positions-selector.py`)

**Mục đích**: Click để đánh dấu vị trí các viên bi và nhập số bi thủ công.

#### Cách dùng:

```bash
# Với table corners (để chuyển đổi tọa độ)
python positions-selector.py \
  --image shots/shot1.jpg \
  --table-corners table_shot1.json \
  --output shots/shot1-output.json
```

#### Hướng dẫn trong giao diện:
1. **Click chuột trái** tại tâm viên bi
2. **Nhập số bi** trong terminal (1-15) hoặc Enter để skip
3. **Nhấn `u`** để undo điểm vừa click
4. **Nhấn `s`** để lưu và thoát
5. **Nhấn `q`** hoặc ESC để hủy

#### Tham số:
| Tham số | Bắt buộc | Mô tả |
|---------|----------|-------|
| `-i, --image` | Có | Ảnh đầu vào |
| `-t, --table-corners` | Không | File JSON góc bàn |
| `-o, --output` | Không | File JSON output (mặc định: positions.json) |

#### Workflow đầy đủ:
```bash
# 1. Chọn góc bàn
python table_corner_selector.py \
  --input_file shots/shot1.jpg \
  --json_file table_shot1.json

# 2. Đánh dấu vị trí bi
python positions-selector.py \
  --image shots/shot1.jpg \
  --table-corners table_shot1.json \
  --output shots/shot1-output.json
```

---

### 4️⃣ So khớp mẫu (`compare_positions.py`)

**Mục đích**: So sánh một shot với tất cả patterns trong thư mục để tìm mẫu khớp.

#### Cách dùng:

```bash
# Cơ bản
python compare_positions.py shots/shot1-output.json

# Chỉ định thư mục patterns
python compare_positions.py shots/shot1-output.json \
  --patterns-dir patterns/position

# So sánh với sắp xếp theo số bi
python compare_positions.py shots/shot1-output.json --order

# Thay đổi tolerance
python compare_positions.py shots/shot1-output.json --tol 0.05
```

#### Tham số:
| Tham số | Mặc định | Mô tả |
|---------|----------|-------|
| `shot` | (bắt buộc) | File JSON shot cần so khớp |
| `-p, --patterns-dir` | `patterns/position` | Thư mục chứa patterns |
| `--tol` | `0.025` | Sai số chấp nhận (0.025 = 2.5%) |
| `--order` | `False` | Sắp xếp theo số bi trước khi so sánh |

#### Chức năng:
- **Tự động thử 4 chế độ flip**:
  - `none` - Không flip
  - `h` - Horizontal flip (x → 1-x)
  - `v` - Vertical flip (y → 1-y)
  - `hv` - Flip cả hai
- **Lọc bi 1-15**: Chỉ so sánh bi từ 1-15 (bỏ qua bi 16)
- **Hỗ trợ 2 cấu trúc JSON**: Cả cũ và mới

#### Kết quả:

**Tìm thấy match:**
```
MATCH found:
  pattern: patterns/position/3.json  flip: none
```

**Không match:**
```
NO MATCH found in patterns directory.
Best candidate: patterns/position/2.json (mode=h) with 3 mismatches
Mismatches:
#1: shot number=1 pattern number=1
  shot x_norm=0.123973 y_norm=0.087912
  pat  x_norm=0.248268 y_norm=0.087912
  dx=0.124295 dy=0.000000 (tol=0.025)
```

---

## 📁 Cấu trúc thư mục

```
Balls-detection-OpenCV/
│
├── main.py                      # Phát hiện bi tự động
├── table_corner_selector.py    # Chọn góc bàn
├── positions-selector.py        # Đánh dấu vị trí bi
├── compare_positions.py         # So khớp mẫu
├── README.md
├── requirements.txt
│
├── input/                       # Đặt ảnh đầu vào ở đây
│   ├── 1.png
│   └── 2.jpg
│
├── output/                      # Kết quả từ main.py
│   ├── annotated/              # Ảnh đã chú thích
│   └── position/               # File JSON tọa độ
│
├── patterns/                    # Patterns mẫu
│   └── position/
│       ├── 1.json
│       └── 2.json
│
├── shots/                       # Shots cần so khớp
│   ├── shot1.jpg
│   └── shot1-output.json
│
└── table_corners.json           # File góc bàn
```

---

## 🔄 Workflow đầy đủ

### Tạo hệ thống patterns:

```bash
# 1. Chụp ảnh các setup mẫu → pattern_images/
# 2. Tạo patterns
for i in 1 2 3; do
  python table_corner_selector.py \
    --input_file pattern_images/$i.jpg \
    --json_file table_pattern_$i.json
  
  python positions-selector.py \
    --image pattern_images/$i.jpg \
    --table-corners table_pattern_$i.json \
    --output patterns/position/$i.json
done
```

### Kiểm tra shot mới:

```bash
# 1. Chụp ảnh shot → shots/
# 2. Xử lý shot (chọn 1 trong 2 cách)

## Cách 1: Thủ công
python table_corner_selector.py \
  --input_file shots/game1.jpg \
  --json_file table_game1.json

python positions-selector.py \
  --image shots/game1.jpg \
  --table-corners table_game1.json \
  --output shots/game1-output.json

## Cách 2: Tự động
python main.py shots/game1.jpg

# 3. So khớp
python compare_positions.py shots/game1-output.json --order
# hoặc
python compare_positions.py output/position/game1.json --order
```

---

## 🐛 Khắc phục sự cố

### Lỗi thường gặp:

**1. ModuleNotFoundError: No module named 'cv2'**
```bash
pip install opencv-python
```

**2. File 'table_corners.json' not found**
```bash
# Tạo file góc bàn trước
python table_corner_selector.py --input_file input/1.jpg
```

**3. No pattern JSON files found**
```bash
# Tạo patterns hoặc chỉ định đúng đường dẫn
python compare_positions.py shot.json --patterns-dir /path/to/patterns
```

**4. NOT MATCH: Different number of balls**
- Shot và pattern có số lượng bi khác nhau
- Kiểm tra lại số bi (chỉ bi 1-15)

### Kiểm tra môi trường:

```bash
python --version                                    # Python 3.7+
python -c "import cv2; print(cv2.__version__)"     # OpenCV
pip list | grep -E "opencv|numpy"                   # Thư viện
```

---

## 💡 Tips

### Chụp ảnh tốt:
- ✅ Ánh sáng đều, không bóng
- ✅ Camera vuông góc với bàn
- ✅ Độ phân giải cao (≥1280x720)
- ✅ Tránh phản quang

### Tạo patterns:
- ✅ Tạo nhiều patterns cho các setup khác nhau
- ✅ Đặt tên rõ ràng (1.json, 2.json, ...)
- ✅ Kiểm tra patterns trước khi dùng

### So khớp:
- ✅ Dùng `--order` nếu cùng số bi nhưng thứ tự khác
- ✅ Tăng `--tol` nếu cần linh hoạt hơn (0.05)
- ✅ Xem "Best candidate" để debug

---

**Chúc bạn sử dụng thành công! 🎱**
