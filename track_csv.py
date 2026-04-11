import argparse
import csv
import numpy as np
from similari import Sort, BoundingBox, PositionalMetricType

BOX_SIZE = 10  # half-width/height of the bounding box placed around each detected point (pixels)


def iter_frames(path):
    current_frame = None
    current_rows  = []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            frame = int(row[0])
            if frame != current_frame:
                if current_rows:
                    yield current_frame, current_rows
                current_frame = frame
                current_rows  = []
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
    max_age=30,    # how many frames a track survives without a detection before deletion
    min_hits=1,    # detections required before a track is confirmed (n_init in Sort)
    iou_threshold=0.3,  # IoU threshold — lower = stricter matching
    shards=4,      # parallelism shards; 1-2 for <100 objects, 4+ for more
):
    # IoU metric: detections must overlap by at least iou_threshold to match a track
    metric = PositionalMetricType.iou(threshold=iou_threshold)

    tracker = Sort(
        shards=shards,
        bbox_history=1,       # we read results every frame so history of 1 is enough
        max_idle_epochs=max_age,
        method=metric,
        min_confidence=0.1,   # minimum box confidence; all our boxes are 1.0 so this is a safe floor
        spatio_temporal_constraints=None,
    )

    print_every = 1  # print progress every N frames
    output_rows = []

    for i, (frame_num, rows) in enumerate(iter_frames(input_path)):
        if i % print_every == 0:
            print(f"Frame {i}...", end="\r", flush=True)

        xs = np.array([r["x"] for r in rows])
        ys = np.array([r["y"] for r in rows])

        # Build Similari BoundingBox list: (left, top, width, height) with confidence
        # Each detection is paired with its index so we can match results back to rows
        boxes = [
            (
                BoundingBox.new_with_confidence(
                    x - BOX_SIZE,   # left
                    y - BOX_SIZE,   # top
                    BOX_SIZE * 2,   # width
                    BOX_SIZE * 2,   # height
                    1.0             # confidence
                ).as_xyaah(),
                idx   # custom_object_id — we pass the detection index for easy lookup
            )
            for idx, (x, y) in enumerate(zip(xs, ys))
        ]

        # predict() runs the Kalman filter + Hungarian matching entirely in Rust
        tracks = tracker.predict(boxes)

        # Build a lookup: detection index → track_id
        # custom_object_id is the idx we passed in above
        det_to_track = {}
        for t in tracks:
            if t.custom_object_id is not None:
                det_to_track[t.custom_object_id] = t.id

        for idx, row in enumerate(rows):
            tid = det_to_track.get(idx, "unmatched")
            output_rows.append((row["frame_idx"], row["circle_idx"], row["x"], row["y"], tid))

        # Clear wasted tracks to free memory (we don't need history)
        tracker.clear_wasted()

    print(f"\nWriting {len(output_rows)} rows...", flush=True)
    with open(output_path, "w", newline="") as out_f:
        writer = csv.writer(out_f)
        writer.writerow(["frame_idx", "circle_idx", "x", "y", "track_id"])
        writer.writerows(output_rows)

    print(f"Done. {len(output_rows)} rows written to {output_path}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",         required=True)
    parser.add_argument("--output",        required=True)
    parser.add_argument("--max_age",       type=int,   default=30)    # idle frames before track dies
    parser.add_argument("--min_hits",      type=int,   default=1)     # hits to confirm a track
    parser.add_argument("--iou_threshold", type=float, default=0.3)   # IoU match threshold
    parser.add_argument("--shards",        type=int,   default=4)     # parallelism
    parser.add_argument("--box_size",      type=int,   default=10)    # bounding box half-size
    args = parser.parse_args()

    BOX_SIZE = args.box_size
    run(args.input, args.output, args.max_age, args.min_hits, args.iou_threshold, args.shards)