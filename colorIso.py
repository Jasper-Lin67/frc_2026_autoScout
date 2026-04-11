import numpy as np
import cv2
def main(videoIn,videoOut):
    video = cv2.VideoCapture(videoIn)
    x1, y1 = 1120, 0
    x2, y2 = 1920, 700

    fps = video.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(videoOut, fourcc, fps, (x2 - x1, y2 - y1))

    if not out.isOpened():
        print("VideoWriter failed to open. Try a different codec or file extension.")
        video.release()
        exit()

    video.set(cv2.CAP_PROP_POS_MSEC, 5000)

    while True:
        _, preframe = video.read()

        roi = preframe[y1:y2, x1:x2]

        frame = cv2.bilateralFilter(roi, d=9, sigmaColor=75, sigmaSpace=75)
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        #hsv = cv2.GaussianBlur(hsv, (3, 3), 0)
        
        #hsv
        lower = np.array([10, 140, 40])
        upper = np.array([55, 255, 255])

        mask = cv2.inRange(hsv, lower, upper)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)


        _, thresh = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        display = frame.copy()
        for cnt in contours:
            if cv2.contourArea(cnt) > 150:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 3 and h > 3:
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 1)


        
        result = cv2.bitwise_and(frame, frame, mask=mask)
        cv2.imshow('Original Frame', cv2.resize(display, None, fx=1, fy=1, interpolation=cv2.INTER_LINEAR))
        cv2.imshow('Blue Mask', cv2.resize(mask, None, fx=1, fy=1, interpolation=cv2.INTER_LINEAR))
        cv2.imshow('Blue Filtered Result', cv2.resize(result, None, fx=1, fy=1, interpolation=cv2.INTER_LINEAR))

        out.write(result)

        if cv2.waitKey(int(1000/30)) & 0xFF == ord('q'):
            break 

    video.release()
    out.release()
    cv2.destroyAllWindows()
    print("Exiting...")
    
if __name__ == "__main__":
    main("data/1080.mp4",'processed/output.mp4')