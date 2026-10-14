


import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import math

# ==========================================
# Gesture-Based Presentation Controller
# Version 3 - No Drawing Mode
# ==========================================

CAMERA_INDEX = 0
HOLD_TIME = 0.5
COOLDOWN = 1.0

enabled = False
last_action_time = 0
candidate = None
candidate_start = time.time()
action_done = False
pinch_was_active = False

# MediaPipe setup
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=1,
    min_detection_confidence=0.65,
    min_tracking_confidence=0.65
)

# Screen and camera setup
screen_w, screen_h = pyautogui.size()
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    cap.release()
    cap = cv2.VideoCapture(0)

if not cap.isOpened():
    hands.close()
    raise SystemExit("Cannot open webcam")

print("Gesture Controller started")
print("Open palm: Unlock | Fist: Lock")
print("Two fingers: Next | Four fingers: Previous")
print("Index: Pointer | Thumbs up/down: Slideshow")
print("Press ESC in the camera window to exit")


def finger_states(lm):
    """Detect four fingers using their tip and middle-joint positions."""
    tips = [8, 12, 16, 20]
    joints = [6, 10, 14, 18]

    return [
        lm[tip].y < lm[joint].y
        for tip, joint in zip(tips, joints)
    ]


def hand_gesture(lm):
    """
    Return a gesture label.
    Finger extension depends on camera angle and hand orientation.
    """
    index, middle, ring, little = finger_states(lm)

    thumb_tip = lm[4]
    thumb_ip = lm[3]
    thumb_mcp = lm[2]

    # Normalized palm width
    palm_width = max(
        math.hypot(lm[5].x - lm[17].x,
                   lm[5].y - lm[17].y),
        0.001
    )

    thumb_index_distance = math.hypot(
        lm[4].x - lm[8].x,
        lm[4].y - lm[8].y
    )

    # Pinch: thumb and index finger close together
    if thumb_index_distance < palm_width * 0.25:
        return "PINCH"

    # Thumb spread for an open palm
    thumb_spread = (
        math.hypot(
            lm[4].x - lm[5].x,
            lm[4].y - lm[5].y
        ) > palm_width * 0.8
    )

    # Open palm
    if index and middle and ring and little and thumb_spread:
        return "OPEN PALM"

    # Four fingers, thumb folded
    if index and middle and ring and little and not thumb_spread:
        return "FOUR FINGERS"

    # Two fingers
    if index and middle and not ring and not little:
        return "TWO FINGERS"

    # Three fingers: not assigned an action
    if index and middle and ring and not little:
        return "THREE FINGERS"

    # Index finger only
    if index and not middle and not ring and not little:
        return "INDEX"

    # Thumb orientation for thumbs-up/down
    other_fingers_folded = not any(
        [index, middle, ring, little]
    )

    if other_fingers_folded:
        if thumb_tip.y < thumb_ip.y < thumb_mcp.y:
            return "THUMBS UP"

        if thumb_tip.y > thumb_ip.y:
            return "THUMBS DOWN"

        return "FIST"

    return "UNKNOWN"


def release_mouse():
    try:
        pyautogui.mouseUp()
    except Exception:
        pass


def perform_action(gesture):
    """Execute a confirmed gesture once."""
    global enabled, last_action_time

    now = time.time()

    # Lock immediately; do not require an enabled state
    if gesture == "FIST":
        enabled = False
        release_mouse()
        print("Controls locked")
        return

    # Unlock
    if gesture == "OPEN PALM":
        enabled = True
        print("Controls unlocked")
        return

    if not enabled:
        return

    if now - last_action_time < COOLDOWN:
        return

    if gesture == "TWO FINGERS":
        pyautogui.press("right")
        print("Next slide")

    elif gesture == "FOUR FINGERS":
        pyautogui.press("left")
        print("Previous slide")

    elif gesture == "THUMBS UP":
        pyautogui.press("f5")
        print("Start slideshow")

    elif gesture == "THUMBS DOWN":
        pyautogui.press("esc")
        print("End slideshow")

    elif gesture == "PINCH":
        pyautogui.click()
        print("Mouse click")

    else:
        return

    last_action_time = now


try:
    while True:
        success, frame = cap.read()

        if not success:
            print("Cannot read webcam frame")
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        gesture = "NO HAND"

        if result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]
            lm = hand.landmark

            mp_draw.draw_landmarks(
                frame, hand, mp_hands.HAND_CONNECTIONS
            )

            gesture = hand_gesture(lm)

            # Pointer movement
            if enabled and gesture == "INDEX":
                h, w, _ = frame.shape

                x = int(lm[8].x * w)
                y = int(lm[8].y * h)

                sx = int(np.interp(
                    x, [0, w], [50, screen_w - 50]
                ))
                sy = int(np.interp(
                    y, [0, h], [50, screen_h - 50]
                ))

                pyautogui.moveTo(sx, sy, duration=0.01)

            # Stable gesture confirmation
            if gesture != candidate:
                candidate = gesture
                candidate_start = time.time()
                action_done = False

            stable = time.time() - candidate_start >= HOLD_TIME

            if stable and not action_done:
                if gesture in (
                    "OPEN PALM", "FIST",
                    "TWO FINGERS", "FOUR FINGERS",
                    "THUMBS UP", "THUMBS DOWN"
                ):
                    perform_action(gesture)
                    action_done = True

            # Pinch click only once per pinch
            if enabled and gesture == "PINCH":
                if not pinch_was_active:
                    if time.time() - last_action_time >= COOLDOWN:
                        pyautogui.click()
                        last_action_time = time.time()
                        print("Mouse click")

                pinch_was_active = True
            else:
                pinch_was_active = False

        else:
            candidate = None
            action_done = False
            pinch_was_active = False
            release_mouse()

        # Camera status display
        status = "UNLOCKED" if enabled else "LOCKED"
        color = (0, 255, 0) if enabled else (0, 0, 255)

        cv2.putText(
            frame, "Controls: " + status,
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
            0.7, color, 2
        )

        cv2.putText(
            frame, "Gesture: " + gesture,
            (10, 65), cv2.FONT_HERSHEY_SIMPLEX,
            0.65, (255, 255, 0), 2
        )

        cv2.imshow("Gesture Controller", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

finally:
    release_mouse()
    cap.release()
    hands.close()
    cv2.destroyAllWindows()
    print("Controller closed safely")
