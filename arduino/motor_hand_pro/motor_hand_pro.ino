/*
 * Motor Hand Pro Controller
 *
 * Controls a prosthetic hand with 5 servo motors (thumb, index, middle, ring, pinky)
 * Receives commands from Multi-Heart-Model HBCM system via serial communication
 * Provides real-time feedback for closed-loop physiological control
 *
 * Hardware Configuration:
 * - Arduino Mega 2560 or Uno
 * - 5x Servo motors (SG90 or MG996R recommended)
 * - Power supply 5-6V for servos
 *
 * Pin Assignments:
 * - Thumb:  Pin 3
 * - Index:  Pin 5
 * - Middle: Pin 6
 * - Ring:   Pin 9
 * - Pinky:  Pin 10
 */

#include <Servo.h>

// Servo definitions
Servo thumbServo;
Servo indexServo;
Servo middleServo;
Servo ringServo;
Servo pinkyServo;

// Pin assignments
const int THUMB_PIN = 3;
const int INDEX_PIN = 5;
const int MIDDLE_PIN = 6;
const int RING_PIN = 9;
const int PINKY_PIN = 10;

// Position constraints (degrees)
const int MIN_ANGLE = 0;
const int MAX_ANGLE = 180;
const int NEUTRAL_ANGLE = 90;

// Current positions
int thumbPos = NEUTRAL_ANGLE;
int indexPos = NEUTRAL_ANGLE;
int middlePos = NEUTRAL_ANGLE;
int ringPos = NEUTRAL_ANGLE;
int pinkyPos = NEUTRAL_ANGLE;

// Target positions for smooth movement
int thumbTarget = NEUTRAL_ANGLE;
int indexTarget = NEUTRAL_ANGLE;
int middleTarget = NEUTRAL_ANGLE;
int ringTarget = NEUTRAL_ANGLE;
int pinkyTarget = NEUTRAL_ANGLE;

// Movement parameters
const int STEP_SIZE = 2;  // degrees per update
const int UPDATE_DELAY = 20;  // milliseconds

// Communication protocol
const char START_MARKER = '<';
const char END_MARKER = '>';
const int MAX_MESSAGE_LENGTH = 64;
char receivedChars[MAX_MESSAGE_LENGTH];
boolean newData = false;

// Status flags
boolean systemEnabled = true;
unsigned long lastCommandTime = 0;
const unsigned long TIMEOUT_MS = 5000;  // 5 second timeout

void setup() {
  Serial.begin(115200);

  // Attach servos to pins
  thumbServo.attach(THUMB_PIN);
  indexServo.attach(INDEX_PIN);
  middleServo.attach(MIDDLE_PIN);
  ringServo.attach(RING_PIN);
  pinkyServo.attach(PINKY_PIN);

  // Initialize to neutral position
  resetToNeutral();

  Serial.println("Motor Hand Pro initialized");
  Serial.println("Ready for HBCM commands");
  sendStatus();
}

void loop() {
  receiveCommand();

  if (newData) {
    parseCommand();
    newData = false;
    lastCommandTime = millis();
  }

  // Safety timeout - return to neutral if no commands received
  if (systemEnabled && (millis() - lastCommandTime > TIMEOUT_MS)) {
    resetToNeutral();
    Serial.println("TIMEOUT: Returning to neutral");
    lastCommandTime = millis();
  }

  // Smooth servo movement
  updateServos();

  delay(UPDATE_DELAY);
}

void receiveCommand() {
  static boolean recvInProgress = false;
  static int ndx = 0;
  char rc;

  while (Serial.available() > 0 && newData == false) {
    rc = Serial.read();

    if (recvInProgress == true) {
      if (rc != END_MARKER) {
        receivedChars[ndx] = rc;
        ndx++;
        if (ndx >= MAX_MESSAGE_LENGTH) {
          ndx = MAX_MESSAGE_LENGTH - 1;
        }
      } else {
        receivedChars[ndx] = '\0';
        recvInProgress = false;
        ndx = 0;
        newData = true;
      }
    } else if (rc == START_MARKER) {
      recvInProgress = true;
    }
  }
}

void parseCommand() {
  char* token = strtok(receivedChars, ",");

  if (token == NULL) return;

  String command = String(token);

  if (command == "SET") {
    // Format: <SET,thumb,index,middle,ring,pinky>
    // Values: 0-180 degrees
    setFingerPositions();
  } else if (command == "GRIP") {
    // Format: <GRIP,strength>
    // strength: 0-100 percentage
    setGripStrength();
  } else if (command == "GESTURE") {
    // Format: <GESTURE,name>
    executeGesture();
  } else if (command == "NEUTRAL") {
    resetToNeutral();
    sendAck("NEUTRAL");
  } else if (command == "STATUS") {
    sendStatus();
  } else if (command == "ENABLE") {
    systemEnabled = true;
    sendAck("ENABLED");
  } else if (command == "DISABLE") {
    systemEnabled = false;
    resetToNeutral();
    sendAck("DISABLED");
  } else {
    sendError("Unknown command");
  }
}

