#include <Wire.h>
#include <Adafruit_BNO08x.h>
#include <Servo.h>

Servo myServo;

// ---------- BNO085 ----------
Adafruit_BNO08x bno08x(-1);
sh2_SensorValue_t sensorValue;

float yawDeg = 0.0;
float pitchDeg = 0.0;
float rollDeg = 0.0;
bool imuDetected = false;

// ---------- DFRobot Underwater Ultrasonic ----------
#define UW_CMD 0x55
int underwaterDistanceMm = -1;

// ---------- Basic Ultrasonic #1 ----------
const int trigPin1 = 7;
const int echoPin1 = 6;
long basicDistanceCm1 = -1;

// ---------- Basic Ultrasonic #2 ----------
const int trigPin2 = 9;
const int echoPin2 = 8;
long basicDistanceCm2 = -1;

// ---------- Timing ----------
unsigned long lastPrint = 0;
const unsigned long intervalMs = 100;

// Convert quaternion to yaw/pitch/roll
void quaternionToEuler(float qr, float qi, float qj, float qk,
                       float &yaw, float &pitch, float &roll) {
  yaw = atan2(2.0 * (qi * qj + qk * qr),
              (qi * qi - qj * qj - qk * qk + qr * qr));

  pitch = asin(-2.0 * (qi * qk - qj * qr));

  roll = atan2(2.0 * (qj * qk + qi * qr),
               (-qi * qi - qj * qj + qk * qk + qr * qr));

  yaw *= 180.0 / PI;
  pitch *= 180.0 / PI;
  roll *= 180.0 / PI;
}

// Read one IMU event if available
void updateIMU() {
  if (bno08x.getSensorEvent(&sensorValue)) {
    if (sensorValue.sensorId == SH2_ROTATION_VECTOR) {
      float qw = sensorValue.un.rotationVector.real;
      float qx = sensorValue.un.rotationVector.i;
      float qy = sensorValue.un.rotationVector.j;
      float qz = sensorValue.un.rotationVector.k;

      quaternionToEuler(qw, qx, qy, qz, yawDeg, pitchDeg, rollDeg);
    }
  }
}

// Read DFRobot underwater ultrasonic
void updateUnderwaterUltrasonic() {
  while (Serial2.available()) {
    Serial2.read();
  }

  Serial2.write(UW_CMD);
  delay(20);

  if (Serial2.available() >= 4) {
    byte b0 = Serial2.read();
    byte b1 = Serial2.read();
    byte b2 = Serial2.read();
    byte b3 = Serial2.read();

    byte checksum = (byte)(b0 + b1 + b2);

    if (b0 == 0xFF && b3 == checksum) {
      underwaterDistanceMm = ((int)b1 << 8) | b2;
    } else {
      underwaterDistanceMm = -1;
    }
  } else {
    underwaterDistanceMm = -1;
  }
}

// Generic function for HC-SR04 style sensors
long readBasicUltrasonicCm(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  unsigned long duration = pulseIn(echoPin, HIGH, 30000UL);

  if (duration == 0) {
    return -1;
  } else {
    return duration / 58;
  }
}

void setup() {
    myServo.attach(11);  // signal pin

  Serial.begin(115200);
  while (!Serial) delay(10);

  // IMU
  Wire.begin();
  Serial.println("BNO085 starting...");

  if (!bno08x.begin_I2C(0x4B)) {
    Serial.println("BNO085 NOT detected at 0x4B");
  } else {
    Serial.println("BNO085 detected!");

    if (!bno08x.enableReport(SH2_ROTATION_VECTOR, 10000)) {
      Serial.println("Failed to enable rotation vector");
    } else {
      imuDetected = true;
    }
  }

  // Underwater ultrasonic
  Serial2.begin(115200);

  // Basic ultrasonic pins
  pinMode(trigPin1, OUTPUT);
  pinMode(echoPin1, INPUT);
  pinMode(trigPin2, OUTPUT);
  pinMode(echoPin2, INPUT);

  Serial.println("All sensors starting...");
}

void loop() {
  
    // 0 → 90
  for (int pos = 0; pos <= 180; pos= pos+ 10) {

    myServo.write(pos);
    delay(500);
    if (imuDetected) {
    updateIMU();
  }
    if (millis() - lastPrint >= intervalMs) {
      lastPrint = millis();

      updateUnderwaterUltrasonic();
      basicDistanceCm1 = readBasicUltrasonicCm(trigPin1, echoPin1);
      basicDistanceCm2 = readBasicUltrasonicCm(trigPin2, echoPin2);

      Serial.print("Yaw: ");
      if (imuDetected) Serial.print(yawDeg, 2);
      else Serial.print("N/A");

      Serial.print("  Pitch: ");
      if (imuDetected) Serial.print(pitchDeg, 2);
      else Serial.print("N/A");

      Serial.print("  Roll: ");
      if (imuDetected) Serial.print(rollDeg, 2);
      else Serial.print("N/A");

      Serial.print("  |  Underwater(mm): ");
      if (underwaterDistanceMm >= 0) Serial.print(underwaterDistanceMm);
      else Serial.print("no data");

      Serial.print("  |  Basic1(cm): ");
      if (basicDistanceCm1 >= 0) Serial.print(basicDistanceCm1);
      else Serial.print("out of range");

      Serial.print("  |  Basic2(cm): ");
      if (basicDistanceCm2 >= 0) Serial.print(basicDistanceCm2);
      else Serial.print("out of range");
Serial.print(yawDeg); Serial.print(",");
Serial.print(pitchDeg); Serial.print(",");
Serial.print(rollDeg); Serial.print(",");
Serial.print(underwaterDistanceMm); Serial.print(",");
Serial.print(basicDistanceCm1); Serial.print(",");
Serial.println(basicDistanceCm2);
      Serial.println();
    }
  }

  // delay(500);

  // 90 → 0
  for (int pos = 180; pos >= 0; pos= pos-10) {

    myServo.write(pos);
    delay(500);
    if (imuDetected) {
    updateIMU();
  }
    if (millis() - lastPrint >= intervalMs) {
      lastPrint = millis();

      updateUnderwaterUltrasonic();
      basicDistanceCm1 = readBasicUltrasonicCm(trigPin1, echoPin1);
      basicDistanceCm2 = readBasicUltrasonicCm(trigPin2, echoPin2);

      Serial.print("Yaw: ");
      if (imuDetected) Serial.print(yawDeg, 2);
      else Serial.print("N/A");

      Serial.print("  Pitch: ");
      if (imuDetected) Serial.print(pitchDeg, 2);
      else Serial.print("N/A");

      Serial.print("  Roll: ");
      if (imuDetected) Serial.print(rollDeg, 2);
      else Serial.print("N/A");

      Serial.print("  |  Underwater(mm): ");
      if (underwaterDistanceMm >= 0) Serial.print(underwaterDistanceMm);
      else Serial.print("no data");

      Serial.print("  |  Basic1(cm): ");
      if (basicDistanceCm1 >= 0) Serial.print(basicDistanceCm1);
      else Serial.print("out of range");

      Serial.print("  |  Basic2(cm): ");
      if (basicDistanceCm2 >= 0) Serial.print(basicDistanceCm2);
      else Serial.print("out of range");
      Serial.print(yawDeg); Serial.print(",");
Serial.print(pitchDeg); Serial.print(",");
Serial.print(rollDeg); Serial.print(",");
Serial.print(underwaterDistanceMm); Serial.print(",");
Serial.print(basicDistanceCm1); Serial.print(",");
Serial.println(basicDistanceCm2);
      Serial.println();
    }
  }


  
}