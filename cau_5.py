# Mô phỏng bộ điều khiển nhiệt độ, khi nhiệt độ tăng cao hơn nhiệt độ phòng thì bật rơ le 1 và rơ le 2,
# nhiệt độ bằng nhiệt độ phòng thì tắt rơ le 2, nhiệt độ nhỏ hơn nhiệt độ phòng thì tất cả hai rơ-le.
# Hiển thị giá trị nhiệt độ lên màn hình LCD.


import RPi.GPIO as GPIO
import time

# Khai báo chân GPIO kết nối DHT11, LCD, và rơ-le
DHT11_PIN = 7  # Chân DHT11 được kết nối
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}  # Chân LCD
RLS = {"RELAY_1": 16, "RELAY_2": 12, "LED": 13}  # Các chân điều khiển rơ-le và LED

# Các hằng số LCD
LCD_WIDTH = 16  # Độ rộng của LCD (16 cột)
LCD_CHR = True  # Chế độ gửi ký tự
LCD_CMD = False  # Chế độ gửi lệnh
LCD_LINE_1 = 0x80  # Địa chỉ dòng 1 trên LCD
LCD_LINE_2 = 0xC0  # Địa chỉ dòng 2 trên LCD
E_PULSE = 0.0005  # Thời gian xung kích hoạt E
E_DELAY = 0.0005  # Độ trễ sau khi gửi dữ liệu
ROOM_TEMPERATURE = 15  # Ngưỡng nhiệt độ phòng để điều khiển rơ-le

# Cấu hình GPIO
GPIO.setmode(GPIO.BCM)  # Sử dụng số GPIO BCM
GPIO.setwarnings(False)  # Tắt cảnh báo GPIO


def read_dht11():
    # Bắt đầu giao tiếp với DHT11 bằng cách gửi tín hiệu khởi động
    GPIO.setup(DHT11_PIN, GPIO.OUT)
    GPIO.output(DHT11_PIN, GPIO.LOW)
    time.sleep(0.02)  # Giữ mức thấp trong 20ms để kích hoạt DHT11
    GPIO.output(DHT11_PIN, GPIO.HIGH)
    GPIO.setup(DHT11_PIN, GPIO.IN)  # Chuyển chân sang chế độ đầu vào

    # Dò tìm tín hiệu đáp ứng từ DHT11
    while GPIO.input(DHT11_PIN) == GPIO.LOW:
        pass
    while GPIO.input(DHT11_PIN) == GPIO.HIGH:
        pass

    # Đọc dữ liệu từ DHT11 (40 bit: độ ẩm, nhiệt độ và checksum)
    data = []
    for i in range(40):
        while GPIO.input(DHT11_PIN) == GPIO.LOW:
            pass
        count = 0
        while GPIO.input(DHT11_PIN) == GPIO.HIGH:
            count += 1
            if count > 100:  # Giới hạn để tránh vòng lặp vô hạn
                break
        if count > 8:  # Dữ liệu 1 nếu xung dài
            data.append(1)
        else:  # Dữ liệu 0 nếu xung ngắn
            data.append(0)

    # Phân tích dữ liệu nhận được
    humidity_bit = data[0:8]  # 8 bit độ ẩm
    humidity_point_bit = data[8:16]  # 8 bit phần thập phân độ ẩm
    temperature_bit = data[16:24]  # 8 bit nhiệt độ
    temperature_point_bit = data[24:32]  # 8 bit phần thập phân nhiệt độ
    check_bit = data[32:40]  # 8 bit kiểm tra

    # Chuyển đổi các bit sang số nguyên
    humidity = 0
    humidity_point = 0
    temperature = 0
    temperature_point = 0
    checksum = 0
    for i in range(8):
        humidity += humidity_bit[i] * 2 ** (7 - i)
        humidity_point += humidity_point_bit[i] * 2 ** (7 - i)
        temperature += temperature_bit[i] * 2 ** (7 - i)
        temperature_point += temperature_point_bit[i] * 2 ** (7 - i)
        checksum += check_bit[i] * 2 ** (7 - i)

    # Kiểm tra dữ liệu hợp lệ
    check = humidity + humidity_point + temperature + temperature_point
    if checksum == check:
        return temperature + temperature_point, humidity + humidity_point
    else:
        return None, None  # Trả về None nếu dữ liệu không hợp lệ


def lcd_init():
    # Thiết lập các chân điều khiển LCD làm đầu ra
    for pin in LCD_PINS.values():
        GPIO.setup(pin, GPIO.OUT)
    # Gửi các lệnh khởi tạo LCD
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:
        lcd_byte(byte, LCD_CMD)


def lcd_clear():
    # Lệnh xóa màn hình
    lcd_byte(0x01, LCD_CMD)


def lcd_byte(bits, mode):
    # Gửi dữ liệu hoặc lệnh tới LCD
    GPIO.output(LCD_PINS['RS'], mode)
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    time.sleep(E_DELAY)
    GPIO.output(LCD_PINS['E'], True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)
    time.sleep(E_DELAY)
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << bit_num) != 0)
    time.sleep(E_DELAY)
    GPIO.output(LCD_PINS['E'], True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)
    time.sleep(E_DELAY)


def lcd_display_string(message, line):
    # Hiển thị chuỗi ký tự trên dòng LCD
    lcd_byte(LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)
    for char in message:
        lcd_byte(ord(char), LCD_CHR)  # Gửi từng ký tự tới LCD


def control_relay(temperature):
    # Thiết lập các chân rơ-le làm đầu ra
    for pin in RLS.values():
        GPIO.setup(pin, GPIO.OUT)
    # Điều khiển rơ-le dựa trên nhiệt độ
    if temperature > ROOM_TEMPERATURE:
        GPIO.output(RLS['RELAY_1'], GPIO.HIGH)
        GPIO.output(RLS['RELAY_2'], GPIO.HIGH)
    elif temperature == ROOM_TEMPERATURE:
        GPIO.output(RLS['RELAY_1'], GPIO.HIGH)
        GPIO.output(RLS['RELAY_2'], GPIO.HIGH)
    else:
        GPIO.output(RLS['RELAY_1'], GPIO.LOW)
        GPIO.output(RLS['RELAY_2'], GPIO.LOW)


def main():
    lcd_init()  # Khởi tạo LCD
    GPIO.output(LCD_PINS['BL'], True)  # Bật đèn nền LCD
    time.sleep(1)
    while True:
        temperature, humidity = read_dht11()  # Đọc dữ liệu từ DHT11
        print(temperature, humidity)
        if humidity is not None and temperature is not None:
            # Hiển thị nhiệt độ và độ ẩm lên LCD
            lcd_display_string('temp :{:.1f}*C'.format(temperature), 1)
            control_relay(temperature)  # Điều khiển rơ-le dựa trên nhiệt độ
            time.sleep(1)
        else:
            time.sleep(1)  # Chờ nếu không đọc được dữ liệu


try:
    main()
except KeyboardInterrupt:
    GPIO.cleanup()  # Giải phóng GPIO khi dừng chương trình
    lcd_clear()  # Xóa màn hình LCD
