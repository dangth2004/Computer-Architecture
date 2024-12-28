import RPi.GPIO as GPIO  # Thư viện để giao tiếp với GPIO của Raspberry Pi
import time  # Thư viện để sử dụng các hàm thời gian

# Khai báo các chân GPIO của Raspberry Pi để kết nối với LCD, nút bấm (buttons) và relay/LED
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}  # Chân kết nối LCD
BTS = {"BT_1": 21, "BT_2": 26, "BT_3": 20, "BT_4": 19}  # Chân kết nối nút bấm
RLS = {"RELAY_1": 16, "RELAY_2": 12, "LED": 13}  # Chân điều khiển relay và LED


# Hàm thiết lập các nút bấm và relay/LED ở chế độ đầu vào và đầu ra
def pull_up_bts():
    for pin in BTS.values():  # Thiết lập các nút bấm ở chế độ đầu vào với điện trở kéo lên
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    for pin in RLS.values():  # Thiết lập relay và LED ở chế độ đầu ra
        GPIO.setup(pin, GPIO.OUT)


# Các hằng số cấu hình LCD
LCD_WIDTH = 16  # Chiều rộng của màn hình LCD (16 ký tự)
LCD_CHR = True  # Chế độ ghi dữ liệu (character)
LCD_CMD = False  # Chế độ ghi lệnh (command)
LCD_LINE_1 = 0x80  # Địa chỉ dòng 1 của LCD
LCD_LINE_2 = 0xC0  # Địa chỉ dòng 2 của LCD
E_PULSE = 0.0005  # Thời gian bật xung EN
E_DELAY = 0.0005  # Thời gian chờ giữa các lệnh

# Khởi tạo chế độ GPIO và tắt cảnh báo
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


# Hàm khởi tạo LCD
def lcd_init():
    for pin in LCD_PINS.values():  # Thiết lập tất cả các chân của LCD là đầu ra
        GPIO.setup(pin, GPIO.OUT)
    # Gửi các lệnh khởi tạo cho LCD
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:
        lcd_byte(byte, LCD_CMD)


# Hàm xóa màn hình LCD
def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Gửi lệnh xóa màn hình


# Hàm gửi dữ liệu hoặc lệnh đến LCD
def lcd_byte(bits, mode):
    GPIO.output(LCD_PINS['RS'], mode)  # Thiết lập chế độ RS (dữ liệu/lệnh)
    for bit_num in range(4):  # Gửi 4 bit cao
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    time.sleep(E_DELAY)
    GPIO.output(LCD_PINS['E'], True)  # Bật xung EN
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


# Hàm hiển thị một chuỗi trên LCD tại dòng chỉ định
def lcd_display_string(message, line):
    lcd_byte(LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)  # Gửi địa chỉ dòng
    for char in message:  # Gửi từng ký tự của chuỗi
        lcd_byte(ord(char), LCD_CHR)


# Hàm hiển thị menu trên LCD
def display_menu(menu_name):
    lcd_clear()  # Xóa màn hình
    lcd_display_string(menu_name, 1)  # Hiển thị tên menu trên dòng 1


# Các biến trạng thái của menu
current_menu = "Main"
current_level = 1
current_pos = 1


# Xử lý khi nút 1 được nhấn (quay về menu cha)
def on_button1_pressed():
    global current_menu, current_level, current_pos
    if current_level > 1:  # Nếu không phải menu chính
        current_level -= 1  # Quay về menu cha
        current_pos = 1
        current_menu = f"Menu {current_level}.{current_pos}"  # Cập nhật menu
        display_menu(current_menu)


# Xử lý khi nút 2 được nhấn (di chuyển sang mục trước đó)
def on_button2_pressed():
    global current_menu, current_level, current_pos
    if current_pos > 1:  # Nếu không phải mục đầu tiên
        current_pos -= 1  # Giảm vị trí
        current_menu = f"Menu {current_level}.{current_pos}"  # Cập nhật menu
        display_menu(current_menu)


# Xử lý khi nút 3 được nhấn (di chuyển sang mục tiếp theo)
def on_button3_pressed():
    global current_menu, current_level, current_pos
    current_pos += 1  # Tăng vị trí
    current_menu = f"Menu {current_level}.{current_pos}"  # Cập nhật menu
    display_menu(current_menu)


# Xử lý khi nút 4 được nhấn (vào menu con hoặc thực hiện chức năng)
def on_button4_pressed():
    global current_menu, current_level, current_pos
    if current_level < 4:  # Nếu chưa đến menu cấp cuối
        current_level += 1  # Chuyển đến menu con
        current_pos = 1
        current_menu = f"Menu {current_level}.{current_pos}"  # Cập nhật menu
        display_menu(current_menu)
    elif current_level == 4:  # Menu cấp cuối thực hiện chức năng
        if current_menu == "Menu 4.1":  # Bật LED
            lcd_display_string("LED On", 2)
            GPIO.output(RLS['LED'], True)
        elif current_menu == "Menu 4.2":  # Bật Relay 1
            lcd_display_string("Relay 1 On", 2)
            GPIO.output(RLS['RELAY_1'], True)
        elif current_menu == "Menu 4.3":  # Bật Relay 2
            lcd_display_string("Relay 2 On", 2)
            GPIO.output(RLS['RELAY_2'], True)


# Hàm chính
def main():
    lcd_init()  # Khởi tạo LCD
    pull_up_bts()  # Thiết lập nút bấm và relay/LED
    display_menu(current_menu)  # Hiển thị menu ban đầu
    GPIO.output(LCD_PINS['BL'], True)  # Bật đèn nền LCD
    while True:  # Vòng lặp chính
        if GPIO.input(BTS['BT_1']) == GPIO.LOW:  # Kiểm tra nút 1
            on_button1_pressed()
            time.sleep(0.25)
        if GPIO.input(BTS['BT_2']) == GPIO.LOW:  # Kiểm tra nút 2
            on_button2_pressed()
            time.sleep(0.25)
        if GPIO.input(BTS['BT_3']) == GPIO.LOW:  # Kiểm tra nút 3
            on_button3_pressed()
            time.sleep(0.25)
        if GPIO.input(BTS['BT_4']) == GPIO.LOW:  # Kiểm tra nút 4
            on_button4_pressed()
            time.sleep(0.25)


# Xử lý ngoại lệ (nhấn Ctrl+C để thoát)
try:
    main()
except KeyboardInterrupt:
    lcd_clear()  # Xóa màn hình LCD
    GPIO.cleanup()  # Dọn dẹp GPIO
