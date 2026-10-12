Gesture-Based Touchless Presentation Controller

Overview:
A Python-based computer vision project that uses hand gestures to control presentation slides through a webcam.

Features:
- Real-time hand tracking
- Open-palm unlock and fist lock
- Two fingers to move to the next slide
- Four fingers to move to the previous slide
- Index-finger pointer control
- Webcam-based gesture recognition

Technologies:
- Python
- OpenCV
- MediaPipe
- PyAutoGUI
- NumPy

Requirements:
- Python 3.11 recommended
- A working webcam
- Windows computer
- PowerPoint or compatible presentation software

Installation:

1. Clone or download this repository.
2. Open a terminal in the project folder.
3. Install dependencies:

   `python -m pip install -r requirements.txt`

4. Run the program:

   `python gestures.py`

5. Show an open palm to unlock gesture controls.

Press Esc in the webcam window to exit.

Limitations:
This application runs locally on a computer with a webcam. Gesture recognition may vary with lighting, hand orientation, and camera quality. Pointer and drawing behavior depends on the active application.

Author:

Lathika
