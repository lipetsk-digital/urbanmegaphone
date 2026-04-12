# ============================================
# Module: Generate voxels for earth ground vector buildings
# ============================================

# Modules import
# ============================================

# Standart modules
import multiprocessing as mp # Use multiprocessing
import ctypes # Use primitive datatypes for multiprocessing data exchange
import numpy as np # For arrays of numbers
import pandas as pd # For tables of data
import geopandas as gpd # For vector objects
from vtkmodules.vtkCommonDataModel import vtkPolyData # Use 3D-primitives
from vtkmodules.vtkRenderingCore import (vtkActor, vtkPolyDataMapper) # Use VTK rendering
import vtk # Use other 3D-visualization features
import gc # For garbage collectors

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition
import modules.earth # The earth's surface routines


# ============================================
# Process vector buildings and generate voxel's world
# ============================================
def GenerateBuildings():

    env.logger.info("Convert vector buildings to our world dimensions...")

    # Convert 2D-coordinates of buildings GeoDataFrame from meters (Web-Mercator ESPG:3857) to vtk's float
    env.logger.trace(env.gdfBuildings)
    env.gdfBuildings = env.gdfBuildings.set_crs(None, allow_override=True)
    env.gdfBuildings.geometry = env.gdfBuildings.geometry.scale(xfact=1.0, yfact=-1.0, zfact=1.0, origin=(0,0))
    env.logger.trace(env.gdfBuildings)
    env.gdfBuildings.geometry = env.gdfBuildings.geometry.translate(xoff=-env.boundsMin[0], yoff=env.boundsMax[1], zoff=0.0)
    env.logger.trace(env.gdfBuildings)
    env.logger.success("{} vector buildings found", env.printLong(len(env.gdfBuildings.index)))

    # Remove buildings outside of currend world
    env.gdfBuildings = env.gdfBuildings.loc[env.gdfBuildings.within(env.plgnBounds)]
    # Add unique identificator of building (UIB)
    env.gdfBuildings['UIB'] = np.arange(len(env.gdfBuildings.index))
    env.logger.success("{} buildings left after removing buildings outside of current world area", env.printLong(len(env.gdfBuildings.index)))
    env.logger.trace(env.gdfBuildings)

    env.logger.info("Split buildings to voxel's grid cells...")

    # Join buildings and centers of voxel's squares GeoDataFrames
    env.gdfCellsBuildings = env.gdfBuildings.sjoin(env.gdfCells, how='inner', predicate='contains')
    env.gdfCellsBuildings = env.gdfCellsBuildings.drop(labels='index_right', axis='columns')
    env.logger.trace(env.gdfCellsBuildings)
    env.logger.success("{} from {} cells are under buildings", 
                       env.printLong(len(env.gdfCellsBuildings.index)), env.printLong(len(env.gdfCells.index)))

    # Find ground points for each cell
    env.logger.info("Looking for ground points of each building...")
    gp = []  # Use "for" loop, not "apply" to show progress bar
    for cell in env.tqdm(env.gdfCellsBuildings.itertuples(), total=len(env.gdfCellsBuildings.index)):
        gp.append(modules.earth.getGroundHeight(cell.x, cell.y, None))
    env.gdfCellsBuildings['GP'] = gp
    #env.gdfCellsBuildings['GP'] = env.gdfCellsBuildings.apply(lambda x : modules.earth.getGroundHeight(x['x'],x['y'],None), axis='columns')
    env.logger.trace(env.gdfCellsBuildings)

    # Find common ground point for each buildnig
    if cfg.BuildingGroundMode != 'levels':
        pdMinGroundPoints = pd.pivot_table(data = env.gdfCellsBuildings, index=['UIB'], values=['GP'], aggfunc={'GP':cfg.BuildingGroundMode})
        env.logger.trace(pdMinGroundPoints)
        env.gdfBuildings = env.gdfBuildings.merge(right=pdMinGroundPoints, how='left', left_on='UIB', right_on='UIB')
        env.gdfCellsBuildings = env.gdfCellsBuildings.merge(right=pdMinGroundPoints, how='left', on='UIB', suffixes=[None, '_agg'])
        env.logger.trace(env.gdfBuildings)
        env.logger.trace(env.gdfCellsBuildings)
        del pdMinGroundPoints
        gc.collect()

    # Save buildings parameters
    # Save floors, flats and average ground for buildings by their UIBs
    env.logger.info("Allocate memory and store buildings parameters...")
    env.countBuildings = len(env.gdfBuildings.index)
    env.countBuildingsCells = len(env.gdfCellsBuildings.index)
    env.LivingBuildings = 0
    env.countFlats = 0
    env.buildings = mp.RawArray(ctypes.c_ushort, env.countBuildings*env.sizeBuilding)
    for b in env.gdfBuildings.itertuples(): # tqdm is not needed
        env.buildings[int(b.UIB*env.sizeBuilding)] = int(b.floors)
        if cfg.BuildingGroundMode != 'levels':
            if not(np.isnan(b.GP)):
                env.buildings[int(b.UIB*env.sizeBuilding+1)] = int(b.GP)
        if not(np.isnan(b.flats)):
            if b.flats>0:
                env.buildings[int(b.UIB*env.sizeBuilding+2)] = int(b.flats)
                env.LivingBuildings = env.LivingBuildings + 1
                env.countFlats = env.countFlats + int(b.flats)
    # Loop through cells and count voxels count. Save voxels index and UIBs for each cell
    env.countVoxels = 0
    env.countLivingVoxels = 0
    for cell in env.tqdm(env.gdfCellsBuildings.itertuples(), total=len(env.gdfCellsBuildings.index)):
        env.uib[cell.x*env.bounds[1]+cell.y] = int(cell.UIB)
        env.VoxelIndex[int(cell.x*env.bounds[1]+cell.y)] = int(env.countVoxels)
        env.countVoxels = env.countVoxels + int(cell.floors)
        if not(np.isnan(cell.flats)):
            if cell.flats>0:
                env.countLivingVoxels = env.countLivingVoxels + int(cell.floors)
        env.buildings[int(cell.UIB*env.sizeBuilding+3)] = env.buildings[int(cell.UIB*env.sizeBuilding+3)] + int(cell.floors)
    # Allocate memory for buildings voxels
    env.audibilityVoxels = mp.RawArray(ctypes.c_byte, env.countVoxels)
    env.logger.success("{} buildings stored (including {} living buildings). {} flats found", 
                       env.printLong(env.countBuildings), env.printLong(env.LivingBuildings), env.printLong(env.countFlats) )
    env.logger.success("{} voxels of buildings allocated (including {} living voxels)",
                       env.printLong(env.countVoxels), env.printLong(env.countLivingVoxels) )

