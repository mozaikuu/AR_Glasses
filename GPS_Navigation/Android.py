from jnius import autoclass
import time
import math

# Android classes
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Context = PythonActivity.mActivity.getApplicationContext()
SensorManager = autoclass('android.hardware.SensorManager')
LocationManager = autoclass('android.location.LocationManager')

# Get system services
sensor_manager = Context.getSystemService(Context.SENSOR_SERVICE)
location_manager = Context.getSystemService(Context.LOCATION_SERVICE)

# Get sensors
mag_sensor = sensor_manager.getDefaultSensor(2)    # TYPE_MAGNETIC_FIELD
acc_sensor = sensor_manager.getDefaultSensor(1)    # TYPE_ACCELEROMETER
gyro_sensor = sensor_manager.getDefaultSensor(4)   # TYPE_GYROSCOPE

# Holder for latest sensor values
acc = [0, 0, 0]
mag = [0, 0, 0]

# Sensor event listener
SensorEventListener = autoclass('android.hardware.SensorEventListener')

class Listener(SensorEventListener):
    def onAccuracyChanged(self, sensor, accuracy):
        pass

    def onSensorChanged(self, event):
        global acc, mag

        if event.sensor.getType() == 1:
            acc = event.values[:]
        elif event.sensor.getType() == 2:
            mag = event.values[:]

listener = Listener()

# Register listeners
sensor_manager.registerListener(listener, acc_sensor, SensorManager.SENSOR_DELAY_GAME)
sensor_manager.registerListener(listener, mag_sensor, SensorManager.SENSOR_DELAY_GAME)

# Function to compute heading
def compute_heading():
    gravity = acc
    geomag = mag

    R = [0]*9
    I = [0]*9

    success = SensorManager.getRotationMatrix(R, I, gravity, geomag)
    if success:
        orientation = [0]*3
        SensorManager.getOrientation(R, orientation)
        azimuth = math.degrees(orientation[0])
        azimuth = (azimuth + 360) % 360
        return azimuth
    return None

# GPS listener
def get_gps():
    provider = location_manager.GPS_PROVIDER
    loc = location_manager.getLastKnownLocation(provider)
    if loc:
        return loc.getLatitude(), loc.getLongitude()
    return None, None

# Main loop
print("Reading Android real sensors...")
while True:
    lat, lon = get_gps()
    heading = compute_heading()

    if lat and lon:
        print(f"GPS: {lat:.6f}, {lon:.6f}")

    if heading is not None:
        print(f"Heading: {heading:.2f}°")

    print("-" * 40)
    time.sleep(0.5)
