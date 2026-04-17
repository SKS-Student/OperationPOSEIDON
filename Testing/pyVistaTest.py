import pyvista as pv
import numpy as np

# Create grid (like a scanned seabed)
x = np.linspace(0, 10, 50)
y = np.linspace(0, 10, 50)
x, y = np.meshgrid(x, y)

# Fake depth data (replace with your sonar later)
z = np.sin(x) * np.cos(y) * -10  # negative = depth

# Create structured grid
grid = pv.StructuredGrid(x, y, z)

# Plot
plotter = pv.Plotter()
plotter.add_mesh(grid, cmap="viridis", show_edges=False)
plotter.add_axes()
plotter.show()