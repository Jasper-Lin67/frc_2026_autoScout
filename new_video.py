import cv2
import both as clean_video
import pandas
import numpy
import detect_circle as scan

def main(CSV_IN, MP4_OUT):
    xdim = clean_video.x2 - clean_video.x1
    ydim = clean_video.y2 - clean_video.y1

    df      = pandas.read_csv(CSV_IN)
    grouped = df.groupby('frame')

    max_frame = scan.frame_idx

    fourcc = cv2.VideoWriter_fourcc(*"avc1")  # avc1 = H.264, best mp4 compatibility
    fps    = 60
    out    = cv2.VideoWriter(MP4_OUT, fourcc, fps, (xdim, ydim))

    if not out.isOpened():
        # fall back to mp4v if avc1 is not available on this system
        print("avc1 unavailable, falling back to mp4v")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out    = cv2.VideoWriter(MP4_OUT, fourcc, fps, (xdim, ydim))

    if not out.isOpened():
        raise IOError(f"VideoWriter failed to open: {MP4_OUT} — check dimensions ({xdim}x{ydim}) and path")

    for frame_idx in range(max_frame + 1):
        frame = numpy.zeros((ydim, xdim, 3), dtype=numpy.uint8)

        print(f"{frame_idx / (max_frame + 1) * 100:.1f}%", end="\r", flush=True)

        if frame_idx in grouped.groups:
            circles = grouped.get_group(frame_idx)
            for _, row in circles.iterrows():
                center = (int(row['x']), int(row['y']))
                radius = int(row['r'])
                cv2.circle(frame, center, radius, (0, 255, 0), 2)

        out.write(frame)

        if frame_idx == 0:
            print(f"Writer backend: {out.getBackendName()}")
            print(f"Frame written, writer open: {out.isOpened()}")

        cv2.imshow('Result', frame.copy())
        cv2.waitKey(1)

    out.release()
    cv2.destroyAllWindows()
    print(f"Video saved to {MP4_OUT} ({max_frame} frames)")