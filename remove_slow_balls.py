import csv
import numpy as np

# ── Tunable values ─────────────────────────────────────────────────────────────

MIN_SPEED = 4  # pixels per frame — remove balls slower than this

# ──────────────────────────────────────────────────────────────────────────────


def calculate_speed(row):
    """
    Calculate average speed in pixels per frame.
    Speed = total distance between start and end / number of frames active.
    Returns None if the row was skipped (no start/end coords).
    """
    if row["skipped"] != "no":
        return None

    dx = float(row["end_x"]) - float(row["start_x"])
    dy = float(row["end_y"]) - float(row["start_y"])
    distance = np.sqrt(dx**2 + dy**2)

    frames = int(row["last_frame"]) - int(row["first_frame"])
    if frames == 0:
        return 0.0

    return distance / frames


def main(input_csv, output_csv):
    kept    = 0
    removed = 0

    with open(input_csv, newline="") as f_in:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames

        rows = list(reader)

    with open(output_csv, "w", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            speed = calculate_speed(row)

            # keep skipped rows as-is — they have no speed to filter on
            if speed is None:
                writer.writerow(row)
                continue

            if speed >= MIN_SPEED:
                writer.writerow(row)
                kept += 1
            else:
                removed += 1

    print(f"Done.")
    print(f"  Kept   : {kept} fast balls (speed >= {MIN_SPEED} px/frame)")
    print(f"  Removed: {removed} slow balls (speed < {MIN_SPEED} px/frame)")
    print(f"  Output : {output_csv}")


if __name__ == "__main__":
    main(
        input_csv  = "/home/jasper/Python projects/Data/DEBUG_csv_parabola_out.csv",
        output_csv = "/home/jasper/Python projects/Data/DEBUG_csv_parabola_fast.csv",
    )