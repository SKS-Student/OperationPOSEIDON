import pyvista as pv
import numpy as np

# Create plotter
plotter = pv.Plotter()
plotter.add_axes()

# Start empty point cloud
points = np.array([[0, 0, 0]])  # 1 initial point
cloud = pv.PolyData(points)
point_actor = plotter.add_points(cloud, color='blue', point_size=8)

# Function to simulate sonar readings
def add_point_callback():
    global points, cloud
    # New simulated point
    new_point = np.random.rand(1, 3) * [10, 10, -10]
    points = np.vstack([points, new_point])
    # Update the PolyData coordinates
    cloud.points = points
    point_actor.update_coordinates(cloud.points)

# Add timer callback: PyVista calls this every 100 ms
plotter.add_callback(add_point_callback, interval=100)

# Show interactive window
plotter.show()