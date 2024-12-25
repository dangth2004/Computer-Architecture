# Nhấn lần lượt nút 1 và 2 thì đèn sáng, bấm lần lượt 3 và 4 thì đèn nền LCD sáng, nhấn giữ đồng thời 1 và 3 thì 2 đèn tắt


import RPi.GPIO as GPIO  # Thư viện để điều khiển GPIO trên Raspberry Pi
import time  # Thư viện để xử lý thời gian

# Định nghĩa các chân GPIO kết nối với LCD và các nút bấm
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}  # Các chân LCD
BTS = {"BT_1": 21, "BT_2": 26, "BT_3": 20, "BT_4": 19}  # Các chân kết nối nút bấm
LED = 13  # Chân điều khiển đèn LED

# Các thông số cài đặt cho LCD
LCD_WIDTH = 16  # Độ rộng của màn hình LCD (16 ký tự)
LCD_CHR = True  # Chế độ ghi dữ liệu
LCD_CMD = False  # Chế độ ghi lệnh
LCD_LINE_1 = 0x80  # Địa chỉ dòng 1 của LCD
LCD_LINE_2 = 0xC0  # Địa chỉ dòng 2 của LCD
E_PULSE = 0.0005  # Thời gian xung tín hiệu Enable
E_DELAY = 0.0005  # Độ trễ tín hiệu Enable

GPIO.setmode(GPIO.BCM)  # Sử dụng cách đánh số chân GPIO theo kiểu BCM
GPIO.setwarnings(False)  # Tắt cảnh báo GPIO
GPIO.setup(LED, GPIO.OUT)  # Thiết lập chân LED làm ngõ ra


def pull_up_bts():
    """Cấu hình các chân nút bấm ở chế độ kéo lên."""
    for pin in BTS.values():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def lcd_init():
    """Khởi tạo LCD."""
    for pin in LCD_PINS.values():
        GPIO.setup(pin, GPIO.OUT)  # Thiết lập các chân LCD làm ngõ ra
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:  # Chuỗi lệnh khởi tạo LCD
        lcd_byte(byte, LCD_CMD)


def lcd_clear():
    """Xóa màn hình LCD."""
    lcd_byte(0x01, LCD_CMD)


def lcd_byte(bits, mode):
    """Gửi một byte đến LCD ở chế độ lệnh hoặc dữ liệu.

    Args:
        bits (int): Byte dữ liệu cần gửi.
        mode (bool): Chế độ (LCD_CMD hoặc LCD_CHR).
    """
    GPIO.output(LCD_PINS['RS'], mode)  # Thiết lập chế độ (lệnh hoặc dữ liệu)

    # Gửi 4 bit cao của byte
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    time.sleep(E_DELAY)
    GPIO.output(LCD_PINS['E'], True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)
    time.sleep(E_DELAY)

    # Gửi 4 bit thấp của byte
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << bit_num) != 0)
    time.sleep(E_DELAY)
    GPIO.output(LCD_PINS['E'], True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)
    time.sleep(E_DELAY)


def lcd_display_string(message, line):
    """Hiển thị một chuỗi trên LCD.

    Args:
        message (str): Chuỗi cần hiển thị.
        line (int): Dòng hiển thị (1 hoặc 2).
    """
    lcd_byte(LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)  # Chọn dòng hiển thị
    for char in message:
        lcd_byte(ord(char), LCD_CHR)  # Gửi từng ký tự đến LCD


def main():
    """Hàm chính để điều khiển LED và LCD dựa trên các nút bấm."""
    lcd_init()  # Khởi tạo LCD
    pull_up_bts()  # Kéo lên các chân nút bấm
    GPIO.setup(LCD_PINS['BL'], GPIO.OUT)  # Thiết lập chân đèn nền LCD làm ngõ ra
    GPIO.output(LCD_PINS['BL'], False)  # Ban đầu tắt đèn nền LCD

    # Biến trạng thái LED và đèn nền LCD
    LED_ON = False
    LCD_BL_ON = False

    # Biến nhớ trạng thái trước đó của các nút bấm
    prev_bt1 = prev_bt3 = False

    while True:
        # Kiểm tra nút bấm 1 và 2 để bật LED
        if GPIO.input(BTS["BT_1"]) == GPIO.LOW and not prev_bt1:  # Nếu nút 1 được nhấn
            prev_bt1 = True
        if GPIO.input(BTS["BT_2"]) == GPIO.LOW and prev_bt1:  # Nếu nút 2 được nhấn sau nút 1
            time.sleep(0.25)  # Chống rung nút
            GPIO.output(LED, GPIO.HIGH)  # Bật LED
            LED_ON = True
            prev_bt1 = False  # Đặt lại trạng thái nút 1

        # Kiểm tra nút bấm 3 và 4 để bật đèn nền LCD
        if GPIO.input(BTS["BT_3"]) == GPIO.LOW and not prev_bt3:  # Nếu nút 3 được nhấn
            prev_bt3 = True
        if GPIO.input(BTS["BT_4"]) == GPIO.LOW and prev_bt3:  # Nếu nút 4 được nhấn sau nút 3
            time.sleep(0.25)  # Chống rung nút
            GPIO.output(LCD_PINS['BL'], True)  # Bật đèn nền LCD
            LCD_BL_ON = True
            prev_bt3 = False  # Đặt lại trạng thái nút 3

        # Kiểm tra nhấn đồng thời nút bấm 1 và 3 để tắt cả LED và đèn nền LCD
        if GPIO.input(BTS["BT_1"]) == GPIO.LOW and GPIO.input(BTS["BT_3"]) == GPIO.LOW:
            GPIO.output(LED, GPIO.LOW)  # Tắt LED
            GPIO.output(LCD_PINS['BL'], False)  # Tắt đèn nền LCD
            LED_ON = False
            LCD_BL_ON = False
            time.sleep(0.25)  # Chống rung nút


try:
    main()  # Chạy chương trình chính
except KeyboardInterrupt:
    GPIO.cleanup()  # Dọn dẹp các cấu hình GPIO khi thoát chương trình
    lcd_clear()  # Xóa màn hình LCD
