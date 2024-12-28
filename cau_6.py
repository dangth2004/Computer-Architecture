# Mô phỏng điều khiển nhiệt độ, độ ẩm trong phòng khi có người.
# Ban đầu, hệ thống đếm số người trong phòng, nếu số người khác 0, hệ thống sẽ phát đo nhiệt độ và độ ẩm trong phòng,
# nếu các giá trị này nhỏ hơn ngưỡng đặt trước sẽ đóng rơ-le 1, ngược lại sẽ đóng rơ-le 2.
# Trong quá trình hoạt động hiển thị giá trị nhiệt độ, độ âm và số người có trong phòng lên màn hình LCD 16x2.


import RPi.GPIO as GPIO  # Thư viện để điều khiển GPIO trên Raspberry Pi
import time  # Thư viện để làm việc với thời gian

# Gán chức năng cho nút nhấn
# BT_1: Tăng số người
# BT_2: Giảm số người

# Khai báo chân GPIO cho các thiết bị
DHT11_PIN = 7  # Cảm biến nhiệt độ và độ ẩm DHT11
RELAY_1 = 16  # Rơ-le 1
RELAY_2 = 12  # Rơ-le 2
BUTTON_1 = 21  # Nút nhấn tăng số người
BUTTON_2 = 26  # Nút nhấn giảm số người
LCD_PINS = {  # Chân điều khiển LCD
    'RS': 23,  # Chân RS
    'E': 27,  # Chân E
    'D4': 18,  # Chân D4
    'D5': 17,  # Chân D5
    'D6': 14,  # Chân D6
    'D7': 3,  # Chân D7
    'BL': 2  # Chân điều khiển đèn nền (Backlight)
}
LCD_WIDTH = 16  # Số ký tự tối đa trên một dòng LCD
LCD_CHR = True  # Chế độ gửi ký tự
LCD_CMD = False  # Chế độ gửi lệnh
LCD_LINE_1 = 0x80  # Lệnh địa chỉ dòng 1
LCD_LINE_2 = 0xC0  # Lệnh địa chỉ dòng 2
E_PULSE = 0.005  # Độ dài xung cho chân Enable
E_DELAY = 0.005  # Độ trễ sau khi gửi lệnh

# Ngưỡng nhiệt độ và độ ẩm để điều khiển rơ-le
ROOM_TEMPERATURE_THRESHOLD = 10  # Ngưỡng nhiệt độ
ROOM_HUMIDITY_THRESHOLD = 10  # Ngưỡng độ ẩm

# Biến toàn cục để lưu số người trong phòng
people_count = 0

# Thiết lập chế độ GPIO
GPIO.setmode(GPIO.BCM)  # Chọn kiểu đánh số chân GPIO là BCM
GPIO.setwarnings(False)  # Tắt cảnh báo GPIO
GPIO.setup(DHT11_PIN, GPIO.IN)  # Chân DHT11 là đầu vào
GPIO.setup(RELAY_1, GPIO.OUT)  # Chân rơ-le 1 là đầu ra
GPIO.setup(RELAY_2, GPIO.OUT)  # Chân rơ-le 2 là đầu ra
GPIO.setup(BUTTON_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Nút nhấn tăng
GPIO.setup(BUTTON_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Nút nhấn giảm
for pin in LCD_PINS.values():
    GPIO.setup(pin, GPIO.OUT)  # Cấu hình các chân LCD là đầu ra


# Đọc dữ liệu từ cảm biến DHT11
def read_dht11():
    # Khởi tạo tín hiệu để lấy dữ liệu từ DHT11
    GPIO.setup(DHT11_PIN, GPIO.OUT)
    GPIO.output(DHT11_PIN, GPIO.LOW)  # Kéo chân xuống LOW để bắt đầu
    time.sleep(0.02)
    GPIO.output(DHT11_PIN, GPIO.HIGH)
    GPIO.setup(DHT11_PIN, GPIO.IN)  # Chuyển về chế độ đầu vào để đọc tín hiệu

    # Đọc tín hiệu từ cảm biến
    while GPIO.input(DHT11_PIN) == GPIO.LOW:
        pass
    while GPIO.input(DHT11_PIN) == GPIO.HIGH:
        pass

    # Lưu trữ 40 bit dữ liệu từ cảm biến
    data = []
    for i in range(40):
        while GPIO.input(DHT11_PIN) == GPIO.LOW:
            pass
        count = 0
        while GPIO.input(DHT11_PIN) == GPIO.HIGH:
            count += 1
            if count > 100:  # Giới hạn đếm để tránh vòng lặp vô hạn
                break
        if count > 8:  # Quy định 1 hoặc 0 dựa trên độ dài xung
            data.append(1)
        else:
            data.append(0)

    # Chuyển đổi dữ liệu
    humidity_bit = data[0:8]
    humidity_point_bit = data[8:16]
    temperature_bit = data[16:24]
    temperature_point_bit = data[24:32]
    check_bit = data[32:40]

    # Giải mã dữ liệu thành số thực
    humidity = sum([humidity_bit[i] * 2 ** (7 - i) for i in range(8)])
    temperature = sum([temperature_bit[i] * 2 ** (7 - i) for i in range(8)])
    checksum = sum([check_bit[i] * 2 ** (7 - i) for i in range(8)])

    # Kiểm tra tính hợp lệ của dữ liệu
    if checksum == humidity + temperature:
        return temperature, humidity
    else:
        return None, None  # Dữ liệu không hợp lệ


# Điều khiển LCD
def lcd_byte(bits, mode):
    # Gửi tín hiệu 4 bit cao
    GPIO.output(LCD_PINS['RS'], mode)  # Chọn chế độ gửi lệnh hoặc ký tự
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    GPIO.output(LCD_PINS['E'], True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)
    time.sleep(E_DELAY)

    # Gửi tín hiệu 4 bit thấp
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << bit_num) != 0)
    GPIO.output(LCD_PINS['E'], True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)
    time.sleep(E_DELAY)


