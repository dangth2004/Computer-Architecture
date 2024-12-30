import RPi.GPIO as GPIO  # Thư viện điều khiển GPIO trên Raspberry Pi
import time  # Thư viện xử lý thời gian

# Cấu hình chân GPIO cho màn hình LCD
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}
LCD_WIDTH = 16  # Chiều rộng LCD (16 ký tự)
LCD_CHR = True  # Chế độ ghi ký tự
LCD_CMD = False  # Chế độ ghi lệnh
LCD_LINE_1 = 0x80  # Địa chỉ dòng 1 của LCD
LCD_LINE_2 = 0xC0  # Địa chỉ dòng 2 của LCD
E_PULSE = 0.0005  # Thời gian xung kích hoạt E
E_DELAY = 0.0005  # Thời gian chờ giữa các lệnh

# Cấu hình chân GPIO khác
BT_1 = 21  # Chân GPIO cho nút nhấn
TRIG = 15  # Chân GPIO đầu ra cho cảm biến siêu âm
ECHO = 4  # Chân GPIO đầu vào cho cảm biến siêu âm
PWM_PIN = 24  # Chân GPIO điều khiển PWM
DIR_PIN = 25  # Chân GPIO điều khiển hướng quay động cơ

direction = 0  # Biến lưu hướng động cơ (0: quay thuận, 1: quay ngược)

# Thiết lập chế độ và cấu hình GPIO
GPIO.setmode(GPIO.BCM)  # Sử dụng chế độ BCM (Broadcom GPIO numbering)
GPIO.setwarnings(False)  # Tắt cảnh báo GPIO
GPIO.setup(BT_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Nút nhấn với điện trở kéo lên
GPIO.setup(TRIG, GPIO.OUT)  # Chân TRIG của cảm biến siêu âm là đầu ra
GPIO.setup(ECHO, GPIO.IN)  # Chân ECHO của cảm biến siêu âm là đầu vào
GPIO.setup(PWM_PIN, GPIO.OUT)  # Chân PWM của động cơ là đầu ra
GPIO.setup(DIR_PIN, GPIO.OUT)  # Chân điều khiển hướng quay động cơ là đầu ra
pwm = GPIO.PWM(PWM_PIN, 1000)  # Khởi tạo PWM với tần số 1000Hz
pwm.start(0)  # Bắt đầu PWM với duty cycle = 0
GPIO.output(TRIG, False)  # Đặt chân TRIG ở mức thấp ban đầu


# Hàm khởi tạo LCD
def lcd_init():
    for pin in LCD_PINS.values():
        GPIO.setup(pin, GPIO.OUT)  # Cấu hình các chân LCD là đầu ra
    # Gửi các lệnh khởi tạo cho LCD
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:
        lcd_byte(byte, LCD_CMD)


# Hàm xóa màn hình LCD
def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Lệnh xóa LCD


# Hàm gửi lệnh hoặc dữ liệu đến LCD
def lcd_byte(bits, mode):
    GPIO.output(LCD_PINS['RS'], mode)  # Chọn chế độ (lệnh hoặc dữ liệu)
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


# Hàm điều khiển động cơ
def motor_control(speed, dir):
    GPIO.output(DIR_PIN, dir)  # Thiết lập hướng quay động cơ
    if dir == 0:  # Nếu quay thuận
        speed = speed  # Tốc độ giữ nguyên
    else:  # Nếu quay ngược
        speed = 100 - speed  # Đảo ngược duty cycle
    pwm.ChangeDutyCycle(speed)  # Thay đổi tốc độ động cơ


# Hàm tính khoảng cách từ cảm biến siêu âm
def cal_distance():
    global distance
    print("dang do")  # Debug
    time.sleep(1)  # Chờ cảm biến ổn định
    GPIO.output(TRIG, True)  # Tạo xung kích hoạt TRIG
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    while GPIO.input(ECHO) == 0:  # Chờ nhận tín hiệu phản hồi
        pulse_start = time.time()
    while GPIO.input(ECHO) == 1:  # Tính thời gian tín hiệu phản hồi
        pulse_end = time.time()
    pulse_duration = pulse_end - pulse_start  # Thời gian tín hiệu
    distance = pulse_duration * 17150  # Tính khoảng cách (cm)
    distance = round(distance, 2)  # Làm tròn đến 2 chữ số thập phân
    return distance


# Hàm chính
def main():
    lcd_init()  # Khởi tạo LCD
    GPIO.output(LCD_PINS['BL'], True)  # Bật đèn nền LCD
    global pulse_end
    while True:
        cal_distance()  # Tính khoảng cách từ cảm biến
        if distance > 100:  # Nếu khoảng cách vượt giới hạn
            lcd_display_string("ERROR", 1)  # Hiển thị lỗi
        else:
            lcd_display_string(f"Distance: {distance}cm", 1)  # Hiển thị khoảng cách
            if distance >= 5:  # Nếu khoảng cách đủ lớn
                motor_control(50, 1)  # Điều khiển động cơ chạy
            elif distance < 5:  # Nếu khoảng cách nhỏ
                motor_control(0, 0)  # Dừng động cơ
            time.sleep(1)  # Chờ 1 giây


# Xử lý ngoại lệ khi kết thúc chương trình bằng Ctrl+C.
try:
    main()  # Gọi hàm chính.
except KeyboardInterrupt:  # Nếu nhận lệnh dừng từ bàn phím.
    pwm.stop()  # Dừng tín hiệu PWM.
    lcd_clear()  # Xóa màn hình LCD.
    GPIO.cleanup()  # Giải phóng các chân GPIO.
