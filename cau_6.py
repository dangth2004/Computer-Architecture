import RPi.GPIO as GPIO  # Thư viện điều khiển GPIO trên Raspberry Pi.
import time  # Thư viện cung cấp các hàm liên quan đến thời gian.

# BT_1 tăng số người, BT_2 giảm số người
# Khai báo chân GPIO
DHT11_PIN = 7  # Chân GPIO kết nối cảm biến DHT11
RELAY_1 = 16  # Chân GPIO điều khiển rơ-le 1
RELAY_2 = 12  # Chân GPIO điều khiển rơ-le 2
BUTTON_1 = 21  # Chân GPIO kết nối nút bấm tăng số người
BUTTON_2 = 26  # Chân GPIO kết nối nút bấm giảm số người
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}  # Các chân GPIO của LCD
LCD_WIDTH = 16  # Chiều rộng của màn hình LCD (16 ký tự)
LCD_CHR = True  # Chế độ gửi dữ liệu tới LCD
LCD_CMD = False  # Chế độ gửi lệnh tới LCD
LCD_LINE_1 = 0x80  # Địa chỉ dòng 1 của LCD
LCD_LINE_2 = 0xC0  # Địa chỉ dòng 2 của LCD
E_PULSE = 0.005  # Thời gian giữ chân E ở mức cao
E_DELAY = 0.005  # Thời gian trễ giữa các lần gửi tín hiệu
ROOM_TEMPERATURE_THRESHOLD = 10  # Ngưỡng nhiệt độ phòng
ROOM_HUMIDITY_THRESHOLD = 10  # Ngưỡng độ ẩm phòng

# Biến toàn cục
people_count = 0  # Biến đếm số lượng người trong phòng

# Thiết lập GPIO
GPIO.setmode(GPIO.BCM)  # Sử dụng chế độ đánh số GPIO kiểu BCM
GPIO.setwarnings(False)  # Tắt cảnh báo GPIO
GPIO.setup(DHT11_PIN, GPIO.IN)  # Thiết lập chân DHT11 là đầu vào
GPIO.setup(RELAY_1, GPIO.OUT)  # Thiết lập chân relay 1 là đầu ra
GPIO.setup(RELAY_2, GPIO.OUT)  # Thiết lập chân relay 2 là đầu ra
GPIO.setup(BUTTON_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Thiết lập nút bấm tăng số người (kích hoạt với mức LOW)
GPIO.setup(BUTTON_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Thiết lập nút bấm giảm số người (kích hoạt với mức LOW)
for pin in LCD_PINS.values():
    GPIO.setup(pin, GPIO.OUT)  # Thiết lập các chân LCD là đầu ra


# Đọc dữ liệu từ cảm biến DHT11
def read_dht11():
    """
    Đọc dữ liệu từ cảm biến DHT11 và trả về nhiệt độ, độ ẩm.
    """
    GPIO.setup(DHT11_PIN, GPIO.OUT)
    GPIO.output(DHT11_PIN, GPIO.LOW)
    time.sleep(0.02)  # Gửi tín hiệu khởi tạo
    GPIO.output(DHT11_PIN, GPIO.HIGH)
    GPIO.setup(DHT11_PIN, GPIO.IN)

    # Chờ tín hiệu từ cảm biến
    while GPIO.input(DHT11_PIN) == GPIO.LOW:
        pass
    while GPIO.input(DHT11_PIN) == GPIO.HIGH:
        pass

    # Đọc 40 bit dữ liệu từ cảm biến
    data = []
    for i in range(40):
        while GPIO.input(DHT11_PIN) == GPIO.LOW:
            pass
        count = 0
        while GPIO.input(DHT11_PIN) == GPIO.HIGH:
            count += 1
            if count > 100:
                break
        if count > 8:
            data.append(1)
        else:
            data.append(0)

    # Tách dữ liệu thành các phần nhiệt độ, độ ẩm và checksum
    humidity_bit = data[0:8]
    humidity_point_bit = data[8:16]
    temperature_bit = data[16:24]
    temperature_point_bit = data[24:32]
    check_bit = data[32:40]

    humidity = 0
    humidity_point = 0
    temperature = 0
    temperature_point = 0
    checksum = 0

    # Chuyển đổi từ bit sang số thực
    for i in range(8):
        humidity += humidity_bit[i] * 2 ** (7 - i)
        humidity_point += humidity_point_bit[i] * 2 ** (7 - i)
        temperature += temperature_bit[i] * 2 ** (7 - i)
        temperature_point += temperature_point_bit[i] * 2 ** (7 - i)
        checksum += check_bit[i] * 2 ** (7 - i)
        check = humidity + humidity_point + temperature + temperature_point

    # Kiểm tra tính hợp lệ của dữ liệu
    if checksum == check:
        return temperature + temperature_point, humidity + humidity_point
    else:
        return None, None


# Điều khiển LCD
def lcd_byte(bits, mode):
    """
    Gửi dữ liệu hoặc lệnh tới màn hình LCD.
    """
    GPIO.output(LCD_PINS['RS'], mode)  # Chọn chế độ gửi (dữ liệu hoặc lệnh)

    # Gửi 4 bit cao
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    GPIO.output(LCD_PINS['E'], True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)
    time.sleep(E_DELAY)

    # Gửi 4 bit thấp
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << bit_num) != 0)
    GPIO.output(LCD_PINS['E'], True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)
    time.sleep(E_DELAY)