void setFingerPositions() {
  int values[5];
  int idx = 0;

  char* token = strtok(NULL, ",");
  while (token != NULL && idx < 5) {
    values[idx] = constrain(atoi(token), MIN_ANGLE, MAX_ANGLE);
    token = strtok(NULL, ",");
    idx++;
  }

  if (idx == 5 && systemEnabled) {
    thumbTarget = values[0];
    indexTarget = values[1];
    middleTarget = values[2];
    ringTarget = values[3];
    pinkyTarget = values[4];
    sendAck("SET");
  } else {
    sendError("Invalid SET command");
  }
}

void setGripStrength() {
  char* token = strtok(NULL, ",");

  if (token != NULL && systemEnabled) {
    int strength = constrain(atoi(token), 0, 100);

    // Map grip strength to finger closure (0=open, 100=closed)
    // Full grip closure pattern
    thumbTarget = map(strength, 0, 100, 0, 90);
    indexTarget = map(strength, 0, 100, 0, 180);
    middleTarget = map(strength, 0, 100, 0, 180);
    ringTarget = map(strength, 0, 100, 0, 180);
    pinkyTarget = map(strength, 0, 100, 0, 180);

    sendAck("GRIP");
  } else {
    sendError("Invalid GRIP command");
  }
}

void executeGesture() {
  char* token = strtok(NULL, ",");

  if (token == NULL) {
    sendError("No gesture specified");
    return;
  }

  String gesture = String(token);

  if (!systemEnabled) {
    sendError("System disabled");
    return;
  }

  if (gesture == "OPEN") {
    thumbTarget = 0;
    indexTarget = 0;
    middleTarget = 0;
    ringTarget = 0;
    pinkyTarget = 0;
    sendAck("GESTURE:OPEN");
  } else if (gesture == "FIST") {
    thumbTarget = 90;
    indexTarget = 180;
    middleTarget = 180;
    ringTarget = 180;
    pinkyTarget = 180;
    sendAck("GESTURE:FIST");
  } else if (gesture == "POINT") {
    thumbTarget = 45;
    indexTarget = 0;
    middleTarget = 180;
    ringTarget = 180;
    pinkyTarget = 180;
    sendAck("GESTURE:POINT");
  } else if (gesture == "PEACE") {
    thumbTarget = 45;
    indexTarget = 0;
    middleTarget = 0;
    ringTarget = 180;
    pinkyTarget = 180;
    sendAck("GESTURE:PEACE");
  } else if (gesture == "OK") {
    thumbTarget = 90;
    indexTarget = 90;
    middleTarget = 0;
    ringTarget = 0;
    pinkyTarget = 0;
    sendAck("GESTURE:OK");
  } else {
    sendError("Unknown gesture");
  }
}

void updateServos() {
  if (!systemEnabled) return;

  // Smooth movement toward target positions
  thumbPos = moveToward(thumbPos, thumbTarget);
  indexPos = moveToward(indexPos, indexTarget);
  middlePos = moveToward(middlePos, middleTarget);
  ringPos = moveToward(ringPos, ringTarget);
  pinkyPos = moveToward(pinkyPos, pinkyTarget);

  // Update servo positions
  thumbServo.write(thumbPos);
  indexServo.write(indexPos);
  middleServo.write(middlePos);
  ringServo.write(ringPos);
  pinkyServo.write(pinkyPos);
}

int moveToward(int current, int target) {
  if (current < target) {
    return min(current + STEP_SIZE, target);
  } else if (current > target) {
    return max(current - STEP_SIZE, target);
  }
  return current;
}

void resetToNeutral() {
  thumbTarget = NEUTRAL_ANGLE;
  indexTarget = NEUTRAL_ANGLE;
  middleTarget = NEUTRAL_ANGLE;
  ringTarget = NEUTRAL_ANGLE;
  pinkyTarget = NEUTRAL_ANGLE;
}

void sendStatus() {
  Serial.print("<STATUS,");
  Serial.print(systemEnabled ? "ENABLED" : "DISABLED");
  Serial.print(",");
  Serial.print(thumbPos);
  Serial.print(",");
  Serial.print(indexPos);
  Serial.print(",");
  Serial.print(middlePos);
  Serial.print(",");
  Serial.print(ringPos);
  Serial.print(",");
  Serial.print(pinkyPos);
  Serial.println(">");
}

void sendAck(String command) {
  Serial.print("<ACK,");
  Serial.print(command);
  Serial.println(">");
}

void sendError(String message) {
  Serial.print("<ERROR,");
  Serial.print(message);
  Serial.println(">");
}
