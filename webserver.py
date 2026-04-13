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
import modules.lighting # Generate lights for 3D-visualization

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
VizualizePoints('sq_only.csv', planeSquare, env.Colors.GetColor3d("Gold"), 0.5) #Gold
VizualizePoints('sq_no.csv', planeSquare, env.Colors.GetColor3d("Tomato"), 0.5)
cubeVoxel = vtk.vtkCubeSource()
cubeVoxel.SetXLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetYLength(cfg.sizeVoxel-cfg.gapVoxel)
cubeVoxel.SetZLength(cfg.sizeVoxel-cfg.gapVoxel)
VizualizePoints('vox_yes.csv', cubeVoxel, env.Colors.GetColor3d("Green"), 1.0)
VizualizePoints('vox_no.csv', cubeVoxel, env.Colors.GetColor3d("Tomato"), 1.0)
VizualizePoints('vox_industrial.csv', cubeVoxel, env.Colors.GetColor3d("Gray"), 1.0)
VizualizePoints('vox_doorphones_fact_yes.csv', cubeVoxel, env.Colors.GetColor3d("Cyan"), 1.0)
VizualizePoints('vox_doorphones_fact_no.csv', cubeVoxel, env.Colors.GetColor3d("Cyan"), 1.0)
VizualizePoints('vox_doorphones_plan_yes.csv', cubeVoxel, env.Colors.GetColor3d("Magenta"), 1.0)
VizualizePoints('vox_doorphones_plan_no.csv', cubeVoxel, env.Colors.GetColor3d("Magenta"), 1.0)
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

# Add lights to the scene
modules.lighting.PrepareLights(env.Renderer) # Generate lights for 3D-visualization
for light in env.lights: env.Renderer.AddLight(light)

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
    layout.title.set_text("Urban megaphone: 3D-modeling of sound wave coverage among urban buildings and streets")
    with layout.content:
        with vuetify.VContainer(fluid=True, classes="pa-0 fill-height"):
            view = vtk_widgets.VtkRemoteView(render_window)
            ctrl.on_server_ready.add(view.update)
            
# Start server
if __name__ == "__main__":
    server.start(host="0.0.0.0", port=80)