def lcd_display_string(message, line):
    """
    Hiển thị một chuỗi ký tự lên dòng LCD cụ thể.
    """
    lcd_byte(LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)
    for char in message:
        lcd_byte(ord(char), LCD_CHR)


def lcd_init():
    """
    Khởi tạo màn hình LCD.
    """
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:
        lcd_byte(byte, LCD_CMD)


def lcd_clear():
    """
    Xóa toàn bộ màn hình LCD.
    """
    lcd_byte(0x01, LCD_CMD)


# Điều khiển rơ-le
def control_relay(temperature, humidity):
    """
    Bật/tắt rơ-le dựa vào nhiệt độ và độ ẩm.
    """
    if temperature < ROOM_TEMPERATURE_THRESHOLD or humidity < ROOM_HUMIDITY_THRESHOLD:
        GPIO.output(RELAY_1, GPIO.HIGH)  # Bật rơ-le 1
        GPIO.output(RELAY_2, GPIO.LOW)  # Tắt rơ-le 2
    else:
        GPIO.output(RELAY_1, GPIO.LOW)  # Tắt rơ-le 1
        GPIO.output(RELAY_2, GPIO.HIGH)  # Bật rơ-le 2


# Xử lý nút bấm
def handle_buttons():
    """
    Xử lý logic nút bấm tăng/giảm số lượng người.
    """
    global people_count
    if GPIO.input(BUTTON_1) == GPIO.LOW:  # Nút bấm tăng được nhấn
        people_count += 1
        time.sleep(0.3)
    if GPIO.input(BUTTON_2) == GPIO.LOW and people_count > 0:  # Nút bấm giảm được nhấn
        people_count -= 1
        time.sleep(0.3)


# Chương trình chính
def main():
    """
    Vòng lặp chính của chương trình.
    """
    global people_count
    lcd_init()
    GPIO.output(LCD_PINS['BL'], True)  # Bật đèn nền LCD
    while True:
        handle_buttons()  # Kiểm tra nút bấm
        if people_count > 0:  # Nếu có người trong phòng
            temperature, humidity = read_dht11()
            if temperature is not None and humidity is not None:  # Dữ liệu cảm biến hợp lệ
                control_relay(temperature, humidity)
                lcd_clear()
                lcd_display_string(f"Ppl: {people_count}", 1)  # Hiển thị số người
                lcd_display_string(f"T: {temperature}C H: {humidity}%", 2)  # Hiển thị nhiệt độ và độ ẩm
            else:  # Lỗi cảm biến
                lcd_clear()
                lcd_display_string("Sensor Error", 2)
                lcd_display_string(f"Ppl: {people_count}", 1)
        else:  # Phòng trống
            GPIO.output(RELAY_1, GPIO.LOW)
            GPIO.output(RELAY_2, GPIO.LOW)
            lcd_display_string("Room Empty", 1)
            lcd_display_string("", 2)
        time.sleep(1)


try:
    main()  # Chạy chương trình chính
except KeyboardInterrupt:  # Xử lý khi người dùng nhấn Ctrl+C
    lcd_clear()  # Xóa màn hình LCD
    GPIO.cleanup()  # Giải phóng tài nguyên GPIO
