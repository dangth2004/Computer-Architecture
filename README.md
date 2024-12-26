# Computer-Architecture
Đáp án đề thi cuối kỳ I năm học 2024 - 2025 môn Kiến trúc máy tính (MAT3505) tại trường Đại học Khoa học Tự nhiên, Đại học Quốc gia Hà Nội (đáp án do sinh viên cung cấp)

## Mô tả hệ thống
**Máy tính nhúng Rasberry Pi 3 B+**
- *Bộ xử lý trung tâm:* CPU Broadcom BCM2837B0, Cortex-A53 (ARMv8) 64-bit SoC tốc độ 1.4GHz
- *Kết nối không dây:* Wi-Fi kép băng tần 2.4GHz và 5GHz, Bluetooth 4.2/BLE
- *RAM:* 1GB LPDDR2 SDRAM
- *Cổng kết nối:* 4 cổng USB 2.0, 1 cổng HDMI, cổng Ethernet Gigabit (tốc độ tối đa 300 Mbps), cổng âm thanh 3.5mm, cổng camera (CSI) và cổng hiển thị (DSI)
- *Hệ điều hành:* Raspbian
- *Giao tiếp GPIO:* 40 chân GPIO được hàn sẵn đầu cắm, cho phép kết nối các thiết bị ngoại vi và nhiều module khác nhau
  
**Thiết bị ngoại vi**
1) Động cơ RC-servo: sử dụng cho các tác vụ điều khiển góc quay chính xác
2) Màn hình LCD 16x2: sử dụng cho các tác vụ hiển thị thông tin
3) Cảm biến siêu âm: sử dụng để đo khoảng cách không tiếp xúc
4) Cảm biến hình ảnh: sử dụng cho các tác vụ thu thập hình ảnh
5) Cảm biến nhiệt độ - độ ẩm: sử dụng để đo nhiệt độ, độ ẩm trong không khí
6) Cảm biến hồng ngoại: để nhận tín hiệu điều khiển từ xa bằng hồng ngoại
7) Cảm biến ánh sáng: để đọc cường độ ánh sáng tương đối của môi trường
8) Cổng cấp nguồn (chuẩn micro USB): cấp nguồn cho bảng mạch
9) LED: dùng để hiển thị các mức logic trong mạch
10) LED ma trận 8x8: dùng để hiển thị đối tượng trên ma trận
11) Nút bấm: dùng để nhận tương tác từ người dùng
12) Relay điều khiển công suất: dùng để điều khiển các tải tiêu thụ công suất cao
13) Động cơ điện một chiều: dùng cho các tác vụ điều khiển chiều quay, tốc độ

**Các chân giao tiếp GPIO**
| Pin Name      | GPIO      | Pin No. | Left State | Right State | Pin No. | GPIO      | Pin Name      |
|:--------------|:----------|:-------:|:----------:|:-----------:|:-------:|:----------|:--------------|
|               | 3.3 Vdc   | 1       | ■          | ●           | 2       | 5.0 Vdc   |               |
| LCD BL        | GPIO 2    | 3       | ●          | ●           | 4       | 5.0 Vdc   |               |
| LCD DATA7     | GPIO 3    | 5       | ●          | ●           | 6       | GND       |               |
| S ECHO        | GPIO 4    | 7       | ●          | ●           | 8       | GPIO 14   | LCD DATA6     |
|               | GND       | 9       | ●          | ●           | 10      | GPIO 15   | S TRIGGER     |
| LCD DATA5     | GPIO 17   | 11      | ●          | ●           | 12      | GPIO 18   | LCD DATA4     |
| LCD ENABLE    | GPIO 27   | 13      | ●          | ●           | 14      | GND       |               |
| RECEIVER IR   | GPIO 22   | 15      | ●          | ●           | 16      | GPIO 23   | LCD RESET     |
|               | 3.3 Vdc   | 17      | ●          | ●           | 18      | GPIO 24   | MOTOR PWM     |
| MATRIX DIN    | GPIO 10   | 19      | ●          | ●           | 20      | GND       |               |
|               | GPIO 9    | 21      | ●          | ●           | 22      | GPIO 25   | MOTOR DIR     |
| MATRIX CLK    | GPIO 11   | 23      | ●          | ●           | 24      | GPIO 8    | MATRIX CS     |
|               | GND       | 25      | ●          | ●           | 26      | GPIO 7    | DHT11         |
|               | GPIO 0    | 27      | ●          | ●           | 28      | GPIO 1    |               |
| LIGHT SS      | GPIO 5    | 29      | ●          | ●           | 30      | GND       |               |
| SERVO         | GPIO 6    | 31      | ●          | ●           | 32      | GPIO 12   | RELAY 2       |
| LED           | GPIO 13   | 33      | ●          | ●           | 34      | GND       |               |
| BUTTON 4      | GPIO 19   | 35      | ●          | ●           | 36      | GPIO 16   | RELAY 1       |
| BUTTON 2      | GPIO 26   | 37      | ●          | ●           | 38      | GPIO 20   | BUTTON 3      |
|               | GND       | 39      | ●          | ●           | 40      | GPIO 21   | BUTTON 1      |


## Đề thi
