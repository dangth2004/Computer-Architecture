import RPi.GPIO as GPIO  # Thư viện điều khiển GPIO trên Raspberry Pi
import time  # Thư viện xử lý thời gian

# Định nghĩa các chân GPIO cho servo và nút nhấn
SERVO = 6  # Chân GPIO điều khiển servo
buttons = {'BT_1': 21, 'BT_2': 26, 'BT_3': 20}  # Các chân GPIO cho 3 nút nhấn

# Định nghĩa các chân GPIO sử dụng cho màn hình LCD
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}
LCD_WIDTH = 16  # Chiều rộng tối đa của LCD (16 ký tự)
LCD_CHR = True  # Chế độ ghi ký tự
LCD_CMD = False  # Chế độ ghi lệnh
LCD_LINE_1 = 0x80  # Địa chỉ dòng 1
LCD_LINE_2 = 0xC0  # Địa chỉ dòng 2
E_PULSE = 0.0005  # Thời gian tạo xung kích hoạt
E_DELAY = 0.0005  # Thời gian chờ giữa các lệnh

# Cấu hình GPIO
GPIO.setmode(GPIO.BCM)  # Sử dụng kiểu đánh số BCM
GPIO.setwarnings(False)  # Tắt cảnh báo GPIO
GPIO.setup(SERVO, GPIO.OUT)  # Đặt chân servo là đầu ra
for button in buttons.values():
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Cấu hình các nút nhấn với điện trở kéo lên

# Khởi tạo PWM cho servo với tần số 50Hz
pwm = GPIO.PWM(SERVO, 50)
pwm.start(0)  # Bắt đầu PWM với duty cycle = 0 (không có tín hiệu)


# Hàm khởi tạo LCD
def lcd_init():
    for pin in LCD_PINS.values():
        GPIO.setup(pin, GPIO.OUT)  # Cấu hình tất cả các chân LCD là đầu ra
    # Gửi các lệnh khởi tạo cần thiết cho LCD
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:
        lcd_byte(byte, LCD_CMD)


# Hàm xóa màn hình LCD
def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Gửi lệnh xóa màn hình


# Hàm gửi lệnh hoặc dữ liệu đến LCD
def lcd_byte(bits, mode):
    GPIO.output(LCD_PINS['RS'], mode)  # Chọn chế độ (ký tự hoặc lệnh)
    # Gửi 4 bit cao
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    time.sleep(E_DELAY)
    GPIO.output(LCD_PINS['E'], True)  # Tạo xung kích hoạt
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


# Hàm hiển thị chuỗi ký tự trên một dòng của LCD
def lcd_display_string(message, line):
    lcd_byte(LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)  # Chọn dòng để hiển thị
    for char in message:
        lcd_byte(ord(char), LCD_CHR)  # Gửi từng ký tự đến LCD


# Hàm điều khiển servo để đặt góc quay
def set_servo_angle(angle):
    duty = angle / 18  # Tính duty cycle từ góc quay (theo công thức PWM)
    pwm.ChangeDutyCycle(duty)  # Đặt giá trị duty cycle cho servo
    time.sleep(0.5)  # Đợi servo xoay đến góc đã đặt
    pwm.ChangeDutyCycle(0)  # Dừng tín hiệu để tránh rung động


# Hàm chính
def main():
    lcd_init()  # Khởi tạo màn hình LCD
    # GPIO.output(LCD_PINS['BL'],True) # Bật đèn nền (nếu cần)
    while True:
        if GPIO.input(buttons['BT_1']) == GPIO.LOW:  # Nếu nút BT_1 được nhấn
            set_servo_angle(20)  # Đặt góc quay của servo là 20 độ
            lcd_display_string("Goc quay 20*", 1)  # Hiển thị thông báo lên LCD
        elif GPIO.input(buttons['BT_2']) == GPIO.LOW:  # Nếu nút BT_2 được nhấn
            set_servo_angle(60)  # Đặt góc quay của servo là 60 độ
            lcd_display_string("Goc quay 60*", 1)  # Hiển thị thông báo lên LCD
        elif GPIO.input(buttons['BT_3']) == GPIO.LOW:  # Nếu nút BT_3 được nhấn
            set_servo_angle(160)  # Đặt góc quay của servo là 160 độ
            lcd_display_string("Goc quay 160*", 1)  # Hiển thị thông báo lên LCD
        time.sleep(0.1)  # Đợi 0.1 giây để tránh lặp lại liên tục


# Xử lý ngoại lệ khi kết thúc chương trình bằng Ctrl+C.
try:
    main()  # Gọi hàm chính.
except KeyboardInterrupt:  # Nếu nhận lệnh dừng từ bàn phím.
    pwm.stop()  # Dừng tín hiệu PWM.
    lcd_clear()  # Xóa màn hình LCD.
    GPIO.cleanup()  # Giải phóng các chân GPIO.
