import RPi.GPIO as GPIO  # Import thư viện GPIO để điều khiển các chân GPIO trên Raspberry Pi.
import time  # Import thư viện time để sử dụng chức năng tạm dừng.

# Thiết lập chế độ đánh số chân GPIO.
GPIO.setmode(GPIO.BCM)  # Sử dụng chế độ đánh số GPIO kiểu BCM
GPIO.setwarnings(False)  # Tắt cảnh báo GPIO

# Khai báo các chân GPIO được sử dụng.
BT_1 = 21  # Chân nối với nút nhấn 1.
BT_2 = 26  # Chân nối với nút nhấn 2.
PWM_PIN = 24  # Chân nối với chân PWM của động cơ.
DIR_PIN = 25  # Chân nối với chân điều khiển hướng của động cơ.

# Thiết lập chế độ hoạt động cho các chân GPIO.
GPIO.setup(PWM_PIN, GPIO.OUT)  # Đặt chân PWM_PIN là đầu ra.
GPIO.setup(DIR_PIN, GPIO.OUT)  # Đặt chân DIR_PIN là đầu ra.
GPIO.setup(BT_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Đặt chân BT_1 là đầu vào với pull-up.
GPIO.setup(BT_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Đặt chân BT_2 là đầu vào với pull-up.

# Khởi tạo tín hiệu PWM cho chân PWM_PIN với tần số 1000 Hz.
pwm = GPIO.PWM(PWM_PIN, 1000)
pwm.start(0)  # Bắt đầu với chu kỳ làm việc (duty cycle) là 0%.

# Khởi tạo các biến toàn cục.
speed = 0  # Tốc độ động cơ.
count_bt1 = 0  # Số lần nhấn nút 1.
count_bt2 = 0  # Số lần nhấn nút 2.
direction = 0  # Hướng động cơ (0: một chiều, 1: chiều ngược lại).


# Hàm điều khiển động cơ với tốc độ và hướng.
def motor_control(speed, direction):
    GPIO.output(DIR_PIN, direction)  # Điều chỉnh hướng của động cơ.
    if direction == 0:  # Nếu hướng là 0, tốc độ giữ nguyên.
        speed = speed
    else:  # Nếu hướng là 1, tốc độ sẽ được đảo ngược (100% - speed).
        speed = 100 - speed
    pwm.ChangeDutyCycle(speed)  # Điều chỉnh chu kỳ làm việc của tín hiệu PWM.


# Hàm xử lý khi nút 1 được nhấn.
def button_1_pressed():
    global speed, count_bt1  # Sử dụng các biến toàn cục.
    count_bt1 += 1  # Tăng biến đếm số lần nhấn nút 1.
    speed += 20  # Tăng tốc độ động cơ thêm 20%.
    if count_bt1 == 3:  # Nếu nút được nhấn lần thứ 3, tốc độ đạt 100%.
        speed = 100
    if count_bt1 == 4:  # Nếu nhấn lần thứ 4, tốc độ trở về 0 và đếm lại từ đầu.
        speed = 0
        count_bt1 = 0
    if speed >= 100:  # Đảm bảo tốc độ không vượt quá 100%.
        speed = 100
    motor_control(speed, 0)  # Điều khiển động cơ chạy một chiều.


# Hàm xử lý khi nút 2 được nhấn.
def button_2_pressed():
    global speed, count_bt2  # Sử dụng các biến toàn cục.
    count_bt2 += 1  # Tăng biến đếm số lần nhấn nút 2.
    speed += 20  # Tăng tốc độ động cơ thêm 20%.
    if count_bt2 == 3:  # Nếu nút được nhấn lần thứ 3, tốc độ đạt 100%.
        speed = 100
    if count_bt2 == 4:  # Nếu nhấn lần thứ 4, tốc độ trở về 0 và đếm lại từ đầu.
        speed = 0
        count_bt2 = 0
    if speed >= 100:  # Đảm bảo tốc độ không vượt quá 100%.
        speed = 100
    motor_control(speed, 1)  # Điều khiển động cơ chạy ngược chiều.


# Hàm chính để đọc trạng thái nút và điều khiển động cơ.
def main():
    motor_control(0, 0)  # Ban đầu động cơ không hoạt động.
    while True:  # Vòng lặp chính.
        if GPIO.input(BT_1) == GPIO.LOW:  # Kiểm tra nếu nút 1 được nhấn (mức thấp).
            button_1_pressed()  # Gọi hàm xử lý nút 1.
            print(f"So lan bam nut 1: {count_bt1}")  # In ra số lần nhấn nút 1.
            time.sleep(0.25)  # Tránh việc nhấn lặp lại nhanh.
        if GPIO.input(BT_2) == GPIO.LOW:  # Kiểm tra nếu nút 2 được nhấn (mức thấp).
            button_2_pressed()  # Gọi hàm xử lý nút 2.
            print(f"So lan bam nut 2: {count_bt2}")  # In ra số lần nhấn nút 2.
            time.sleep(0.25)  # Tránh việc nhấn lặp lại nhanh.


# Xử lý ngoại lệ khi kết thúc chương trình bằng Ctrl+C.
try:
    main()  # Gọi hàm chính.
except KeyboardInterrupt:  # Nếu nhận lệnh dừng từ bàn phím.
    pwm.stop()  # Dừng tín hiệu PWM.
    GPIO.cleanup()  # Giải phóng các chân GPIO.
