# ============================================
# Web server to show saved 3D visualization of the model
# ============================================

# Modules import
# ============================================
from pathlib import Path # Crossplatform pathing
import vtk # Use 3D-visualization features
import pandas as pd # Use pandas for data processing
from trame.app import get_server # Use Trame for web-server
from trame.ui.vuetify import SinglePageLayout # Use Vuetify for web-interface
from trame.widgets import vuetify, vtk as vtk_widgets # Use VTK for 3D-visualization
import re # Use regular expressions
from vtkmodules.util import numpy_support # Fro quick import coordinates from pandas DataFrame

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition

# VTK objects
renderer = vtk.vtkRenderer()

# ============================================
# Vizualize points from .csv file with 3D-glyph, color and opacity
# ============================================
def VizualizePoints(fileP, glyph, color, opacity):
    # Read .csv file with points coordinates
    df = pd.read_csv(Path('.',cfg.folderOUTPUT,fileP))
    points = vtk.vtkPoints()
    # Convert pandas DataFrame to vtkDataArray without loop
    vtk_array = numpy_support.numpy_to_vtk(df[["x", "y", "z"]].to_numpy(), deep=True, array_type=vtk.VTK_FLOAT)
    # Set vtkDataArray to vtkPoints
    points.SetData(vtk_array)
    #for _, row in df.iterrows():
    #    points.InsertNextPoint(row["x"], row["y"], row["z"])
    # Put Voxels on intersection points
    polyData = vtk.vtkPolyData()
    polyData.SetPoints(points)
    glyphs = vtk.vtkGlyph3D()
    glyphs.SetInputData(polyData)
    glyphs.SetSourceConnection(glyph.GetOutputPort())
    glyphs.ScalingOff()
    glyphs.Update()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(glyphs.GetOutputPort())
    mapper.ScalarVisibilityOff()
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(color)
    actor.GetProperty().SetOpacity(opacity)
    renderer.AddActor(actor)
    print(f"{fileP} loaded")

# ============================================
# Function to enforce y-axis as vertical
# ============================================
def enforce_y_axis_vertical(**kwargs):
    print("s\n")
    camera = renderer.GetActiveCamera()
    camera.SetViewUp(0, 1, 0)  # Ensure y-axis is vertical
    renderer.ResetCameraClippingRange()
    
# ============================================
# Read .vtp files with mesh of earth surface
# Generate VTK-objects of 3D-surface with textures
# ============================================
for fileP in Path('.',cfg.folderOUTPUT).glob("*.vtp", case_sensitive=False):
    reader = vtk.vtkXMLPolyDataReader()
    reader.SetFileName(fileP)
    reader.Update()
    polydata = reader.GetOutput()

    # Find raster file name from .vtp file name
    file_name = fileP.stem  # Get the file name without extension
    match = re.match(r"(\d+)_?(.*)", file_name)
    if match:
        index = match.group(1)  # One or more digits
        fileR = Path('.',cfg.folderRASTER,match.group(2))  # All other characters after '_'

    imageReader = env.readerFactory.CreateImageReader2(str(fileR))
    imageReader.SetFileName(fileR)
    imageReader.Update()

    texture = vtk.vtkTexture()
    texture.SetInputConnection(imageReader.GetOutputPort())
    texture.InterpolateOn()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(polydata)
    mapper.ScalarVisibilityOff()

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.SetTexture(texture)
    actor.GetProperty().SetOpacity(1)
    renderer.AddActor(actor)
    print(f"{fileR} loaded")

