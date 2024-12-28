# Điều khiển tốc độ động cơ một chiều theo kịch bản sau:
# Ban đầu động cơ đứng yên, nhấn nút bấm 1 và giữ, động cơ quay theo một chiều bất kỳ với tốc độ tăng dần 10% theo mỗi giây
# và khi đạt đến tốc độ 100% thì duy trì tốc độ này, khi thả nút bấm 1 thì động cơ sẽ quay theo quán tính và dừng hẳn.
# Nhấn nút bấm 3 và giữ, động cơ sẽ quay theo chiều ngược lại với tốc độ tăng dần 10% theo mỗi giây
# và khi đạt đến tốc độ 100% thì duy trì tốc độ này, khi thả nút bấm 3 thì động cơ sẽ quay theo quán tính và dừng hẳn.
# Trong quá trình động cơ đang quay, nếu nhấn nút bấm 2 động cơ ngay lập tức dừng lại hẳn.
# Hiển thị trạng thái của động cơ gồm: chiều quay, tốc độ lên màn hình LCD 16x2


import RPi.GPIO as GPIO
import time

# Các chân GPIO được định nghĩa cho màn hình LCD và các nút bấm
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}
BTS = {"BT_1": 21, "BT_2": 26, "BT_3": 20}  # Các nút bấm BT_1 (quay tới), BT_2 (dừng), BT_3 (quay lui)
PWM_PIN = 24  # Chân điều khiển PWM (tốc độ động cơ)
DIR_PIN = 25  # Chân điều khiển hướng động cơ
LCD_WIDTH = 16  # Chiều rộng màn hình LCD (số ký tự)
LCD_CHR = True  # Chế độ gửi ký tự
LCD_CMD = False  # Chế độ gửi lệnh
LCD_LINE_1 = 0x80  # Địa chỉ lệnh để đặt con trỏ về dòng 1
LCD_LINE_2 = 0xC0  # Địa chỉ lệnh để đặt con trỏ về dòng 2
E_PULSE = 0.0005  # Thời gian xung cho chân E
E_DELAY = 0.0005  # Thời gian chờ giữa các thao tác

# Cấu hình GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PWM_PIN, GPIO.OUT)  # Thiết lập PWM_PIN làm chân output
GPIO.setup(DIR_PIN, GPIO.OUT)  # Thiết lập DIR_PIN làm chân output

pwm = GPIO.PWM(PWM_PIN, 1000)  # Khởi tạo PWM với tần số 1kHz
pwm.start(0)  # Bắt đầu PWM với độ rộng xung là 0%
speed = 0  # Tốc độ ban đầu
count = 0  # Biến đếm số lần nhấn nút 1
count1 = 0  # Biến đếm số lần nhấn nút 3
direction = 0  # Hướng quay ban đầu (0: quay tới, 1: quay lui)
previous_line_1 = ""  # Lưu nội dung dòng 1 để tránh hiển thị lại
previous_line_2 = ""  # Lưu nội dung dòng 2 để tránh hiển thị lại


# Hàm khởi tạo LCD
def lcd_init():
    for pin in LCD_PINS.values():
        GPIO.setup(pin, GPIO.OUT)  # Cấu hình các chân của LCD làm output
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:  # Gửi các lệnh khởi tạo LCD
        lcd_byte(byte, LCD_CMD)


# Hàm xóa màn hình LCD
def lcd_clear():
    lcd_byte(0x01, LCD_CMD)


# Hàm gửi byte tới LCD (4-bit mode)
def lcd_byte(bits, mode):
    GPIO.output(LCD_PINS['RS'], mode)  # Chọn chế độ lệnh hoặc ký tự
    # Gửi 4 bit cao
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    time.sleep(E_DELAY)
    GPIO.output(LCD_PINS['E'], True)  # Kích hoạt xung E
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


# Hàm hiển thị chuỗi trên LCD
def lcd_display_string(message, line):
    global previous_line_1, previous_line_2
    if line == 1 and message != previous_line_1:
        previous_line_1 = message
        lcd_byte(LCD_LINE_1, LCD_CMD)  # Đặt con trỏ ở dòng 1
        for char in message.ljust(LCD_WIDTH):  # Lấp đầy bằng khoảng trắng nếu cần
            lcd_byte(ord(char), LCD_CHR)  # Gửi ký tự
    elif line == 2 and message != previous_line_2:
        previous_line_2 = message
        lcd_byte(LCD_LINE_2, LCD_CMD)  # Đặt con trỏ ở dòng 2
        for char in message.ljust(LCD_WIDTH):  # Lấp đầy bằng khoảng trắng nếu cần
            lcd_byte(ord(char), LCD_CHR)  # Gửi ký tự