# ============================================
# Generate necessary voxel VTK objects from vtkPoints 
# with the specified color and opacity to buildings vizualization
# IN: 
# points - vtkPoints collection
# color - tuple of three float number 0..1 for R,G,B values of color (0% .. 100%)
# opacity - float number 0..1 for opacity value (0% .. 100%)
# OUT:
# No return values. Modify variables of environment.py in which VTK objects for further vizualization
# ============================================
def VizualizePartOfVoxels(points, color, opacity):
    # Put Voxels on intersection points
    polyDataVoxels = vtkPolyData()
    polyDataVoxels.SetPoints(points)
    env.pldtVoxels.append(polyDataVoxels)
    cubeVoxel = vtk.vtkCubeSource()
    cubeVoxel.SetXLength(cfg.sizeVoxel-cfg.gapVoxel)
    cubeVoxel.SetYLength(cfg.sizeVoxel-cfg.gapVoxel)
    cubeVoxel.SetZLength(cfg.sizeVoxel-cfg.gapVoxel)
    env.cbVoxels.append(cubeVoxel)
    glyphVoxels = vtk.vtkGlyph3D()
    glyphVoxels.SetInputData(polyDataVoxels)
    glyphVoxels.SetSourceConnection(cubeVoxel.GetOutputPort())
    glyphVoxels.ScalingOff()
    glyphVoxels.Update()
    env.glphVoxels.append(glyphVoxels)
    pointsMapperVoxels = vtkPolyDataMapper()
    pointsMapperVoxels.SetInputConnection(glyphVoxels.GetOutputPort())
    pointsMapperVoxels.ScalarVisibilityOff()
    env.mapVoxels.append(pointsMapperVoxels)
    pointsActorVoxels = vtkActor()
    pointsActorVoxels.SetMapper(pointsMapperVoxels)
    pointsActorVoxels.GetProperty().SetColor(color)
    pointsActorVoxels.GetProperty().SetOpacity(opacity)
    env.actVoxels.append(pointsActorVoxels)

