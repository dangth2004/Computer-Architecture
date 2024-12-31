import RPi.GPIO as GPIO  # Thư viện để giao tiếp với GPIO của Raspberry Pi
import time  # Thư viện để sử dụng hàm thời gian

# Định nghĩa các chân GPIO sử dụng
CLK = 11  # Chân Clock của giao thức SPI
DIN = 10  # Chân Data Input của giao thức SPI
CS = 8  # Chân Chip Select để chọn thiết bị SPI
BUTTON = 21  # Chân nối nút bấm để điều khiển trạng thái hiển thị

# Bảng ký tự định nghĩa hình trái tim
character = {
    'heart': [
        0x00,  # ........
        0x66,  # .XX..XX. (hàng 2: hai nhóm pixel sáng)
        0xFF,  # XXXXXXXX (hàng 3: toàn bộ pixel sáng)
        0xFF,  # XXXXXXXX (hàng 4: toàn bộ pixel sáng)
        0x7E,  # .XXXXXX. (hàng 5: các pixel giữa sáng)
        0x3C,  # ..XXXX.. (hàng 6: 4 pixel ở giữa sáng)
        0x18,  # ...XX... (hàng 7: 2 pixel giữa sáng)
        0x00  # ........ (hàng 8: không sáng pixel nào)
    ]
}

# Cài đặt chế độ chân GPIO
GPIO.setmode(GPIO.BCM)  # Sử dụng đánh số chân GPIO theo kiểu BCM
GPIO.setwarnings(False)  # Tắt cảnh báo nếu chân đã được sử dụng
GPIO.setup(CLK, GPIO.OUT)  # Chân CLK là đầu ra
GPIO.setup(DIN, GPIO.OUT)  # Chân DIN là đầu ra
GPIO.setup(CS, GPIO.OUT)  # Chân CS là đầu ra
GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Chân BUTTON là đầu vào, sử dụng pull-up nội bộ


# Hàm gửi dữ liệu qua giao thức SPI
def spi_send_byte(register, data):
    GPIO.output(CS, GPIO.LOW)  # Kích hoạt thiết bị SPI bằng cách kéo CS xuống mức thấp
    # Gửi byte đầu tiên (thanh ghi)
    for bit in range(8):
        GPIO.output(CLK, GPIO.LOW)  # Đưa tín hiệu Clock xuống thấp
        GPIO.output(DIN, (register >> (7 - bit)) & 0x01)  # Gửi từng bit từ MSB đến LSB
        GPIO.output(CLK, GPIO.HIGH)  # Đưa tín hiệu Clock lên cao
    # Gửi byte thứ hai (dữ liệu)
    for bit in range(8):
        GPIO.output(CLK, GPIO.LOW)
        GPIO.output(DIN, (data >> (7 - bit)) & 0x01)
        GPIO.output(CLK, GPIO.HIGH)
    GPIO.output(CS, GPIO.HIGH)  # Ngừng kích hoạt thiết bị SPI bằng cách kéo CS lên mức cao


# Hàm khởi tạo MAX7219
def max7219_init():
    spi_send_byte(0x0F, 0x00)  # Tắt chế độ kiểm tra
    spi_send_byte(0x09, 0x00)  # Tắt chế độ giải mã
    spi_send_byte(0x0B, 0x07)  # Hiển thị cả 8 hàng
    spi_send_byte(0x0A, 0x0F)  # Cài đặt độ sáng tối đa
    spi_send_byte(0x0C, 0x01)  # Bật thiết bị hiển thị


# Hàm xóa màn hình (tắt toàn bộ LED)
def clear_display():
    for row in range(1, 9):  # Lặp qua từng hàng (1-8)
        spi_send_byte(row, 0x00)  # Gửi giá trị 0x00 để tắt LED


# Hàm hiển thị mẫu ký tự trên màn hình LED
def display_pattern(pattern):
    for row in range(8):  # Lặp qua từng hàng trong mẫu ký tự
        spi_send_byte(8 - row, pattern[row])  # Gửi dữ liệu hàng tương ứng đến MAX7219


# Hàm chính điều khiển chương trình
def main():
    max7219_init()  # Khởi tạo thiết bị hiển thị
    clear_display()  # Xóa màn hình trước khi bắt đầu

    heart_display = False  # Biến trạng thái hiển thị hình trái tim, mặc định là tắt

    while True:
        button_state = GPIO.input(BUTTON)  # Đọc trạng thái của nút bấm

        if button_state == GPIO.LOW:  # Nếu nút bấm được nhấn
            heart_display = not heart_display  # Đổi trạng thái hiển thị
            time.sleep(0.2)  # Chờ 200ms để tránh hiện tượng nhấn nút liên tiếp do nhiễu

        if heart_display:  # Nếu trạng thái là hiển thị hình trái tim
            display_pattern(character['heart'])  # Hiển thị hình trái tim
            time.sleep(1)  # Hiển thị trong 1 giây
            clear_display()  # Xóa màn hình
            time.sleep(1)  # Chờ 1 giây trước khi lặp
        else:
            clear_display()  # Xóa màn hình nếu trạng thái là tắt


# Khối xử lý ngoại lệ khi thoát chương trình
try:
    main()  # Chạy chương trình chính
except KeyboardInterrupt:  # Bắt phím Ctrl+C để thoát
    clear_display()  # Xóa màn hình trước khi thoát
    GPIO.cleanup()  # Dọn dẹp các thiết lập GPIO
