import cv2
import mediapipe as mp
import uiautomator2 as u2
import time
import subprocess
import threading
import platform
import ctypes
import math

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Initialize uiautomator2 device connection
# You can connect via ADB or IP address
# For ADB: u2.connect() or u2.connect('device_id')
# For IP: u2.connect('192.168.1.100:5555')
try:
    device = u2.connect()  # Connect to the first available device
    print("Connected to Android device successfully")
except Exception as e:
    print(f"Failed to connect to Android device: {e}")
    print("Make sure your Android device is connected via ADB and USB debugging is enabled")
    exit(1)

# Configure webcam
cap = cv2.VideoCapture(0)

prev_x, prev_y = None, None
prev_action = None
last_action_time = 0
action_cooldown = 0.5  # 0.3 second delay between actions
last_gesture_state = None  # Previous gesture state
gesture_start_y = None  # Initial Y position when gesture starts
gesture_start_time = None  # Initial time when gesture starts
gesture_threshold = 0.02  # Minimum movement threshold
gesture_time_threshold = 0.2  # Minimum time to recognize gesture

# Get device screen dimensions for better scroll control
device_info = device.info
screen_width = device_info['displayWidth']
screen_height = device_info['displayHeight']
print(f"Device screen size: {screen_width}x{screen_height}")

# OK gesture tracking - can be used multiple times after TikTok is closed
ok_gesture_used = False
tiktok_closed_by_gesture = False

# Cross arms X gesture tracking for exit
cross_arms_detected = False


