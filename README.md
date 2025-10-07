# 🎱 Hệ thống phát hiện bi bi-a bằng OpenCV

Hệ thống tự động phát hiện và phân loại các viên bi trong ảnh bàn bi-a sử dụng computer vision với OpenCV và Python.

## 📋 Mục lục
- [Tính năng](#-tính-năng)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt môi trường](#-cài-đặt-môi-trường)
- [Cấu trúc thư mục](#-cấu-trúc-thư-mục)
- [Cách sử dụng](#-cách-sử-dụng)
- [Kết quả đầu ra](#-kết-quả-đầu-ra)
- [Cấu hình nâng cao](#-cấu-hình-nâng-cao)
- [Khắc phục sự cố](#-khắc-phục-sự-cố)

## 🎯 Tính năng

- ✅ **Phát hiện tự động** các viên bi 1-15 trong ảnh
- ✅ **Phát hiện tùy chọn** bi số 16 (cue ball - bi trắng)
- ✅ **Phân loại màu sắc** chính xác cho từng loại bi
- ✅ **Loại trừ vùng lỗ** để tránh nhận diện sai
- ✅ **Xử lý hàng loạt** nhiều ảnh cùng lúc
- ✅ **Xuất kết quả** dưới dạng ảnh có chú thích và file JSON
- ✅ **Giao diện dòng lệnh** linh hoạt và dễ sử dụng

## 🔧 Yêu cầu hệ thống

### Phần mềm cần thiết:
- **Python**: 3.7 hoặc cao hơn
- **Hệ điều hành**: Windows, macOS, hoặc Linux

### Thư viện Python:
- `opencv-python` (cv2)
- `numpy`
- `matplotlib` (chỉ import, không sử dụng trực tiếp)

## 🚀 Cài đặt môi trường

### Bước 1: Clone hoặc tải project
```bash
# Clone repository (nếu có)
git clone <repository-url>
cd detect-balls-opencv

# Hoặc tạo thư mục mới
mkdir detect-balls-opencv
cd detect-balls-opencv
```

### Bước 2: Tạo môi trường ảo (khuyến nghị)
```bash
# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
# Trên Windows:
venv\Scripts\activate

# Trên macOS/Linux:
source venv/bin/activate
```

### Bước 3: Cài đặt các thư viện cần thiết
```bash
# Cài đặt từ requirements (nếu có file requirements.txt)
pip install -r requirements.txt

# Hoặc cài đặt thủ công
pip install opencv-python numpy matplotlib
```

### Bước 4: Tạo cấu trúc thư mục
```bash
# Tạo các thư mục cần thiết
mkdir input
mkdir -p output/annotated
mkdir -p output/position
```

## 📁 Cấu trúc thư mục

```
detect-balls-opencv/
│
├── main.py                    # File chính chứa code xử lý
├── README.md                  # Tài liệu hướng dẫn (file này)
├── requirements.txt           # Danh sách thư viện cần thiết (tùy chọn)
│
├── input/                     # Thư mục chứa ảnh đầu vào
│   ├── 1.png
│   ├── 2.jpg
│   └── ...
│
├── output/                    # Thư mục chứa kết quả
│   ├── annotated/            # Ảnh đã được chú thích
│   │   ├── 1.png
│   │   ├── 2.jpg
│   │   └── ...
│   │
│   └── position/             # File JSON chứa tọa độ bi
│       ├── 1.json
│       ├── 2.json
│       └── ...
│
└── venv/                     # Môi trường ảo (nếu sử dụng)
```

## 💻 Cách sử dụng

### Sử dụng cơ bản

#### 1. Xử lý tất cả ảnh trong thư mục `input`
```bash
python main.py
```

#### 2. Xử lý một ảnh cụ thể
```bash
python main.py path/to/image.jpg
```

#### 3. Xử lý tất cả ảnh trong thư mục khác
```bash
python main.py path/to/folder/
```

### Sử dụng nâng cao

#### 4. Bao gồm phát hiện bi 16 (cue ball)
```bash
# Xử lý với bi 16
python main.py --cue-ball

# Xử lý ảnh cụ thể với bi 16
python main.py image.jpg --cue-ball

# Xử lý thư mục khác với bi 16
python main.py /path/to/folder --cue-ball
```

### Tùy chọn dòng lệnh

| Tham số | Mô tả | Ví dụ |
|---------|-------|-------|
| `input_path` | Đường dẫn ảnh hoặc thư mục | `python main.py input/1.jpg` |
| `--cue-ball` | Phát hiện bi 16 (cue ball) | `python main.py --cue-ball` |
| `-h, --help` | Hiển thị trợ giúp | `python main.py -h` |

## 📊 Kết quả đầu ra

### 1. Ảnh chú thích (`output/annotated/`)
- **Border đen** xung quanh mỗi viên bi được phát hiện
- **Nhãn số bi** hiển thị phía trên viên bi
- **Tọa độ** hiển thị bên phải viên bi
- **Thống kê tổng quan** ở góc trên bên trái

### 2. File JSON (`output/position/`)
```json
{
  "balls": [
    {
      "number": 1,
      "x": 150,
      "y": 200
    },
    {
      "number": 2,
      "x": 300,
      "y": 250
    }
  ]
}
```

### 3. Thông tin console
```
Đang xử lý ảnh 1/5: image1.jpg
----------------------------------------
Bi số 1:
  Tọa độ: (150, 200)
  Bán kính: 10
  Màu BGR: B=45.2, G=180.1, R=200.3
  Màu RGB: R=200.3, G=180.1, B=45.2
  Độ sáng trung bình: 165.2
  Số bi được xác định: 1
----------------------------------------
```

## 🔧 Cấu hình nâng cao

### Tùy chỉnh tham số phát hiện hình tròn
Trong file `main.py`, bạn có thể điều chỉnh các tham số sau:

```python
circles = cv2.HoughCircles(
    combined,
    cv2.HOUGH_GRADIENT,
    dp=1.0,           # Tỷ lệ độ phân giải
    minDist=15,       # Khoảng cách tối thiểu giữa các hình tròn
    param1=200,       # Ngưỡng Canny edge detector
    param2=15,        # Ngưỡng tích lũy
    minRadius=8,      # Bán kính tối thiểu
    maxRadius=13      # Bán kính tối đa
)
```

### Điều chỉnh vùng loại trừ (exclusion zones)
Vùng lỗ bi-a được định nghĩa trong hàm `is_in_exclusion_zone()`:

```python
exclusion_zones = [
    (22, 22, 38),     # (x, y, radius)
    (472, 10, 31),
    (925, 22, 41),
    (925, 490, 38),
    (472, 506, 33),
    (20, 491, 38)
]
```

## 🐛 Khắc phục sự cố

### Lỗi thường gặp:

#### 1. **ModuleNotFoundError: No module named 'cv2'**
```bash
# Giải pháp: Cài đặt OpenCV
pip install opencv-python
```

#### 2. **Folder 'input' không tồn tại**
```bash
# Giải pháp: Tạo thư mục input
mkdir input

# Hoặc chỉ định đường dẫn khác
python main.py /path/to/your/images
```

#### 3. **Không phát hiện được bi**
- Kiểm tra chất lượng ảnh (độ phân giải, độ sáng)
- Điều chỉnh tham số `HoughCircles`
- Đảm bảo bi không nằm trong vùng loại trừ

#### 4. **Phát hiện sai bi**
- Kiểm tra điều kiện ánh sáng khi chụp
- Điều chỉnh các tham số màu sắc trong `get_ball_number()`
- Xem xét việc cải thiện thuật toán phân loại màu

### Kiểm tra hệ thống:

```bash
# Kiểm tra phiên bản Python
python --version

# Kiểm tra các thư viện đã cài
pip list

# Kiểm tra OpenCV
python -c "import cv2; print(cv2.__version__)"
```

## 📞 Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra phần [Khắc phục sự cố](#-khắc-phục-sự-cố)
2. Đảm bảo đã cài đặt đúng môi trường theo hướng dẫn
3. Kiểm tra format và chất lượng ảnh đầu vào

---

**Chúc bạn sử dụng thành công! 🎱**