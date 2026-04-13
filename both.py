import numpy as np
import cv2

def main(videoIn, videoOut):
    video = cv2.VideoCapture(videoIn)
    global x1, x2, y1, y2
    x1, y1 = 1120, 0
    x2, y2 = 1920, 700

    fps    = video.get(cv2.CAP_PROP_FPS)
    width  = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Input: {width}x{height} @ {fps}fps")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out    = cv2.VideoWriter(videoOut, fourcc, fps, (width, height))  # match full frame size
    if not out.isOpened():
        raise IOError(f"VideoWriter failed to open: {videoOut}")

    subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=False)
    lower = np.array([10,  60,  80])
    upper = np.array([55, 255, 255])

    while True:
        ret, frame = video.read()
        if not ret or frame is None:
            break

        fg_mask       = subtractor.apply(frame)
        kernel        = np.ones((3, 3), np.uint8)
        fg_mask       = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN,  kernel, iterations=1)
        fg_mask       = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        motion_result = cv2.bitwise_and(frame, frame, mask=fg_mask)
        motion_result = cv2.GaussianBlur(motion_result, (5, 5), 0)
        hsv           = cv2.cvtColor(motion_result, cv2.COLOR_BGR2HSV)
        color_mask    = cv2.inRange(hsv, lower, upper)
        color_mask    = cv2.GaussianBlur(color_mask, (5, 5), 0)
        _, thresh     = cv2.threshold(color_mask, 127, 255, cv2.THRESH_BINARY)
        contours, _   = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        display = frame.copy()
        for cnt in contours:
            if cv2.contourArea(cnt) > 1000:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 3 and h > 3:
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 1)

        # convert single channel mask to 3 channel BGR for the writer
        result = cv2.bitwise_and(frame, frame, mask=color_mask)

        cv2.imshow('Tracking',    cv2.resize(display,    None, fx=1, fy=1, interpolation=cv2.INTER_LINEAR))
        cv2.imshow('Motion Mask', cv2.resize(fg_mask,    None, fx=1, fy=1, interpolation=cv2.INTER_LINEAR))
        cv2.imshow('Color Mask',  cv2.resize(color_mask, None, fx=1, fy=1, interpolation=cv2.INTER_LINEAR))
        cv2.imshow('Result',      cv2.resize(result,     None, fx=1, fy=1, interpolation=cv2.INTER_LINEAR))

        out.write(result)  # result is already 3 channel BGR

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video.release()
    out.release()
    cv2.destroyAllWindows()
    print("Exiting...")


if __name__ == "__main__":
    main("/home/jasper/Python projects/Data/original.mp4",
         "/home/jasper/Python projects/Data/originalTEST123out.mp4")