# ============================================
# Generate voxels of building vizualization
# from previously calculated and classified points
# ============================================
def VizualizeAllVoxels():
    env.logger.info("Build voxels of buildings...")

    # Loop throught grid of the earth's surface cells audibility
    idx2D = 0
    totalCells = 0
    totalFlats = 0
    totalVoxels = 0
    audibilityFlats = 0
    for x in env.tqdm(range(env.bounds[0])):
        for y in range(env.bounds[1]):
            uib = env.uib[idx2D]
            if uib>=0:
                totalCells = totalCells + 1
                idxZ = env.VoxelIndex[idx2D]
                floors = env.buildings[uib*env.sizeBuilding]
                flats = env.buildings[uib*env.sizeBuilding+2]
                voxels = env.buildings[uib*env.sizeBuilding+3]
                totalVoxels = totalVoxels + floors
                if cfg.BuildingGroundMode != 'levels':
                    z = env.buildings[uib*env.sizeBuilding+1]
                else:
                    z = env.ground[idx2D]
                for floor in range(floors):
                    audibility = env.audibilityVoxels[idxZ+floor]
                    if audibility>0:
                        env.pntsVoxels_yes.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.5+floor)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel)
                        totalFlats = totalFlats + flats/voxels
                        audibilityFlats = audibilityFlats + flats/voxels
                    elif audibility<0:
                        env.pntsVoxels_no.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.5+floor)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel)
                        totalFlats = totalFlats + flats/voxels
                    else:
                        if flats>0:
                            env.pntsVoxels_no.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.5+floor)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel) # not env.pntsVoxels_living
                            totalFlats = totalFlats + flats/voxels
                        else:
                            env.pntsVoxels_industrial.InsertNextPoint((x+0.5)*cfg.sizeVoxel, (z+0.5+floor)*cfg.sizeVoxel, (y+0.5)*cfg.sizeVoxel)
            idx2D = idx2D + 1

    VizualizePartOfVoxels(env.pntsVoxels_yes, env.Colors.GetColor3d("Green"), 1)
    VizualizePartOfVoxels(env.pntsVoxels_no, env.Colors.GetColor3d("Tomato"), 1)
    VizualizePartOfVoxels(env.pntsVoxels_industrial, env.Colors.GetColor3d("Gray"), 1)
    VizualizePartOfVoxels(env.pntsVoxels_doorphones, env.Colors.GetColor3d("Cyan"), 1)

    env.vtkPoints2CSV('vox_industrial.csv', env.pntsVoxels_industrial)
    env.vtkPoints2CSV('vox_yes.csv', env.pntsVoxels_yes)
    env.vtkPoints2CSV('vox_no.csv', env.pntsVoxels_no)
    env.vtkPoints2CSV('vox_doorphones.csv', env.pntsVoxels_doorphones)
    env.logger.success("Voxels exported")

    livingVoxels = env.pntsVoxels_yes.GetNumberOfPoints() + env.pntsVoxels_no.GetNumberOfPoints()

    env.writeStat("=========================================================================================================")
    env.writeStat("|| BUILDINGS STATISTICS:")
    env.writeStat("|| {} ({}) audibility voxels, {} ({}) non-audibility voxels, {} non-living voxels".format(
                  env.printLong(env.pntsVoxels_yes.GetNumberOfPoints()),
                  f'{env.pntsVoxels_yes.GetNumberOfPoints()/livingVoxels:.0%}',
                  env.printLong(env.pntsVoxels_no.GetNumberOfPoints()),
                  f'{env.pntsVoxels_no.GetNumberOfPoints()/livingVoxels:.0%}',
                  env.printLong(env.pntsVoxels_industrial.GetNumberOfPoints()) ) )
    env.logger.debug("|| {} ({}) of {} building's cells analyzed",
                     env.printLong(totalCells), f'{totalCells/env.countBuildingsCells:.0%}', env.printLong(env.countBuildingsCells) )
    env.logger.debug("|| {} ({}) of {} voxels analyzed",
                     env.printLong(totalVoxels), f'{totalVoxels/env.countVoxels:.0%}', env.printLong(env.countVoxels) )
    env.writeStat("|| {} ({}) of {} living voxels analyzed".format(
                    env.printLong(livingVoxels), f'{livingVoxels/env.countLivingVoxels:.0%}', env.printLong(env.countLivingVoxels) ), "info" )
    env.writeStat("|| {} ({}) of {} flats are audibility, {} ({}) non-audibility flats".format(
                       env.printLong(round(audibilityFlats)), f'{audibilityFlats/totalFlats:.0%}', env.printLong(round(totalFlats)),
                       env.printLong(round(totalFlats)-round(audibilityFlats)), f'{(1-audibilityFlats/totalFlats):.0%}' ) )
    env.writeStat("|| {} ({}) of {} flats analyzed".format(
                       env.printLong(round(totalFlats)), f'{totalFlats/env.countFlats:.0%}', env.printLong(env.countFlats) ), "info" )
    env.writeStat("=========================================================================================================")
