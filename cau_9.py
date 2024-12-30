import RPi.GPIO as GPIO  # Thư viện điều khiển GPIO trên Raspberry Pi
import time  # Thư viện xử lý thời gian

# Định nghĩa các chân GPIO được sử dụng cho LCD
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}
LCD_WIDTH = 16  # Chiều rộng tối đa của màn hình LCD (16 ký tự)
LCD_CHR = True  # Chế độ ghi ký tự vào LCD
LCD_CMD = False  # Chế độ ghi lệnh vào LCD
LCD_LINE_1 = 0x80  # Địa chỉ dòng 1 trên LCD
LCD_LINE_2 = 0xC0  # Địa chỉ dòng 2 trên LCD
E_PULSE = 0.0005  # Thời gian tạo xung kích hoạt
E_DELAY = 0.0005  # Thời gian chờ giữa các lệnh

# Định nghĩa các chân cho nút nhấn và điều khiển động cơ
BT_1 = 21  # Nút nhấn tăng tốc
BT_2 = 26  # Nút nhấn dừng động cơ
PWM_PIN = 24  # Chân điều khiển PWM của động cơ
DIR_PIN = 25  # Chân điều khiển chiều quay động cơ

# Cấu hình GPIO
GPIO.setmode(GPIO.BCM)  # Sử dụng kiểu đánh số BCM cho chân GPIO
GPIO.setwarnings(False)  # Tắt cảnh báo về trạng thái GPIO
GPIO.setup(PWM_PIN, GPIO.OUT)  # Thiết lập chân PWM là đầu ra
GPIO.setup(DIR_PIN, GPIO.OUT)  # Thiết lập chân điều khiển chiều quay là đầu ra
GPIO.setup(BT_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Cấu hình nút nhấn BT_1 với điện trở kéo lên
GPIO.setup(BT_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Cấu hình nút nhấn BT_2 với điện trở kéo lên

# Tạo đối tượng PWM với tần số 1000Hz
pwm = GPIO.PWM(PWM_PIN, 1000)
pwm.start(0)  # Bắt đầu với duty cycle = 0 (không có tín hiệu)

# Biến toàn cục
count_human = 0  # Biến đếm số lần tác động
speed = 0  # Tốc độ hiện tại của động cơ
direction = 0  # Chiều quay động cơ (0 hoặc 1)


# Hàm khởi tạo LCD
def lcd_init():
    for pin in LCD_PINS.values():
        GPIO.setup(pin, GPIO.OUT)  # Thiết lập tất cả các chân LCD là đầu ra
    # Gửi các lệnh khởi tạo cần thiết cho màn hình LCD
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:
        lcd_byte(byte, LCD_CMD)


# Hàm xóa màn hình LCD
def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Gửi lệnh xóa màn hình


# Hàm gửi dữ liệu hoặc lệnh đến LCD
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
    lcd_byte(LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)  # Chọn dòng
    for char in message:
        lcd_byte(ord(char), LCD_CHR)  # Gửi từng ký tự đến LCD


# Hàm điều khiển động cơ
def motort_controller(speed, direction):
    GPIO.output(DIR_PIN, direction)  # Đặt chiều quay
    pwm.ChangeDutyCycle(speed)  # Thay đổi tốc độ


# Hàm xử lý khi nhấn nút BT_1 (tăng tốc)
def button_1_pressed():
    global speed
    if speed < 100:
        speed += 10
        motort_controller(speed, direction)
        lcd_clear()
        lcd_display_string("Tang toc", 1)
        lcd_display_string(f"Toc do:{speed}%", 2)
    else:
        lcd_display_string("Toc do toi da", 1)


# Hàm xử lý khi nhấn nút BT_2 (dừng động cơ)
def button_2_pressed():
    global speed
    speed = 0
    motort_controller(0, 0)
    lcd_clear()
    lcd_display_string("Dung quay", 1)
    lcd_display_string(f"Toc do:{speed}", 2)


# Hàm chính
def main():
    lcd_init()  # Khởi tạo LCD
    motort_controller(0, 0)  # Đặt tốc độ ban đầu là 0
    global speed
    last_time = time.time()  # Biến lưu thời gian lần nhấn nút gần nhất
    while True:
        if GPIO.input(BT_1) == GPIO.LOW:  # Kiểm tra nếu BT_1 được nhấn
            while GPIO.input(BT_1) == GPIO.LOW:
                current_time = time.time()
                if current_time - last_time >= 1:  # Nhấn giữ hơn 1 giây
                    button_1_pressed()
                    last_time = current_time
                time.sleep(0.05)
                if GPIO.input(BT_2) == GPIO.LOW:  # Nếu BT_2 được nhấn
                    button_2_pressed()
                    time.sleep(0.1)
        elif GPIO.input(BT_2) == GPIO.LOW:  # Nếu BT_2 được nhấn
            button_2_pressed()
            time.sleep(0.1)
        time.sleep(1)


# Xử lý ngoại lệ khi kết thúc chương trình bằng Ctrl+C.
try:
    main()  # Gọi hàm chính.
except KeyboardInterrupt:  # Nếu nhận lệnh dừng từ bàn phím.
    pwm.stop()  # Dừng tín hiệu PWM.
    lcd_clear()  # Xóa màn hình LCD.
    GPIO.cleanup()  # Giải phóng các chân GPIO.