# ============================================
# Read .csv files with points coordinates
# Generate VTK-objects of squares, voxels and megaphones
# ============================================'''
planeSquare = vtk.vtkPlaneSource()
planeSquare.SetOrigin(0, 0, 0)
planeSquare.SetPoint1(cfg.sizeVoxel, 0, 0)
planeSquare.SetPoint2(0, 0, cfg.sizeVoxel)
VizualizePoints('sq_full.csv', planeSquare, env.Colors.GetColor3d("Green"), 0.5)
planeSquare = vtk.vtkPlaneSource()
planeSquare.SetOrigin(0, 0, 0)
planeSquare.SetPoint1(cfg.sizeVoxel, 0, 0)
planeSquare.SetPoint2(0, 0, cfg.sizeVoxel)
VizualizePoints('sq_only.csv', planeSquare, env.Colors.GetColor3d("Green"), 0.5) #Gold
planeSquare = vtk.vtkPlaneSource()
planeSquare.SetOrigin(0, 0, 0)
planeSquare.SetPoint1(cfg.sizeVoxel, 0, 0)
planeSquare.SetPoint2(0, 0, cfg.sizeVoxel)
VizualizePoints('sq_no.csv', planeSquare, env.Colors.GetColor3d("Tomato"), 0.5)
cubeVoxel = vtk.vtkCubeSource()
cubeVoxel.SetXLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetYLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetZLength(cfg.sizeVoxel-cfg.gapVoxel)
VizualizePoints('vox_yes.csv', cubeVoxel, env.Colors.GetColor3d("Green"), 1.0)
cubeVoxel = vtk.vtkCubeSource()
cubeVoxel.SetXLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetYLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetZLength(cfg.sizeVoxel-cfg.gapVoxel)
VizualizePoints('vox_no.csv', cubeVoxel, env.Colors.GetColor3d("Tomato"), 1.0)
cubeVoxel = vtk.vtkCubeSource()
cubeVoxel.SetXLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetYLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetZLength(cfg.sizeVoxel-cfg.gapVoxel)
VizualizePoints('vox_industrial.csv', cubeVoxel, env.Colors.GetColor3d("Gray"), 1.0)
cubeVoxel = vtk.vtkCubeSource()
cubeVoxel.SetXLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetYLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetZLength(cfg.sizeVoxel-cfg.gapVoxel)
VizualizePoints('vox_doorphones_fact.csv', cubeVoxel, env.Colors.GetColor3d("Cyan"), 1.0)
cubeVoxel = vtk.vtkCubeSource()
cubeVoxel.SetXLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetYLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetZLength(cfg.sizeVoxel-cfg.gapVoxel)
VizualizePoints('vox_doorphones_plan.csv', cubeVoxel, env.Colors.GetColor3d("Magenta"), 1.0)
coneMegaphone = vtk.vtkConeSource()
coneMegaphone.SetDirection(0, 1, 0)
coneMegaphone.SetHeight(cfg.sizeVoxel)
coneMegaphone.SetRadius(cfg.sizeVoxel/4)
VizualizePoints('mgphn_buildings.csv', coneMegaphone, env.Colors.GetColor3d("GreenYellow"), 1.0)
coneMegaphone = vtk.vtkConeSource()
coneMegaphone.SetDirection(0, 1, 0)
coneMegaphone.SetHeight(cfg.heightStansaloneMegaphone)
coneMegaphone.SetRadius(cfg.sizeVoxel)
VizualizePoints('mgphn_standalone.csv', coneMegaphone, env.Colors.GetColor3d("GreenYellow"), 1.0)
sphereMegaphone = vtk.vtkSphereSource()
sphereMegaphone.SetRadius(cfg.sizeVoxel/4)
VizualizePoints('mgphn_spehres.csv', sphereMegaphone, env.Colors.GetColor3d("GreenYellow"), 1.0)

