import RPi.GPIO as GPIO  # Thư viện để giao tiếp với GPIO của Raspberry Pi
import time  # Thư viện để sử dụng hàm thời gian
import cv2  # Thư viện OpenCV để xử lý ảnh và video
import numpy as np  # Thư viện numpy để xử lý mảng

# Định nghĩa các chân GPIO sử dụng cho LCD và nút bấm
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}
BT1 = 21  # Chân nút bấm 1
BT2 = 26  # Chân nút bấm 2

# Các hằng số cho việc điều khiển LCD
LCD_WIDTH = 16  # Độ rộng LCD (số ký tự mỗi dòng)
LCD_CHR = True  # Chế độ truyền ký tự vào LCD
LCD_CMD = False  # Chế độ truyền lệnh vào LCD
LCD_LINE_1 = 0x80  # Địa chỉ của dòng 1 trên LCD
LCD_LINE_2 = 0xC0  # Địa chỉ của dòng 2 trên LCD
E_PULSE = 0.005  # Thời gian xung E
E_DELAY = 0.005  # Thời gian delay giữa các lệnh

# Thiết lập chế độ GPIO
GPIO.setmode(GPIO.BCM)  # Sử dụng chế độ đánh số chân BCM
GPIO.setwarnings(False)  # Tắt cảnh báo nếu chân đã được sử dụng
GPIO.setup(BT1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Nút BT1 là đầu vào với pull-up nội bộ
GPIO.setup(BT2, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Nút BT2 là đầu vào với pull-up nội bộ


# Hàm khởi tạo LCD
def lcd_init():
    for pin in LCD_PINS.values():
        GPIO.setup(pin, GPIO.OUT)  # Cài đặt tất cả chân LCD làm đầu ra
    lcd_byte(0x33, LCD_CMD)  # Gửi lệnh khởi tạo LCD
    lcd_byte(0x32, LCD_CMD)  # Gửi lệnh khởi tạo LCD
    lcd_byte(0x28, LCD_CMD)  # Cài đặt giao diện LCD (2 dòng, 5x8 điểm)
    lcd_byte(0x0C, LCD_CMD)  # Bật chế độ hiển thị LCD
    lcd_byte(0x06, LCD_CMD)  # Cài đặt chế độ tự động di chuyển con trỏ
    lcd_byte(0x01, LCD_CMD)  # Xóa màn hình LCD


# Hàm xóa màn hình LCD
def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Gửi lệnh xóa màn hình LCD


# Hàm gửi dữ liệu (lệnh hoặc ký tự) tới LCD
def lcd_byte(bits, mode):
    GPIO.output(LCD_PINS['RS'], mode)  # Chọn chế độ (lệnh hoặc ký tự)
    for bit_num in range(4):  # Gửi nửa byte đầu (4 bit)
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    time.sleep(E_DELAY)
    GPIO.output(LCD_PINS['E'], True)  # Tạo xung E
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)  # Kết thúc xung E
    time.sleep(E_DELAY)
    for bit_num in range(4):  # Gửi nửa byte sau (4 bit)
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << bit_num) != 0)
    time.sleep(E_DELAY)
    GPIO.output(LCD_PINS['E'], True)  # Tạo xung E
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)  # Kết thúc xung E
    time.sleep(E_DELAY)


# Hàm hiển thị chuỗi ký tự trên LCD
def lcd_display_string(message, line):
    lcd_byte(LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)  # Chọn dòng hiển thị
    for char in message:  # Hiển thị từng ký tự trong thông điệp
        lcd_byte(ord(char), LCD_CHR)


# Hàm đếm số pixel đỏ trong ảnh
def count_red_pixels(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)  # Chuyển đổi ảnh sang không gian màu HSV

    # Định nghĩa dải màu đỏ trong không gian HSV
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    # Tạo mặt nạ cho các pixel đỏ trong ảnh
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = mask1 + mask2  # Ghép hai mặt nạ để lấy tất cả các pixel đỏ

    # Đếm số pixel đỏ trong mặt nạ
    red_pixels = cv2.countNonZero(mask)
    return red_pixels  # Trả về số pixel đỏ


# Hàm chính điều khiển chương trình
def main():
    namewindow = "Camera User"  # Tên cửa sổ hiển thị ảnh
    capture = cv2.VideoCapture(0)  # Khởi tạo đối tượng VideoCapture để đọc từ camera
    if not capture.isOpened():
        print("Không thể mở camera.")  # Kiểm tra nếu không thể mở camera
        return

    print("Camera đã sẵn sàng.")
    lcd_init()  # Khởi tạo LCD
    lcd_display_string("Press BT1 to", 1)  # Hiển thị hướng dẫn trên LCD
    lcd_display_string("Capture Photo", 2)  # Hiển thị hướng dẫn trên LCD

    last_frame = None  # Biến lưu trữ ảnh đã chụp

    while True:
        ret, frame = capture.read()  # Đọc một khung hình từ camera
        if not ret:
            print("Không thể đọc từ camera.")  # Kiểm tra nếu không thể đọc khung hình
            break

        if GPIO.input(BT1) == GPIO.LOW:  # Nếu nút BT1 được nhấn
            last_frame = frame.copy()  # Lưu ảnh chụp
            cv2.imshow(namewindow, frame)  # Hiển thị ảnh trên cửa sổ
            cv2.imwrite("captured_image.jpg", frame)  # Lưu ảnh vào tệp
            lcd_clear()  # Xóa màn hình LCD
            lcd_display_string("Photo Captured", 1)  # Hiển thị thông báo trên LCD
            cv2.waitKey(3000)  # Chờ 3 giây
            cv2.destroyWindow(namewindow)  # Đóng cửa sổ hiển thị ảnh

        if GPIO.input(BT2) == GPIO.LOW:  # Nếu nút BT2 được nhấn
            if last_frame is not None:  # Nếu đã có ảnh được chụp
                red_pixel_count = count_red_pixels(last_frame)  # Đếm số pixel đỏ
                lcd_clear()  # Xóa màn hình LCD
                lcd_display_string("Red Pixels:", 1)  # Hiển thị thông báo trên LCD
                lcd_display_string(f"{red_pixel_count}", 2)  # Hiển thị số pixel đỏ trên LCD
                time.sleep(2)  # Chờ 2 giây
            else:
                lcd_clear()  # Xóa màn hình LCD
                lcd_display_string("No Image", 1)  # Hiển thị thông báo trên LCD
                lcd_display_string("Captured", 2)  # Hiển thị thông báo trên LCD
                time.sleep(2)  # Chờ 2 giây

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Nếu nhấn phím 'q', thoát chương trình
            break

    capture.release()  # Giải phóng tài nguyên camera


# Khối xử lý ngoại lệ khi thoát chương trình
try:
    main()  # Chạy chương trình chính
except KeyboardInterrupt:  # Bắt phím Ctrl+C để thoát
    lcd_clear()  # Xóa màn hình LCD trước khi thoát
    cv2.destroyAllWindows()  # Đóng tất cả cửa sổ OpenCV
    GPIO.cleanup()  # Dọn dẹp các thiết lập GPIO
