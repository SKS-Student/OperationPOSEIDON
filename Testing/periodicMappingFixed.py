import pyvista as pv
import numpy as np
import threading
import time
import sys

pv.global_theme.allow_empty_mesh = True

# Global state
points = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [-2.0, -2.0, -2.0], [0.5, 0.5, 2.0]])
should_run = [True]
update_count = [0]

def create_plotter():
    """Initialize the plotter with initial mesh"""
    plotter = pv.Plotter()
    
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
    
    return plotter, actor, mesh_actor

def read_data_thread(plotter, actor, mesh_actor):
    """Background thread that reads data and updates mesh every 1-2 seconds"""
    global points
    
    print("Background thread started!")
    
    while should_run[0]:
        time.sleep(1.5)  # 1.5 second interval
        
        # Placeholder: random point within bounds
        new_point = np.random.rand(3) * 10
        points = np.vstack([points, new_point])
        
        try:
            print(f"Updating with point {new_point}...")
            
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
            
            # Update actors
            actor.mapper.dataset = cloud
            actor.mapper.SelectColorArray("z")
            actor.mapper.SetScalarModeToUsePointFieldData()
            actor.mapper.ScalarVisibilityOn()
            if cloud.n_points > 0:
                actor.mapper.SetScalarRange(cloud.points[:, 2].min(), cloud.points[:, 2].max())
            actor.mapper.Modified()
            
            mesh_actor.mapper.dataset = surf
            mesh_actor.mapper.Modified()
            
            update_count[0] += 1
            print(f"Update {update_count[0]}: {cloud.n_points} points")
            
        except Exception as e:
            print(f"Update error: {e}")

def main():
    """Main function - create plotter and run with background thread"""
    plotter, actor, mesh_actor = create_plotter()
    
    # Start background thread
    data_thread = threading.Thread(target=read_data_thread, args=(plotter, actor, mesh_actor), daemon=True)
    data_thread.start()
    
    # Define quit function for key event
    def quit_app(obj=None, event=None):
        should_run[0] = False
        plotter.close()
    
    plotter.add_key_event("q", quit_app)
    
    print("Running periodic mapper. Press 'q' to quit.")
    print("Updates happen in background every 1.5 seconds.")
    
    # Use blocking show - but now our background thread will update the data
    # and VTK's native event loop will handle rendering
    plotter.show()
    
    print("Mapper closed.")

if __name__ == "__main__":
    main()
