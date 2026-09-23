/*
 * AirPen v2 — Companion BLE GATT Firmware Sketch
 * K. J. Somaiya Institute of Technology · Group 11
 * 
 * Hardware Wiring:
 *   MPU6050 VCC -> ESP32 3.3V
 *   MPU6050 GND -> ESP32 GND
 *   MPU6050 SDA -> ESP32 GPIO21
 *   MPU6050 SCL -> ESP32 GPIO22
 *   Button      -> ESP32 GPIO4 (active LOW with internal pull-up)
 * 
 * BLE GATT Service UUID:        19B10000-E8F2-537E-4F6C-D104768A1214
 * IMU Stream Characteristic:    19B10001-E8F2-537E-4F6C-D104768A1214 (NOTIFY)
 * Stroke Event Characteristic:  19B10002-E8F2-537E-4F6C-D104768A1214 (NOTIFY)
 * Control/Config Characteristic:19B10003-E8F2-537E-4F6C-D104768A1214 (WRITE/READ)
 */

#include <Wire.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define BUTTON_PIN 4
#define MPU_ADDR 0x68

// Service & Characteristic UUIDs
#define SERVICE_UUID        "19B10000-E8F2-537E-4F6C-D104768A1214"
#define CHAR_IMU_UUID       "19B10001-E8F2-537E-4F6C-D104768A1214"
#define CHAR_STROKE_UUID    "19B10002-E8F2-537E-4F6C-D104768A1214"
#define CHAR_CONTROL_UUID   "19B10003-E8F2-537E-4F6C-D104768A1214"

BLEServer* pServer = NULL;
BLECharacteristic* pIMUCharacteristic = NULL;
BLECharacteristic* pStrokeCharacteristic = NULL;
BLECharacteristic* pControlCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;

// Calibration Offsets
int16_t ax_offset = 0, ay_offset = 0, az_offset = 0;
int16_t gx_offset = 0, gy_offset = 0, gz_offset = 0;

// Button state tracking
bool lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 30;

// Binary packet structure (20 bytes total - fits standard BLE MTU 23)
#pragma pack(push, 1)
struct IMUPacket {
  uint32_t t_ms;     // 4 bytes: timestamp in milliseconds
  int16_t ax;        // 2 bytes: Accel X (raw)
  int16_t ay;        // 2 bytes: Accel Y (raw)
  int16_t az;        // 2 bytes: Accel Z (raw)
  int16_t gx;        // 2 bytes: Gyro X (raw)
  int16_t gy;        // 2 bytes: Gyro Y (raw)
  int16_t gz;        // 2 bytes: Gyro Z (raw)
  uint8_t btn;       // 1 byte:  1 = pressed (pen down), 0 = released
  uint8_t stroke_id; // 1 byte:  incremental stroke counter
};
#pragma pack(pop)

IMUPacket currentPacket;
uint8_t currentStrokeId = 0;
unsigned long lastSampleTime = 0;
const unsigned long sampleInterval = 20; // 50 Hz streaming (20ms)

class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    deviceConnected = true;
    Serial.println("[BLE] Companion App Connected!");
  }

  void onDisconnect(BLEServer* pServer) {
    deviceConnected = false;
    Serial.println("[BLE] Companion App Disconnected.");
  }
};

class ControlCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic* pCharacteristic) {
    String value = pCharacteristic->getValue();
    if (value.length() > 0) {
      Serial.print("[BLE] Control Command Received: ");
      Serial.println(value.c_str());
      if (value == "CALIBRATE_BIAS") {
        calibrateMPU();
      } else if (value == "RESET_STROKE") {
        currentStrokeId = 0;
      }
    }
  }
};

void initMPU6050() {
  Wire.begin(21, 22, 400000); // 400kHz I2C
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B); // PWR_MGMT_1 register
  Wire.write(0x00); // Wake up MPU6050
  Wire.endTransmission(true);

  // Configure DLPF (Digital Low-Pass Filter) -> 0x1A CONFIG register
  // Value 3: ~44 Hz Accel bandwidth, ~42 Hz Gyro bandwidth (ideal for air-writing)
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x1A);
  Wire.write(0x03);
  Wire.endTransmission(true);

  // Configure Gyro Full Scale (+/- 500 deg/s) -> 0x1B GYRO_CONFIG register
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x1B);
  Wire.write(0x08);
  Wire.endTransmission(true);

  Serial.println("[MPU6050] Initialized with DLPF ~44Hz.");
}

