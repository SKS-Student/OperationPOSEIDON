"""
live_sonar_viz.py
=================
Reads sonar + IMU data from Arduino over serial, computes the 3D position
of detected objects via SonarLocalizer, and plots them live in a PyVista
3D viewer — no manual input needed.

Press  Q  or close the window to quit.
"""

import threading
import time
import serial
import pyvista as pv
import numpy as np

from sonar_localization import SonarLocalizer, SensorFrame

# ── Config ──────────────────────────────────────────────────────────────────
COM_PORT  = "COM4"       # change to your port  (Linux: "/dev/ttyUSB0")
BAUD_RATE = 115200
# ────────────────────────────────────────────────────────────────────────────

pv.global_theme.allow_empty_mesh = True

# Shared state between the serial thread and the render thread
points_lock = threading.Lock()
new_points:  list = []          # raw [x, y, z] triples not yet added to the plot
all_points:  np.ndarray = None  # full accumulated array  (None until first point)
stop_event   = threading.Event()


# ── Serial / localization thread ─────────────────────────────────────────────

def serial_reader():
    localizer = SonarLocalizer()
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
        print(f"[serial] Connected on {COM_PORT}")
    except serial.SerialException as e:
        print(f"[serial] Could not open port: {e}")
        stop_event.set()
        return

    while not stop_event.is_set():
        try:
            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                continue

            parts = line.split(",")
            if len(parts) != 7:
                print("[serial] RAW:", line)
                continue

            yaw, pitch, roll, uw, d1, d2, servo = parts

            frame = SensorFrame(
                yaw         = float(yaw),
                pitch       = float(pitch),
                roll        = float(roll),
                sonar_dist  = float(uw) / 1000.0,  # mm → m
                us_forward  = float(d1) / 100.0,   # cm → m
                us_side     = float(d2) / 100.0,   # cm → m
                servo_angle = float(servo),
            )

            result    = localizer.process(frame)
            dp        = result.device_position
            op        = result.object_position

            print(f"[serial] Device ({dp[0]:.2f}, {dp[1]:.2f}, {dp[2]:.2f}) m  |  "
                  f"Object ({op[0]:.2f}, {op[1]:.2f}, {op[2]:.2f}) m")

            with points_lock:
                new_points.append(op.tolist())

        except ValueError:
            print("[serial] Parse error on:", line)
        except serial.SerialException as e:
            print(f"[serial] Serial error: {e}")
            break

    ser.close()


# ── PyVista visualizer ────────────────────────────────────────────────────────

def run_visualizer():
    global all_points

    plotter = pv.Plotter()
    plotter.set_background("white")
    plotter.enable_eye_dome_lighting()
    plotter.enable_trackball_style()

    # Placeholder actors — replaced as soon as the first point arrives
    cloud_actor = [None]
    mesh_actor  = [None]

    def update_plot():
        """Called on a timer — drains new_points and refreshes the scene."""
        global all_points

        with points_lock:
            if not new_points:
                return
            batch = new_points.copy()
            new_points.clear()

        # Accumulate points
        arr = np.array(batch, dtype=float)
        all_points = arr if all_points is None else np.vstack([all_points, arr])

        cloud = pv.PolyData(all_points)
        cloud["z"] = all_points[:, 2]

        z_min, z_max = all_points[:, 2].min(), all_points[:, 2].max()

        # ── Point cloud actor ──
        if cloud_actor[0] is None:
            cloud_actor[0] = plotter.add_mesh(
                cloud,
                scalars="z",
                cmap="viridis",
                point_size=10,
                render_points_as_spheres=True,
                show_scalar_bar=True,
            )
        else:
            cloud_actor[0].mapper.dataset = cloud
            cloud_actor[0].mapper.Modified()
            cloud_actor[0].mapper.SelectColorArray("z")
            cloud_actor[0].mapper.SetScalarModeToUsePointFieldData()
            cloud_actor[0].mapper.ScalarVisibilityOn()
            cloud_actor[0].mapper.SetScalarRange(z_min, z_max)

        # ── Surface mesh actor (needs ≥ 3 non-collinear points) ──
        if all_points.shape[0] >= 3:
            surf = cloud.delaunay_2d()
            if surf.n_points:
                surf["z"] = surf.points[:, 2]
                if mesh_actor[0] is None:
                    mesh_actor[0] = plotter.add_mesh(
                        surf,
                        scalars="z",
                        cmap="viridis",
                        opacity=0.4,
                        show_edges=True,
                    )
                else:
                    mesh_actor[0].mapper.dataset = surf
                    mesh_actor[0].mapper.Modified()
                    mesh_actor[0].mapper.SelectColorArray("z")
                    mesh_actor[0].mapper.SetScalarModeToUsePointFieldData()
                    mesh_actor[0].mapper.ScalarVisibilityOn()
                    mesh_actor[0].mapper.SetScalarRange(z_min, z_max)

        plotter.render()
        plotter.camera.reset_clipping_range()

    # Poll for new points every 200 ms
    plotter.add_timer_event(max_steps=999_999, duration=200, callback=update_plot)

    plotter.show(title="Live Sonar Map")
    stop_event.set()   # window closed → stop serial thread


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    t = threading.Thread(target=serial_reader, daemon=True)
    t.start()

    run_visualizer()   # blocks until window is closed

    stop_event.set()
    t.join(timeout=2)
    print("Done.")