import argparse
import csv
import numpy as np
from collections import defaultdict
from deep_sort_realtime.deepsort_tracker import DeepSort

BOX_SIZE = 10  # half-width/height of the bounding box placed around each detected point (pixels)

def count_frames(path):
    frames = set()
    with open(path, newline="") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            frames.add(int(row[0]))
    return len(frames)

def iter_frames(path):
    current_frame = None
    current_rows = []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            frame = int(row[0])
            if frame != current_frame:
                if current_rows:
                    yield current_frame, current_rows
                current_frame = frame
                current_rows = []
            current_rows.append({
                "frame_idx":  frame,
                "circle_idx": row[1],
                "x":          float(row[2]),
                "y":          float(row[3]),
            })
    if current_rows:
        yield current_frame, current_rows

def run(
    input_path,
    output_path,
    max_age=30,   # how many frames a track can go undetected before being deleted
    min_hits=1,   # how many detections needed before a track is confirmed
    max_iou=10   # max IoU distance for matching detections to tracks (lower = stricter)
):
    tracker = DeepSort(
        max_age=max_age,
        n_init=min_hits,
        max_iou_distance=max_iou,
        embedder=None,
    )

    print("Counting frames...", flush=True)
    total_frames = count_frames(input_path)
    print(f"{total_frames} frames found. Starting tracking...", flush=True)

    print_every = 1  # print progress every N frames (increase to reduce terminal noise)

    total_rows = 0
    with open(output_path, "w", newline="") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=["frame_idx", "circle_idx", "x", "y", "track_id"])
        writer.writeheader()

        for i, (frame_num, rows) in enumerate(iter_frames(input_path)):
            if i % print_every == 0:
                print(f"Frame {i}/{total_frames} ({100*i//total_frames}%)", end="\r", flush=True)

            detections = [
                # bounding box: [left, top, width, height], confidence, class label
                ([r["x"] - BOX_SIZE, r["y"] - BOX_SIZE, BOX_SIZE * 2, BOX_SIZE * 2], 1.0, "point")
                for r in rows
            ]

            # random embeddings — no appearance model; tracking relies on position only
            embeds = [np.random.uniform(0.01, 0.1, 128).tolist() for _ in detections]

            tracks = tracker.update_tracks(detections, embeds=embeds)

            track_map = {}
            for track in tracks:
                if not track.is_confirmed():
                    continue
                l, t, r, b = track.to_ltrb()
                cx, cy = (l + r) / 2, (t + b) / 2
                track_map[(cx, cy)] = track.track_id

            for row in rows:
                x, y = row["x"], row["y"]
                best_id = "unmatched"
                best_dist = float("inf")  # nearest-centroid matching threshold (unbounded)
                for (tcx, tcy), tid in track_map.items():
                    dist = ((x - tcx) ** 2 + (y - tcy) ** 2) ** 0.5
                    if dist < best_dist:
                        best_dist = dist
                        best_id = tid

                writer.writerow({
                    "frame_idx":  row["frame_idx"],
                    "circle_idx": row["circle_idx"],
                    "x":          x,
                    "y":          y,
                    "track_id":   best_id,
                })
                total_rows += 1

    print(f"Done. {total_rows} rows written to {output_path}", flush=True)

