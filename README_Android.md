# Hand Gesture Control for Android

This project allows you to control Android devices using hand gestures detected through your webcam.

## Features

- **Hand Detection**: Uses MediaPipe to detect hand landmarks
- **Gesture Recognition**: Recognizes specific finger configurations for scrolling
- **Android Control**: Uses uiautomator2 to control Android devices
- **Real-time Processing**: Live webcam feed with gesture recognition

## Gesture Controls

- **Scroll Down**: Extend index and middle fingers, move hand up or swipe right
- **Scroll Up**: Extend index and middle fingers, move hand down
- **Gesture Requirements**: Only works with the right hand

## Prerequisites

### Android Device Setup

1. **Enable Developer Options**:
   - Go to Settings > About Phone
   - Tap "Build Number" 7 times
   - Developer Options will appear in Settings

2. **Enable USB Debugging**:
   - Go to Settings > Developer Options
   - Enable "USB Debugging"
   - Enable "Install via USB" (if available)

3. **Connect Device**:
   - Connect your Android device via USB
   - Allow USB debugging when prompted
   - Or connect via WiFi ADB (see below)

### WiFi ADB Connection (Optional)

If you prefer wireless connection:

1. Connect device via USB first
2. Run: `adb tcpip 5555`
3. Disconnect USB
4. Run: `adb connect <device_ip>:5555`
5. Update the connection code in the script if needed

## Installation

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements_android.txt
   ```

2. **Install uiautomator2 on Android Device**:
   ```bash
   python -m uiautomator2 init
   ```

3. **Verify Connection**:
   ```bash
   python -c "import uiautomator2 as u2; print(u2.connect().info)"
   ```

## Usage

1. **Connect your Android device** via USB or WiFi ADB
2. **Run the script**:
   ```bash
   python hand_detection_android.py
   ```
3. **Position your right hand** in front of the webcam
4. **Use gestures**:
   - Extend index and middle fingers
   - Move hand up/down to scroll
   - Press 'q' to quit

## Troubleshooting

### Connection Issues
- Ensure USB debugging is enabled
- Check ADB connection: `adb devices`
- Try reconnecting the device
- For WiFi connection, ensure both devices are on the same network

### Gesture Recognition Issues
- Ensure good lighting
- Keep hand clearly visible in webcam
- Use only the right hand
- Make deliberate movements

### Performance Issues
- Close unnecessary applications
- Ensure stable webcam connection
- Check device performance

## File Structure

- `hand_detection_android.py`: Main Android control script
- `requirements_android.txt`: Python dependencies
- `README_Android.md`: This documentation

## Customization

You can modify the following parameters in the script:

- `gesture_threshold`: Minimum movement to trigger gesture (default: 0.02)
- `gesture_time_threshold`: Minimum time to hold gesture (default: 0.1s)
- `action_cooldown`: Delay between actions (default: 0.3s)
- Scroll distance and speed in the swipe commands

## Notes

- The script requires a webcam for hand detection
- Only works with Android devices that support uiautomator2
- Make sure to grant necessary permissions on your Android device
- The script will automatically detect your device's screen dimensions
