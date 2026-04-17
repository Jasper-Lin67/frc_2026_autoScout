import cv2
import numpy as np
from pathlib import Path
from boxmot.trackers import BotSort


# ── Per-object display colours (box + path trail) ────────────────────────────
COLORS = [
    (50,  255,  50),   # Object 1 – green
    (50,  200, 255),   # Object 2 – gold
    (255,  80, 200),   # Object 3 – pink/magenta
]
WINDOW = "BoT-SORT Multi-Tracker"


# ── Helper factories ──────────────────────────────────────────────────────────

def make_bot_sort(fps: float) -> BotSort:
    return BotSort(
        reid_weights=Path("osnet_x0_25_msmt17.pt"),  # unused when with_reid=False
        device="cpu",
        half=False,
        with_reid=False,
        frame_rate=max(1, int(fps)),
    )


def make_kalman() -> cv2.KalmanFilter:
    kf = cv2.KalmanFilter(4, 2)
    kf.measurementMatrix = np.array([[1, 0, 0, 0],
                                      [0, 1, 0, 0]], np.float32)
    kf.transitionMatrix  = np.array([[1, 0, 1, 0],
                                      [0, 1, 0, 1],
                                      [0, 0, 1, 0],
                                      [0, 0, 0, 1]], np.float32)
    kf.processNoiseCov   = np.eye(4, dtype=np.float32) * 0.03
    return kf


def init_object(frame: np.ndarray, roi: tuple, preserve_paths=None) -> dict:
    """Create a fresh tracking slot, optionally inheriting an existing path."""
    x, y, w, h = roi
    csrt = cv2.TrackerCSRT.create()
    csrt.init(frame, roi)
    kf = make_kalman()
    cx, cy = x + w // 2, y + h // 2
    kf.statePost    = np.array([[np.float32(cx)], [np.float32(cy)],
                                 [0.0],            [0.0]], np.float32)
    kf.errorCovPost = np.eye(4, dtype=np.float32)
    return {
        "csrt":     csrt,
        "kf":       kf,
        "paths":    preserve_paths if preserve_paths is not None else [],
        "last_box": (x, y, w, h),
    }


# ── ROI helpers ───────────────────────────────────────────────────────────────

def select_roi(title: str, frame: np.ndarray):
    """Open selectROI window in full screen; return (x,y,w,h) or None on cancel."""
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    roi = cv2.selectROI(title, frame, fromCenter=False, showCrosshair=True)
    cv2.destroyWindow(title)
    return None if roi == (0, 0, 0, 0) else roi


