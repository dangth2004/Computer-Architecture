import RPi.GPIO as GPIO  # Thư viện để giao tiếp với GPIO của Raspberry Pi
import time  # Thư viện để sử dụng các hàm thời gian

button_state = 0  # Biến toàn cục lưu trạng thái nút nhấn
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}  # Định nghĩa chân GPIO cho LCD
BT_1 = 21  # Chân GPIO kết nối nút bấm
LCD_WIDTH = 16  # Số ký tự tối đa trên mỗi dòng của LCD
LCD_CHR = True  # Chế độ ghi ký tự
LCD_CMD = False  # Chế độ ghi lệnh
LCD_LINE_1 = 0x80  # Địa chỉ dòng 1 của LCD
LCD_LINE_2 = 0xC0  # Địa chỉ dòng 2 của LCD
E_PULSE = 0.0005  # Thời gian của xung E (enable)
E_DELAY = 0.0005  # Độ trễ giữa các lệnh

# Cấu hình GPIO
GPIO.setmode(GPIO.BCM)  # Sử dụng số hiệu GPIO BCM
GPIO.setwarnings(False)  # Tắt cảnh báo GPIO đã được sử dụng
GPIO.setup(BT_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Cấu hình chân nút bấm với điện trở pull-up


# Hàm khởi tạo LCD
def lcd_init():
    for pin in LCD_PINS.values():
        GPIO.setup(pin, GPIO.OUT)  # Đặt các chân của LCD là đầu ra
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:  # Chuỗi lệnh khởi tạo LCD
        lcd_byte(byte, LCD_CMD)


# Hàm xóa nội dung LCD
def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Gửi lệnh xóa màn hình đến LCD


# Hàm gửi dữ liệu (lệnh hoặc ký tự) đến LCD
def lcd_byte(bits, mode):
    GPIO.output(LCD_PINS['RS'], mode)  # Chọn chế độ ghi (lệnh hoặc ký tự)
    # Gửi 4 bit cao
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    time.sleep(E_DELAY)
    GPIO.output(LCD_PINS['E'], True)  # Tạo xung E để gửi dữ liệu
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


# Hiển thị chuỗi từ trái sang phải
def show_left2right(message):
    global button_state
    message_list = list(message)  # Tách chuỗi thành danh sách ký tự
    new_message = ""  # Chuỗi đã hiển thị
    while len(message_list) > 0:
        ch = message_list.pop()  # Lấy ký tự cuối
        length_loop = LCD_WIDTH - len(new_message) - 1  # Tính khoảng trống còn lại
        for i in range(length_loop):
            lcd_clear()
            lcd_display_string(" " * i + ch + " " * (length_loop - i) + new_message,
                               1)  # Hiển thị ký tự trượt từ trái sang phải
            time.sleep(0.1)
            if GPIO.input(BT_1) == GPIO.LOW:  # Kiểm tra nút nhấn để thay đổi trạng thái
                button_state = button_state + 1
                time.sleep(0.25)
                return
        new_message = ch + new_message  # Thêm ký tự vào chuỗi đã hiển thị


# Hiển thị chuỗi từ phải sang trái
def show_right2left(message):
    global button_state
    message_list = list(message)[::-1]  # Đảo ngược chuỗi thành danh sách ký tự
    new_message = ""  # Chuỗi đã hiển thị
    while len(message_list) > 0:
        ch = message_list.pop()  # Lấy ký tự cuối
        length_loop = LCD_WIDTH - len(new_message) - 1  # Tính khoảng trống còn lại
        for i in range(length_loop, -1, -1):  # Duyệt từ phải sang trái
            lcd_clear()
            lcd_display_string(new_message + " " * i + ch, 1)  # Hiển thị ký tự trượt từ phải sang trái
            time.sleep(0.1)
            if GPIO.input(BT_1) == GPIO.LOW:  # Kiểm tra nút nhấn để thay đổi trạng thái
                button_state = button_state + 1
                time.sleep(0.25)
                return
        new_message = new_message + ch  # Thêm ký tự vào chuỗi đã hiển thị


# Chương trình chính
def main():
    lcd_init()  # Khởi tạo LCD
    GPIO.output(LCD_PINS['BL'], True)  # Bật đèn nền LCD
    global button_state
    button_state = 0  # Khởi tạo trạng thái nút nhấn
    message = "Hello-World"  # Chuỗi cần hiển thị
    while True:
        if GPIO.input(BT_1) == GPIO.LOW:  # Kiểm tra nút nhấn
            button_state = button_state + 1  # Cập nhật trạng thái
            time.sleep(0.25)  # Chống nhiễu
        if button_state == 1:  # Trạng thái 1: Hiển thị từ phải sang trái
            show_right2left(message)
        elif button_state == 2:  # Trạng thái 2: Hiển thị từ trái sang phải
            show_left2right(message)
        elif button_state >= 3:  # Trạng thái 3: Xóa LCD và quay lại trạng thái ban đầu
            lcd_clear()
            time.sleep(0.1)
            button_state = 0


# Xử lý ngoại lệ khi kết thúc chương trình
try:
    main()
except KeyboardInterrupt:  # Nhấn Ctrl+C để thoát chương trình
    lcd_clear()  # Xóa màn hình LCD
    GPIO.cleanup()  # Dọn dẹp GPIO
