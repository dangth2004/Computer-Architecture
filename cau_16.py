import RPi.GPIO as GPIO  # Thư viện để giao tiếp với GPIO của Raspberry Pi
import time  # Thư viện để sử dụng hàm thời gian
import cv2  # Thư viện OpenCV để xử lý ảnh và video
import numpy as np  # Thư viện numpy để xử lý mảng

# Định nghĩa các chân GPIO cho màn hình LCD và nút bấm
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}
BT1 = 21  # Nút bấm 1
BT2 = 26  # Nút bấm 2
RELAY1 = 16  # Relay 1
RELAY2 = 12  # Relay 2

# Cài đặt thông số cho LCD
LCD_WIDTH = 16
LCD_CHR = True
LCD_CMD = False
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0
E_PULSE = 0.005  # Thời gian xung cho E
E_DELAY = 0.005  # Thời gian trì hoãn

# Cấu hình GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(BT1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Cấu hình nút bấm 1
GPIO.setup(BT2, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Cấu hình nút bấm 2
GPIO.setup(RELAY1, GPIO.OUT)  # Cấu hình Relay 1
GPIO.setup(RELAY2, GPIO.OUT)  # Cấu hình Relay 2
GPIO.output(RELAY1, GPIO.LOW)  # Tắt Relay 1 ban đầu
GPIO.output(RELAY2, GPIO.LOW)  # Tắt Relay 2 ban đầu


# Hàm khởi tạo LCD
def lcd_init():
    for pin in LCD_PINS.values():
        GPIO.setup(pin, GPIO.OUT)  # Cấu hình các chân GPIO cho LCD
    lcd_byte(0x33, LCD_CMD)  # Đưa LCD về chế độ 4 bit
    lcd_byte(0x32, LCD_CMD)  # Đưa LCD về chế độ 4 bit
    lcd_byte(0x28, LCD_CMD)  # Cấu hình LCD 2 dòng, 5x8 điểm
    lcd_byte(0x0C, LCD_CMD)  # Bật hiển thị và tắt con trỏ
    lcd_byte(0x06, LCD_CMD)  # Cài đặt tự động dịch chuyển con trỏ sang phải
    lcd_byte(0x01, LCD_CMD)  # Xóa màn hình


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


# Hàm hiển thị chuỗi lên màn hình LCD
def lcd_display_string(message, line):
    lcd_byte(LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)  # Chọn dòng LCD
    for char in message:
        lcd_byte(ord(char), LCD_CHR)  # Gửi từng ký tự để hiển thị


# Hàm đếm số lượng điểm ảnh màu đỏ
def count_red_pixels(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)  # Chuyển ảnh sang không gian màu HSV
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    # Tạo mặt nạ (mask) cho màu đỏ
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = mask1 + mask2

    red_pixels = cv2.countNonZero(mask)  # Đếm số điểm ảnh màu đỏ
    return red_pixels


# Hàm đếm số lượng điểm ảnh màu xanh lá
def count_green_pixels(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)  # Chuyển ảnh sang không gian màu HSV
    mask = cv2.inRange(hsv, (35, 89, 107), (45, 241, 213))  # Tạo mặt nạ cho màu xanh lá
    green_pixels = cv2.countNonZero(mask)  # Đếm số điểm ảnh màu xanh
    return green_pixels


# Hàm chính
def main():
    namewindow = "Camera User"
    capture = cv2.VideoCapture(0)  # Khởi tạo camera
    if not capture.isOpened():  # Kiểm tra xem camera có mở được không
        print("Không thể mở camera.")
        return

    print("Camera đã sẵn sàng.")
    lcd_init()  # Khởi tạo LCD
    lcd_display_string("Press BT1 to", 1)  # Hiển thị thông báo trên LCD
    lcd_display_string("Capture Photo", 2)

    last_frame = None  # Biến lưu ảnh chụp cuối cùng

    while True:
        ret, frame = capture.read()  # Đọc frame từ camera
        if not ret:
            print("Không thể đọc từ camera.")
            break
        if GPIO.input(BT1) == GPIO.LOW:  # Nếu nút bấm BT1 được nhấn
            last_frame = frame.copy()  # Lưu lại ảnh hiện tại
            cv2.imshow(namewindow, frame)  # Hiển thị ảnh trên cửa sổ OpenCV
            cv2.imwrite("captured_image.jpg", frame)  # Lưu ảnh vào file
            lcd_clear()  # Xóa màn hình LCD
            lcd_display_string("Photo Captured", 1)  # Hiển thị thông báo trên LCD
            cv2.waitKey(3000)  # Chờ 3 giây
            cv2.destroyWindow(namewindow)  # Đóng cửa sổ ảnh

        if GPIO.input(BT2) == GPIO.LOW:  # Nếu nút bấm BT2 được nhấn
            if last_frame is not None:  # Kiểm tra nếu đã có ảnh được chụp
                red_pixel_count = count_red_pixels(last_frame)  # Đếm điểm ảnh đỏ
                green_pixel_count = count_green_pixels(last_frame)  # Đếm điểm ảnh xanh
                lcd_clear()  # Xóa màn hình LCD
                lcd_display_string("Red: " + str(red_pixel_count), 1)  # Hiển thị số điểm ảnh đỏ
                lcd_display_string("Green: " + str(green_pixel_count), 2)  # Hiển thị số điểm ảnh xanh
                time.sleep(2)

                # Điều khiển relay dựa trên số điểm ảnh đỏ và xanh
                if red_pixel_count > green_pixel_count:
                    GPIO.output(RELAY2, GPIO.LOW)  # Tắt Relay 2
                    GPIO.output(RELAY1, GPIO.HIGH)  # Bật Relay 1
                    lcd_clear()  # Xóa màn hình LCD
                    lcd_display_string("Relay 1 ON", 1)  # Hiển thị thông báo Relay 1 ON
                else:
                    GPIO.output(RELAY2, GPIO.HIGH)  # Bật Relay 2
                    GPIO.output(RELAY1, GPIO.LOW)  # Tắt Relay 1
                    lcd_clear()  # Xóa màn hình LCD
                    lcd_display_string("Relay 2 ON", 1)  # Hiển thị thông báo Relay 2 ON
                time.sleep(2)
                GPIO.output(RELAY1, GPIO.LOW)  # Tắt cả 2 Relay sau khi chờ 2 giây
                GPIO.output(RELAY2, GPIO.LOW)
            else:
                lcd_clear()  # Nếu không có ảnh, hiển thị thông báo
                lcd_display_string("No Image", 1)
                lcd_display_string("Captured", 2)
                time.sleep(2)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Dừng chương trình khi nhấn 'q'
            break

    capture.release()  # Giải phóng tài nguyên camera


# Bắt lỗi khi nhấn Ctrl+C
try:
    main()
except KeyboardInterrupt:
    lcd_clear()  # Xóa màn hình LCD khi bị ngắt
    cv2.destroyAllWindows()  # Đóng tất cả cửa sổ OpenCV
    GPIO.cleanup()  # Dọn dẹp các cấu hình GPIO
