# ============================================
# Urban megaphone
# 3D-modeling of sound wave coverage among urban buildings and streets
# ============================================

# Modules import
# ============================================
from pathlib import Path # Crossplatform pathing
import vtk # Use other 3D-visualization features
import time # Tracking the execution time

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition
import modules.bounds # Read raster and DEM data and calculate wolrd bounds
import modules.earth # Read raster and DEM data and generate the earth's surface
import modules.buildings # Generate voxels for earth ground vector buildings
import modules.megaphones # Load megaphones points and calculate audibility level
import modules.doorphones # Load doorphones data and assign to buildings
import modules.audibility # Multiprocessing audibility calculation
import modules.lighting # Generate lights for 3D-visualization

# Only for main process
if __name__ == '__main__':
    start_time = time.time() # Record the start time

    # Delete all files in folderOUTPUT directory
    # ============================================
    for fileD in Path('.',cfg.folderOUTPUT).glob("*.*", case_sensitive=False):
        fileD.unlink()

    # Real work
    # ============================================
    modules.bounds.ReadWorldBounds() # Read .tif files of RASTER and DEM models, find the dimensions of the world being explored
    modules.earth.GenerateEarthSurface() # Read .tif files of RASTER and DEM models, generate 3D-surface with textures
    modules.buildings.GenerateBuildings() # Process vector buildings and generate voxel's world
    modules.earth.PrepareLivingBuffer() # Calculate buffer zones around living buildings if ShowSquares mode is 'buffer'
    modules.megaphones.LoadMegaphones() # Load megaphones points
    modules.doorphones.LoadDoorphones() # Load doorphones data and assign flags to gdfBuildings
    env.clearMemory() # Clear memory from unused variables
    modules.audibility.CalculateAudibility() # Calculate audibility of squares and voxels
    modules.earth.VizualizeAllSquares() # Generate squares of the earth's surface vizualization
    modules.buildings.VizualizeAllVoxels() # Generate voxels of buildings vizualiztion
    modules.megaphones.VizualizeAllMegaphones() # Generate cones and spheres for megaphones vizualization

    # Prepare VTK-window for view and interact
    # ============================================
    env.logger.info("Prepare 3D model in viewer window...")
    env.Window.AddRenderer(env.Renderer)
    env.Renderer.SetBackground(0.2, 0.3, 0.4) #env.Colors.GetColor3d("ivory_black")
    env.Interactor.SetRenderWindow(env.Window)
    env.Window.AddRenderer(env.Renderer)
    env.Interactor.SetRenderWindow(env.Window)

    # Prepare VTK 3D-objects
    # ============================================
    for actor in env.actAxes: env.Renderer.AddActor(actor) # tqdm is not needed
    for actor in env.actCube: env.Renderer.AddActor(actor)
    for actor in env.actDEM: env.Renderer.AddActor(actor)
    for actor in env.actSurface: env.Renderer.AddActor(actor)
    for actor in env.actTexture: env.Renderer.AddActor(actor)
    for actor in env.actSquares: env.Renderer.AddActor(actor)
    for actor in env.actVoxels: env.Renderer.AddActor(actor)
    for actor in env.actMegaphones: env.Renderer.AddActor(actor)
    modules.lighting.PrepareLights(env.Renderer) # Generate lights for 3D-visualization
    for light in env.lights: env.Renderer.AddLight(light)

    # Prepare VTK-window
    # ============================================
    env.Interactor.Initialize()
    env.Renderer.ResetCamera()
    env.Window.Render()
    env.Interactor.SetInteractorStyle(vtk.vtkInteractorStyleTerrain())

    # Calculate and print the elapsed time
    # ============================================
    end_time = time.time() # Record the end time
    elapsed_time = end_time - start_time
    elapsed_minutes = int(elapsed_time // 60)
    elapsed_seconds = int(elapsed_time % 60)
    env.logger.success("The whole job took: {} minutes {} seconds", elapsed_minutes, elapsed_seconds)

    # Run VTK-window
    # ============================================
    env.logger.success("Done. Ready for viewing!")
    env.Interactor.Start()

    # Finish
    # ============================================
    env.logger.success("Glad to work hard, see you again!")
    env.logger.info("Please wait for the completion of memory cleanup...")