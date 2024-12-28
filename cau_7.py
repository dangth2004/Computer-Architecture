# Điều khiển tốc độ động cơ một chiều theo kịch bản sau:
# Ban đầu động cơ đứng yên nhấn nút bấm 1 lần 1 động cơ quay theo một chiều bất kỳ tốc độ 20%,
# nhấn nút bấm 1 lần 2 động cơ tăng tốc lên 40%, nhấn nút bẩm 1 lần 3 động cơ tăng tốc lên 100%,
# nhấn nút bấm 1 lần 4 động cơ dừng quay. Tương tự khi nhấn nút bấm 2 theo cùng kịch bản nhưng lúc này động cơ đảo chiều quay.


import RPi.GPIO as GPIO  # Thư viện để điều khiển GPIO của Raspberry Pi
import time  # Thư viện để xử lý thời gian

# Thiết lập chế độ đánh số chân GPIO theo chuẩn BCM
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)  # Tắt cảnh báo GPIO đã được sử dụng trước đó

# Khai báo các chân GPIO
BT_1 = 21  # Nút bấm 1
BT_2 = 26  # Nút bấm 2
PWM_PIN = 24  # Chân PWM để điều khiển tốc độ động cơ
DIR_PIN = 25  # Chân DIR để điều khiển hướng động cơ

# Thiết lập chế độ cho các chân GPIO
GPIO.setup(PWM_PIN, GPIO.OUT)  # Chân PWM làm đầu ra
GPIO.setup(DIR_PIN, GPIO.OUT)  # Chân DIR làm đầu ra
GPIO.setup(BT_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Nút bấm 1 với chế độ kéo lên
GPIO.setup(BT_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Nút bấm 2 với chế độ kéo lên

# Khởi tạo PWM trên chân PWM_PIN với tần số 1000 Hz
pwm = GPIO.PWM(PWM_PIN, 1000)
pwm.start(0)  # Bắt đầu với chu kỳ nhiệm vụ (duty cycle) là 0%

# Biến toàn cục
speed = 0  # Tốc độ động cơ (duty cycle từ 0% đến 100%)
count = 0  # Đếm số lần nhấn nút BT_1
count1 = 0  # Đếm số lần nhấn nút BT_2
direction = 0  # Hướng động cơ: 0 (tiến), 1 (lùi)


# Hàm điều khiển động cơ
def motor_control(speed, direction):
    """
    Điều khiển động cơ với tốc độ và hướng được chỉ định.
    :param speed: Tốc độ động cơ (0-100)
    :param direction: Hướng động cơ (0: tiến, 1: lùi)
    """
    GPIO.output(DIR_PIN, direction)  # Đặt hướng động cơ
    if direction == 0:  # Nếu hướng là tiến
        speed = speed  # Tốc độ không đổi
    else:  # Nếu hướng là lùi
        speed = 100 - speed  # Đảo ngược tốc độ
    pwm.ChangeDutyCycle(speed)  # Thay đổi chu kỳ nhiệm vụ của PWM


# Hàm xử lý khi nhấn nút BT_1
def button_1_pressed():
    global speed, count
    count += 1  # Tăng biến đếm số lần nhấn
    speed += 20  # Tăng tốc độ thêm 20
    if count == 3:  # Nếu nhấn lần thứ 3
        speed = 100  # Đặt tốc độ là 100%
    if count == 4:  # Nếu nhấn lần thứ 4
        speed = 0  # Tắt động cơ
        count = 0  # Reset biến đếm
    if speed >= 100:  # Đảm bảo tốc độ không vượt quá 100%
        speed = 100
    motor_control(speed, 0)  # Điều khiển động cơ theo hướng tiến


# Hàm xử lý khi nhấn nút BT_2
def button_2_pressed():
    global speed, count1
    count1 += 1  # Tăng biến đếm số lần nhấn
    speed += 20  # Tăng tốc độ thêm 20
    if count1 == 3:  # Nếu nhấn lần thứ 3
        speed = 100  # Đặt tốc độ là 100%
    if count1 == 4:  # Nếu nhấn lần thứ 4
        speed = 0  # Tắt động cơ
        count1 = 0  # Reset biến đếm
    if speed >= 100:  # Đảm bảo tốc độ không vượt quá 100%
        speed = 100
    motor_control(speed, 1)  # Điều khiển động cơ theo hướng lùi


# Hàm chính
def main():
    motor_control(0, 0)  # Khởi động động cơ với tốc độ 0 và hướng tiến
    while True:
        if GPIO.input(BT_1) == GPIO.LOW:  # Nếu nút BT_1 được nhấn
            button_1_pressed()  # Gọi hàm xử lý BT_1
            print(f"So lan bam nut 1: {count}")  # In số lần nhấn nút BT_1
            print(f"Toc do quay: {speed}")
            time.sleep(0.25)  # Chống dội phím
        if GPIO.input(BT_2) == GPIO.LOW:  # Nếu nút BT_2 được nhấn
            button_2_pressed()  # Gọi hàm xử lý BT_2
            print(f"So lan bam nut 2: {count1}")  # In số lần nhấn nút BT_2
            print(f"Toc do quay: {speed}")
            time.sleep(0.25)  # Chống dội phím


# Xử lý kết thúc chương trình
try:
    main()  # Chạy chương trình chính
except KeyboardInterrupt:  # Nếu nhấn Ctrl+C
    pwm.stop()  # Dừng PWM
    GPIO.cleanup()  # Dọn dẹp GPIO
