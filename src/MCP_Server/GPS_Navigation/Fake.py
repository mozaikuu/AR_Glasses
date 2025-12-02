import math
import time
import random

# ================================
# FAKE SENSOR MODULE
# ================================

class FakeIMU:
    def __init__(self):
        self.heading = 0     # degrees
        self.tilt = 0        # fake tilt
        self.mag_noise = 5   # +- degrees random
        self.acc_noise = 0.02

    def rotate_left(self, amount=3):
        self.heading = (self.heading - amount) % 360

    def rotate_right(self, amount=3):
        self.heading = (self.heading + amount) % 360

    def read_magnetometer(self):
        return self.heading + random.uniform(-self.mag_noise, self.mag_noise)

    def read_accelerometer(self):
        return (
            0 + random.uniform(-self.acc_noise, self.acc_noise),
            0 + random.uniform(-self.acc_noise, self.acc_noise),
            9.8 + random.uniform(-self.acc_noise, self.acc_noise)
        )


class FakeGPS:
    def __init__(self):
        self.lat = 30.000000
        self.lon = 31.000000

    def wander(self):
        self.lat += random.uniform(-0.00005, 0.00005)
        self.lon += random.uniform(-0.00005, 0.00005)

    def read(self):
        self.wander()
        return self.lat, self.lon


# ================================
# MAIN APP
# ================================

imu = FakeIMU()
gps = FakeGPS()

print("Fake GPS + Fake IMU Simulation Running…")
print("Press A/D then Enter to turn left/right.")

while True:
    # Fake rotation input
    key = input("A=left, D=right, Enter=stay still: ")

    if key.lower() == "a":
        imu.rotate_left()
    elif key.lower() == "d":
        imu.rotate_right()

    # Read fake sensors
    heading = imu.read_magnetometer()
    acc = imu.read_accelerometer()
    lat, lon = gps.read()

    print(f"GPS: {lat:.6f}, {lon:.6f}")
    print(f"Heading: {heading:.2f}°")
    print(f"Accel: {acc}")
    print("-" * 40)
    time.sleep(0.3)
