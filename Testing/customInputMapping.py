import pyvista as pv
import numpy as np

pv.global_theme.allow_empty_mesh = True

plotter = pv.Plotter()
points = []

# grid resolution
for x in range(0, 61, 2):
    for y in range(0, 61, 2):

        # distance from center (30,30)
        dx = x - 30
        dy = y - 30
        dist = np.sqrt(dx**2 + dy**2)

        # --- base basin shape (deep center, shallow edges) ---
        depth = -8 - (dist * 0.25)

        # --- add central deep basin ---
        depth += -6 * np.exp(-(dist**2) / 400)

        # --- add ridges (wave-like patterns) ---
        depth += 2 * np.sin(x * 0.2) * np.cos(y * 0.15)

        # --- add trench (diagonal feature) ---
        trench = np.exp(-((x - y - 10)**2) / 50)
        depth += -5 * trench

        # --- small random variation (natural noise) ---
        depth += np.random.uniform(-0.5, 0.5)

        points.append([x, y, depth])

points = np.array(points)

# points = np.array([[0.0, 0.0, 0.0], [6.0, 1.0, 13.0], [2.0, 4.0, -2.0]])
cloud = pv.PolyData(points)
cloud["z"] = points[:, 2]

actor = plotter.add_mesh(
    cloud,
    scalars="z",
    cmap='Blues',
    point_size=2,
    render_points_as_spheres=True,
    show_scalar_bar=True,
)


# build initial mesh from points and create a mesh actor
surf = cloud.delaunay_2d()
if surf.n_points:
    surf["z"] = surf.points[:, 2]
mesh_actor = plotter.add_mesh(
    surf,
    scalars='z',
    cmap='Blues',
    opacity=0.7,
    show_edges=True,
    # clim=(points[:, 2].min(), points[:, 2].max())
    clim=[-25,-8]
)

plotter.set_background("#c0e4fa")
plotter.enable_eye_dome_lighting()
plotter.enable_trackball_style()  # <-- Enable free camera movement

plotter.reset_camera()
# def update_mesh():
#     global points, mesh, mesh_actor
#     cloud = pv.PolyData(points)
#     surf = cloud.delaunay_2d()
#     surf["z"] = surf.points[:, 2]
#     mesh_actor.mapper.dataset = surf
#     mesh_actor.mapper.Modified()
#     plotter.render()

def add_random_point():
    global points, cloud, actor, coords, mesh_actor
    try:
        user_input = input("Enter point (x y z) or 'q' to quit: ").strip()
        coords = list(map(float, user_input.split()))
        if len(coords) != 3:
                print("Please enter exactly 3 numbers")
                return
    except ValueError:
        print("Invalid input. Enter 3 numbers separated by spaces")
        return    
    if user_input.lower() == 'q':
        plotter.close()
        return

    points = np.vstack([points, coords])
    # update_mesh()

    # Rebuild the PolyData from scratch instead of modifying in-place
    cloud = pv.PolyData(points)
    cloud["z"] = points[:, 2]
    surf = cloud.delaunay_2d()
    if surf.n_points:
        surf["z"] = surf.points[:,2]
    # Update the actor's dataset
    actor.mapper.dataset = cloud
    actor.mapper.Modified()

    mesh_actor.mapper.dataset = surf
    mesh_actor.mapper.Modified()
    actor.mapper.SelectColorArray("z")
    actor.mapper.SetScalarModeToUsePointFieldData()
    actor.mapper.ScalarVisibilityOn()
    actor.mapper.SetScalarRange(points[:, 2].min(), points[:, 2].max())

    plotter.render()
    plotter.camera.reset_clipping_range()
    print(f"Added point: {coords}")

plotter.add_key_event("a", add_random_point)

plotter.show()
