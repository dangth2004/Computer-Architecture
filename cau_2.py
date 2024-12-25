# Bấm nút 1 lần 1 ký tự chữ Hello-World chạy từ phải qua trái, bấm lần 2 thì trái qua phải, lần 3 để xóa trắng màn hình


import RPi.GPIO as GPIO  # Thư viện để điều khiển các chân GPIO trên Raspberry Pi
import time  # Thư viện để sử dụng các hàm liên quan đến thời gian

# Biến toàn cục lưu trạng thái nút bấm
button_state = 0

# Cấu hình các chân GPIO kết nối với màn hình LCD
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}

# Chân GPIO cho nút bấm
BT_1 = 21

# Các thông số LCD
LCD_WIDTH = 16  # Chiều rộng tối đa của màn hình LCD (16 ký tự)
LCD_CHR = True  # Chế độ ghi ký tự
LCD_CMD = False  # Chế độ ghi lệnh
LCD_LINE_1 = 0x80  # Địa chỉ bắt đầu của dòng 1
LCD_LINE_2 = 0xC0  # Địa chỉ bắt đầu của dòng 2
E_PULSE = 0.0005  # Độ dài xung nhịp tín hiệu `Enable`
E_DELAY = 0.0005  # Thời gian trễ trước và sau tín hiệu `Enable`

# Cấu hình chế độ GPIO
GPIO.setmode(GPIO.BCM)  # Chọn kiểu đánh số GPIO theo chip BCM
GPIO.setwarnings(False)  # Tắt cảnh báo GPIO
GPIO.setup(BT_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Cấu hình nút bấm ở chế độ pull-up


# Hàm khởi tạo LCD
def lcd_init():
    for pin in LCD_PINS.values():  # Cấu hình tất cả các chân LCD làm đầu ra
        GPIO.setup(pin, GPIO.OUT)
    # Gửi các lệnh khởi tạo cho LCD
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:
        lcd_byte(byte, LCD_CMD)


# Hàm xóa màn hình LCD
def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Gửi lệnh xóa màn hình


# Hàm gửi dữ liệu hoặc lệnh đến LCD
def lcd_byte(bits, mode):
    GPIO.output(LCD_PINS['RS'], mode)  # Thiết lập chế độ (ghi lệnh hoặc ghi ký tự)

    # Gửi 4 bit cao
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    time.sleep(E_DELAY)
    GPIO.output(LCD_PINS['E'], True)  # Kích hoạt tín hiệu `Enable`
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)  # Ngắt tín hiệu `Enable`
    time.sleep(E_DELAY)

    # Gửi 4 bit thấp
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << bit_num) != 0)
    time.sleep(E_DELAY)
    GPIO.output(LCD_PINS['E'], True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)
    time.sleep(E_DELAY)


# Hàm hiển thị chuỗi ký tự lên một dòng của LCD
def lcd_display_string(message, line):
    lcd_byte(LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)  # Chọn dòng để hiển thị
    for char in message:  # Gửi từng ký tự trong chuỗi
        lcd_byte(ord(char), LCD_CHR)


# Hiển thị chuỗi theo hiệu ứng từ trái sang phải
def show_left2right(message):
    global button_state
    message_list = list(message)  # Chuyển chuỗi thành danh sách ký tự
    new_message = ""
    while len(message_list) > 0:
        ch = message_list.pop()  # Lấy ký tự cuối cùng
        length_loop = LCD_WIDTH - len(new_message) - 1
        for i in range(length_loop):
            lcd_clear()  # Xóa màn hình
            lcd_display_string(" " * i + ch + " " * (length_loop - i) + new_message, 1)  # Tạo hiệu ứng
            time.sleep(0.1)  # Chờ để tạo chuyển động
            if GPIO.input(BT_1) == GPIO.LOW:  # Kiểm tra nút bấm
                button_state += 1
                time.sleep(0.25)  # Tránh lặp nhanh
                return
        new_message = ch + new_message  # Thêm ký tự vào chuỗi mới


# Hiển thị chuỗi theo hiệu ứng từ phải sang trái
def show_right2left(message):
    global button_state
    message_list = list(message)[::-1]  # Đảo ngược danh sách ký tự
    new_message = ""
    while len(message_list) > 0:
        ch = message_list.pop()  # Lấy ký tự cuối cùng
        length_loop = LCD_WIDTH - len(new_message) - 1
        for i in range(length_loop, -1, -1):
            lcd_clear()
            lcd_display_string(new_message + " " * i + ch, 1)  # Tạo hiệu ứng
            time.sleep(0.1)
            if GPIO.input(BT_1) == GPIO.LOW:
                button_state += 1
                time.sleep(0.25)
                return
        new_message = new_message + ch


# Hàm chính điều khiển chương trình
def main():
    lcd_init()  # Khởi tạo LCD
    GPIO.output(LCD_PINS['BL'], True)  # Bật đèn nền LCD
    global button_state
    button_state = 0
    message = "Hello-World"  # Thông điệp hiển thị
    while True:
        if GPIO.input(BT_1) == GPIO.LOW:  # Kiểm tra nút bấm
            button_state += 1
            time.sleep(0.25)
        if button_state == 1:
            show_right2left(message)  # Hiển thị hiệu ứng từ phải sang trái
        elif button_state == 2:
            show_left2right(message)  # Hiển thị hiệu ứng từ trái sang phải
        elif button_state >= 3:
            lcd_clear()  # Xóa màn hình
            time.sleep(0.1)
            button_state = 0  # Đặt lại trạng thái nút bấm


# Bắt đầu chương trình
try:
    main()
except KeyboardInterrupt:  # Thoát khi nhấn Ctrl+C
    lcd_clear()
    GPIO.cleanup()  # Dọn dẹp GPIO
