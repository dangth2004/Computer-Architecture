import RPi.GPIO as GPIO  # Thư viện để giao tiếp với GPIO của Raspberry Pi
import time  # Thư viện để sử dụng các hàm thời gian

# Định nghĩa các chân GPIO sử dụng:
BT1 = 21  # Chân nút bấm
RL1 = 16  # Chân điều khiển rơ-le
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}  # Cấu hình chân LCD

# Các hằng số LCD
LCD_WIDTH = 16  # Chiều dài dòng LCD (16 ký tự)
LCD_CHR = True  # Chế độ gửi dữ liệu (character mode)
LCD_CMD = False  # Chế độ gửi lệnh (command mode)
LCD_LINE_1 = 0x80  # Địa chỉ dòng 1
LCD_LINE_2 = 0xC0  # Địa chỉ dòng 2
E_PULSE = 0.0005  # Độ dài xung Enable
E_DELAY = 0.0005  # Thời gian trễ

# Cấu hình GPIO:
GPIO.setmode(GPIO.BCM)  # Sử dụng chuẩn đánh số BCM
GPIO.setwarnings(False)  # Vô hiệu hóa cảnh báo GPIO
GPIO.setup(BT1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Cấu hình nút bấm là input với điện trở kéo lên
GPIO.setup(RL1, GPIO.OUT)  # Cấu hình rơ-le là output
GPIO.output(RL1, GPIO.LOW)  # Khởi tạo rơ-le ở trạng thái tắt


def lcd_init():
    # Cấu hình các chân LCD là output
    for pin in LCD_PINS.values():
        GPIO.setup(pin, GPIO.OUT)
    # Gửi chuỗi lệnh khởi tạo LCD
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:
        lcd_byte(byte, LCD_CMD)


def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Lệnh xóa màn hình


def lcd_byte(bits, mode):
    GPIO.output(LCD_PINS['RS'], mode)  # Đặt chế độ (lệnh hoặc dữ liệu)
    # Gửi 4 bit cao
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    time.sleep(E_DELAY)
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


def lcd_display_string(message, line):
    lcd_byte(LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)  # Chọn dòng
    for char in message:
        lcd_byte(ord(char), LCD_CHR)  # Gửi từng ký tự đến LCD


def show_password_on_lcd(password):
    masked_password = "".join(["*" for _ in password])  # Hiển thị mật khẩu dưới dạng dấu *
    lcd_clear()
    lcd_display_string(masked_password, 1)


def main():
    lcd_init()  # Khởi tạo LCD
    lcd_display_string("Enter password:", 1)  # Hiển thị yêu cầu nhập mật khẩu
    password = ""  # Chuỗi lưu mật khẩu

    while True:
        if GPIO.input(BT1) == GPIO.LOW:  # Kiểm tra trạng thái nút bấm
            time.sleep(0.5)  # Khử nhiễu (debounce)

            # Hiển thị các số từ 0-9 để lựa chọn
            for number in range(10):
                lcd_clear()
                lcd_display_string(f"Select: {number}", 1)
                time.sleep(1)  # Cho người dùng quan sát số hiện tại

                # Nếu nhả nút, ghi nhận số làm lựa chọn
                if GPIO.input(BT1) == GPIO.HIGH:
                    password += str(number)  # Thêm số vào mật khẩu
                    show_password_on_lcd(password)  # Hiển thị mật khẩu
                    time.sleep(1)  # Khử nhiễu sau khi nhả nút
                    break

        # Kiểm tra độ dài và tính hợp lệ của mật khẩu
        if len(password) >= 3:
            if password == "999":  # Nếu đúng mật khẩu
                lcd_clear()
                lcd_display_string("Success!", 1)  # Hiển thị thành công
                GPIO.output(RL1, GPIO.HIGH)  # Đóng rơ-le
                time.sleep(5)  # Giữ rơ-le 5 giây
                GPIO.output(RL1, GPIO.LOW)  # Tắt rơ-le
                password = ""  # Reset mật khẩu
                lcd_display_string("Enter password:", 1)
            else:
                lcd_clear()
                lcd_display_string("Wrong password", 1)  # Hiển thị sai mật khẩu
                time.sleep(2)
                password = ""  # Reset mật khẩu
                lcd_display_string("Enter password:", 1)


try:
    main()  # Chạy chương trình chính
except KeyboardInterrupt:  # Xử lý khi người dùng nhấn Ctrl+C
    lcd_clear()  # Xóa màn hình LCD
    GPIO.cleanup()  # Giải phóng tài nguyên GPIO
