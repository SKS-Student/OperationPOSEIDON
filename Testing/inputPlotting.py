#HORRIBLE DONT USE

#HORRIBLE DONT USE
#HORRIBLE DONT USE
#HORRIBLE DONT USE
#HORRIBLE DONT USE



# import pyvista as pv
# import numpy as np
# import sys

# pv.global_theme.allow_empty_mesh = True  # allow empty data

# plotter = pv.Plotter()
# points = np.array([[0.0, 0.0, 0.0], [6.0, 1.0, 13.0], [2.0, 4.0, -2.0]])

# # initial empty cloud actor
# cloud = pv.PolyData(points)
# actor = plotter.add_mesh(
#     cloud,
#     scalars=points[:, 2] if points.size else None,
#     cmap='coolwarm',
#     point_size=10,
#     render_points_as_spheres=True,
#     show_scalar_bar=True,
# )
# if points.size > 0 and plotter.camera.position is None:
#     max_vals = points.max(axis=0)
#     plotter.camera.position = tuple(max_vals + 5)
#     plotter.camera.focal_point = points.mean(axis=0)
# # plotter.show()  # keep window open
# def add_point():
#     global points, cloud

#     user_input = input("Enter point (x y z) or 'q' to quit: ").strip()

#     if user_input.lower() == 'q':
#         plotter.close()
#         sys.exit(0)
#         return

#     try:
#         coords = list(map(float, user_input.split()))
#         if len(coords) != 3:
#             print("Please enter exactly 3 numbers")
#             return
        
#         print(f"Adding point: {coords}" )
#         points = np.vstack([points, coords])

#         # update data
#         cloud.points = points
#         cloud["z"] = points[:, 2]
#         cloud.Modified()  # let VTK know geometry changed

#         # Make sure mapper uses updated point scalars
        
#         actor.GetMapper().SelectColorArray("z")
#         actor.GetMapper().SetScalarModeToUsePointFieldData()
#         actor.GetMapper().ScalarVisibilityOn()
#         actor.GetMapper().SetScalarRange(points[:, 2].min(), points[:, 2].max())
#         actor.GetProperty().SetPointSize(10)

#         plotter.update()
#         plotter.render()
#     except ValueError:
#         print("Invalid input. Enter 3 numbers separated by spaces")

# def update_actor():
#     global points, cloud, actor, plotter
#     cloud.points = points
#     cloud["z"] = points[:, 2]
#     cloud.Modified()
#     actor.GetMapper().SelectColorArray("z")
#     actor.GetMapper().SetScalarModeToUsePointFieldData()
#     actor.GetMapper().ScalarVisibilityOn()
#     actor.GetMapper().SetScalarRange(points[:, 2].min(), points[:, 2].max())
#     actor.GetProperty().SetPointSize(10)
#     plotter.reset_camera()
#     plotter.render()            

# def recenter_camera():
#     if points.size == 0:
#         return
#     bbox_min = points.min(axis=0)
#     bbox_max = points.max(axis=0)
#     center = (bbox_min + bbox_max) / 2
#     plotter.camera.focal_point = center
#     plotter.camera.position = tuple(bbox_max + 5)
#     plotter.render()

# plotter.add_key_event("r", recenter_camera)        

# plotter.add_key_event("a", add_point)

# plotter.show()
