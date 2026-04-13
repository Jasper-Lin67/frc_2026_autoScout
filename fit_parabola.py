import csv
import numpy as np
from collections import defaultdict

# ── Tunable value ─────────────────────────────────────────────────────────────

MIN_POINTS = 20  # need at least 3 points to fit a parabola

# ──────────────────────────────────────────────────────────────────────────────


def load_trajectories(path):
    """
    Read the formatted CSV (one row per ball, dynamic x_i/y_i columns)
    and reconstruct each ball's list of (x, y) positions.

    Returns:
        {
            track_id: {
                "points":      [(x, y), ...],
                "first_frame": int,
                "last_frame":  int,
            },
            ...
        }
    """
    trajectories = {}

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            track_id    = row["track_id"]
            first_frame = int(row["first_frame"])
            last_frame  = int(row["last_frame"])

            # Collect all x_i / y_i pairs that exist in this row
            points = []
            i = 0
            while f"x_{i}" in row and row[f"x_{i}"] != "":
                x = float(row[f"x_{i}"])
                y = float(row[f"y_{i}"])
                points.append((x, y))
                i += 1

            trajectories[track_id] = {
                "points":      points,
                "first_frame": first_frame,
                "last_frame":  last_frame,
            }

    return trajectories


def fit_parabola(points):
    """
    Fit a parabola (degree-2 polynomial) to a list of (x, y) points
    using numpy.polyfit, which minimises least-squares error.

    The parabola is expressed as:
        y = a*x² + b*x + c

    where:
        a — curvature  (positive = opens up, negative = opens down, ~0 = nearly straight)
        b — slope at x=0
        c — y-intercept

    Returns:
        (a, b, c)  coefficients, or None if fitting fails.
    """
    xs = np.array([p[0] for p in points])
    ys = np.array([p[1] for p in points])

    try:
        # deg=2 fits a parabola; full=False returns just the coefficients
        coeffs = np.polyfit(xs, ys, deg=2)
        return coeffs  # [a, b, c]
    except np.linalg.LinAlgError:
        return None


def residual_error(points, coeffs):
    """
    Calculate the mean squared error between the actual points and
    the fitted parabola. Lower = better fit.

    Useful for flagging balls whose path wasn't actually parabolic
    (e.g. bounced, or was occluded mid-flight).
    """
    a, b, c = coeffs
    xs = np.array([p[0] for p in points])
    ys = np.array([p[1] for p in points])
    y_pred = a * xs**2 + b * xs + c
    return float(np.mean((ys - y_pred) ** 2))


def write_output(trajectories, path):
    """
    For each ball, write one row containing:

        track_id     — ball ID from DeepSort
        num_points   — number of (x,y) detections used for the fit
        first_frame  — frame the ball first appeared
        last_frame   — frame the ball last appeared
        start_x      — x position at first detection
        start_y      — y position at first detection
        end_x        — x position at last detection
        end_y        — y position at last detection
        curvature_a  — the 'a' coefficient (degree-2 term); main measure of curve
        slope_b      — the 'b' coefficient (degree-1 term)
        intercept_c  — the 'c' coefficient (constant term)
        fit_mse      — mean squared error of the parabola fit (lower = better)
        skipped      — "yes" if the ball had too few points to fit
    """
    fieldnames = [
        "track_id", "num_points", "first_frame", "last_frame",
        "start_x", "start_y", "end_x", "end_y",
        "curvature_a", "slope_b", "intercept_c", "fit_mse", "skipped"
    ]

    skipped = 0
    written = 0

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for track_id in sorted(trajectories.keys(), key=lambda t: int(t) if str(t).isdigit() else t):
            data   = trajectories[track_id]
            points = data["points"]

            row = {
                "track_id":   track_id,
                "num_points": len(points),
                "first_frame": data["first_frame"],
                "last_frame":  data["last_frame"],
            }

            if len(points) < MIN_POINTS:
                # Not enough points to fit a parabola reliably
                row.update({
                    "start_x": points[0][0]  if points else "",
                    "start_y": points[0][1]  if points else "",
                    "end_x":   points[-1][0] if points else "",
                    "end_y":   points[-1][1] if points else "",
                    "curvature_a": "",
                    "slope_b":     "",
                    "intercept_c": "",
                    "fit_mse":     "",
                    "skipped":     "yes",
                })
                skipped += 1

            else:
                coeffs = fit_parabola(points)

                if coeffs is None:
                    # polyfit failed (e.g. all x values identical)
                    row.update({
                        "start_x": points[0][0],
                        "start_y": points[0][1],
                        "end_x":   points[-1][0],
                        "end_y":   points[-1][1],
                        "curvature_a": "",
                        "slope_b":     "",
                        "intercept_c": "",
                        "fit_mse":     "",
                        "skipped":     "yes (fit failed)",
                    })
                    skipped += 1
                else:
                    a, b, c = coeffs
                    mse = residual_error(points, coeffs)
                    row.update({
                        "start_x":     points[0][0],
                        "start_y":     points[0][1],
                        "end_x":       points[-1][0],
                        "end_y":       points[-1][1],
                        "curvature_a": round(a,   6),
                        "slope_b":     round(b,   6),
                        "intercept_c": round(c,   6),
                        "fit_mse":     round(mse, 4),
                        "skipped":     "no",
                    })
                    written += 1

            writer.writerow(row)

    print(f"  Written : {written} parabolas")
    print(f"  Skipped : {skipped} (too few points or fit failed)")
    print(f"  Output  : {path}")


def main(input_csv, output_csv):
    print(f"Loading trajectories from: {input_csv}")
    trajectories = load_trajectories(input_csv)
    print(f"  Found {len(trajectories)} balls")

    print("Fitting parabolas...")
    write_output(trajectories, output_csv)

    print("Done.")