# Thực hiện chức năng của menu tương tác 4 cấp sử dụng màn hình LCD và các nút bấm
# Nút bấm 1 đóng vai trò phím quay lại, nút bấm 2 và 3 đóng vai trò di chuyển lên xuống, nút bấm 4 đóng vai trò chọn menu.
# Cấp 1 là menu chính, cấp 2 chứa các menu 1, menu 2, cấp 3 chứa các menu 1_1 và menu 2_2, cấp 4 chứa các chương trình bật LED. bật rơ-le 1 và bật rơ-le 2


import RPi.GPIO as GPIO  # Thư viện điều khiển GPIO của Raspberry Pi
import time  # Thư viện hỗ trợ xử lý thời gian

# Cấu hình các chân GPIO cho LCD, nút bấm và relay/LED
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}  # Các chân điều khiển LCD
BTS = {"BT_1": 21, "BT_2": 26, "BT_3": 20, "BT_4": 19}  # Các chân của nút bấm
RLS = {"RELAY_1": 16, "RELAY_2": 12, "LED": 13}  # Các chân điều khiển relay và LED


# Cấu hình các chân GPIO cho nút bấm (INPUT) và relay/LED (OUTPUT)
def pull_up_bts():
    for pin in BTS.values():  # Duyệt qua tất cả các chân nút bấm
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Thiết lập chế độ PULL-UP để tránh nhiễu
    for pin in RLS.values():  # Duyệt qua tất cả các chân relay/LED
        GPIO.setup(pin, GPIO.OUT)  # Thiết lập chế độ OUTPUT


# Cấu hình các thông số cơ bản cho LCD
LCD_WIDTH = 16  # Chiều rộng của LCD (16 cột)
LCD_CHR = True  # Chế độ ghi dữ liệu (Character)
LCD_CMD = False  # Chế độ ghi lệnh (Command)
LCD_LINE_1 = 0x80  # Địa chỉ bắt đầu dòng 1
LCD_LINE_2 = 0xC0  # Địa chỉ bắt đầu dòng 2
E_PULSE = 0.0005  # Thời gian xung Enable
E_DELAY = 0.0005  # Thời gian trễ giữa các xung

GPIO.setmode(GPIO.BCM)  # Sử dụng số GPIO theo chuẩn BCM
GPIO.setwarnings(False)  # Tắt cảnh báo GPIO


# Khởi tạo LCD
def lcd_init():
    for pin in LCD_PINS.values():  # Thiết lập các chân LCD làm OUTPUT
        GPIO.setup(pin, GPIO.OUT)
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:  # Các lệnh khởi tạo LCD
        lcd_byte(byte, LCD_CMD)  # Gửi từng lệnh đến LCD


# Hàm xóa màn hình LCD
def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Gửi lệnh xóa màn hình


# Gửi một byte dữ liệu hoặc lệnh tới LCD
def lcd_byte(bits, mode):
    GPIO.output(LCD_PINS['RS'], mode)  # Chọn chế độ dữ liệu/lệnh
    # Gửi 4 bit cao
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    time.sleep(E_DELAY)  # Thời gian chờ
    GPIO.output(LCD_PINS['E'], True)  # Tạo xung Enable
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


# Hiển thị chuỗi trên LCD
def lcd_display_string(message, line):
    lcd_byte(LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)  # Chọn dòng hiển thị
    for char in message:  # Gửi từng ký tự đến LCD
        lcd_byte(ord(char), LCD_CHR)


# Hiển thị menu trên LCD
def display_menu(menu_name):
    lcd_clear()  # Xóa màn hình trước
    lcd_display_string(menu_name, 1)  # Hiển thị tên menu ở dòng 1


# Biến toàn cục cho menu
current_menu = "Main"  # Menu hiện tại
current_level = 1  # Cấp độ menu hiện tại
current_pos = 1  # Vị trí menu hiện tại


# Xử lý khi nhấn nút 1 (Quay lại cấp trước)
def on_button1_pressed():
    global current_menu, current_level, current_pos
    if current_level > 1:  # Chỉ thực hiện nếu không phải cấp đầu tiên
        current_level -= 1
        current_pos = 1
        current_menu = f"Menu {current_level}.{current_pos}"
        display_menu(current_menu)


# Xử lý khi nhấn nút 2 (Di chuyển sang menu trước đó trong cùng cấp)
def on_button2_pressed():
    global current_menu, current_level, current_pos
    if current_pos > 1:
        current_pos -= 1
        current_menu = f"Menu {current_level}.{current_pos}"
        display_menu(current_menu)


# Xử lý khi nhấn nút 3 (Di chuyển tới menu tiếp theo trong cùng cấp)
def on_button3_pressed():
    global current_menu, current_level, current_pos
    current_pos += 1
    current_menu = f"Menu {current_level}.{current_pos}"
    display_menu(current_menu)


# Xử lý khi nhấn nút 4 (Chuyển cấp hoặc thực thi hành động)
def on_button4_pressed():
    global current_menu, current_level, current_pos
    if current_level < 4:  # Nếu chưa đến cấp cuối, chuyển lên cấp tiếp theo
        current_level += 1
        current_pos = 1
        current_menu = f"Menu {current_level}.{current_pos}"
        display_menu(current_menu)
    elif current_level == 4:  # Nếu ở cấp cuối, thực hiện các hành động
        if current_menu == "Menu 4.1":
            lcd_display_string("LED On", 2)  # Hiển thị trạng thái LED
            GPIO.output(RLS['LED'], True)  # Bật LED
        elif current_menu == "Menu 4.2":
            lcd_display_string("Relay 1 On", 2)
            GPIO.output(RLS['RELAY_1'], True)  # Bật relay 1
        elif current_menu == "Menu 4.3":
            lcd_display_string("Relay 2 On", 2)
            GPIO.output(RLS['RELAY_2'], True)  # Bật relay 2


# Hàm chính
def main():
    lcd_init()  # Khởi tạo LCD
    pull_up_bts()  # Thiết lập GPIO cho nút bấm và relay
    display_menu(current_menu)  # Hiển thị menu chính
    GPIO.output(LCD_PINS['BL'], True)  # Bật đèn nền LCD
    while True:  # Vòng lặp chính
        if GPIO.input(BTS['BT_1']) == GPIO.LOW:  # Nếu nhấn nút 1
            on_button1_pressed()
            time.sleep(0.25)  # Chống dội phím
        if GPIO.input(BTS['BT_2']) == GPIO.LOW:  # Nếu nhấn nút 2
            on_button2_pressed()
            time.sleep(0.25)
        if GPIO.input(BTS['BT_3']) == GPIO.LOW:  # Nếu nhấn nút 3
            on_button3_pressed()
            time.sleep(0.25)
        if GPIO.input(BTS['BT_4']) == GPIO.LOW:  # Nếu nhấn nút 4
            on_button4_pressed()
            time.sleep(0.25)


# Xử lý thoát chương trình
try:
    main()
except KeyboardInterrupt:  # Thoát khi nhấn Ctrl+C
    lcd_clear()  # Xóa LCD
    GPIO.cleanup()  # Dọn dẹp GPIO
