import numpy as np
import cv2
def main(videoIn,videoOut):
    video = cv2.VideoCapture(videoIn)
    video.set(cv2.CAP_PROP_POS_MSEC, 3500)
    x1, y1 = 0, 0
    x2, y2 = 1920, 1080

    fps = video.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(videoOut, fourcc, fps, (x2 - x1, y2 - y1))

    ret, bg = video.read()
    roi = bg[y1:y2, x1:x2]
    bgframe = cv2.bilateralFilter(roi, d=9, sigmaColor=75, sigmaSpace=75)
    bggray = cv2.cvtColor(bgframe, cv2.COLOR_BGR2GRAY)

    while True:
        _, preframe = video.read()

        roi = preframe[y1:y2, x1:x2]
        frame = cv2.bilateralFilter(roi, d=9, sigmaColor=75, sigmaSpace=75)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        diff = cv2.absdiff(bggray, gray)

        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        thresh = cv2.GaussianBlur(thresh, (5, 5), 0)

        result = cv2.bitwise_and(frame, frame, mask=thresh)
        
        cv2.imshow("og", frame)
        cv2.imshow("dif", diff)
        cv2.imshow("result", result)

        out.write(result)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break 

    video.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main("data/1080.mp4",'staticbgremoval.mp4')