# Add lights for uniform illumination from all angles
bounds = renderer.ComputeVisiblePropBounds()
x_min, x_max, y_min, y_max, z_min, z_max = bounds
scene_center = [(x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2]
scene_width = x_max - x_min
scene_depth = y_max - y_min
scene_height = z_max - z_min

# Add stronger ambient light for overall illumination
ambient_light = vtk.vtkLight()
ambient_light.SetLightTypeToHeadlight()
ambient_light.SetColor(1, 1, 1)
ambient_light.SetIntensity(0.5)  # Increased from 0.3
renderer.AddLight(ambient_light)

# Add main directional light from above (like sun)
sun_light = vtk.vtkLight()
sun_light.SetLightTypeToSceneLight()
sun_light.SetPosition(scene_center[0], y_max + scene_depth * 2, scene_center[2])
sun_light.SetFocalPoint(scene_center[0], scene_center[1], scene_center[2])
sun_light.SetColor(1, 1, 1)
sun_light.SetIntensity(0.7)
renderer.AddLight(sun_light)

# Add four corner lights above the scene for ground illumination
corner_height = y_max + scene_depth
corner_intensity = 0.4

# Front-left corner
corner1 = vtk.vtkLight()
corner1.SetLightTypeToSceneLight()
corner1.SetPosition(x_min - scene_width * 0.3, corner_height, z_max + scene_height * 0.3)
corner1.SetFocalPoint(scene_center[0], y_min, scene_center[2])
corner1.SetColor(1, 1, 1)
corner1.SetIntensity(corner_intensity)
renderer.AddLight(corner1)

# Front-right corner
corner2 = vtk.vtkLight()
corner2.SetLightTypeToSceneLight()
corner2.SetPosition(x_max + scene_width * 0.3, corner_height, z_max + scene_height * 0.3)
corner2.SetFocalPoint(scene_center[0], y_min, scene_center[2])
corner2.SetColor(1, 1, 1)
corner2.SetIntensity(corner_intensity)
renderer.AddLight(corner2)

# Back-left corner
corner3 = vtk.vtkLight()
corner3.SetLightTypeToSceneLight()
corner3.SetPosition(x_min - scene_width * 0.3, corner_height, z_min - scene_height * 0.3)
corner3.SetFocalPoint(scene_center[0], y_min, scene_center[2])
corner3.SetColor(1, 1, 1)
corner3.SetIntensity(corner_intensity)
renderer.AddLight(corner3)

# Back-right corner
corner4 = vtk.vtkLight()
corner4.SetLightTypeToSceneLight()
corner4.SetPosition(x_max + scene_width * 0.3, corner_height, z_min - scene_height * 0.3)
corner4.SetFocalPoint(scene_center[0], y_min, scene_center[2])
corner4.SetColor(1, 1, 1)
corner4.SetIntensity(corner_intensity)
renderer.AddLight(corner4)

# Add side lights at mid-height for building sides
side_height = scene_center[1] + scene_depth * 0.3

# Left side
left_light = vtk.vtkLight()
left_light.SetLightTypeToSceneLight()
left_light.SetPosition(x_min - scene_width, side_height, scene_center[2])
left_light.SetFocalPoint(scene_center[0], scene_center[1], scene_center[2])
left_light.SetColor(1, 1, 1)
left_light.SetIntensity(0.3)
renderer.AddLight(left_light)

# Right side
right_light = vtk.vtkLight()
right_light.SetLightTypeToSceneLight()
right_light.SetPosition(x_max + scene_width, side_height, scene_center[2])
right_light.SetFocalPoint(scene_center[0], scene_center[1], scene_center[2])
right_light.SetColor(1, 1, 1)
right_light.SetIntensity(0.3)
renderer.AddLight(right_light)

# Prepare VTK-window
renderer.SetBackground(0.2, 0.3, 0.4)

# VTK Render Window
render_window = vtk.vtkRenderWindow()
render_window.AddRenderer(renderer)

interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(render_window)
interactor.SetInteractorStyle(vtk.vtkInteractorStyleTerrain())
renderer.ResetCamera()

# Initialize server
server = get_server(client_type="vue2")
state, ctrl = server.state, server.controller

# Configure Trame UI
with SinglePageLayout(server) as layout:
    layout.title.set_text("Rotating Cone")
    with layout.content:
        with vuetify.VContainer(fluid=True, classes="pa-0 fill-height"):
            view = vtk_widgets.VtkRemoteView(render_window)
            
# Start server
if __name__ == "__main__":
    server.start()
