import numpy as np
from ahrs.filters import Madgwick
from ahrs.common.orientation import q2euler
import time

# ---------------------------
# Simulated IMU sensor values
# ---------------------------

def simulate_imu(yaw_deg):
    """
    Simulate IMU readings as if the device is physically facing
    a specific direction (yaw in degrees).
    """

    yaw_rad = np.radians(yaw_deg)

    # Assume device is flat on table (pitch=roll=0)
    accel = np.array([0.0, 0.0, 9.81])     # Gravity straight down
    gyro = np.array([0.0, 0.0, 0.0])       # Not rotating

    # Ideal magnetometer values for a yaw angle
    # Magnetic field projected into X/Y plane
    mag = np.array([
        np.cos(yaw_rad),   # magnetometer X
        np.sin(yaw_rad),   # magnetometer Y
        0.2                # slight vertical component
    ])

    return accel, gyro, mag


# ---------------------------
# Madgwick Fusion filter
# ---------------------------

fusion = Madgwick()

q = np.array([1.0, 0.0, 0.0, 0.0])   # initial quaternion


# ---------------------------
# MAIN LOOP
# ---------------------------

print("Simulating facing direction detection...\n")

yaw_target = 120    # Change this to ANY facing direction (0–360°)

while True:
    acc, gyro, mag = simulate_imu(yaw_target)

    q = fusion.updateM(q, gyro, acc, mag)
    yaw, pitch, roll = q2euler(q)        # radians

    yaw_deg = (np.degrees(yaw) + 360) % 360

    print(f"Simulated Facing Direction (Yaw): {yaw_deg:.2f}°")
    print(f"Pitch: {np.degrees(pitch):.2f}°    Roll: {np.degrees(roll):.2f}°")
    print("-" * 40)

    time.sleep(0.5)
