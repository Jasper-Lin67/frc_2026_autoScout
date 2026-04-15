import cv2
import numpy as np

# 1. Setup Video and Tracker
video_path = "/home/jasper/Python projects/Data/red_out.mp4" 
cap = cv2.VideoCapture(video_path)
tracker = cv2.TrackerCSRT.create()

ret, frame = cap.read()
if not ret: exit()

# Manually box your robot
roi = cv2.selectROI("Select Robot", frame, False)
tracker.init(frame, roi)
cv2.destroyWindow("Select Robot")

# 2. Setup Kalman Filter (The Guessing Math)
kf = cv2.KalmanFilter(4, 2)
kf.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
kf.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
kf.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03

paths = []

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    # 3. Kalman Predict (Where we think it is)
    predicted = kf.predict()
    pred_x, pred_y = int(predicted[0][0]), int(predicted[1][0])

    # 4. Tracker Update (Where it actually is)
    success, box = tracker.update(frame)

    if success:
        (x, y, w, h) = [int(v) for v in box]
        center_x, center_y = int(x + w / 2), int(y + h / 2)
        
        # Correct the Kalman Filter with real data
        kf.correct(np.array([[np.float32(center_x)], [np.float32(center_y)]]))
        current_pos = (center_x, center_y)
        
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, "TRACKING", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    else:
        # If hidden, use the Kalman "Guess"
        current_pos = (pred_x, pred_y)
        cv2.putText(frame, "LOST - PREDICTING", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # 5. Draw the Red Path
    paths.append(current_pos)
    for i in range(1, len(paths)):
        cv2.line(frame, paths[i - 1], paths[i], (0, 0, 255), 2)

    cv2.imshow("Original Tracker + Kalman", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()