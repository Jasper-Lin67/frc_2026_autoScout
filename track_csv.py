import csv
import numpy as np
from collections import defaultdict

# ── Tunable values ─────────────────────────────────────────────────────────────

MAX_MOVE_DIST = 80  # pixels — how far a ball can move between frames and still be the same ball

# ──────────────────────────────────────────────────────────────────────────────


def match_detections(prev_tracks, detections):
    """
    Match new detections to existing tracks using nearest-centroid.
    Returns:
        updated:  {track_id: (x, y, r)}
        used_det: set of detection indices that were matched
    """
    updated  = {}
    used_det = set()

    for tid, (px, py, pr) in prev_tracks.items():
        best_dist = MAX_MOVE_DIST
        best_idx  = None

        for i, (x, y, r) in enumerate(detections):
            if i in used_det:
                continue
            dist = np.sqrt((x - px)**2 + (y - py)**2)
            if dist < best_dist:
                best_dist = dist
                best_idx  = i

        if best_idx is not None:
            used_det.add(best_idx)
            updated[tid] = detections[best_idx]

    return updated, used_det


def main(input_csv, output_csv):
    # load all detections grouped by frame
    frames = defaultdict(list)
    with open(input_csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            frames[int(row["frame"])].append((
                int(row["circle_index"]),
                float(row["x"]),
                float(row["y"]),
                float(row["r"]),
            ))

    max_frame   = max(frames.keys())
    prev_tracks = {}  # {track_id: (x, y, r)}
    next_id     = 1   # start at 1 to match DeepSort style
    output_rows = []

    for frame_idx in range(max_frame + 1):
        detections     = frames.get(frame_idx, [])
        det_coords     = [(x, y, r) for _, x, y, r in detections]
        circle_indices = [c for c, _, _, _ in detections]

        updated, used_det = match_detections(prev_tracks, det_coords)

        # assign new IDs to unmatched detections
        for i, det in enumerate(det_coords):
            if i not in used_det:
                updated[next_id] = det
                next_id += 1

        for i, (tid, (x, y, r)) in enumerate(updated.items()):
            circle_idx = circle_indices[i] if i < len(circle_indices) else i
            output_rows.append((frame_idx, circle_idx, x, y, tid))

        prev_tracks = updated
        print(f"Frame {frame_idx}/{max_frame}", end="\r", flush=True)

    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame_idx", "circle_idx", "x", "y", "track_id"])
        writer.writerows(output_rows)

    print(f"\nDone — {max_frame + 1} frames, {len(output_rows)} rows written to {output_csv}")


if __name__ == "__main__":
    main(
        input_csv  = "/home/jasper/Python projects/Data/DEBUG_csv_log.csv",
        output_csv = "/home/jasper/Python projects/Data/DEBUG_csv_tracked.csv",
    )