void calibrateMPU() {
  Serial.println("[MPU6050] Calibrating bias (keep pen still for 2 seconds)...");
  int32_t gx_sum = 0, gy_sum = 0, gz_sum = 0;
  const int samples = 200;
  for (int i = 0; i < samples; i++) {
    Wire.beginTransmission(MPU_ADDR);
    Wire.write(0x43); // Gyro start register
    Wire.endTransmission(false);
    Wire.requestFrom(MPU_ADDR, 6, true);
    if (Wire.available() >= 6) {
      gx_sum += (int16_t)(Wire.read() << 8 | Wire.read());
      gy_sum += (int16_t)(Wire.read() << 8 | Wire.read());
      gz_sum += (int16_t)(Wire.read() << 8 | Wire.read());
    }
    delay(10);
  }
  gx_offset = gx_sum / samples;
  gy_offset = gy_sum / samples;
  gz_offset = gz_sum / samples;
  Serial.printf("[MPU6050] Bias offsets: Gx=%d, Gy=%d, Gz=%d\n", gx_offset, gy_offset, gz_offset);
}

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  initMPU6050();
  calibrateMPU();

  // Initialize BLE
  BLEDevice::init("AirPen_v2");
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new ServerCallbacks());

  BLEService* pService = pServer->createService(SERVICE_UUID);

  // IMU Data characteristic
  pIMUCharacteristic = pService->createCharacteristic(
    CHAR_IMU_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
  );
  pIMUCharacteristic->addDescriptor(new BLE2902());

  // Stroke Event characteristic
  pStrokeCharacteristic = pService->createCharacteristic(
    CHAR_STROKE_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
  );
  pStrokeCharacteristic->addDescriptor(new BLE2902());

  // Control characteristic
  pControlCharacteristic = pService->createCharacteristic(
    CHAR_CONTROL_UUID,
    BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_READ
  );
  pControlCharacteristic->setCallbacks(new ControlCallbacks());

  pService->start();

  BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);
  pAdvertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();
  Serial.println("[BLE] Advertising started. Ready for Companion App pairing!");
}

void loop() {
  // Read button with debounce
  int reading = digitalRead(BUTTON_PIN);
  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }

  uint8_t isPressed = 0;
  if ((millis() - lastDebounceTime) > debounceDelay) {
    isPressed = (reading == LOW) ? 1 : 0; // Active LOW
    if (isPressed && !currentPacket.btn) {
      // Stroke started!
      currentStrokeId++;
      Serial.printf("[STROKE] Start Stroke #%d\n", currentStrokeId);
      if (deviceConnected) {
        uint8_t strokeEvent[2] = {0x01, currentStrokeId}; // 0x01 = Stroke Start
        pStrokeCharacteristic->setValue(strokeEvent, 2);
        pStrokeCharacteristic->notify();
      }
    } else if (!isPressed && currentPacket.btn) {
      // Stroke ended
      Serial.printf("[STROKE] End Stroke #%d\n", currentStrokeId);
      if (deviceConnected) {
        uint8_t strokeEvent[2] = {0x00, currentStrokeId}; // 0x00 = Stroke End
        pStrokeCharacteristic->setValue(strokeEvent, 2);
        pStrokeCharacteristic->notify();
      }
    }
    currentPacket.btn = isPressed;
  }
  lastButtonState = reading;

  // Stream IMU samples at fixed interval (50Hz)
  if (millis() - lastSampleTime >= sampleInterval) {
    lastSampleTime = millis();

    Wire.beginTransmission(MPU_ADDR);
    Wire.write(0x3B); // Accel start register
    Wire.endTransmission(false);
    Wire.requestFrom(MPU_ADDR, 14, true);

    if (Wire.available() >= 14) {
      int16_t raw_ax = (Wire.read() << 8 | Wire.read());
      int16_t raw_ay = (Wire.read() << 8 | Wire.read());
      int16_t raw_az = (Wire.read() << 8 | Wire.read());
      Wire.read(); Wire.read(); // Skip temp register
      int16_t raw_gx = (Wire.read() << 8 | Wire.read()) - gx_offset;
      int16_t raw_gy = (Wire.read() << 8 | Wire.read()) - gy_offset;
      int16_t raw_gz = (Wire.read() << 8 | Wire.read()) - gz_offset;

      currentPacket.t_ms = millis();
      currentPacket.ax = raw_ax;
      currentPacket.ay = raw_ay;
      currentPacket.az = raw_az;
      currentPacket.gx = raw_gx;
      currentPacket.gy = raw_gy;
      currentPacket.gz = raw_gz;
      currentPacket.stroke_id = currentStrokeId;

      if (deviceConnected) {
        pIMUCharacteristic->setValue((uint8_t*)&currentPacket, sizeof(IMUPacket));
        pIMUCharacteristic->notify();
      }
    }
  }

  // Handle BLE disconnect & re-advertising
  if (!deviceConnected && oldDeviceConnected) {
    delay(500);
    pServer->startAdvertising();
    Serial.println("[BLE] Restarted advertising.");
    oldDeviceConnected = deviceConnected;
  }
  if (deviceConnected && !oldDeviceConnected) {
    oldDeviceConnected = deviceConnected;
  }
}