# Hàm cấu hình các nút bấm với chế độ pull-up
def pull_up_bts():
    for pin in BTS.values():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# Hàm điều khiển động cơ (tốc độ và hướng)
def motor_control(speed, direction):
    GPIO.output(DIR_PIN, direction)  # Chọn hướng quay
    if direction == 0:
        speed = speed  # Quay tới
    else:
        speed = 100 - speed  # Quay lui (tốc độ giảm dần)
    pwm.ChangeDutyCycle(speed)  # Thay đổi độ rộng xung PWM để điều chỉnh tốc độ


# Hàm xử lý khi nút 1 được nhấn (quay tới)
def button_1_pressed():
    global speed, count
    count += 1
    speed += 10
    if speed >= 100:
        speed = 100  # Giới hạn tốc độ tối đa là 100%
    motor_control(speed, 0)  # Quay tới với tốc độ mới


# Hàm xử lý khi nút 3 được nhấn (quay lui)
def button_3_pressed():
    global speed, count1
    count1 += 1
    speed += 10
    if speed >= 100:
        speed = 100  # Giới hạn tốc độ tối đa là 100%
    motor_control(speed, 1)  # Quay lui với tốc độ mới


# Hàm main chính để chạy chương trình
def main():
    lcd_init()  # Khởi tạo LCD
    pull_up_bts()  # Cấu hình các nút bấm
    motor_control(0, 0)  # Mặc định quay tới với tốc độ 0
    global speed, direction
    while True:
        if GPIO.input(BTS["BT_1"]) == GPIO.LOW:  # Nhấn nút 1 (quay tới)
            speed = 0  # Đặt lại tốc độ
            direction = 0  # Hướng quay là quay tới
            while True:
                if GPIO.input(BTS["BT_1"]) == GPIO.LOW:
                    button_1_pressed()  # Tăng tốc quay tới
                    lcd_display_string(f"Huong: {direction}", 1)  # Hiển thị hướng (0)
                    lcd_display_string(f"Toc do: {speed}", 2)  # Hiển thị tốc độ
                    time.sleep(0.1)
                else:  # Dừng tăng tốc, giảm tốc từ từ
                    for new_speed in range(speed, -1, -10):
                        motor_control(new_speed, direction)
                        lcd_display_string(f"Huong: {direction}", 1)
                        lcd_display_string(f"Toc do: {new_speed}", 2)
                        time.sleep(0.25)
                        if GPIO.input(BTS["BT_2"]) == GPIO.LOW:  # Nhấn nút dừng
                            motor_control(0, direction)  # Dừng động cơ
                            lcd_clear()
                            lcd_display_string(f"Huong: {direction}", 1)
                            lcd_display_string(f"Toc do: 0", 2)
                            break
                    break

        if GPIO.input(BTS["BT_3"]) == GPIO.LOW:  # Nhấn nút 3 (quay lui)
            speed = 0  # Đặt lại tốc độ
            direction = 1  # Hướng quay là quay lui
            while True:
                if GPIO.input(BTS["BT_3"]) == GPIO.LOW:
                    button_3_pressed()  # Tăng tốc quay lui
                    lcd_display_string(f"Huong: {direction}", 1)  # Hiển thị hướng (1)
                    lcd_display_string(f"Toc do: {speed}", 2)  # Hiển thị tốc độ
                    time.sleep(0.1)
                elif GPIO.input(BTS["BT_2"]) == GPIO.LOW:  # Nhấn nút dừng
                    motor_control(0, direction)  # Dừng động cơ
                    lcd_display_string(f"Huong: {direction}", 1)
                    lcd_display_string(f"Toc do: {speed}", 2)
                    break
                else:  # Dừng tăng tốc, giảm tốc từ từ
                    for new_speed in range(speed, -1, -10):
                        motor_control(new_speed, direction)
                        lcd_display_string(f"Huong: {direction}", 1)
                        lcd_display_string(f"Toc do: {new_speed}", 2)
                        time.sleep(0.25)
                        if GPIO.input(BTS["BT_2"]) == GPIO.LOW:  # Nhấn nút dừng
                            motor_control(0, 0)  # Dừng động cơ
                            lcd_display_string(f"Huong: {direction}", 1)
                            lcd_display_string(f"Toc do: 0", 2)
                            break
                    break


# Chạy chương trình chính
try:
    main()
except KeyboardInterrupt:  # Nếu nhấn Ctrl+C, thoát khỏi chương trình
    pwm.stop()  # Dừng PWM
    lcd_clear()  # Xóa màn hình LCD
    GPIO.cleanup()  # Dọn dẹp GPIO