# Anti-sleep functionality
def prevent_sleep():
    """Prevent system from going to sleep while the application is running"""
    system = platform.system().lower()
    
    if system == "windows":
        # Windows: Prevent system sleep
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001 | 0x00000002)
            print("Windows sleep prevention enabled")
        except Exception as e:
            print(f"Failed to prevent Windows sleep: {e}")
    
    elif system == "darwin":  # macOS
        # macOS: Prevent system sleep using caffeinate
        try:
            subprocess.Popen(["caffeinate", "-d", "-i", "-m", "-u", "-t", "3600"], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("macOS sleep prevention enabled")
        except Exception as e:
            print(f"Failed to prevent macOS sleep: {e}")
    
    elif system == "linux":
        # Linux: Prevent system sleep using systemd
        try:
            subprocess.Popen(["systemd-inhibit", "--what=sleep", "--who=HandGestureControl", 
                            "--why=Hand gesture detection in progress", "sleep", "3600"], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Linux sleep prevention enabled")
        except Exception as e:
            print(f"Failed to prevent Linux sleep: {e}")

def restore_sleep():
    """Restore normal sleep behavior"""
    system = platform.system().lower()
    
    if system == "windows":
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
            print("Windows sleep behavior restored")
        except Exception as e:
            print(f"Failed to restore Windows sleep: {e}")
    
    # For macOS and Linux, the subprocess will automatically terminate
    # when the main process exits, so no explicit cleanup needed

# Global variables for text display
text_display = None
text_start_time = 0
text_duration = 0

def show_large_text(frame, text, duration=2000):
    """Show large text on frame for a specific duration without blocking"""
    global text_display, text_start_time, text_duration
    
    # Set text to display
    text_display = text
    text_start_time = time.time()
    text_duration = duration / 1000.0  # Convert ms to seconds
    
    # Draw text on current frame
    draw_text_on_frame(frame)

def draw_text_on_frame(frame):
    """Draw the current text on frame if it should be displayed"""
    global text_display, text_start_time, text_duration
    
    if text_display and (time.time() - text_start_time) < text_duration:
        # Calculate center position
        center_x = frame.shape[1] // 2
        center_y = frame.shape[0] // 2
        
        # Calculate text size for centering
        font_scale = 2
        thickness = 4
        (text_width, text_height), _ = cv2.getTextSize(text_display, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        
        # Center the text
        text_x = center_x - text_width // 2
        text_y = center_y + text_height // 2
        
        # Draw the text
        cv2.putText(frame, text_display, (text_x, text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 255), thickness)
    elif text_display and (time.time() - text_start_time) >= text_duration:
        # Clear text when duration is over
        text_display = None

# Function to handle TikTok operations in background
def handle_tiktok_operation(operation, frame):
    """Handle TikTok open/close operations in background thread"""
    def operation_thread():
        try:
            if operation == "open":
                device.app_start("com.ss.android.ugc.trill")
                print("TikTok opened successfully")
            elif operation == "close":
                device.app_stop("com.ss.android.ugc.trill")
                print("TikTok closed successfully")
        except Exception as e:
            print(f"Failed to {operation} TikTok: {e}")
    
    # Start operation in background
    thread = threading.Thread(target=operation_thread)
    thread.daemon = True
    thread.start()
    
    # Show text immediately without waiting
    if operation == "open":
        show_large_text(frame, "TIKTOK OPENED!", 1500)
    elif operation == "close":
        show_large_text(frame, "TIKTOK CLOSED!", 1500)

# Function to open TikTok using multiple methods
def open_tiktok():
    print("Opening TikTok...")
    
    # Method 1: Try different TikTok package names
    tiktok_packages = [
        "com.ss.android.ugc.trill",  # Your TikTok package
        "com.zhiliaoapp.musically",  # International TikTok
        "com.ss.android.ugc.aweme",  # Chinese TikTok
        "com.zhiliaoapp.musically.lite",  # TikTok Lite
    ]
    
    for package in tiktok_packages:
        try:
            print(f"Trying to open {package}...")
            device.app_start(package)
            time.sleep(3)
            
            # Check if app is running
            if device.app_current()['package'] == package:
                print(f"TikTok opened successfully: {package}")
                return True
        except Exception as e:
            print(f"Failed to open {package}: {e}")
            continue
    
    # Method 2: Try ADB commands
    adb_commands = [
        "adb shell am start -n com.ss.android.ugc.trill/.main.MainActivity",
        "adb shell monkey -p com.ss.android.ugc.trill -c android.intent.category.LAUNCHER 1",
        "adb shell am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER com.ss.android.ugc.trill",
        "adb shell am start -n com.zhiliaoapp.musically/.main.MainActivity",
        "adb shell am start -n com.ss.android.ugc.aweme/.main.MainActivity",
        "adb shell monkey -p com.zhiliaoapp.musically -c android.intent.category.LAUNCHER 1",
        "adb shell am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER com.zhiliaoapp.musically"
    ]
    
    for cmd in adb_commands:
        try:
            print(f"Trying ADB command: {cmd}")
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("TikTok opened successfully via ADB")
                time.sleep(3)
                return True
        except Exception as e:
            print(f"ADB command failed: {e}")
            continue
    
    print("Failed to open TikTok with all methods.")
    print("Please make sure TikTok is installed and open it manually.")
    return False

# Start hand gesture detection
print("\n" + "="*50)
print("TikTok Hand Control for Android")
print("="*50)
print("Use OK gesture (thumb + index finger) to open TikTok")
print("Use index + middle fingers to scroll")
print("Use cross arms X gesture (both hands with index fingers crossed) to close TikTok")
print("Use OK gesture to reopen TikTok after closing")
print("\nStarting hand gesture detection...")
print("Press 'q' to quit the program")
print("="*50)

# Enable sleep prevention
prevent_sleep()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Flip image for easier control
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Detect hands
    result = hands.process(rgb_frame)
    
    if result.multi_hand_landmarks:
        # Check for cross arms X gesture (both hands forming X shape)
        if len(result.multi_hand_landmarks) >= 2:
            # Get both hands
            left_hand = None
            right_hand = None
            
            for hand_idx, hand_landmarks in enumerate(result.multi_hand_landmarks):
                hand_label = "Unknown"
                if result.multi_handedness and hand_idx < len(result.multi_handedness):
                    hand_label = result.multi_handedness[hand_idx].classification[0].label
                
                if hand_label == "Left":
                    left_hand = hand_landmarks
                elif hand_label == "Right":
                    right_hand = hand_landmarks
            
            # Check cross arms X gesture (both hands with index fingers extended and crossed)
            if left_hand and right_hand:
                # Get wrist positions for both hands
                left_wrist = left_hand.landmark[mp_hands.HandLandmark.WRIST]
                right_wrist = right_hand.landmark[mp_hands.HandLandmark.WRIST]
                
                # Check if both hands have index fingers extended
                left_index_extended = left_hand.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y < left_hand.landmark[mp_hands.HandLandmark.INDEX_FINGER_DIP].y
                right_index_extended = right_hand.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y < right_hand.landmark[mp_hands.HandLandmark.INDEX_FINGER_DIP].y
                
                # Check if hands are crossed (left wrist is to the right of right wrist) - more sensitive
                hands_crossed = left_wrist.x > (right_wrist.x - 0.05)  # Allow some overlap
                
                # Check if hands are at similar height (forming X) - more sensitive
                hands_similar_height = abs(left_wrist.y - right_wrist.y) < 0.25
                
                # Cross arms X gesture: both index fingers extended, hands crossed, similar height
                cross_arms_gesture = (left_index_extended and right_index_extended and 
                                    hands_crossed and hands_similar_height)
                
                
                # Debug information for cross arms (simplified) - only show when detected
                # Removed debug text to reduce visual clutter
                
                if cross_arms_gesture and not cross_arms_detected:
                    cross_arms_detected = True
                    print("Cross arms X gesture detected - Closing TikTok...")
                    
                    # Handle TikTok close operation in background
                    handle_tiktok_operation("close", frame)
                    
                    # Update state
                    tiktok_closed_by_gesture = True
                    ok_gesture_used = False  # Reset OK gesture to allow reopening
                    
                    # Reset cross arms detection after a delay
                    time.sleep(1)
                    cross_arms_detected = False
                
        
        # Process each hand individually for normal gestures
        for hand_idx, hand_landmarks in enumerate(result.multi_hand_landmarks):
            # Get hand label for this specific hand
            hand_label = "Unknown"
            if result.multi_handedness and hand_idx < len(result.multi_handedness):
                hand_label = result.multi_handedness[hand_idx].classification[0].label
                confidence = result.multi_handedness[hand_idx].classification[0].score
            
            # Skip processing if left hand is detected (for normal gestures)
            if hand_label == "Left":
                cv2.putText(frame, "Left hand detected - Skipping", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                continue  # Skip this hand, but continue processing other hands
            
            # Only process right hand
            if hand_label == "Right":
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # Display hand information
                cv2.putText(frame, f"Hand: {hand_label}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # Get wrist position (for tracking movement)
                wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                x, y = wrist.x, wrist.y  # Normalized to image size
                # Get finger positions
                landmarks = hand_landmarks.landmark
                fingers = {
                    "thumb": landmarks[mp_hands.HandLandmark.THUMB_TIP],
                    "index": landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP],
                    "middle": landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
                    "ring": landmarks[mp_hands.HandLandmark.RING_FINGER_TIP],
                    "pinky": landmarks[mp_hands.HandLandmark.PINKY_TIP]
                }

                # Check finger state
                def is_finger_folded(finger_tip, finger_dip):
                    return finger_tip.y > finger_dip.y  # If fingertip is lower than middle joint → finger is folded

                # Check each finger state
                # Thumb: check horizontal (x) instead of vertical (y)
                thumb_folded = fingers["thumb"].x < landmarks[mp_hands.HandLandmark.THUMB_IP].x
                index_extended = fingers["index"].y < landmarks[mp_hands.HandLandmark.INDEX_FINGER_DIP].y
                middle_extended = fingers["middle"].y < landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_DIP].y
                ring_folded = is_finger_folded(fingers["ring"], landmarks[mp_hands.HandLandmark.RING_FINGER_DIP])
                pinky_folded = is_finger_folded(fingers["pinky"], landmarks[mp_hands.HandLandmark.PINKY_DIP])

                # Always show finger states
                cv2.putText(frame, f"Thumb: {'Extended' if not thumb_folded else 'Folded'}", (50, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(frame, f"Index: {'Extended' if index_extended else 'Folded'}", (50, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(frame, f"Middle: {'Extended' if middle_extended else 'Folded'}", (50, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(frame, f"Ring: {'Folded' if ring_folded else 'Extended'}", (50, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(frame, f"Pinky: {'Folded' if pinky_folded else 'Extended'}", (50, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
                # Right-hand cross gesture (index and thumb crossed): tuned per provided keypoints
                # - 3 fingers (middle/ring/pinky) folded
                # - Thumb roughly horizontal (tip-ip x distance large, y distance small)
                # - Index extended
                # - Thumb-Index tips very close together (crossing contact)
                # - Index tip is above thumb tip (index over thumb)
                # - Wrist->index and wrist->thumb lengths similar (overlap region)
                thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
                thumb_ip = landmarks[mp_hands.HandLandmark.THUMB_IP]
                index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                wrist_pt = landmarks[mp_hands.HandLandmark.WRIST]

                # Compute index finger direction using vector TIP - PIP
                index_pip_joint = landmarks[mp_hands.HandLandmark.INDEX_FINGER_PIP]
                dir_ix = index_tip.x - index_pip_joint.x
                dir_iy = index_tip.y - index_pip_joint.y
                index_dir_angle = math.degrees(math.atan2(dir_iy, dir_ix))  # deg, y axis downward
                # Map angle to a coarse direction label
                def classify_angle_deg(angle_deg: float) -> str:
                    if abs(angle_deg) <= 25:
                        return "right"
                    if abs(abs(angle_deg) - 180) <= 25:
                        return "left"
                    if -115 <= angle_deg <= -65:
                        return "up"
                    if 65 <= angle_deg <= 115:
                        return "down"
                    return "diagonal"
                index_dir_label = classify_angle_deg(index_dir_angle)
                # print(f"index_dir: angle={index_dir_angle:.1f}°, label={index_dir_label}")

                # Compute thumb direction angle using TIP - IP
                thumb_dir_x = thumb_tip.x - thumb_ip.x
                thumb_dir_y = thumb_tip.y - thumb_ip.y
                thumb_dir_angle = math.degrees(math.atan2(thumb_dir_y, thumb_dir_x))
                print(f"thumb_dir: angle={thumb_dir_angle:.1f}°")
                # Desired range for thumb angle
                # Thumb angle must be between -60 and -10 degrees
                thumb_angle_ok = (-60 <= thumb_dir_angle <= -10)

                # Show distance between thumb tip and index tip (normalized 0-1)
                dx_ti = thumb_tip.x - index_tip.x
                dy_ti = thumb_tip.y - index_tip.y
                dist_ti = math.hypot(dx_ti, dy_ti)
                cv2.putText(frame, f"Thumb-Index Dist: {dist_ti:.3f}", (50, 410),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

                # Determine states for heart gesture
                # Thumb horizontal to either side
                thumb_horizontal = (abs(thumb_tip.y - thumb_ip.y) < 0.07 and abs(thumb_tip.x - thumb_ip.x) > 0.03)
                middle_folded = not middle_extended
                three_folded = (middle_folded and ring_folded and pinky_folded)

                # Compute angle between vectors wrist->index and wrist->thumb
                v_ix = index_tip.x - wrist_pt.x
                v_iy = index_tip.y - wrist_pt.y
                v_tx = thumb_tip.x - wrist_pt.x
                v_ty = thumb_tip.y - wrist_pt.y
                dot = v_ix * v_tx + v_iy * v_ty
                norm_i = math.hypot(v_ix, v_iy)
                norm_t = math.hypot(v_tx, v_ty)
                angle_ok = False
                angle_deg = None
                if norm_i > 1e-6 and norm_t > 1e-6:
                    # Log lengths of wrist->index and wrist->thumb vectors
                    print(f"norm_i={norm_i:.4f}, norm_t={norm_t:.4f}")
                    cosang = max(-1.0, min(1.0, dot / (norm_i * norm_t)))
                    angle_deg = math.degrees(math.acos(cosang))
                    # Angle not strictly required for crossing; allow wide range
                    angle_ok = 15 <= angle_deg <= 100
                    # Display angle between index and thumb (degrees)
                    cv2.putText(frame, f"Thumb-Index Angle: {angle_deg:.1f} deg", (50, 440),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 2)

                # Distance between tips should be very small (crossing contact)
                tips_dx = thumb_tip.x - index_tip.x
                tips_dy = thumb_tip.y - index_tip.y
                tips_dist = math.hypot(tips_dx, tips_dy)
                # Log distance between thumb and index tips
                print(f"tips_dist={tips_dist:.4f}")
                dist_ok = tips_dist < 0.15

                # Index above thumb (visual crossing with index on top)
                index_above_thumb = index_tip.y < (thumb_tip.y - 0.005)

                # Similar reach length from wrist to tips (so they overlap spatially)
                len_i = norm_i
                len_t = norm_t
                length_similar = abs(len_i - len_t) < 0.12

                right_hand_heart_gesture = (
                    index_extended and three_folded and thumb_horizontal and thumb_angle_ok and
                    dist_ok and index_above_thumb and length_similar and angle_ok
                )

                # Ensure cooldown variables exist before logging
                current_time = time.time()
                in_cooldown = (current_time - last_action_time) < action_cooldown

                # Debug print all conditions used for right_hand_heart_gesture
                print(
                    f"[heart] index_ext={index_extended} three_folded={three_folded} "
                    f"thumb_horizontal={thumb_horizontal} tips_dist={tips_dist:.3f} dist_ok={dist_ok} "
                    f"index_above_thumb={index_above_thumb} len_i={norm_i:.3f} len_t={norm_t:.3f} "
                    f"length_similar={length_similar} angle={('NA' if angle_deg is None else f'{angle_deg:.1f}')} angle_ok={angle_ok}"
                )
                # Log app state flags affecting like action
                print(f"[state] ok_gesture_used={ok_gesture_used} tiktok_closed_by_gesture={tiktok_closed_by_gesture} in_cooldown={in_cooldown} thumb_angle_ok={thumb_angle_ok}")
             

                # Check OK gesture (thumb and index finger forming a circle)
                def is_ok_gesture():
                    # Calculate distance between thumb tip and index tip
                    thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
                    index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    distance = ((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)**0.5
                    
                    # OK gesture: thumb and index close together, other 3 fingers extended
                    return (distance < 0.05 and 
                            middle_extended == True and 
                            ring_folded == False and 
                            pinky_folded == False)
                
                # Check OK gesture
                ok_gesture = is_ok_gesture()
                
                # Debug: Display key information only
                if ok_gesture:
                    cv2.putText(frame, "OK GESTURE DETECTED", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                # Check if we're in cooldown period
                current_time = time.time()
                in_cooldown = (current_time - last_action_time) < action_cooldown
                
                # Handle right-hand heart gesture to like (double tap center), only when TikTok is open
                if (right_hand_heart_gesture and not in_cooldown and ok_gesture_used and not tiktok_closed_by_gesture):
                    try:
                        center_x = screen_width // 2
                        center_y = screen_height // 2
                        # Double tap in center
                        device.click(center_x, center_y)
                        time.sleep(0.1)
                        device.click(center_x, center_y)
                        show_large_text(frame, "LIKED! ❤", 1200)
                        last_action_time = current_time
                        last_gesture_state = "like"
                    except Exception as e:
                        print(f"Failed to like via heart gesture: {e}")

                # Handle OK gesture to open TikTok (can be used multiple times after TikTok is closed)
                if ok_gesture and not ok_gesture_used:
                    print("OK gesture detected - Opening TikTok...")
                    
                    # Handle TikTok open operation in background
                    handle_tiktok_operation("open", frame)
                    
                    # Update state
                    ok_gesture_used = True  # Mark as used
                    tiktok_closed_by_gesture = False  # Reset closed flag
                elif ok_gesture and ok_gesture_used and not tiktok_closed_by_gesture:
                    cv2.putText(frame, "TikTok already open", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                elif tiktok_closed_by_gesture:
                    cv2.putText(frame, "TikTok closed - Use OK gesture to reopen", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
                
                
                # Skip all gesture processing during cooldown
                if in_cooldown:
                    cv2.putText(frame, f"Cooldown: {action_cooldown - (current_time - last_action_time):.1f}s", 
                               (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    # Reset gesture state during cooldown
                    gesture_start_y = None
                    gesture_start_time = None
                    current_action = None
                else:
                    # Check actions only when not in cooldown
                    current_action = None

                    # **Scroll and Page Control: Only index and middle fingers extended**
                    gesture_active = (index_extended and middle_extended and 
                                     ring_folded and pinky_folded)
                    
                    if gesture_active:
                        # If gesture just started, save initial position and time
                        if gesture_start_y is None:
                            gesture_start_y = y
                            gesture_start_time = current_time
                            current_action = None
                            time_elapsed = 0
                        else:
                            # Calculate movement from initial position
                            delta_y_from_start = y - gesture_start_y
                            time_elapsed = current_time - gesture_start_time
                            
                            # Only recognize gesture after moving far enough and long enough
                            if abs(delta_y_from_start) > gesture_threshold and time_elapsed > gesture_time_threshold:
                                if delta_y_from_start < -gesture_threshold:  # Move up from initial position
                                    current_action = "scroll_down"
                                elif delta_y_from_start > gesture_threshold:  # Move down from initial position
                                    current_action = "scroll_up"
                            else:
                                current_action = None
                        
                        # Check horizontal swipe (still use immediate delta)
                        if prev_x is not None:
                            delta_x = x - prev_x
                            if delta_x > 0.02:  # Swipe right → scroll down
                                current_action = "scroll_down"
                            elif delta_x < -0.05:  # Swipe left → scroll up
                                current_action = "scroll_up"
                        
                        # Display simplified debug information
                        if gesture_start_y is not None:
                            delta_y_from_start = y - gesture_start_y
                            cv2.putText(frame, f"Scroll Delta: {delta_y_from_start:.3f}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                        
                        cv2.putText(frame, "SCROLL MODE", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    else:
                        # Reset when no gesture
                        current_action = None
                        gesture_start_y = None
                        gesture_start_time = None

                    # **Execute decisive actions with cooldown**
                    # Only execute action when:
                    # 1. Current gesture exists
                    # 2. Gesture is different from previous one (decisive)
                    # 3. Cooldown time has passed
                    if (current_action and 
                        current_action != last_gesture_state and 
                        (current_time - last_action_time) > action_cooldown):
                        
                        try:
                            if current_action == "scroll_down":
                                # Scroll down on Android device - increased swipe distance for smoother action
                                device.swipe(screen_width // 2, screen_height * 0.8, 
                                           screen_width // 2, screen_height * 0.2, 
                                           duration=0.05)
                                cv2.putText(frame, "Scroll Down", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 165, 0), 3)
                                last_action_time = current_time
                            elif current_action == "scroll_up":
                                # Scroll up on Android device - increased swipe distance for smoother action
                                device.swipe(screen_width // 2, screen_height * 0.2, 
                                           screen_width // 2, screen_height * 0.8, 
                                           duration=0.05)
                                cv2.putText(frame, "Scroll Up", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
                                last_action_time = current_time
                        except Exception as e:
                            print(f"Error executing scroll action: {e}")
                            cv2.putText(frame, f"Error: {str(e)[:30]}...", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    # Update gesture state
                    last_gesture_state = current_action
                
                # Update hand position (only for right hand)
                prev_y = y
                prev_x = x

    else:
        prev_action = None  # If no hand detected, stop all actions

    # Draw any pending text on frame
    draw_text_on_frame(frame)
    
    # Display frame
    cv2.imshow("Hand Gesture Control - Android", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Restore sleep behavior and cleanup
print("\nRestoring sleep behavior...")
restore_sleep()

# Close TikTok when exiting the application
print("Closing TikTok...")
try:
    device.app_stop("com.ss.android.ugc.trill")
    print("TikTok closed successfully")
except Exception as e:
    print(f"Failed to close TikTok: {e}")

cap.release()
cv2.destroyAllWindows()
