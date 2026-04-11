import csv
from collections import defaultdict

# ── Tunable value ─────────────────────────────────────────────────────────────

MIN_FRAMES = 30  # discard any ball that appears in fewer than this many frames

# ──────────────────────────────────────────────────────────────────────────────


def load_tracks(path):
    """
    Read the DeepSort output CSV and group rows by track_id.

    Returns a dict:
        {
            track_id: [
                {"frame_idx": int, "x": float, "y": float},
                ...
            ],
            ...
        }
    Rows are stored in frame order (the CSV is assumed to be frame-sorted).
    """
    tracks = defaultdict(list)

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            track_id = row["track_id"]

            # Skip detections that were never matched to a track
            if track_id == "unmatched":
                continue

            tracks[track_id].append({
                "frame_idx": int(row["frame_idx"]),
                "x":         float(row["x"]),
                "y":         float(row["y"]),
            })

    return tracks


def filter_short_tracks(tracks, min_frames):
    """
    Remove any track that appears in fewer than min_frames unique frames.

    Returns a filtered dict with the same structure as the input.
    """
    filtered = {}
    removed  = 0

    for track_id, detections in tracks.items():
        unique_frames = len(set(d["frame_idx"] for d in detections))

        if unique_frames >= min_frames:
            filtered[track_id] = detections
        else:
            removed += 1

    print(f"  Kept   {len(filtered)} tracks")
    print(f"  Removed {removed} tracks (fewer than {min_frames} frames)")
    return filtered


def write_output(tracks, path):
    """
    Write one row per unique ball ID.

    Each row contains:
        track_id        — the stable DeepSort ID for this ball
        num_frames      — how many frames the ball was detected in
        first_frame     — first frame it appeared
        last_frame      — last frame it appeared
        x_0,y_0 ...     — (x, y) position for every detection, in frame order

    Because different balls appear for different numbers of frames, the
    position columns are dynamic: x_0/y_0, x_1/y_1, x_2/y_2, ...
    up to the maximum track length across all surviving balls.
    """

    # Find the longest track so we know how many position columns to create
    max_detections = max(len(dets) for dets in tracks.values())

    # Build header: fixed columns first, then paired x/y columns
    fixed_cols    = ["track_id", "num_frames", "first_frame", "last_frame"]
    position_cols = []
    for i in range(max_detections):
        position_cols.append(f"frame_{i}")
        position_cols.append(f"x_{i}")
        position_cols.append(f"y_{i}")

    fieldnames = fixed_cols + position_cols

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        # Sort rows by track_id so output is deterministic
        for track_id in sorted(tracks.keys(), key=lambda t: int(t) if str(t).isdigit() else t):
            detections = tracks[track_id]

            # Sort detections by frame just in case they arrived out of order
            detections = sorted(detections, key=lambda d: d["frame_idx"])

            unique_frames = len(set(d["frame_idx"] for d in detections))
            first_frame   = detections[0]["frame_idx"]
            last_frame    = detections[-1]["frame_idx"]

            row = {
                "track_id":   track_id,
                "num_frames": unique_frames,
                "first_frame": first_frame,
                "last_frame":  last_frame,
            }

            # Write each detection as a set of frame/x/y columns
            for i, det in enumerate(detections):
                row[f"frame_{i}"] = det["frame_idx"]
                row[f"x_{i}"]     = det["x"]
                row[f"y_{i}"]     = det["y"]

            # Columns beyond this ball's track length are left empty automatically
            writer.writerow(row)

    print(f"  Written to: {path}")


def main(IN_PATH,OUT_PATH): 
    print(f"Loading tracks from: {IN_PATH}")
    tracks = load_tracks(IN_PATH)
    print(f"  Found {len(tracks)} unique track IDs (including unmatched)")

    print(f"Filtering tracks shorter than {MIN_FRAMES} frames...")
    tracks = filter_short_tracks(tracks, MIN_FRAMES)

    print("Writing output CSV...")
    write_output(tracks, OUT_PATH)

    print("Done.")