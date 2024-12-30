import RPi.GPIO as GPIO  # Thư viện điều khiển GPIO trên Raspberry Pi
import time  # Thư viện xử lý thời gian

# Định nghĩa chân GPIO cho servo và nút nhấn
SERVO = 6  # Chân GPIO điều khiển servo
BT_1 = 21  # Chân GPIO cho nút nhấn

# Định nghĩa các chân GPIO cho màn hình LCD
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}
LCD_WIDTH = 16  # Chiều rộng của LCD (16 ký tự)
LCD_CHR = True  # Chế độ ghi ký tự
LCD_CMD = False  # Chế độ ghi lệnh
LCD_LINE_1 = 0x80  # Địa chỉ dòng 1
LCD_LINE_2 = 0xC0  # Địa chỉ dòng 2
E_PULSE = 0.0005  # Thời gian xung kích hoạt E
E_DELAY = 0.0005  # Thời gian chờ giữa các lệnh

# Cấu hình GPIO
GPIO.setmode(GPIO.BCM)  # Sử dụng kiểu đánh số GPIO theo BCM
GPIO.setwarnings(False)  # Tắt cảnh báo GPIO
GPIO.setup(SERVO, GPIO.OUT)  # Cấu hình chân servo là đầu ra
GPIO.setup(BT_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Cấu hình nút nhấn với điện trở kéo lên

# Khởi tạo PWM cho servo
pwm = GPIO.PWM(SERVO, 50)  # PWM với tần số 50Hz
pwm.start(0)  # Bắt đầu với duty cycle = 0

# Biến lưu góc hiện tại của servo
current_angle = 0  # Ban đầu góc của servo là 0 độ


# Hàm điều chỉnh góc quay của servo
def set_servo_angle(angle):
    duty = angle / 18  # Tính duty cycle tương ứng với góc quay
    pwm.ChangeDutyCycle(duty)  # Điều chỉnh PWM để quay servo
    time.sleep(0.5)  # Đợi servo quay đến góc mới
    pwm.ChangeDutyCycle(0)  # Dừng tín hiệu PWM để tránh rung động


# Hàm khởi tạo LCD
def lcd_init():
    for pin in LCD_PINS.values():
        GPIO.setup(pin, GPIO.OUT)  # Cấu hình các chân LCD là đầu ra
    # Gửi các lệnh khởi tạo cho LCD
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:
        lcd_byte(byte, LCD_CMD)


# Hàm xóa màn hình LCD
def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Gửi lệnh xóa màn hình LCD


# Hàm gửi dữ liệu hoặc lệnh đến LCD
def lcd_byte(bits, mode):
    GPIO.output(LCD_PINS['RS'], mode)  # Chọn chế độ (ký tự hoặc lệnh)
    # Gửi 4 bit cao trước
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    time.sleep(E_DELAY)
    GPIO.output(LCD_PINS['E'], True)  # Tạo xung kích hoạt E
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)
    time.sleep(E_DELAY)
    # Gửi 4 bit thấp
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << bit_num) != 0)
    time.sleep(E_DELAY)
    GPIO.output(LCD_PINS['E'], True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)
    time.sleep(E_DELAY)


# Hàm hiển thị chuỗi ký tự trên LCD
def lcd_display_string(message, line):
    lcd_byte(LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)  # Chọn dòng hiển thị
    for char in message:
        lcd_byte(ord(char), LCD_CHR)  # Gửi từng ký tự đến LCD


# Hàm chính
def main():
    global current_angle  # Biến toàn cục để lưu góc hiện tại
    lcd_init()  # Khởi tạo LCD
    GPIO.output(LCD_PINS['BL'], True)  # Bật đèn nền LCD
    while True:
        if GPIO.input(BT_1) == GPIO.LOW:  # Nếu nút nhấn được nhấn
            while GPIO.input(BT_1) == GPIO.LOW:  # Giữ cho đến khi nhả nút
                current_angle += 10  # Tăng góc quay thêm 10 độ
                if current_angle > 160:  # Nếu góc vượt quá 160 độ
                    current_angle = 10  # Quay lại góc 10 độ
                # Hiển thị góc quay hiện tại trên LCD
                lcd_display_string(f"goc quay: {current_angle} *", 1)
                set_servo_angle(current_angle)  # Điều chỉnh servo đến góc mới
                time.sleep(2)  # Thời gian chờ giữa các lần điều chỉnh
                lcd_clear()  # Xóa LCD sau mỗi lần hiển thị


# Xử lý ngoại lệ khi kết thúc chương trình bằng Ctrl+C.
try:
    main()  # Gọi hàm chính.
except KeyboardInterrupt:  # Nếu nhận lệnh dừng từ bàn phím.
    pwm.stop()  # Dừng tín hiệu PWM.
    lcd_clear()  # Xóa màn hình LCD.
    GPIO.cleanup()  # Giải phóng các chân GPIO.
