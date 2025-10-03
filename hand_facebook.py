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
action_cooldown = 0.1  # Reduced delay between actions for smoother response
last_gesture_state = None  # Previous gesture state
gesture_start_y = None  # Initial Y position when gesture starts
gesture_start_time = None  # Initial time when gesture starts
gesture_threshold = 0.01  # Reduced threshold for more sensitive movement detection
gesture_time_threshold = 0.05  # Reduced time threshold for quicker gesture recognition

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
            
            # Only process right hand gestures
            hand_label = "Unknown"
            if result.multi_handedness:
                for idx, handedness in enumerate(result.multi_handedness):
                    if idx < len(result.multi_hand_landmarks):
                        if handedness.classification[0].label == "Right":
                            hand_label = "Right"
                            break
            
            if hand_label == "Right":
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
                        
                        # Enhanced smooth scrolling with dynamic updates
                        base_multiplier = 30  # Increased base scroll amount per step
                        if abs(delta_y_from_start) > gesture_threshold and time_elapsed > gesture_time_threshold:
                            # Calculate scroll direction and intensity with enhanced sensitivity
                            scroll_intensity = abs(delta_y_from_start) * 15  # Increased scaling factor
                            scroll_direction = -1 if delta_y_from_start < 0 else 1  # Invert for natural feel
                            
                            # Calculate dynamic steps and amounts
                            num_steps = min(int(scroll_intensity * 8), 20)  # Increased to maximum 20 steps per frame
                            base_amount = max(int(base_multiplier * scroll_intensity), 8)  # Increased minimum amount
                            
                            # Calculate progressive scroll amounts for each step
                            scroll_steps = []
                            for step in range(num_steps):
                                # Progressive intensity - stronger in the middle of the gesture
                                step_intensity = 1.0 + abs(step - num_steps/2) / (num_steps/2)
                                step_amount = int(base_amount * step_intensity) * scroll_direction
                                scroll_steps.append(step_amount)
                            
                            # Create a sequence of dynamic scrolls
                            current_action = ("smooth_scroll", {
                                "steps": scroll_steps,
                                "start_y": y,  # Store current Y for continuous tracking
                                "base_amount": base_amount,
                                "direction": scroll_direction
                            })
                            
                            # Debug info
                            print(f"Steps: {num_steps}, Base amount: {base_amount}, Direction: {scroll_direction}")
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
                    
                    if isinstance(current_action, tuple) and current_action[0] == "smooth_scroll":
                        scroll_params = current_action[1]
                        scroll_steps = scroll_params["steps"]
                        start_y = scroll_params["start_y"]
                        base_amount = scroll_params["base_amount"]
                        initial_direction = scroll_params["direction"]
                        
                        # Execute dynamic scrolling with continuous tracking
                        total_amount = 0
                        current_y = y  # Get current hand position
                        
                        for step_amount in scroll_steps:
                            # Check for direction change during scroll
                            current_delta = current_y - start_y
                            if abs(current_delta) > gesture_threshold:
                                # Update direction based on current hand position
                                current_direction = -1 if current_delta < 0 else 1
                                if current_direction != initial_direction:
                                    # Adjust step amount if direction changed
                                    step_amount = -step_amount
                            
                            # Execute scroll with dynamic amount
                            adjusted_amount = int(step_amount * (1 + abs(current_delta) * 2))
                            pyautogui.scroll(adjusted_amount)
                            total_amount += adjusted_amount
                            
                            # Small delay for smoother scrolling
                            time.sleep(0.005)
                        
                        # Visual feedback with enhanced information
                        direction = "Up" if total_amount > 0 else "Down"
                        intensity = "Strong" if abs(total_amount) > base_amount * len(scroll_steps) else "Normal"
                        cv2.putText(frame, f"{intensity} {direction} Scroll: {len(scroll_steps)} steps", (50, 150), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 165, 0), 3)
                        
                        # Minimal cooldown for continuous scrolling
                        last_action_time = current_time - (action_cooldown * 0.8)  # Reduced cooldown further
                
                # Update gesture state
                last_gesture_state = current_action
                # Update hand position (only for right hand)
                prev_y = y
                prev_x = x

    else:
        prev_action = None  # If no hand detected, stop all actions

    # Display frame
    cv2.imshow("Hand Gesture Control", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
