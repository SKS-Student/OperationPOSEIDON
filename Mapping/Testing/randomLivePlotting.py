import pyvista as pv
import numpy as np

pv.global_theme.allow_empty_mesh = True

plotter = pv.Plotter()

points = np.array([[0.0, 0.0, 0.0], [6.0, 1.0, 13.0], [2.0, 4.0, -2.0]])
cloud = pv.PolyData(points)
cloud["z"] = points[:, 2]

actor = plotter.add_mesh(
    cloud,
    scalars="z",
    cmap='coolwarm',
    point_size=10,
    render_points_as_spheres=True,
    show_scalar_bar=True,
)

actor.GetProperty().SetPointSize(10)

plotter.set_background("white")
plotter.enable_eye_dome_lighting()
plotter.enable_trackball_style()  # <-- Enable free camera movement

plotter.reset_camera()

def add_random_point():
    global points, cloud, actor
    new_point = np.random.rand(3) * 10
    points = np.vstack([points, new_point])

    # Rebuild the PolyData from scratch instead of modifying in-place
    cloud = pv.PolyData(points)
    cloud["z"] = points[:, 2]
    
    # Update the actor's dataset
    actor.mapper.dataset = cloud
    actor.mapper.SelectColorArray("z")
    actor.mapper.SetScalarModeToUsePointFieldData()
    actor.mapper.ScalarVisibilityOn()
    actor.mapper.SetScalarRange(points[:, 2].min(), points[:, 2].max())

    plotter.render()
    plotter.camera.reset_clipping_range()
    print(f"Added point: {new_point}")

plotter.add_key_event("a", add_random_point)

plotter.show()