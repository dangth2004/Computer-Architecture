import RPi.GPIO as GPIO  # Thư viện điều khiển GPIO trên Raspberry Pi
import time  # Thư viện xử lý thời gian

# Định nghĩa các chân GPIO cho LCD
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}

# Định nghĩa các chân GPIO cho các nút nhấn
BTS = {"BT_1": 21, "BT_2": 26, "BT_3": 20}

# Chân điều khiển động cơ
PWM_PIN = 24  # Chân điều khiển tốc độ động cơ (PWM)
DIR_PIN = 25  # Chân điều khiển hướng động cơ

# Các hằng số cấu hình LCD
LCD_WIDTH = 16  # Số ký tự tối đa trên mỗi dòng của LCD
LCD_CHR = True  # Chế độ ghi dữ liệu
LCD_CMD = False  # Chế độ ghi lệnh
LCD_LINE_1 = 0x80  # Địa chỉ bắt đầu của dòng 1
LCD_LINE_2 = 0xC0  # Địa chỉ bắt đầu của dòng 2
E_PULSE = 0.0005  # Độ dài xung điều khiển
E_DELAY = 0.0005  # Độ trễ giữa các thao tác

# Cài đặt chế độ hoạt động GPIO
GPIO.setmode(GPIO.BCM)  # Đánh số chân GPIO theo chuẩn BCM
GPIO.setwarnings(False)

# Cài đặt chân PWM và DIR cho động cơ
GPIO.setup(PWM_PIN, GPIO.OUT)
GPIO.setup(DIR_PIN, GPIO.OUT)

# Khởi tạo tín hiệu PWM
pwm = GPIO.PWM(PWM_PIN, 1000)  # Tạo PWM với tần số 1000 Hz
pwm.start(0)  # Bắt đầu với chu kỳ làm việc là 0%

# Khởi tạo các biến toàn cục
speed = 0  # Tốc độ hiện tại của động cơ
count_bt1 = 0  # Số lần nhấn nút 1
count_bt3 = 0  # Số lần nhấn nút 3
direction = 0  # Hướng quay (0: quay tới, 1: quay lui)
previous_line_1 = ""  # Lưu trạng thái dòng 1 của LCD
previous_line_2 = ""  # Lưu trạng thái dòng 2 của LCD


# Hàm khởi tạo LCD
def lcd_init():
    for pin in LCD_PINS.values():  # Thiết lập các chân LCD làm đầu ra
        GPIO.setup(pin, GPIO.OUT)
    # Gửi các lệnh khởi tạo LCD
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:
        lcd_byte(byte, LCD_CMD)


# Hàm xóa màn hình LCD
def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Gửi lệnh xóa LCD


# Hàm gửi dữ liệu hoặc lệnh tới LCD
def lcd_byte(bits, mode):
    GPIO.output(LCD_PINS['RS'], mode)  # Thiết lập chế độ ghi (lệnh/dữ liệu)

    # Gửi 4 bit cao
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    time.sleep(E_DELAY)
    GPIO.output(LCD_PINS['E'], True)
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


# Hàm hiển thị chuỗi ký tự lên LCD
def lcd_display_string(message, line):
    global previous_line_1, previous_line_2
    if line == 1 and message != previous_line_1:  # Nếu dòng 1 thay đổi
        previous_line_1 = message
        lcd_byte(LCD_LINE_1, LCD_CMD)  # Di chuyển con trỏ tới dòng 1
        for char in message.ljust(LCD_WIDTH):  # Đảm bảo chuỗi có độ dài đủ
            lcd_byte(ord(char), LCD_CHR)
    elif line == 2 and message != previous_line_2:  # Nếu dòng 2 thay đổi
        previous_line_2 = message
        lcd_byte(LCD_LINE_2, LCD_CMD)  # Di chuyển con trỏ tới dòng 2
        for char in message.ljust(LCD_WIDTH):
            lcd_byte(ord(char), LCD_CHR)