def annotate_existing(frame: np.ndarray, slots: list) -> np.ndarray:
    """Draw current boxes on a copy of frame (used during selection screens)."""
    preview = frame.copy()
    for i, s in enumerate(slots):
        if s is not None:
            x, y, w, h = s["last_box"]
            cv2.rectangle(preview, (x, y), (x + w, y + h), COLORS[i], 2)
            cv2.putText(preview, f"OBJ {i+1}", (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLORS[i], 2)
    return preview


# ── Track→detection matching ──────────────────────────────────────────────────

def match_tracks_to_dets(det_centers, tracks):
    """Greedy nearest-centre match."""
    matched   = {}
    used      = set()
    for i, (dcx, dcy, dw, dh) in enumerate(det_centers):
        threshold = max(dw, dh) ** 2   
        best_dist, best_j = float("inf"), None
        for j, t in enumerate(tracks):
            if j in used:
                continue
            tcx, tcy = (t[0] + t[2]) / 2, (t[1] + t[3]) / 2
            d2 = (tcx - dcx) ** 2 + (tcy - dcy) ** 2
            if d2 < best_dist:
                best_dist, best_j = d2, j
        if best_j is not None and best_dist < threshold:
            matched[i] = tracks[best_j]
            used.add(best_j)
    return matched


# ── HUD overlay ───────────────────────────────────────────────────────────────

def draw_hud(frame: np.ndarray, slots: list, pending, height: int):
    active_count = sum(1 for s in slots if s is not None)

    if pending == "delete":
        hint  = "DELETE which object?  1 / 2 / 3   (ESC = cancel)"
        color = (30, 120, 255)
    else:
        parts = ["Q=quit"]
        for i, s in enumerate(slots):
            if s is not None:
                parts.append(f"{i+1}=redraw OBJ{i+1}")
        if active_count < 3:
            parts.append("A=add")
        if active_count > 0:
            parts.append("D=delete")
        hint  = "  |  ".join(parts)
        color = (190, 190, 190)

    cv2.putText(frame, hint, (10, height - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1, cv2.LINE_AA)


# ── Main ──────────────────────────────────────────────────────────────────────

def main(video_path: str, video_out: str):

    # 1. Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    ret, first_frame = cap.read()
    if not ret:
        print("Error: Could not read first frame.")
        return

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS) or 30.0
    out    = cv2.VideoWriter(video_out, cv2.VideoWriter_fourcc(*"mp4v"),
                             fps, (width, height))

    # 2. Select initial objects
    print("Select 1-3 objects.  ENTER = confirm box.  ESC = done selecting.")
    slots = [None, None, None]

    for i in range(3):
        preview = annotate_existing(first_frame, slots)
        roi = select_roi(
            f"Select Object {i+1}  (ENTER=confirm  ESC=stop adding)", preview)
        if roi is None:
            break
        slots[i] = init_object(first_frame, roi)

    if all(s is None for s in slots):
        print("No objects selected - exiting.")
        cap.release()
        return

    # 3. BoT-SORT warm-up
    bot_sort = make_bot_sort(fps)
    init_dets = []
    for s in slots:
        if s is not None:
            x, y, w, h = s["last_box"]
            init_dets.append([x, y, x + w, y + h, 1.0, 0])
    bot_sort.update(np.array(init_dets, dtype=np.float32), first_frame)

    # ── Initialize Tracking Window in Full Screen ───────────────────────────
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(WINDOW, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # 4. Main tracking loop
    pending_action = None
    print("\nTracking started.")
    print("  1 / 2 / 3  =  redraw that object's box  (path trail preserved)")
    print("  A          =  add a new object (up to 3)")
    print("  D          =  delete an object")
    print("  Q          =  quit\n")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # ── CSRT + Kalman predict
        csrt_boxes = []
        kf_preds   = []

        for slot in slots:
            if slot is None:
                csrt_boxes.append(None)
                kf_preds.append(None)
                continue

            pred = slot["kf"].predict()
            kf_preds.append((int(pred[0][0]), int(pred[1][0])))

            ok, box = slot["csrt"].update(frame)
            if ok:
                b = tuple(int(v) for v in box)
                slot["last_box"] = b
                csrt_boxes.append(b)
            else:
                csrt_boxes.append(None)

        # ── Build detection array for BoT-SORT
        dets_list          = []
        active_indices     = []
        active_det_centers = []

        for i, slot in enumerate(slots):
            if slot is None:
                continue
            active_indices.append(i)
            box = csrt_boxes[i] if csrt_boxes[i] is not None else slot["last_box"]
            x, y, w, h = box
            conf = 1.0 if csrt_boxes[i] is not None else 0.4
            dets_list.append([x, y, x + w, y + h, conf, 0])
            active_det_centers.append((x + w / 2, y + h / 2, w, h))

        all_dets = (np.array(dets_list, dtype=np.float32)
                    if dets_list else np.empty((0, 6), dtype=np.float32))

        tracks    = bot_sort.update(all_dets, frame)
        track_map = match_tracks_to_dets(active_det_centers, tracks)

        # ── Draw boxes, labels, path trails
        for active_idx, slot_idx in enumerate(active_indices):
            slot  = slots[slot_idx]
            color = COLORS[slot_idx]
            t     = track_map.get(active_idx)

            if t is not None:
                x1, y1, x2, y2 = int(t[0]), int(t[1]), int(t[2]), int(t[3])
                track_id        = int(t[4])
                cx, cy          = (x1 + x2) // 2, (y1 + y2) // 2

                slot["kf"].correct(np.array([[np.float32(cx)],
                                              [np.float32(cy)]]))
                slot["paths"].append((cx, cy))

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"OBJ{slot_idx+1} ID:{track_id}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            else:
                px, py = kf_preds[slot_idx]
                slot["paths"].append((px, py))
                cv2.putText(frame, f"OBJ{slot_idx+1} LOST",
                            (20, 40 + slot_idx * 26),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 255), 2)

            path = slot["paths"]
            for k in range(1, len(path)):
                cv2.line(frame, path[k - 1], path[k], color, 2)

        # ── HUD + write frame
        draw_hud(frame, slots, pending_action, height)
        out.write(frame)
        cv2.imshow(WINDOW, frame)

        key = cv2.waitKey(1) & 0xFF

        # ── Delete-mode
        if pending_action == "delete":
            if key in (ord("1"), ord("2"), ord("3")):
                target = key - ord("1")
                if slots[target] is not None:
                    slots[target] = None
                    bot_sort = make_bot_sort(fps)
                    print(f"  -> Object {target + 1} removed.")
                else:
                    print(f"  -> Slot {target + 1} is already empty.")
                pending_action = None
            elif key == 27:   # ESC
                pending_action = None
            continue

        # ── Normal key handling
        if key == ord("q"):
            break

        elif key in (ord("1"), ord("2"), ord("3")):
            idx = key - ord("1")
            if slots[idx] is not None:
                preview = annotate_existing(frame, slots)
                new_roi = select_roi(
                    f"Redraw Object {idx+1}  (ENTER=confirm  ESC=cancel)",
                    preview)
                if new_roi is not None:
                    old_paths  = slots[idx]["paths"]
                    slots[idx] = init_object(frame, new_roi,
                                              preserve_paths=old_paths)
                    bot_sort   = make_bot_sort(fps)
                    print(f"  -> Object {idx + 1} redrawn.")
            else:
                print(f"  -> Slot {idx + 1} is empty – use A to add.")

        elif key == ord("a"):
            empty = next((i for i, s in enumerate(slots) if s is None), None)
            if empty is not None:
                preview = annotate_existing(frame, slots)
                new_roi = select_roi(
                    f"Add Object {empty+1}  (ENTER=confirm  ESC=cancel)",
                    preview)
                if new_roi is not None:
                    slots[empty] = init_object(frame, new_roi)
                    bot_sort     = make_bot_sort(fps)
                    print(f"  -> Object {empty + 1} added.")
            else:
                print("  -> Already tracking 3 objects (maximum).")

        elif key == ord("d"):
            if any(s is not None for s in slots):
                pending_action = "delete"
            else:
                print("  -> No active objects to delete.")

    # ── Cleanup
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"Video saved to: {video_out}")


if __name__ == "__main__":
    main(
        "/home/jasper/Python projects/Data/noise_out.mp4",
        "/home/jasper/Python projects/Data/robot_out.mp4",
    )