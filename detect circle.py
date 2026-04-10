import cv2
import numpy as np

def find_circles(img):
    output = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 1)

    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=10,
        param1=100,
        param2=10,
        minRadius=2,
        maxRadius=11
    )

    positions = []
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for x, y, r in circles[0]:
            cv2.circle(output, (x, y), r, (0, 255, 0), 1)
            cv2.circle(output, (x, y), 2, (0, 0, 255), 2)
            positions.append((x, y, r))

    return output, positions


img = cv2.imread("test2.png")
output, positions = find_circles(img)

print(f"Found {len(positions)} circles:")
for i, (x, y, r) in enumerate(positions):
    print(f"  Circle {i+1}: center=({x}, {y}), radius={r}")

cv2.imshow('Detected Circles', output)
cv2.waitKey(0)
cv2.destroyAllWindows()