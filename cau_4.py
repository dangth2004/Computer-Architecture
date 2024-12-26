# Nhập mật khẩu từ các nút bấm hiển thị lên LCD 16x2 theo kịch bản sau.
# Khi nhấn nút bấm 1 trong khoảng thời gian 0.5s sẽ cho các lựa chọn các số từ 0 đến 9,
# khi nhả nút bấm 1 thì số cuối cùng hiện lên màn hình sẽ là số được lựa chọn.
# Sau khi lựa chọn, các số hiển thị trên màn hình sẽ chuyển sang ký tự x x x x để bảo mật.
# Kiểm tra điều kiện nếu mật khẩu nhận được là “999” thì sẽ đóng rơ-le 1 và hiện thông báo “thành công” trên màn hình LCD 16x2


import RPi.GPIO as GPIO  # Thư viện RPi.GPIO để giao tiếp với các chân GPIO
import time  # Thư viện time để xử lý thời gian

# Khai báo các chân GPIO
BT1 = 21  # Nút nhấn (Button) được kết nối với chân GPIO 21
RL1 = 16  # Rơ-le (Relay) được kết nối với chân GPIO 16
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}  # Cấu hình chân LCD
LCD_WIDTH = 16  # Độ rộng tối đa của màn hình LCD
LCD_CHR = True  # Gửi dữ liệu ký tự đến LCD
LCD_CMD = False  # Gửi lệnh đến LCD
LCD_LINE_1 = 0x80  # Địa chỉ dòng 1 trên LCD
LCD_LINE_2 = 0xC0  # Địa chỉ dòng 2 trên LCD
E_PULSE = 0.0005  # Thời gian xung của chân "Enable" (E) trên LCD
E_DELAY = 0.0005  # Thời gian trễ giữa các xung

# Cấu hình GPIO
GPIO.setmode(GPIO.BCM)  # Sử dụng chế độ đánh số chân GPIO theo kiểu BCM
GPIO.setwarnings(False)  # Tắt cảnh báo về GPIO
GPIO.setup(BT1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Cấu hình BT1 làm đầu vào với điện trở kéo lên
GPIO.setup(RL1, GPIO.OUT)  # Cấu hình RL1 làm đầu ra
GPIO.output(RL1, GPIO.LOW)  # Đặt trạng thái ban đầu của rơ-le là tắt


# Hàm khởi tạo LCD
def lcd_init():
    for pin in LCD_PINS.values():
        GPIO.setup(pin, GPIO.OUT)  # Cấu hình tất cả các chân LCD làm đầu ra
    # Gửi chuỗi lệnh khởi tạo LCD
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:
        lcd_byte(byte, LCD_CMD)


# Hàm xóa màn hình LCD
def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Lệnh xóa màn hình


# Hàm gửi byte đến LCD (dữ liệu hoặc lệnh)
def lcd_byte(bits, mode):
    GPIO.output(LCD_PINS['RS'], mode)  # Đặt chế độ (dữ liệu/ký tự hoặc lệnh)
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
    lcd_byte(LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)  # Chọn dòng 1 hoặc dòng 2
    for char in message:
        lcd_byte(ord(char), LCD_CHR)  # Gửi từng ký tự đến LCD


# Hàm hiển thị mật khẩu ẩn dưới dạng '*'
def show_password_on_lcd(password):
    masked_password = "".join(["*" for _ in password])  # Tạo chuỗi '*' tương ứng với độ dài mật khẩu
    lcd_clear()
    lcd_display_string(masked_password, 1)  # Hiển thị mật khẩu dạng ẩn


# Hàm chính của chương trình
def main():
    lcd_init()  # Khởi tạo LCD
    lcd_display_string("Enter password:", 1)  # Hiển thị yêu cầu nhập mật khẩu
    password = ""  # Chuỗi lưu mật khẩu

    while True:
        if GPIO.input(BT1) == GPIO.LOW:  # Kiểm tra nút nhấn BT1
            time.sleep(0.5)  # Thời gian debounce

            # Vòng lặp hiển thị các lựa chọn số
            for number in range(10):
                lcd_clear()
                lcd_display_string(f"Select: {number}", 1)  # Hiển thị số hiện tại
                time.sleep(1)  # Chờ 1 giây để người dùng xem số

                if GPIO.input(BT1) == GPIO.HIGH:  # Khi nhả nút
                    password += str(number)  # Thêm số vào mật khẩu
                    show_password_on_lcd(password)  # Hiển thị mật khẩu đã nhập
                    time.sleep(1)  # Debounce khi nhả nút
                    break

        if len(password) >= 3:  # Khi mật khẩu đủ 3 ký tự
            if password == "999":  # Kiểm tra mật khẩu chính xác
                lcd_clear()
                lcd_display_string("Success!", 1)  # Hiển thị thông báo thành công
                GPIO.output(RL1, GPIO.HIGH)  # Bật rơ-le
                time.sleep(5)  # Giữ rơ-le trong 5 giây
                GPIO.output(RL1, GPIO.LOW)  # Tắt rơ-le
                password = ""  # Reset mật khẩu
                lcd_display_string("Enter password:", 1)  # Yêu cầu nhập lại mật khẩu
            else:
                lcd_clear()
                lcd_display_string("Wrong password", 1)  # Hiển thị sai mật khẩu
                time.sleep(2)
                password = ""  # Reset mật khẩu
                lcd_display_string("Enter password:", 1)


# Chạy chương trình và xử lý ngắt
try:
    main()
except KeyboardInterrupt:  # Khi nhấn Ctrl+C
    lcd_clear()  # Xóa LCD
    GPIO.cleanup()  # Dọn dẹp GPIO
