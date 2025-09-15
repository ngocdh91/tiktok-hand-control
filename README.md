# Hand Gesture Control for TikTok/Douyin

## 🎯 Purpose
This project uses hand gestures to control TikTok/Douyin scrolling in a natural and convenient way. Instead of touching the screen, you can use hand gestures to scroll through videos.

## ✨ Key Features

### 🖐️ Supported Hand Gestures
- **Index + Middle fingers extended**: Activate control mode
- **Ring + Pinky fingers folded**: Complete gesture
- **Ignore thumb**: Flexible hand position

### 📱 Control Actions
- **Swipe up**: Scroll down (Page Down + Scroll -200)
- **Swipe down**: Scroll up (Scroll 200) 
- **Swipe right**: Scroll down (Page Down + Scroll -200)

### 🎮 Technical Features
- **Right hand only**: Avoid conflicts with left hand
- **Initial position tracking**: Accurate direction detection from starting point
- **0.3s cooldown**: Prevent action spam, smooth scrolling
- **High sensitivity**: Quick response to small gestures

## 🛠️ Installation

### System Requirements
- Python 3.7+
- macOS (for pyautogui)
- Webcam

### Install Dependencies
```bash
pip install opencv-python
pip install mediapipe
pip install pyautogui
```

## 🎥 Video Demo

Watch the project in action:

[![Hand Gesture Control Demo](https://img.youtube.com/vi/TbRj-IEGmFo/0.jpg)](https://youtu.be/TbRj-IEGmFo)

*Click the image above to watch the demo on YouTube*

## 🚀 Usage

### Run the Program
```bash
python hand_detection_action.py
```

### How to Use
1. **Open TikTok/Douyin** in your browser
2. **Run the program** - camera window will appear
3. **Place your right hand** in the frame
4. **Extend index + middle fingers**, fold ring + pinky fingers
5. **Swipe your hand** in the desired direction:
   - Swipe up/right → Scroll to next video
   - Swipe down → Scroll to previous video

### Exit Program
- Press `q` key in the camera window

## 📊 Debug Information

The program displays debug information on screen:
- **Hand: Right/Left**: Detected hand type
- **Start Y**: Initial Y position when gesture starts
- **Current Y**: Current Y position
- **Delta**: Movement distance from initial position
- **Time**: Elapsed time

## ⚙️ Customization

### Adjust Sensitivity
```python
gesture_threshold = 0.02  # Minimum movement threshold (decrease = more sensitive)
gesture_time_threshold = 0.1  # Minimum time to recognize gesture
action_cooldown = 0.3  # Delay between actions (seconds)
```

### Adjust Scroll
```python
pyautogui.scroll(-200)  # Scroll down 200 pixels
pyautogui.scroll(200)   # Scroll up 200 pixels
```

## 🎯 Applications

### Perfect for
- **TikTok/Douyin scrolling** without touching screen
- **Remote control** when hands are dirty or wet
- **Hands-free experience** while watching videos
- **For lazy people** - minimal hand movement required

### Compatibility
- ✅ TikTok (tiktok.com)
- ✅ Douyin (douyin.com) 
- ✅ YouTube (youtube.com)
- ✅ Any website that supports scrolling

## 🔧 Code Structure

### Main Components
- **MediaPipe Hands**: Hand detection and tracking
- **OpenCV**: Video processing and display
- **PyAutoGUI**: Mouse and keyboard control
- **Gesture Recognition**: Gesture detection logic

### Workflow
1. **Capture video** from webcam
2. **Detect hands** using MediaPipe
3. **Identify hand type** (left/right)
4. **Track position** and time
5. **Recognize gestures** based on movement
6. **Execute corresponding actions**

## 🐛 Troubleshooting

### Common Issues
- **Hand not detected**: Ensure good lighting, hand in frame
- **Inaccurate gestures**: Adjust `gesture_threshold`
- **Action spam**: Increase `action_cooldown`
- **Up/down confusion**: Ensure tracking from initial position

### Debug
- Enable debug display to see tracking information
- Check console for errors
- Adjust sensitivity based on environment

## 📝 License

MIT License - Free to use for personal and commercial purposes.

## 🤝 Contributing

All contributions are welcome! Please create issues or pull requests.

## 📞 Contact

If you have issues or suggestions, please create an issue on GitHub.

---

**Enjoy your hands-free TikTok/Douyin experience! 🎉**
