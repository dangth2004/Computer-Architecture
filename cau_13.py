import RPi.GPIO as GPIO  # Thư viện điều khiển GPIO trên Raspberry Pi
import time  # Thư viện xử lý thời gian

# Định nghĩa các chân GPIO kết nối với LCD và các thiết bị khác
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}  # Chân điều khiển LCD
LCD_WIDTH = 16  # Số ký tự tối đa của LCD
LCD_CHR = True  # Chế độ gửi dữ liệu (character)
LCD_CMD = False  # Chế độ gửi lệnh (command)
LCD_LINE_1 = 0x80  # Địa chỉ dòng 1
LCD_LINE_2 = 0xC0  # Địa chỉ dòng 2
E_PULSE = 0.0005  # Thời gian xung Enable
E_DELAY = 0.0005  # Thời gian trễ khi gửi dữ liệu

# Định nghĩa các chân GPIO cho các nút bấm, relay, cảm biến và các thiết bị khác
BTS = {"BT1": 21, "BT2": 26, "BT3": 20, "BT4": 19}  # Các nút bấm
RELAY_1 = 16  # Chân điều khiển relay
TRIG = 15  # Chân trigger của cảm biến siêu âm
ECHO = 4  # Chân echo của cảm biến siêu âm
LED = 13  # Chân điều khiển đèn LED
PWM_PIN = 24  # Chân điều khiển động cơ PWM
DIR_PIN = 25  # Chân điều khiển hướng động cơ

# Thiết lập GPIO
GPIO.setmode(GPIO.BCM)  # Sử dụng sơ đồ chân BCM
GPIO.setwarnings(False)  # Tắt cảnh báo
GPIO.setup(RELAY_1, GPIO.OUT)  # Thiết lập chân relay là output
GPIO.setup(LED, GPIO.OUT)  # Thiết lập chân LED là output
GPIO.output(LED, False)  # Tắt đèn LED ban đầu
GPIO.setup(TRIG, GPIO.OUT)  # Thiết lập chân trigger là output
GPIO.setup(ECHO, GPIO.IN)  # Thiết lập chân echo là input
GPIO.output(TRIG, False)  # Tắt chân trigger ban đầu
GPIO.setup(PWM_PIN, GPIO.OUT)  # Thiết lập chân PWM là output
GPIO.setup(DIR_PIN, GPIO.OUT)  # Thiết lập chân điều khiển hướng là output
pwm = GPIO.PWM(PWM_PIN, 1000)  # Tạo PWM với tần số 1000Hz
pwm.start(0)  # Bắt đầu PWM với chu kỳ làm việc là 0%


# Hàm điều khiển động cơ
def motor_control(speed, dir):
    GPIO.output(DIR_PIN, dir)  # Thiết lập hướng động cơ
    if dir == 0:
        speed = speed  # Hướng 0 giữ nguyên tốc độ
    else:
        speed = 100 - speed  # Hướng 1 đảo ngược tốc độ
    pwm.ChangeDutyCycle(speed)  # Điều chỉnh chu kỳ làm việc của PWM


# Hàm đo khoảng cách sử dụng cảm biến siêu âm
def cal_distance():
    global distance  # Khai báo biến khoảng cách là biến toàn cục
    time.sleep(1)  # Tạm dừng 1 giây trước khi đo
    GPIO.output(TRIG, True)  # Gửi tín hiệu trigger
    time.sleep(0.00001)  # Giữ trigger trong 10µs
    GPIO.output(TRIG, False)  # Tắt tín hiệu trigger
    while GPIO.input(ECHO) == 0:  # Chờ tín hiệu echo bắt đầu
        pulse_start = time.time()
    while GPIO.input(ECHO) == 1:  # Chờ tín hiệu echo kết thúc
        pulse_end = time.time()
    pulse_duration = pulse_end - pulse_start  # Tính thời gian xung
    distance = pulse_duration * 17150  # Tính khoảng cách (cm)
    distance = round(distance, 1)  # Làm tròn đến 1 chữ số thập phân
    return distance


# Hàm khởi tạo LCD
def lcd_init():
    for pin in LCD_PINS.values():
        GPIO.setup(pin, GPIO.OUT)  # Thiết lập các chân LCD là output
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:  # Gửi các lệnh khởi tạo
        lcd_byte(byte, LCD_CMD)


# Hàm xóa LCD
def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Gửi lệnh xóa LCD


# Hàm gửi dữ liệu/command đến LCD
def lcd_byte(bits, mode):
    GPIO.output(LCD_PINS['RS'], mode)  # Thiết lập chế độ (data/command)
    for bit_num in range(4):  # Gửi 4 bit cao
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    time.sleep(E_DELAY)
    GPIO.output(LCD_PINS['E'], True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)
    time.sleep(E_DELAY)
    for bit_num in range(4):  # Gửi 4 bit thấp
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


# Hàm chính điều khiển hệ thống
def main():
    lcd_init()  # Khởi tạo LCD
    GPIO.output(LCD_PINS['BL'], True)  # Bật đèn nền LCD
    global pulse_end
    while True:
        cal_distance()  # Đo khoảng cách
        if distance > 100:  # Kiểm tra lỗi nếu khoảng cách vượt ngưỡng
            lcd_clear()
            lcd_display_string("ERROR", 1)
        else:
            lcd_display_string(f"Distance: {distance}cm", 1)
            if distance > 30:  # Điều kiện bình thường
                GPIO.output(LED, GPIO.LOW)
                motor_control(0, 0)
                GPIO.output(RELAY_1, GPIO.LOW)
                lcd_display_string("Binh thuong", 2)
            elif distance > 20:  # Cấp độ 1
                GPIO.output(LED, GPIO.HIGH)
                motor_control(0, 0)
                GPIO.output(RELAY_1, GPIO.LOW)
                lcd_display_string("Cap do 1", 2)
            elif distance >= 15:  # Cấp độ 2
                GPIO.output(LED, GPIO.HIGH)
                GPIO.output(RELAY_1, GPIO.HIGH)
                motor_control(0, 0)
                lcd_display_string("Cap do 2", 2)
            elif distance < 15:  # Cấp độ 3
                GPIO.output(LED, GPIO.HIGH)
                GPIO.output(RELAY_1, GPIO.HIGH)
                motor_control(100, 0)
                lcd_display_string("Cap do 3", 2)
        time.sleep(0.1)  # Dừng 0.1 giây trước khi thực hiện vòng lặp tiếp theo


# Xử lý ngoại lệ khi kết thúc chương trình bằng Ctrl+C.
try:
    main()  # Gọi hàm chính
except KeyboardInterrupt:  # Nếu nhận lệnh dừng từ bàn phím
    pwm.stop()  # Dừng tín hiệu PWM
    lcd_clear()  # Xóa màn hình LCD
    GPIO.cleanup()  # Giải phóng các chân GPIO
