import os
import RPi.GPIO as GPIO
from threading import Timer

desire_temp = 43
power = 100

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(12, GPIO.OUT)
p = GPIO.PWM(12, 50)
p.start(power)


def get_temp_value():
    return float(f'{cat_temp() / 1000:.1f}')


def cat_temp():
    with open('/sys/class/thermal/thermal_zone0/temp', mode='r') as f:
        return int(f.read())


def save_power(pwr):
    os.system(f"echo {pwr} > /tmp/cpu_fan_pwr")


def control_fan():
    global power
    temp = cat_temp() / 1000
    if temp > desire_temp:
        power = min(100, max(int(power + 5 * (temp - desire_temp)), 30))
    else:
        power = min(100, max(power - 5, 30))
    p.ChangeDutyCycle(power)
    save_power(power)
    Timer(10, control_fan).start()


save_power(power)
Timer(10, control_fan).start()
