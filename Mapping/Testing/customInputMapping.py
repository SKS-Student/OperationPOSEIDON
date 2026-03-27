import pyvista as pv
import numpy as np

pv.global_theme.allow_empty_mesh = True

plotter = pv.Plotter()

# points = np.array([
# [0,0,-2],[10,0,-3],[20,0,-4],[30,0,-3],[40,0,-2],[50,0,-1],
# [0,10,-3],[10,10,-5],[20,10,-6],[30,10,-5],[40,10,-3],[50,10,-2],
# [0,20,-4],[10,20,-6],[20,20,-9],[30,20,-7],[40,20,-5],[50,20,-3],
# [0,30,-3],[10,30,-5],[20,30,-7],[30,30,-8],[40,30,-6],[50,30,-4],
# [0,40,-2],[10,40,-4],[20,40,-6],[30,40,-7],[40,40,-5],[50,40,-3],
# [0,50,-1],[10,50,-2],[20,50,-3],[30,50,-4],[40,50,-3],[50,50,-2],

# [5,5,-3],[15,5,-4],[25,5,-5],[35,5,-4],[45,5,-3],
# [5,15,-5],[15,15,-7],[25,15,-8],[35,15,-6],[45,15,-4],
# [5,25,-6],[15,25,-8],[25,25,-10],[35,25,-7],[45,25,-5],
# [5,35,-5],[15,35,-7],[25,35,-9],[35,35,-8],[45,35,-6],
# [5,45,-3],[15,45,-5],[25,45,-6],[35,45,-5],[45,45,-4]
# ])
points = np.array([[0.0, 0.0, 0.0], [6.0, 1.0, 13.0], [2.0, 4.0, -2.0]])
cloud = pv.PolyData(points)
cloud["z"] = points[:, 2]

actor = plotter.add_mesh(
    cloud,
    scalars="z",
    cmap='viridis',
    point_size=10,
    render_points_as_spheres=True,
    show_scalar_bar=True,
)

actor.GetProperty().SetPointSize(10)

# build initial mesh from points and create a mesh actor
surf = cloud.delaunay_3d().extract_surface()
if surf.n_points:
    surf["z"] = surf.points[:, 2]
mesh_actor = plotter.add_mesh(
    surf,
    scalars='z',
    cmap='viridis',
    opacity=0.4,
    show_edges=True,
)

plotter.set_background("white")
plotter.enable_eye_dome_lighting()
plotter.enable_trackball_style()  # <-- Enable free camera movement

plotter.reset_camera()
# def update_mesh():
#     global points, mesh, mesh_actor
#     cloud = pv.PolyData(points)
#     surf = cloud.delaunay_3d().extract_surface()
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
    surf = cloud.delaunay_3d().extract_surface()
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