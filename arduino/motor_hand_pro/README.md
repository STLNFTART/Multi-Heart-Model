# Motor Hand Pro - Arduino Controller

Arduino firmware for controlling a 5-finger prosthetic hand integrated with the Heart-Brain Coupling Model (HBCM).

## Hardware Requirements

- **Microcontroller**: Arduino Mega 2560 or Uno
- **Servos**: 5x servo motors (SG90 or MG996R recommended)
- **Power Supply**: 5-6V DC for servos (separate from Arduino)
- **Connections**: USB cable for serial communication

## Pin Configuration

| Finger | Arduino Pin | Servo Wire |
|--------|-------------|------------|
| Thumb  | D3          | PWM Signal |
| Index  | D5          | PWM Signal |
| Middle | D6          | PWM Signal |
| Ring   | D9          | PWM Signal |
| Pinky  | D10         | PWM Signal |

## Wiring Diagram

```
Arduino Mega/Uno          Servos
  ┌──────────┐
  │          │           ┌─────────┐
  │  D3  ────┼──────────▶│ Thumb   │
  │  D5  ────┼──────────▶│ Index   │
  │  D6  ────┼──────────▶│ Middle  │
  │  D9  ────┼──────────▶│ Ring    │
  │  D10 ────┼──────────▶│ Pinky   │
  │          │           └─────────┘
  │  GND ────┼──────────▶ GND (common)
  │          │
  │  USB ────┼────── To Computer
  └──────────┘

  External 5-6V Power ───▶ Servo VCC (common)
```

**IMPORTANT**: Connect servo power to an external supply, NOT Arduino 5V pin (insufficient current).

## Installation

1. Open `motor_hand_pro.ino` in Arduino IDE
2. Install required library: `Servo` (usually pre-installed)
3. Select board: Tools → Board → Arduino Mega 2560 (or Uno)
4. Select port: Tools → Port → (your Arduino port)
5. Upload sketch: Sketch → Upload

## Communication Protocol

The firmware uses a simple serial protocol with `<START>` and `>END` markers.

**Baud Rate**: 115200

### Commands

#### Set Individual Finger Positions
```
<SET,thumb,index,middle,ring,pinky>
```
- Values: 0-180 degrees
- Example: `<SET,90,45,90,120,180>`

#### Set Grip Strength
```
<GRIP,strength>
```
- Strength: 0-100 (percentage)
- Example: `<GRIP,75>` (75% closed grip)

#### Execute Gesture
```
<GESTURE,name>
```
- Available gestures: OPEN, FIST, POINT, PEACE, OK
- Example: `<GESTURE,FIST>`

#### Reset to Neutral
```
<NEUTRAL>
```
- Returns all fingers to 90° position

#### Get Status
```
<STATUS>
```
- Returns: `<STATUS,ENABLED/DISABLED,thumb,index,middle,ring,pinky>`

#### Enable/Disable System
```
<ENABLE>
<DISABLE>
```
- DISABLE automatically returns hand to neutral position

### Responses

#### Acknowledgment
```
<ACK,command>
```

#### Error
```
<ERROR,message>
```

#### Status
```
<STATUS,state,thumb,index,middle,ring,pinky>
```

## Safety Features

1. **Timeout Protection**: If no commands received for 5 seconds, hand returns to neutral
2. **Position Constraints**: Servo angles constrained to 0-180°
3. **Smooth Movement**: Gradual position changes prevent jerky motion
4. **Emergency Disable**: `<DISABLE>` command immediately stops and neutralizes

## Integration with HBCM

The Motor Hand Pro is designed to receive control signals from the Multi-Heart-Model's physiological simulations. See the Python interface in `/src/hardware/motor_hand_interface.py` for integration examples.

### Example Use Cases

1. **Stress Response**: Hand grip strength modulated by simulated heart rate variability
2. **Autonomic Feedback**: Finger movements synchronized with neural oscillations
3. **Closed-loop Control**: Hand position sensors feed back into HBCM for bidirectional coupling

## Troubleshooting

**Servos not moving**:
- Check power supply connection
- Verify correct pin assignments
- Test with STATUS command

**Serial communication issues**:
- Confirm baud rate is 115200
- Check USB cable connection
- Verify correct COM port selected

**Erratic movements**:
- Ensure adequate power supply (servos draw significant current)
- Check for loose connections
- Reduce STEP_SIZE if movements too fast

## Testing

Use Arduino Serial Monitor (Tools → Serial Monitor) to test commands manually:
1. Set baud rate to 115200
2. Set line ending to "Newline"
3. Send test commands like `<STATUS>` or `<GRIP,50>`

## License

MIT License - Part of the Multi-Heart-Model project
