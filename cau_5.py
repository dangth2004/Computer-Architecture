import RPi.GPIO as GPIO  # Thư viện điều khiển GPIO trên Raspberry Pi.
import time  # Thư viện cung cấp các hàm liên quan đến thời gian.

# Cấu hình các chân GPIO cho cảm biến DHT11 và LCD.
DHT11_PIN = 7  # Chân GPIO kết nối với cảm biến DHT11.
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3, 'BL': 2}  # Các chân LCD.
RLS = {"RELAY_1": 16, "RELAY_2": 12, "LED": 13}  # Các chân điều khiển relay và LED.

# Các hằng số cho việc điều khiển LCD
LCD_WIDTH = 16  # Chiều rộng màn hình LCD (16 ký tự).
LCD_CHR = True  # Chế độ gửi dữ liệu.
LCD_CMD = False  # Chế độ gửi lệnh.
LCD_LINE_1 = 0x80  # Địa chỉ dòng 1 của LCD.
LCD_LINE_2 = 0xC0  # Địa chỉ dòng 2 của LCD.
E_PULSE = 0.0005  # Thời gian xung cho chân Enable.
E_DELAY = 0.0005  # Thời gian trễ giữa các lệnh.

ROOM_TEMPERATURE = 15  # Nhiệt độ chuẩn để so sánh.

# Cài đặt chế độ làm việc cho GPIO.
GPIO.setmode(GPIO.BCM)  # Sử dụng sơ đồ chân BCM.
GPIO.setwarnings(False)  # Tắt cảnh báo GPIO.


# Hàm đọc dữ liệu từ cảm biến DHT11.
def read_dht11():
    GPIO.setup(DHT11_PIN, GPIO.OUT)  # Thiết lập chân DHT11 là đầu ra.
    GPIO.output(DHT11_PIN, GPIO.LOW)  # Gửi tín hiệu khởi tạo đến DHT11.
    time.sleep(0.02)  # Chờ 20ms.
    GPIO.output(DHT11_PIN, GPIO.HIGH)  # Dừng tín hiệu khởi tạo.
    GPIO.setup(DHT11_PIN, GPIO.IN)  # Chuyển chân thành đầu vào để đọc dữ liệu.

    # Đọc tín hiệu từ DHT11 (gồm 40 bit dữ liệu).
    while GPIO.input(DHT11_PIN) == GPIO.LOW:
        pass
    while GPIO.input(DHT11_PIN) == GPIO.HIGH:
        pass

    data = []
    for i in range(40):  # Đọc từng bit dữ liệu.
        while GPIO.input(DHT11_PIN) == GPIO.LOW:
            pass
        count = 0
        while GPIO.input(DHT11_PIN) == GPIO.HIGH:
            count += 1
            if count > 100:
                break
        data.append(1 if count > 8 else 0)  # Phân biệt bit 0 và 1.

    # Tách dữ liệu thành các thành phần (độ ẩm, nhiệt độ, checksum).
    humidity_bit = data[0:8]
    humidity_point_bit = data[8:16]
    temperature_bit = data[16:24]
    temperature_point_bit = data[24:32]
    check_bit = data[32:40]

    # Chuyển dữ liệu bit sang số.
    humidity = sum([humidity_bit[i] * 2 ** (7 - i) for i in range(8)])
    temperature = sum([temperature_bit[i] * 2 ** (7 - i) for i in range(8)])
    checksum = sum([check_bit[i] * 2 ** (7 - i) for i in range(8)])

    # Kiểm tra tính hợp lệ của dữ liệu dựa trên checksum.
    if checksum == humidity + temperature:
        return temperature, humidity
    else:
        return None, None


# Hàm khởi tạo màn hình LCD.
def lcd_init():
    for pin in LCD_PINS.values():
        GPIO.setup(pin, GPIO.OUT)  # Thiết lập chân LCD là đầu ra.
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:  # Gửi các lệnh khởi tạo.
        lcd_byte(byte, LCD_CMD)


# Hàm xóa màn hình LCD.
def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Gửi lệnh xóa màn hình.


# Hàm gửi dữ liệu hoặc lệnh đến LCD.
def lcd_byte(bits, mode):
    GPIO.output(LCD_PINS['RS'], mode)  # Thiết lập chế độ gửi (lệnh/dữ liệu).
    for bit_num in range(4):  # Gửi 4 bit cao.
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    GPIO.output(LCD_PINS['E'], True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)
    for bit_num in range(4):  # Gửi 4 bit thấp.
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << bit_num) != 0)
    GPIO.output(LCD_PINS['E'], True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)


# Hàm hiển thị chuỗi ký tự trên màn hình LCD.
def lcd_display_string(message, line):
    lcd_byte(LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)  # Chọn dòng hiển thị.
    for char in message:
        lcd_byte(ord(char), LCD_CHR)  # Gửi từng ký tự.


# Hàm điều khiển relay dựa trên nhiệt độ.
def control_relay(temperature):
    for pin in RLS.values():
        GPIO.setup(pin, GPIO.OUT)  # Thiết lập chân relay là đầu ra.
    if temperature > ROOM_TEMPERATURE:
        GPIO.output(RLS['RELAY_1'], GPIO.HIGH)  # Bật cả hai relay.
        GPIO.output(RLS['RELAY_2'], GPIO.HIGH)
    elif temperature == ROOM_TEMPERATURE:
        GPIO.output(RLS['RELAY_1'], GPIO.HIGH)  # Bật relay 1, tắt relay 2.
        GPIO.output(RLS['RELAY_2'], GPIO.LOW)
    else:
        GPIO.output(RLS['RELAY_1'], GPIO.LOW)  # Tắt cả hai relay.
        GPIO.output(RLS['RELAY_2'], GPIO.LOW)


# Hàm chính điều khiển chương trình.
def main():
    lcd_init()  # Khởi tạo LCD.
    GPIO.output(LCD_PINS['BL'], True)  # Bật đèn nền LCD.
    while True:
        temperature, humidity = read_dht11()  # Đọc dữ liệu từ cảm biến.
        print(temperature, humidity)  # In ra màn hình console.
        if humidity is not None and temperature is not None:  # Nếu dữ liệu hợp lệ.
            lcd_display_string('temp :{:.1f}*C'.format(temperature), 1)  # Hiển thị nhiệt độ.
            control_relay(temperature)  # Điều khiển relay dựa trên nhiệt độ.
        time.sleep(1)  # Chờ 1 giây.


# Xử lý ngắt chương trình bằng Ctrl+C.
try:
    main()
except KeyboardInterrupt:
    lcd_clear()  # Xóa màn hình LCD.
    GPIO.cleanup()  # Giải phóng tài nguyên GPIO.
