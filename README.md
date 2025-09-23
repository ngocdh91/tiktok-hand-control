# Hand Gesture Control for Android (TikTok)

Control the TikTok app on an Android device using hand gestures detected from your webcam.

## Dependencies

Install Python packages:

```bash
pip install -r requirements_android.txt
```

Contents of `requirements_android.txt`:

- opencv-python
- mediapipe
- uiautomator2

Other standard libraries used by the script: `threading`, `subprocess`, `platform`, `ctypes`, `math`, `time` (không cần cài thêm).

## Android setup

1) Bật Developer Options và USB debugging trên máy Android.
2) Kết nối thiết bị với máy tính qua USB (hoặc Wi‑Fi ADB).
3) Cài uiautomator2 vào thiết bị:

```bash
python -m uiautomator2 init
```

4) Kiểm tra kết nối:

```bash
python -c "import uiautomator2 as u2; print(u2.connect().info)"
```

Tùy chọn Wi‑Fi ADB:

```bash
adb tcpip 5555
adb connect <device_ip>:5555
```

## Run

```bash
python hand_detection_android.py
```

Sau khi chạy, cửa sổ camera sẽ hiển thị. Script tự kết nối thiết bị Android đầu tiên qua ADB (`u2.connect()`).

## Gestures (từ mã nguồn `hand_detection_android.py`)

- Right hand only: Bỏ qua tay trái với gestures thông thường.
- Smart cooldown: `action_cooldown = 0.5s` để tránh spam hành động.
- Anti‑sleep đa nền tảng được bật khi khởi động; tự phục hồi khi thoát.

### Mở TikTok (OK gesture)

- Ngón cái và ngón trỏ chạm nhau (tạo vòng) và 3 ngón còn lại duỗi.
- Khi detect, chạy `device.app_start("com.ss.android.ugc.trill")` (hiển thị overlay “TIKTOK OPENED!”).
- Có thể dùng nhiều lần sau khi đã đóng TikTok bằng gesture khác.

### Đóng TikTok (Cross arms X)

- Cả hai tay cùng xuất hiện, hai ngón trỏ duỗi, cổ tay chéo nhau và cao độ tương tự.
- Khi detect, chạy `device.app_stop("com.ss.android.ugc.trill")` (overlay “TIKTOK CLOSED!”). Không thoát script.

### Scroll video (Index + Middle extended)

- Kích hoạt khi ngón trỏ và ngón giữa duỗi, còn lại gập.
- Dựa vào dịch chuyển so với vị trí ban đầu và/hoặc vuốt ngang:
  - Lên từ vị trí ban đầu → scroll down.
  - Xuống từ vị trí ban đầu → scroll up.
  - Vuốt phải (delta_x > 0.02) → scroll down.
  - Vuốt trái (delta_x < -0.05) → scroll up.
- Thao tác trên Android bằng `device.swipe(...)` với khoảng cách ~60% chiều cao màn hình, `duration=0.05` (rất nhanh).

### Like video (Index và Thumb đan chéo – tùy chọn)

- Chỉ hoạt động khi TikTok đang mở và không trong cooldown.
- Điều kiện chính (được tinh chỉnh theo code):
  - 3 ngón (middle/ring/pinky) gập; `index_extended = True`.
  - `thumb_horizontal` ~ ngang; góc ngón cái `thumb_dir_angle` trong khoảng `[-60°, -10°]`.
  - Hai đầu ngón trỏ–cái gần nhau: `tips_dist < 0.15` (tọa độ chuẩn hóa 0–1).
  - Ngón trỏ nằm trên ngón cái: `index_tip.y < thumb_tip.y - 0.005`.
  - Độ dài wrist→index và wrist→thumb gần nhau: `|norm_i - norm_t| < 0.12`.
  - Góc giữa hướng wrist→index và wrist→thumb trong `15°..100°`.
- Khi thỏa, script double‑tap giữa màn hình bằng `device.click` 2 lần (thay cho bấm nút like).

## Tùy chỉnh nhanh

- Cooldown: `action_cooldown = 0.5`
- Ngưỡng chuyển động dọc: `gesture_threshold = 0.02`
- Thời gian giữ: `gesture_time_threshold = 0.2`
- Tốc độ vuốt: `duration=0.05` trong `device.swipe`
- Package TikTok: `com.ss.android.ugc.trill`

## Troubleshooting

- `adb devices` phải hiển thị thiết bị ở trạng thái `device`.
- Nếu không mở/đóng được app, kiểm tra đúng package name.
- Ánh sáng yếu làm giảm độ chính xác MediaPipe – tăng sáng và đưa tay gần camera.
- Nếu khung hình giật khi hiển thị chữ lớn, script đã tối ưu bằng overlay không chặn; đảm bảo CPU/GPU không quá tải.

## Notes

- Nhấn `q` để thoát.
- Khi thoát, script sẽ khôi phục chế độ sleep và gọi `app_stop` để đóng TikTok.
