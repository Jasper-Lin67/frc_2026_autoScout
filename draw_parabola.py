import cv2
import csv
import numpy as np

# ── Tunable values ─────────────────────────────────────────────────────────────

DRAW_COLOUR    = (0, 255, 0)   # colour of the parabola curve
ID_COLOUR      = (0, 255, 255) # colour of the track ID label
POINT_DENSITY  = 20         # how many points to sample along each parabola curve

# ──────────────────────────────────────────────────────────────────────────────


def load_parabolas(csv_path):
    """
    Load the parabola CSV produced by fit_parabola.py.
    Returns a list of dicts, one per ball, containing:
        track_id, first_frame, last_frame, start_x, start_y,
        end_x, end_y, a, b, c  (parabola coefficients)
    Skipped or failed fits are excluded.
    """
    parabolas = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["curvature_a"] == "":
                continue
            parabolas.append({
                "track_id":    row["track_id"],
                "first_frame": int(row["first_frame"]),
                "last_frame":  int(row["last_frame"]),
                "start_x":     float(row["start_x"]),
                "end_x":       float(row["end_x"]),
                "a":           float(row["curvature_a"]),
                "b":           float(row["slope_b"]),
                "c":           float(row["intercept_c"]),
            })
    return parabolas


def draw_parabola(frame, parabola):
    """
    Draw a parabola curve onto a frame by sampling POINT_DENSITY
    points between start_x and end_x and connecting them with lines.
    Also draws the track ID at the start point.
    """

    a, b, c   = parabola["a"], parabola["b"], parabola["c"]
    x_start   = parabola["start_x"]
    x_end     = parabola["end_x"]
    track_id  = parabola["track_id"]

    # Sample x values across the ball's horizontal range
    xs = np.linspace(x_start, x_end, POINT_DENSITY)
    ys = a * xs**2 + b * xs + c

    # Convert to integer pixel coordinates and draw connected line segments
    points = [(int(round(x)), int(round(y))) for x, y in zip(xs, ys)]
    for j in range(len(points) - 1):
        x1, y1 = points[j]
        x2, y2 = points[j + 1]

        # Skip segments where either point is outside the frame
        h, w = frame.shape[:2]
        if not (0 <= x1 < w and 0 <= y1 < h and 0 <= x2 < w and 0 <= y2 < h):
            continue

        cv2.line(frame, (x1, y1), (x2, y2), DRAW_COLOUR, 1)

    # Draw track ID label at the start of the parabola
    label     = f"id:{track_id}"
    font      = cv2.FONT_HERSHEY_SIMPLEX
    scale     = 0.4
    thickness = 1
    sx, sy    = int(round(x_start)), int(round(a * x_start**2 + b * x_start + c))
    (tw, th), _ = cv2.getTextSize(label, font, scale, thickness)
    cv2.rectangle(frame, (sx - 1, sy - th - 5), (sx + tw + 1, sy - 3), (0, 0, 0), -1)
    cv2.putText(frame, label, (sx, sy - 4), font, scale, ID_COLOUR, thickness)


def overlay_parabolas(input_video_path, csv_path, output_video_path):
    """
    For each frame in the video, draw every parabola whose track was
    active during that frame (i.e. first_frame <= frame_idx <= last_frame).
    """
    parabolas = load_parabolas(csv_path)
    print(f"Loaded {len(parabolas)} fitted parabolas")

    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {input_video_path}")

    fps    = cap.get(cv2.CAP_PROP_FPS)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Draw every parabola that was active during this frame
        for p in parabolas:
            if p["first_frame"] <= frame_idx <= p["last_frame"]:
                draw_parabola(frame, p)
                
        writer.write(frame)
        frame_idx += 1
        print(f"  Processed {frame_idx} frames...", end="\r", flush=True)


    cap.release()
    writer.release()
    print(f"\nDone — {frame_idx} frames processed")
    print(f"  Output: {output_video_path}")


if __name__ == "__main__":
    overlay_parabolas(
        input_video_path="/home/jasper/Python projects/Data/original.mp4",
        csv_path="/home/jasper/Python projects/Data/csv_parabola_out.csv",
        output_video_path="/home/jasper/Python projects/Data/parabola_overlay.mp4",
    )