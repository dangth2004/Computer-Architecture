import RPi.GPIO as GPIO  # Thư viện để giao tiếp với GPIO của Raspberry Pi
import time  # Thư viện để sử dụng các hàm thời gian

# Định nghĩa các chân GPIO cho LCD và nút bấm
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}
BTS = {"BT_1": 21, "BT_2": 26, "BT_3": 20, "BT_4": 19}
LED = 13  # Định nghĩa chân GPIO điều khiển đèn LED
LCD_WIDTH = 16  # Chiều dài dòng hiển thị của LCD
LCD_CHR = True  # Chế độ ghi ký tự
LCD_CMD = False  # Chế độ ghi lệnh
LCD_LINE_1 = 0x80  # Địa chỉ dòng 1 của LCD
LCD_LINE_2 = 0xC0  # Địa chỉ dòng 2 của LCD
E_PULSE = 0.0005  # Độ dài xung E (enable) của LCD
E_DELAY = 0.0005  # Độ trễ giữa các lệnh

# Cấu hình GPIO
GPIO.setmode(GPIO.BCM)  # Sử dụng số hiệu GPIO BCM
GPIO.setwarnings(False)  # Tắt cảnh báo GPIO đã được sử dụng
GPIO.setup(LED, GPIO.OUT)  # Đặt chân điều khiển LED là đầu ra


# Hàm cấu hình nút bấm sử dụng pull-up
def pull_up_bts():
    for pin in BTS.values():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# Hàm khởi tạo LCD
def lcd_init():
    for pin in LCD_PINS.values():
        GPIO.setup(pin, GPIO.OUT)  # Cấu hình các chân LCD là đầu ra
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:  # Chuỗi lệnh khởi tạo LCD
        lcd_byte(byte, LCD_CMD)


# Hàm xóa nội dung LCD
def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Gửi lệnh xóa màn hình đến LCD


# Hàm gửi dữ liệu (lệnh hoặc ký tự) đến LCD
def lcd_byte(bits, mode):
    GPIO.output(LCD_PINS['RS'], mode)  # Chọn chế độ ghi lệnh hoặc ký tự
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


# Chương trình chính
def main():
    lcd_init()  # Khởi tạo LCD
    pull_up_bts()  # Cấu hình nút bấm
    GPIO.setup(LCD_PINS['BL'], GPIO.OUT)  # Cấu hình chân điều khiển đèn nền LCD
    GPIO.output(LCD_PINS['BL'], False)  # Tắt đèn nền ban đầu
    LED_ON = False  # Trạng thái LED
    LCD_BL_ON = False  # Trạng thái đèn nền LCD
    prev_bt1 = prev_bt3 = False  # Biến lưu trạng thái nút bấm trước đó

    while True:
        # Kiểm tra nút bấm 1 và 2 để bật LED
        if GPIO.input(BTS["BT_1"]) == GPIO.LOW and not prev_bt1:  # Nếu nút 1 được nhấn
            prev_bt1 = True
        if GPIO.input(BTS["BT_2"]) == GPIO.LOW and prev_bt1:  # Nếu nút 2 được nhấn sau nút 1
            time.sleep(0.25)  # Chống nhiễu
            GPIO.output(LED, GPIO.HIGH)  # Bật LED
            LED_ON = True
            prev_bt1 = False

        # Kiểm tra nút bấm 3 và 4 để bật đèn nền LCD
        if GPIO.input(BTS["BT_3"]) == GPIO.LOW and not prev_bt3:  # Nếu nút 3 được nhấn
            prev_bt3 = True
        if GPIO.input(BTS["BT_4"]) == GPIO.LOW and prev_bt3:  # Nếu nút 4 được nhấn sau nút 3
            time.sleep(0.25)  # Chống nhiễu
            GPIO.output(LCD_PINS['BL'], True)  # Bật đèn nền LCD
            LCD_BL_ON = True
            prev_bt3 = False

        # Kiểm tra nhấn đồng thời nút bấm 1 và 3 để tắt cả LED và đèn nền LCD
        if GPIO.input(BTS["BT_1"]) == GPIO.LOW and GPIO.input(BTS["BT_3"]) == GPIO.LOW:
            GPIO.output(LED, GPIO.LOW)  # Tắt LED
            GPIO.output(LCD_PINS['BL'], False)  # Tắt đèn nền LCD
            LED_ON = False
            LCD_BL_ON = False
            time.sleep(0.25)  # Chống nhiễu


# Xử lý ngoại lệ khi kết thúc chương trình
try:
    main()
except KeyboardInterrupt:  # Nhấn Ctrl+C để thoát chương trình
    GPIO.cleanup()  # Dọn dẹp GPIO
    lcd_clear()  # Xóa LCD