# Hiển thị chuỗi trên LCD
def lcd_display_string(message, line):
    lcd_byte(LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)  # Chọn dòng hiển thị
    for char in message:
        lcd_byte(ord(char), LCD_CHR)  # Hiển thị từng ký tự


# Khởi tạo LCD
def lcd_init():
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:  # Gửi lệnh khởi tạo
        lcd_byte(byte, LCD_CMD)


# Xóa màn hình LCD
def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Lệnh xóa màn hình


# Điều khiển rơ-le dựa trên ngưỡng nhiệt độ và độ ẩm
def control_relay(temperature, humidity):
    if temperature < ROOM_TEMPERATURE_THRESHOLD or humidity < ROOM_HUMIDITY_THRESHOLD:
        GPIO.output(RELAY_1, GPIO.HIGH)  # Bật rơ-le 1
        GPIO.output(RELAY_2, GPIO.LOW)  # Tắt rơ-le 2
    else:
        GPIO.output(RELAY_1, GPIO.LOW)
        GPIO.output(RELAY_2, GPIO.HIGH)  # Bật rơ-le 2


# Xử lý nút bấm
def handle_buttons():
    global people_count
    if GPIO.input(BUTTON_1) == GPIO.LOW:  # Nếu nút BT_1 được nhấn
        people_count += 1
        time.sleep(0.3)  # Tránh bấm liên tục
    if GPIO.input(BUTTON_2) == GPIO.LOW and people_count > 0:  # Nếu nút BT_2 được nhấn
        people_count -= 1
        time.sleep(0.3)


# Chương trình chính
def main():
    global people_count
    lcd_init()
    GPIO.output(LCD_PINS['BL'], True)  # Bật đèn nền LCD
    while True:
        handle_buttons()  # Kiểm tra các nút
        if people_count > 0:  # Nếu có người trong phòng
            temperature, humidity = read_dht11()
            if temperature is not None and humidity is not None:  # Nếu đọc được dữ liệu cảm biến
                control_relay(temperature, humidity)
                lcd_clear()
                lcd_display_string(f"Ppl: {people_count}", 1)  # Hiển thị số người
                lcd_display_string(f"T: {temperature}C H: {humidity}%", 2)  # Hiển thị nhiệt độ, độ ẩm
            else:
                lcd_clear()
                lcd_display_string("Sensor Error", 2)  # Báo lỗi cảm biến
                lcd_display_string(f"Ppl: {people_count}", 1)
        else:
            GPIO.output(RELAY_1, GPIO.LOW)  # Tắt rơ-le
            GPIO.output(RELAY_2, GPIO.LOW)
            lcd_display_string("Room Empty", 1)  # Hiển thị phòng trống
            lcd_display_string("", 2)
        time.sleep(1)


# Xử lý khi dừng chương trình
try:
    main()
except KeyboardInterrupt:
    GPIO.cleanup()  # Reset trạng thái GPIO
    lcd_clear()  # Xóa LCD khi kết thúc
