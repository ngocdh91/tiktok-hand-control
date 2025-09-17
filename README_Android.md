# Hand Gesture Control for Android

This project allows you to control Android devices using hand gestures detected through your webcam, specifically designed for TikTok scrolling.

## Features

- **Hand Detection**: Uses MediaPipe to detect hand landmarks
- **Gesture Recognition**: Recognizes specific finger configurations for scrolling and app control
- **Android Control**: Uses uiautomator2 to control Android devices
- **Real-time Processing**: Live webcam feed with gesture recognition
- **Smart Cooldown**: Prevents excessive actions during cooldown periods
- **Left Hand Filtering**: Completely ignores left hand gestures

## Gesture Controls

### **Scroll Gestures** (Index + Middle fingers extended):
- **Scroll Down**: 
  - Move hand up from initial position
  - Swipe hand right
- **Scroll Up**: 
  - Move hand down from initial position  
  - Swipe hand left

### **App Control Gestures**:
- **Open TikTok**: OK gesture (thumb + index finger forming circle + 3 other fingers extended)
  - Works anytime, even during scroll cooldown
  - Can be used multiple times after TikTok is closed
- **Close TikTok**: Cross arms X gesture (both hands with index fingers crossed)
  - Only closes TikTok, not the application
  - Allows reopening with OK gesture

### **Gesture Requirements**:
- **Right Hand Only**: Left hand is completely ignored for normal gestures
- **Cross Arms**: Requires both hands for TikTok control
- **Precise Finger Control**: Specific finger configurations required

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
2. **Open TikTok manually** on your Android device (or use OK gesture later)
3. **Run the script**:
   ```bash
   python hand_detection_android.py
   ```
4. **Position your hands** in front of the webcam
5. **Use gestures**:
   - **OK gesture** (thumb + index + 3 other fingers): Open TikTok app
   - **Index + Middle fingers**: Scroll up/down
   - **Cross arms X** (both hands with index fingers): Close TikTok
   - **Move hand up/down or left/right** to scroll
   - Press 'q' to quit application

## Gesture Details

### **OK Gesture (Open TikTok)**:
- **Finger Position**: Thumb and index finger forming a circle
- **Other Fingers**: Middle, ring, and pinky fingers extended
- **Cooldown**: Can be used multiple times after TikTok is closed
- **Works Anytime**: Even during scroll cooldown periods

### **Cross Arms X Gesture (Close TikTok)**:
- **Finger Position**: Both hands with index fingers extended
- **Hand Position**: Left hand to the right of right hand (crossed)
- **Height**: Both hands at similar height (forming X shape)
- **Sensitivity**: Allows some overlap and height variation
- **Function**: Closes TikTok only, not the application

### **Scroll Gestures**:
- **Finger Position**: Index and middle fingers extended, others folded
- **Vertical Movement**: Move hand up (scroll down) or down (scroll up)
- **Horizontal Movement**: Swipe right (scroll down) or left (scroll up)
- **Cooldown**: 0.5 seconds between scroll actions
- **Threshold**: Minimum movement required to trigger action

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

### **Gesture Parameters**:
- `gesture_threshold`: Minimum movement to trigger gesture (default: 0.02)
- `gesture_time_threshold`: Minimum time to hold gesture (default: 0.2s)
- `action_cooldown`: Delay between scroll actions (default: 0.5s)

### **Swipe Parameters**:
- `duration`: Swipe speed (default: 0.05s - very fast)
- Swipe distance: 60% of screen height (80% to 20%)
- Horizontal thresholds: Right swipe > 0.02, Left swipe < -0.05

### **OK Gesture Parameters**:
- `distance < 0.05`: Thumb and index finger proximity
- Multiple uses: Can be used after TikTok is closed
- Package name: `com.ss.android.ugc.trill` (TikTok)

### **Cross Arms Parameters**:
- `hands_crossed`: Left wrist x > (right wrist x - 0.05) - allows overlap
- `hands_similar_height`: Height difference < 0.25 - more sensitive
- Cooldown: 2 seconds between cross arms gestures

### **Debug Information** (Optimized):
- Simplified debug display for better performance
- Key gesture detection status only
- Cooldown timer display
- Essential movement information

## Notes

- The script requires a webcam for hand detection
- Only works with Android devices that support uiautomator2
- Make sure to grant necessary permissions on your Android device
- The script will automatically detect your device's screen dimensions
- **Left hand is completely ignored** for normal gestures - only right hand gestures are processed
- **Cross arms requires both hands** for TikTok control
- **TikTok package**: `com.ss.android.ugc.trill` (update if different)
- **No auto-launch**: TikTok must be opened manually or via OK gesture
- **Smart cooldown**: Prevents excessive actions during cooldown periods
- **Performance optimized**: Reduced debug information for smoother operation
- **TikTok control**: Can open/close TikTok without exiting the application
