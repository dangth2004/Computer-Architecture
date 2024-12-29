import RPi.GPIO as GPIO  # Thư viện điều khiển GPIO trên Raspberry Pi.
import time  # Thư viện cung cấp các hàm liên quan đến thời gian.

DHT11_PIN = 7  # Chân GPIO kết nối với cảm biến DHT11.
LCD_PINS = {'RS': 23, 'E': 27, 'D4': 18, 'D5': 17, 'D6': 14, 'D7': 3,
            'BL': 2}  # Các chân GPIO kết nối với màn hình LCD.
RLS = {"RELAY_1": 16, "RELAY_2": 12, "LED": 13}  # Các chân GPIO điều khiển relay và LED.
LCD_WIDTH = 16  # Chiều rộng của màn hình LCD (16 ký tự).
LCD_CHR = True  # Chế độ gửi dữ liệu.
LCD_CMD = False  # Chế độ gửi lệnh.
LCD_LINE_1 = 0x80  # Địa chỉ dòng 1 của màn hình LCD.
LCD_LINE_2 = 0xC0  # Địa chỉ dòng 2 của màn hình LCD.
E_PULSE = 0.0005  # Thời gian giữ chân E ở mức cao.
E_DELAY = 0.0005  # Thời gian trễ giữa các lần gửi tín hiệu.
ROOM_TEMPERATURE = 15  # Nhiệt độ tiêu chuẩn của phòng.

GPIO.setmode(GPIO.BCM)  # Thiết lập chế độ đánh số chân GPIO kiểu BCM.
GPIO.setwarnings(False)  # Tắt cảnh báo từ thư viện GPIO.


def read_dht11():
    GPIO.setup(DHT11_PIN, GPIO.OUT)  # Thiết lập chân DHT11 ở chế độ xuất.
    GPIO.output(DHT11_PIN, GPIO.LOW)  # Gửi tín hiệu bắt đầu.
    time.sleep(0.02)  # Chờ 20ms.
    GPIO.output(DHT11_PIN, GPIO.HIGH)  # Dừng tín hiệu thấp.
    GPIO.setup(DHT11_PIN, GPIO.IN)  # Chuyển chân sang chế độ nhập.
    # Đo tín hiệu từ cảm biến DHT11.
    while GPIO.input(DHT11_PIN) == GPIO.LOW:
        pass
    while GPIO.input(DHT11_PIN) == GPIO.HIGH:
        pass
    # Đọc 40 bit dữ liệu (bao gồm độ ẩm, nhiệt độ và checksum).
    data = []
    for i in range(40):
        while GPIO.input(DHT11_PIN) == GPIO.LOW:
            pass
        count = 0
        while GPIO.input(DHT11_PIN) == GPIO.HIGH:
            count += 1
            if count > 100:
                break
        data.append(1 if count > 8 else 0)  # Phân biệt 0 và 1 dựa trên thời gian giữ mức cao.
    # Tách các phần dữ liệu.
    humidity_bit = data[0:8]
    humidity_point_bit = data[8:16]
    temperature_bit = data[16:24]
    temperature_point_bit = data[24:32]
    check_bit = data[32:40]
    # Chuyển đổi từ bit sang giá trị số.
    humidity = sum(humidity_bit[i] * 2 ** (7 - i) for i in range(8))
    temperature = sum(temperature_bit[i] * 2 ** (7 - i) for i in range(8))
    checksum = sum(check_bit[i] * 2 ** (7 - i) for i in range(8))
    check = humidity + temperature
    if checksum == check:  # Kiểm tra tính hợp lệ của dữ liệu.
        return temperature, humidity
    else:
        return None, None


def lcd_init():
    for pin in LCD_PINS.values():
        GPIO.setup(pin, GPIO.OUT)  # Thiết lập các chân LCD ở chế độ xuất.
    for byte in [0x33, 0x32, 0x28, 0x0C, 0x06, 0x01]:  # Gửi các lệnh khởi tạo.
        lcd_byte(byte, LCD_CMD)


def lcd_clear():
    lcd_byte(0x01, LCD_CMD)  # Gửi lệnh xóa màn hình.


def lcd_byte(bits, mode):
    GPIO.output(LCD_PINS['RS'], mode)  # Thiết lập chế độ gửi (lệnh/dữ liệu).
    # Gửi 4 bit cao.
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << (4 + bit_num)) != 0)
    GPIO.output(LCD_PINS['E'], True)  # Tạo xung trên chân E.
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)
    # Gửi 4 bit thấp.
    for bit_num in range(4):
        GPIO.output(LCD_PINS[f'D{bit_num + 4}'], bits & (1 << bit_num) != 0)
    GPIO.output(LCD_PINS['E'], True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_PINS['E'], False)


def lcd_display_string(message, line):
    lcd_byte(LCD_LINE_1 if line == 1 else LCD_LINE_2, LCD_CMD)  # Chọn dòng hiển thị.
    for char in message:
        lcd_byte(ord(char), LCD_CHR)  # Hiển thị từng ký tự.


def control_relay(temperature):
    for pin in RLS.values():
        GPIO.setup(pin, GPIO.OUT)  # Thiết lập chân relay ở chế độ xuất.
    if temperature > ROOM_TEMPERATURE:
        GPIO.output(RLS['RELAY_1'], GPIO.HIGH)  # Bật relay.
        GPIO.output(RLS['RELAY_2'], GPIO.HIGH)
    else:
        GPIO.output(RLS['RELAY_1'], GPIO.LOW)  # Tắt relay.
        GPIO.output(RLS['RELAY_2'], GPIO.LOW)


def main():
    lcd_init()  # Khởi tạo LCD.
    GPIO.output(LCD_PINS['BL'], True)  # Bật đèn nền LCD.
    while True:
        temperature, humidity = read_dht11()  # Đọc nhiệt độ và độ ẩm.
        print(temperature, humidity)  # In giá trị lên console.
        if humidity is not None and temperature is not None:  # Nếu dữ liệu hợp lệ.
            lcd_display_string('temp :{:.1f}*C'.format(temperature), 1)  # Hiển thị nhiệt độ.
            control_relay(temperature)  # Điều khiển relay dựa trên nhiệt độ.
        time.sleep(1)


try:
    main()
except KeyboardInterrupt:
    GPIO.cleanup()  # Dọn dẹp GPIO khi dừng chương trình.
    lcd_clear()  # Xóa màn hình LCD.
