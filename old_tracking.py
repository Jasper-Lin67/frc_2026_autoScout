import cv2
import numpy as np

def main(video_path, video_out):
    # 1. Setup Video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    ret, frame = cap.read()
    if not ret: return

    # Setup Video Writer
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_out, fourcc, fps, (width, height))

    # Setup Tracker
    tracker = cv2.TrackerCSRT.create()

    # Manually box your robot
    roi = cv2.selectROI("Select Robot", frame, False)
    if roi == (0, 0, 0, 0): # Handle user canceling selection
        return
    tracker.init(frame, roi)
    cv2.destroyWindow("Select Robot")

    # 2. Setup Kalman Filter
    kf = cv2.KalmanFilter(4, 2)
    kf.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
    kf.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
    kf.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03

    paths = []

    print("Processing video... Press 'q' to stop.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        # 3. Kalman Predict
        predicted = kf.predict()
        pred_x, pred_y = int(predicted[0][0]), int(predicted[1][0])

        # 4. Tracker Update
        success, box = tracker.update(frame)

        if success:
            (x, y, w, h) = [int(v) for v in box]
            center_x, center_y = int(x + w / 2), int(y + h / 2)
            
            kf.correct(np.array([[np.float32(center_x)], [np.float32(center_y)]]))
            current_pos = (center_x, center_y)
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, "TRACKING", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        else:
            current_pos = (pred_x, pred_y)
            cv2.putText(frame, "LOST - PREDICTING", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # 5. Draw the Red Path
        paths.append(current_pos)
        # Optimization: only draw recent path if video is very long to prevent lag
        for i in range(1, len(paths)):
            cv2.line(frame, paths[i - 1], paths[i], (0, 0, 255), 2)

        # --- SAVE THE FRAME ---
        out.write(frame)

        cv2.imshow("Original Tracker + Kalman", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    out.release() # CRITICAL: If you don't release, the video file will be corrupted
    cv2.destroyAllWindows()
    print(f"Video saved to: {video_out}")
    
if __name__ == "__main__":
    main("/home/jasper/Python projects/Data/noise_out.mp4", "/home/jasper/Python projects/Data/robot_out.mp4")