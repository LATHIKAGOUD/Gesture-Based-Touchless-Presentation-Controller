
import cv2
import mediapipe as mp
import pyautogui
import time
import numpy as np

# -------------------------
# Configuration
# -------------------------
COOLDOWN = 0.8
INDEX_HOLD_DURATION = 1.0

last_action_time = 0
index_hold_start = None
enable_control = False  # Start locked

# -------------------------
# MediaPipe setup
# -------------------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# -------------------------
# PyAutoGUI setup
# -------------------------
screen_w, screen_h = pyautogui.size()
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01

# -------------------------
# Webcam setup
# -------------------------
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
time.sleep(2)

if not cap.isOpened():
    print("ERROR: Cannot open webcam.")
    hands.close()
    raise SystemExit

success, test_frame = cap.read()

if not success:
    print("ERROR: Webcam opened but cannot provide frames.")
    cap.release()
    hands.close()
    raise SystemExit

print("Webcam frame received successfully.")

if not cap.isOpened():
    print("ERROR: Cannot access webcam.")
    print("Check camera permissions or close other apps using the camera.")
    hands.close()
    raise SystemExit

print("Webcam started successfully.")
print("Show an open palm to unlock gesture control.")
print("Press ESC in the camera window to exit.")

# -------------------------
# Helper function
# -------------------------
def fingers_up(hand):
    tips = [4, 8, 12, 16, 20]
    fingers = []

    # Thumb: works best with the expected hand orientation
    fingers.append(
        hand.landmark[4].x < hand.landmark[3].x
    )

    # Index, middle, ring and little fingers
    for i in range(1, 5):
        fingers.append(
            hand.landmark[tips[i]].y
            < hand.landmark[tips[i] - 2].y
        )

    return fingers


# -------------------------
# Main loop
# -------------------------
try:
    while True:
        success, frame = cap.read()

        if not success:
            print("Cannot read webcam frame.")
            break

        # Mirror the webcam image
        frame = cv2.flip(frame, 1)

        # Convert BGR to RGB for MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        gesture_name = "No hand detected"

        if result.multi_hand_landmarks:
            for hand in result.multi_hand_landmarks:

                mp_draw.draw_landmarks(
                    frame,
                    hand,
                    mp_hands.HAND_CONNECTIONS
                )

                fingers = fingers_up(hand)

                # Gesture definitions
                open_palm = fingers == [
                    True, True, True, True, True
                ]

                fist = fingers == [
                    False, False, False, False, False
                ]

                index_only = fingers == [
                    False, True, False, False, False
                ]

                two_fingers = fingers == [
                    False, True, True, False, False
                ]

                four_fingers = fingers == [
                    False, True, True, True, True
                ]

                # Index finger position
                index_tip = hand.landmark[8]
                h, w, _ = frame.shape

                x = int(index_tip.x * w)
                y = int(index_tip.y * h)

                cv2.circle(
                    frame, (x, y), 8, (0, 0, 255), -1
                )

                # Lock / unlock
                if open_palm:
                    enable_control = True

                elif fist:
                    enable_control = False

                if not enable_control:
                    gesture_name = "LOCKED"

                    # Release any held mouse/key state
                    pyautogui.mouseUp()
                    pyautogui.keyUp("ctrl")
                    index_hold_start = None

                else:
                    # Next slide: two fingers
                    if two_fingers:
                        gesture_name = "Next Slide"

                        if time.time() - last_action_time > COOLDOWN:
                            pyautogui.press("right")
                            last_action_time = time.time()

                    # Previous slide: four fingers
                    elif four_fingers:
                        gesture_name = "Previous Slide"

                        if time.time() - last_action_time > COOLDOWN:
                            pyautogui.press("left")
                            last_action_time = time.time()

                    # Pointer and drawing mode
                    elif index_only:
                        gesture_name = "Pointer / Draw"

                        screen_x = np.interp(
                            x, [0, w], [50, screen_w - 50]
                        )
                        screen_y = np.interp(
                            y, [0, h], [50, screen_h - 50]
                        )

                        pyautogui.moveTo(
                            int(screen_x),
                            int(screen_y),
                            duration=0.01
                        )

                        if index_hold_start is None:
                            index_hold_start = time.time()

                        if (
                            time.time() - index_hold_start
                            >= INDEX_HOLD_DURATION
                        ):
                            gesture_name = "Drawing Mode"

                        # Ctrl + mouse hold for drawing in
                        # applications that support this action
                        pyautogui.keyDown("ctrl")
                        pyautogui.mouseDown()

                    else:
                        index_hold_start = None
                        pyautogui.mouseUp()
                        pyautogui.keyUp("ctrl")

                        if open_palm:
                            gesture_name = "Unlocked"
                        elif fist:
                            gesture_name = "Locked"
                        else:
                            gesture_name = "Ready"

                # Show lock status and gesture
                status = (
                    "CONTROL ENABLED"
                    if enable_control
                    else "CONTROL LOCKED"
                )

                status_color = (
                    (0, 255, 0)
                    if enable_control
                    else (0, 0, 255)
                )

                cv2.putText(
                    frame, status, (10, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, status_color, 2
                )

                cv2.putText(
                    frame, "Gesture: " + gesture_name, (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65, (255, 255, 0), 2
                )

        else:
            # If the hand disappears, release held inputs
            pyautogui.mouseUp()
            pyautogui.keyUp("ctrl")
            index_hold_start = None

        # Always display the webcam frame
        cv2.imshow("Gesture Controller", frame)

        # Press ESC to exit
        if cv2.waitKey(1) & 0xFF == 27:
            break

except KeyboardInterrupt:
    print("\nProgram stopped by user.")

finally:
    # Release all held inputs and close resources
    try:
        pyautogui.mouseUp()
        pyautogui.keyUp("ctrl")
    except Exception:
        pass

    cap.release()
    hands.close()
    cv2.destroyAllWindows()

    print("Gesture controller closed safely.")