# Hàm cấu hình nút nhấn
def pull_up_bts():
    for pin in BTS.values():  # Đặt các chân nút nhấn là đầu vào với điện trở kéo lên
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# Hàm điều khiển động cơ
def motor_control(speed, direction):
    GPIO.output(DIR_PIN, direction)  # Thiết lập hướng động cơ
    pwm.ChangeDutyCycle(speed if direction == 0 else 100 - speed)  # Điều chỉnh tốc độ động cơ


# Hàm xử lý khi nút 1 được nhấn (quay tới)
def button_1_pressed():
    global speed
    speed += 10  # Tăng tốc độ thêm 10%
    speed = min(speed, 100)  # Giới hạn tốc độ tối đa là 100%
    motor_control(speed, 0)  # Điều khiển động cơ quay tới


# Hàm xử lý khi nút 3 được nhấn (quay lui)
def button_3_pressed():
    global speed
    speed += 10  # Tăng tốc độ thêm 10%
    speed = min(speed, 100)  # Giới hạn tốc độ tối đa là 100%
    motor_control(speed, 1)  # Điều khiển động cơ quay lui


# Hàm chính của chương trình
def main():
    lcd_init()  # Khởi tạo LCD
    pull_up_bts()  # Cấu hình nút nhấn
    motor_control(0, 0)  # Đặt động cơ về trạng thái ban đầu (dừng)
    global speed, direction
    while True:  # Vòng lặp chính
        # Xử lý khi nút 1 được nhấn
        if GPIO.input(BTS["BT_1"]) == GPIO.LOW:
            speed = 0
            direction = 0
            while True:
                if GPIO.input(BTS["BT_1"]) == GPIO.LOW:
                    button_1_pressed()
                    lcd_display_string(f"Huong: {direction}", 1)
                    lcd_display_string(f"Toc do: {speed}", 2)
                    time.sleep(0.1)
                else:
                    for new_speed in range(speed, -1, -10):
                        motor_control(new_speed, direction)
                        lcd_display_string(f"Huong: {direction}", 1)
                        lcd_display_string(f"Toc do: {new_speed}", 2)
                        time.sleep(0.25)
                        if GPIO.input(BTS["BT_2"]) == GPIO.LOW:
                            motor_control(0, direction)
                            lcd_clear()
                            lcd_display_string(f"Huong: {direction}", 1)
                            lcd_display_string(f"Toc do: 0", 2)
                            break
                    break

        # Xử lý khi nút 3 được nhấn
        if GPIO.input(BTS["BT_3"]) == GPIO.LOW:
            speed = 0
            direction = 1
            while True:
                if GPIO.input(BTS["BT_3"]) == GPIO.LOW:
                    button_3_pressed()
                    lcd_display_string(f"Huong: {direction}", 1)
                    lcd_display_string(f"Toc do: {speed}", 2)
                    time.sleep(0.1)
                elif GPIO.input(BTS["BT_2"]) == GPIO.LOW:
                    motor_control(0, direction)
                    lcd_display_string(f"Huong: {direction}", 1)
                    lcd_display_string(f"Toc do: {speed}", 2)
                    break
                else:
                    for new_speed in range(speed, -1, -10):
                        motor_control(new_speed, direction)
                        lcd_display_string(f"Huong: {direction}", 1)
                        lcd_display_string(f"Toc do: {new_speed}", 2)
                        time.sleep(0.25)
                        if GPIO.input(BTS["BT_2"]) == GPIO.LOW:
                            motor_control(0, 0)
                            lcd_display_string(f"Huong: {direction}", 1)
                            lcd_display_string(f"Toc do: 0", 2)
                            break
                    break


# Xử lý ngoại lệ khi kết thúc chương trình bằng Ctrl+C.
try:
    main()  # Gọi hàm chính.
except KeyboardInterrupt:  # Nếu nhận lệnh dừng từ bàn phím.
    pwm.stop()  # Dừng tín hiệu PWM.
    lcd_clear()  # Xóa màn hình LCD.
    GPIO.cleanup()  # Giải phóng các chân GPIO.
