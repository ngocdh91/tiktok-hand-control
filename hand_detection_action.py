import cv2
import mediapipe as mp
import pyautogui
import time

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)


# Configure webcam
cap = cv2.VideoCapture(0)
screen_width, screen_height = pyautogui.size()

prev_x, prev_y = None, None
prev_action = None
last_action_time = 0
action_cooldown = 0.3  # 0.3 second delay between actions
last_gesture_state = None  # Previous gesture state
gesture_start_y = None  # Initial Y position when gesture starts
gesture_start_time = None  # Initial time when gesture starts
gesture_threshold = 0.02  # Minimum movement threshold
gesture_time_threshold = 0.1  # Minimum time to recognize gesture

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
        for hand_landmarks in result.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Detect left/right hand
            hand_label = "Unknown"
            if result.multi_handedness:
                for idx, handedness in enumerate(result.multi_handedness):
                    if idx < len(result.multi_hand_landmarks):
                        hand_label = handedness.classification[0].label
                        confidence = handedness.classification[0].score
                        break
            
            # Display hand information
            cv2.putText(frame, f"Hand: {hand_label}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Get wrist position (for tracking movement)
            wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
            x, y = wrist.x, wrist.y  # Normalized to image size
            
            # Only process gestures when right hand is detected
            if hand_label == "Right":
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
                
                # Debug: Display finger states
                cv2.putText(frame, f"Thumb: {'Folded' if thumb_folded else 'Extended'}", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(frame, f"Index: {'Extended' if index_extended else 'Folded'}", (50, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(frame, f"Middle: {'Extended' if middle_extended else 'Folded'}", (50, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(frame, f"Ring: {'Folded' if ring_folded else 'Extended'}", (50, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(frame, f"Pinky: {'Folded' if pinky_folded else 'Extended'}", (50, 370), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

                # Check actions
                current_action = None

                # **Scroll and Page Control: Only index and middle fingers extended**
                gesture_active = (index_extended and middle_extended and 
                                 ring_folded and pinky_folded)
                
                if gesture_active:
                    current_time = time.time()
                    
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
                                current_action = "page_down"
                            elif delta_y_from_start > gesture_threshold:  # Move down from initial position
                                current_action = "page_up"
                        else:
                            current_action = None
                    
                    # Check horizontal swipe (still use immediate delta)
                    if prev_x is not None:
                        delta_x = x - prev_x
                        if delta_x > 0.015:  # Swipe right → page down
                            current_action = "page_down"
                    
                    # Display debug information
                    if gesture_start_y is not None:
                        delta_y_from_start = y - gesture_start_y
                        cv2.putText(frame, f"Start Y: {gesture_start_y:.3f}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                        cv2.putText(frame, f"Current Y: {y:.3f}", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                        cv2.putText(frame, f"Delta: {delta_y_from_start:.3f}", (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                        cv2.putText(frame, f"Time: {time_elapsed:.2f}s", (50, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                    
                    cv2.putText(frame, "Gesture Mode - Index and middle fingers extended", (50, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                else:
                    # Reset when no gesture
                    current_action = None
                    gesture_start_y = None
                    gesture_start_time = None

                # **Execute decisive actions with cooldown**
                current_time = time.time()
                
                # Only execute action when:
                # 1. Current gesture exists
                # 2. Gesture is different from previous one (decisive)
                # 3. Cooldown time has passed
                if (current_action and 
                    current_action != last_gesture_state and 
                    (current_time - last_action_time) > action_cooldown):
                    
                    if current_action == "page_down":
                        # pyautogui.press('pagedown')
                        pyautogui.scroll(-20)
                        cv2.putText(frame, "Page Down + Scroll -200", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 165, 0), 3)
                        last_action_time = current_time
                    elif current_action == "page_up":
                        # pyautogui.press('pageup')
                        pyautogui.scroll(20)
                        cv2.putText(frame, "Page Up + Scroll 200", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
                        last_action_time = current_time
                
                # Update gesture state
                last_gesture_state = current_action
            else:
                # If not right hand, display message and reset state
                cv2.putText(frame, "Please use RIGHT hand", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                prev_action = None

            # Update hand position (for both right and left hands)
            prev_y = y
            prev_x = x

    else:
        prev_action = None  # If no hand detected, stop all actions

    # Display frame
    # cv2.imshow("Hand Gesture Control", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
