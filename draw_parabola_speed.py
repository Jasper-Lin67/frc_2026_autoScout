import cv2
import csv
import numpy as np

# ── Tunable values ─────────────────────────────────────────────────────────────

DRAW_COLOUR   = (0, 255, 0)   # colour of the parabola curve
ID_COLOUR     = (0, 255, 255) # colour of the track ID label
SPEED_COLOUR  = (0, 165, 255) # colour of the speed label
POINT_DENSITY = 20            # how many points to sample along each parabola curve

# ──────────────────────────────────────────────────────────────────────────────


def load_parabolas(csv_path):
    """
    Load the parabola CSV. Skipped/failed fits are excluded.
    Returns list of dicts with track_id, frame range, coefficients.
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


def compute_max_speed(parabola, fps):
    """
    Estimate max speed of a ball by sampling its position at every frame
    and computing the largest frame-to-frame displacement.

    Position along x is linearly interpolated between start_x and end_x
    across the frame range. y is computed from the parabola equation.

    Returns max speed in pixels/second.
    """
    a, b, c   = parabola["a"], parabola["b"], parabola["c"]
    x_start   = parabola["start_x"]
    x_end     = parabola["end_x"]
    first     = parabola["first_frame"]
    last      = parabola["last_frame"]
    n_frames  = last - first + 1

    if n_frames < 2:
        return 0.0

    # interpolate x position at each frame
    xs = np.linspace(x_start, x_end, n_frames)
    ys = a * xs**2 + b * xs + c

    # compute frame-to-frame distance
    dx = np.diff(xs)
    dy = np.diff(ys)
    distances = np.sqrt(dx**2 + dy**2)  # pixels per frame

    max_speed_px_per_frame  = float(np.max(distances))
    max_speed_px_per_second = max_speed_px_per_frame * fps

    return max_speed_px_per_second


def draw_parabola(frame, parabola, max_speed):
    """
    Draw the parabola curve, track ID, and max speed onto the frame.
    """
    a, b, c  = parabola["a"], parabola["b"], parabola["c"]
    x_start  = parabola["start_x"]
    x_end    = parabola["end_x"]
    track_id = parabola["track_id"]

    xs = np.linspace(x_start, x_end, POINT_DENSITY)
    ys = a * xs**2 + b * xs + c

    points = [(int(round(x)), int(round(y))) for x, y in zip(xs, ys)]
    h, w   = frame.shape[:2]

    for j in range(len(points) - 1):
        x1, y1 = points[j]
        x2, y2 = points[j + 1]
        if not (0 <= x1 < w and 0 <= y1 < h and 0 <= x2 < w and 0 <= y2 < h):
            continue
        cv2.line(frame, (x1, y1), (x2, y2), DRAW_COLOUR, 1)

    # draw track ID and max speed at start of parabola
    sx = int(round(x_start))
    sy = int(round(a * x_start**2 + b * x_start + c))

    font, scale, thickness = cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1

    id_label    = f"id:{track_id}"
    speed_label = f"{max_speed:.1f}px/s"

    (tw, th), _ = cv2.getTextSize(id_label, font, scale, thickness)
    cv2.rectangle(frame, (sx - 1, sy - th - 5), (sx + tw + 1, sy - 3), (0, 0, 0), -1)
    cv2.putText(frame, id_label, (sx, sy - 4), font, scale, ID_COLOUR, thickness)

    (sw, sh), _ = cv2.getTextSize(speed_label, font, scale, thickness)
    cv2.rectangle(frame, (sx - 1, sy - th - sh - 10), (sx + sw + 1, sy - th - 6), (0, 0, 0), -1)
    cv2.putText(frame, speed_label, (sx, sy - th - 7), font, scale, SPEED_COLOUR, thickness)


def overlay_parabolas(input_video_path, csv_path, output_video_path):
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

    # pre-compute max speed for every parabola
    speeds = {p["track_id"]: compute_max_speed(p, fps) for p in parabolas}

    # print speed summary
    print("\n── Max speeds ───────────────────────────────")
    for p in sorted(parabolas, key=lambda x: speeds[x["track_id"]], reverse=True):
        print(f"  track {p['track_id']:>6} : {speeds[p['track_id']]:>8.1f} px/s")
    overall_max = max(speeds.values()) if speeds else 0
    print(f"  Fastest ball  : {overall_max:.1f} px/s")
    print("─────────────────────────────────────────────\n")

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        for p in parabolas:
            if p["first_frame"] <= frame_idx <= p["last_frame"]:
                draw_parabola(frame, p, speeds[p["track_id"]])

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