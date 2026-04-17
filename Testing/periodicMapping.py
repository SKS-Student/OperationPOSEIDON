import pyvista as pv
import numpy as np
import threading
import time
from queue import Queue
from threading import Lock
import sys

pv.global_theme.allow_empty_mesh = True

plotter = pv.Plotter()

# Initial points (at least 4 non-coplanar for delaunay_3d)
points = np.array([[0.0, 0.0, 0.0], [1.0, -5.0, 1.0], [-2.0, -2.0, -2.0], [0.5, 0.5, 2.0]])
cloud = pv.PolyData(points)
cloud["z"] = points[:, 2]

# Point cloud actor
actor = plotter.add_mesh(
    cloud,
    scalars="z",
    cmap='viridis',
    point_size=10,
    render_points_as_spheres=True,
    show_scalar_bar=True,
)

actor.GetProperty().SetPointSize(10)

# Initial mesh
cloud_clean = cloud.clean()
try:
    surf = cloud_clean.delaunay_2d()
    if surf.n_points:
        surf["z"] = surf.points[:, 2]
except:
    surf = pv.PolyData()

mesh_actor = plotter.add_mesh(
    surf,
    scalars="z",
    cmap='viridis',
    opacity=0.7,
    show_edges=True,
)

plotter.set_background("white")
plotter.enable_eye_dome_lighting()
plotter.enable_trackball_style()
plotter.reset_camera()

# Shared state for threading
update_count = [0]
should_run = [True]
data_queue = Queue()
render_lock = Lock()

def read_data_thread():
    """Background thread that reads data and updates mesh every 1-2 seconds"""
    global points, cloud, actor, mesh_actor
    
    print("Background thread started!")  # DEBUG
    
    while should_run[0]:
        time.sleep(1.5)  # 1.5 second interval
        
        print("Attempting update...")  # DEBUG
        
        # TODO: Replace this with your actual data source
        # Examples:
        #   - Socket: data = socket.recv()
        #   - File: data = read_next_line_from_file()
        #   - Queue: data = data_queue.get_nowait()
        #   - Serial: data = ser.readline()
        
        # Placeholder: random point within bounds
        new_point = np.random.rand(3) * 10
        
        points = np.vstack([points, new_point])
        
        try:
            print(f"Updating with point {new_point}...")  # DEBUG
            # Rebuild cloud and mesh
            cloud = pv.PolyData(points).clean()
            cloud["z"] = cloud.points[:, 2]
            
            # Update mesh with error handling
            surf = pv.PolyData()
            if cloud.n_points >= 3:
                try:
                    surf = cloud.delaunay_2d()
                    if surf.n_points:
                        surf["z"] = surf.points[:, 2]
                except Exception as e:
                    print(f"Delaunay failed: {e}")
                    surf = pv.PolyData()
            
            # Update point cloud actor
            actor.mapper.dataset = cloud
            actor.mapper.SelectColorArray("z")
            actor.mapper.SetScalarModeToUsePointFieldData()
            actor.mapper.ScalarVisibilityOn()
            if cloud.n_points > 0:
                actor.mapper.SetScalarRange(cloud.points[:, 2].min(), cloud.points[:, 2].max())
            actor.mapper.Modified()
            
            # Update mesh actor
            mesh_actor.mapper.dataset = surf
            mesh_actor.mapper.Modified()
            
            plotter.render()
            
            update_count[0] += 1
            print(f"Update {update_count[0]}: {cloud.n_points} points")  # DEBUG
        except Exception as e:
            print(f"Update error: {e}")
def quit_app(obj=None, event=None):
    """Close the plotter"""
    should_run[0] = False
    print("Quitting application...")  # DEBUG
    plotter.close()
    sys.exit(0)

# Start background thread for periodic data reads
data_thread = threading.Thread(target=read_data_thread, daemon=True)
data_thread.start()

# Add quit key
plotter.add_key_event("q", quit_app)

# Open window and run event loop
print("Running periodic mapper. Press 'q' to quit.")
plotter.show()

print("Mapper closed.")
