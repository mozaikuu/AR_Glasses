import gps

session = gps.gps(mode=gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

print("Listening for GPS data...")

while True:
    report = session.next()

    if report['class'] == 'TPV':
        lat = getattr(report, 'lat', None)
        lon = getattr(report, 'lon', None)
        track = getattr(report, 'track', None)

        if lat and lon:
            print(f"Lat: {lat}, Lon: {lon}")

        if track is not None:
            print(f"Heading (track): {track} degrees")
