import serial

ser = serial.Serial('COM4', 115200, timeout=1)  # change COM port

print("Reading Arduino data...\n")

while True:
    try:
        line = ser.readline().decode(errors='ignore').strip()

        if line:
            try:
                yaw, pitch, roll, uw, d1, d2, servo = line.split(",")

                print(f"Yaw: {yaw} | Pitch: {pitch} | Roll: {roll}")
                print(f"Underwater: {uw} mm | Sensor1: {d1} cm | Sensor2: {d2} cm")
                print("-" * 60)

            except:
                print("RAW:", line)

    except KeyboardInterrupt:
        break