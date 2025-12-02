# wrapper for GPS module
# Replace import with your actual function
try:
    from GPS_Navigation.read_heading import get_current_heading
except Exception:
    # stub
    def get_current_heading():
        return {"heading": 123.4}

def gps_tool(params):
    heading = get_current_heading()
    return {"heading": heading}
