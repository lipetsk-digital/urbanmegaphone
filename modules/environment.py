# ============================================
# Module: Environment defenition
# ============================================


# Modules import
# ============================================

# Standart modules
from loguru import logger # Write log
from tqdm import tqdm # Write log
from vtkmodules.vtkCommonCore import vtkPoints # Use points clouds in 3D-world
from vtkmodules.vtkIOImage import vtkImageReader2Factory # Read raster images from files
from vtkmodules.vtkRenderingCore import ( vtkRenderer, vtkRenderWindow, vtkRenderWindowInteractor ) # All for render 3D-models
from vtkmodules.vtkCommonColor import vtkNamedColors # Use colors
import vtkmodules.vtkRenderingOpenGL2 # Use OpenGL for render
import math # For rounding up numbers
import gc # For garbage collectors
from pathlib import Path # Crossplatform pathing

# Own core modules
import modules.settings as cfg # Settings defenition


# Global variables defenition
# ============================================

# World dimensions (float, meters, Web-Mercator ESPG:3857)
boundsMin = [None, None, None] #lon, lat, height
boundsMax = [None, None, None] #lon, lat, height

# Voxel's world dimensions (integer)
bounds = [None, None, None] #x_lon, y_lat, z_height

# Multiprocessing data in shared memory
# ============================================

# Squares matrix: 2D-array of signed short integer values [−32 767, +32 767]:
# integer vertical z-coordinate of first voxel over earth's surface in current point.
# At first initialized by -1 values
ground = None

# Squares matrix: 2D-array of signed byte integer values [−127, +127]:
# integer value of audibility on the earth's surface in this place: 
# -1 (no), 0 (unknown), 1(only on the streets here), 2(on the streets and in the buildings)
# At first initialized by 0 values
audibility2D = None # Just matrix

# Squares matrix: 2D-array of signed long integer values [−2 147 483 647, +2 147 483 647]:
# integer unique building's identificator in this place.
# At first initialized by -1 values
countBuildingsCells = None # Total count of buildings cells (uib>=0)
uib = None # Just array

# Squares matrix: 2D-array of unsigned long integer values [0, 4 294 967 295]:
# integer index of first signed byte element of first floor voxel in flat audibilityVoxels array
# At first initialized by 0 values
VoxelIndex = None

# Linear array: 1D-array of signed byte integer values [−127, +127]:
# integer value of audibility on voxels of buildings: -1 (no), 0 (unknown), 1 or 2 (yes)
# use VoxelIndex matrix to find desired index of element in this array
# Contains separate sequential values for each floor
# At first initialized by 0 values
countVoxels = None # Total count of buildings voxels
countLivingVoxels = None # Count of living-buildings voxels
audibilityVoxels = None # Just array

# Linear array: 1D-array of the six values of unsigned short integer values [0, 65535]:
# [UIB*6] value - count of floors
# [UIB*6+1] value - integer vertical coordinate of voxel of the first floor (if BuildingGroundMode != 'levels')
# [UIB*6+2] value - count of flats in building (0 for non-living buildings)
# [UIB*6+3] value - count of total voxels
# [UIB*6+4] value - count of total voxels with audibility
# [UIB*6+5] value - flag of doorphones: 0 (no), 1 (fact), 2 (plan)
sizeBuilding = 6 # count of values for each building
countBuildings = None # count of buildings
LivingBuildings = None # count of living buildings
countFlats = None # count of flats
buildings = None

# Store coordinates of cells for megaphones and its buffer zones
sizeCell = 2 # Each cell have two signed long integer values [−2 147 483 647, +2 147 483 647] for its (x,y) cells coordinates
countMegaphones = None # Total count of megaphones
leftMegaphones = None # Linear 1D-array [UIM] unsigned char with 1 if calculation process of current megaphone is still planed or running, and 0 if it is just finished
countMegaphonesCells = None # Count of cells under megaphones
MegaphonesCells = None # Linear 1D-array with couples (x,y) signed long integer coordinates of cells under megaphones
MegaphonesCells_count = None # Linear 1D-array with signed long integer values counts of each MegaphonesCells_count[UIM] cells in MegaphonesCells array
MegaphonesCells_index = None # Linear 1D-array with signed long integer values indexes first of MegaphonesCells_index[UIM] cell in MegaphonesCells array
countMegaphonesBuffersInt = None # Count of cells in megaphones buffer zones in the buildings
MegaphonesBuffersInt = None # Linear 1D-array with couples (x,y) signed long integer coordinates of cells under buffer zones in the buildings of megaphones
MegaphonesBuffersInt_count = None # Linear 1D-array with signed long integer values counts of each MegaphonesBuffers_count[UIM] cells in MegaphonesBuffers array
MegaphonesBuffersInt_index = None # Linear 1D-array with signed long integer values indexes first of MegaphonesBuffers_index[UIM] cell in MegaphonesBuffers array
countMegaphonesBuffersExt = None # Count of cells in megaphones buffer zones on the streets
MegaphonesBuffersExt = None # Linear 1D-array with couples (x,y) signed long integer coordinates of cells under buffer zones on the streets of megaphones
MegaphonesBuffersExt_count = None # Linear 1D-array with signed long integer values counts of each MegaphonesBuffers_count[UIM] cells in MegaphonesBuffers array
MegaphonesBuffersExt_index = None # Linear 1D-array with signed long integer values indexes first of MegaphonesBuffers_index[UIM] cell in MegaphonesBuffers array
countChecks = None # Linear 1D-array [UIM] unsigned long long with count of total ckesks for audibility calculation (combination of megaphones cells and buffers cells)
madeChecks = None # Linear 1D-array [UIM] unsigned long long with counters of calculated checks at current time
totalChecks = None # integer count of total ckesks for audibility calculation (combination of megaphones cells and buffers cells)

# DatraFrame, GeoDataFrame tables, Shapely geometries
# ============================================

# Shapely Geometries
plgnBounds = None # 2D rectangle of VTK's world (shapely.geometry.Polygon)

# GeoPandas GeoDataFrames
gdfBuildings = None # Geometric 2D vector objects of buildings loaded from vector files
gdfCells = None # 2D grid of points - centers of voxels on the plane # Excluded to save memory
gdfCellsBuildings = None # 2D intersect of buildings and voxels centers
gdfBuffersLiving = None # 2D voxels centers of buffer zones arround living buildings (if ShowSquares = 'buffer')
gdfMegaphones = None # 2D points of megaphones
gdfCellsMegaphones = None # 2D cells under megaphones
gdfBuffersMegaphonesInt = None # 2D voxels centers of buffer zones of possible audibility arround megaphones in the buildings
gdfBuffersMegaphonesExt = None # 2D voxels centers of buffer zones of possible audibility arround megaphones at the streets

# Miscellaneous data
# ============================================

# Buildings statistic:
maxFloors = None 
sumFlats = None

# VTK 3D-vizualization objects
# ============================================

# Single VTK objects
readerFactory = vtkImageReader2Factory()
Colors = vtkNamedColors()
Renderer = vtkRenderer()
Window = vtkRenderWindow()
Interactor = vtkRenderWindowInteractor()

# Arrays of VTK objects: axis of coordinate system
actAxes = [] # vtkAxesActor

# Arrays of VTK objects: original raster texture files
cubeRASTER = [] # vtkCudeSource
mapCube = [] # vtkPolyDataMapper
actCube = [] # vtkActor
boxRASTER = [] # vtkBox
imgrdrRASTER = [] # vtkImageReader2

# Arrays of VTK objects: points of DEM
pntsDEM = [] # vtkPoints
pldtDEM = [] # vtkPolyData
sphrDEM = [] # vtkSphereSource
glphDEM = [] # vtkGlyph3D
mapDEM = [] # vtkPolyDataMapper
actDEM = [] # vtkActor

# Arrays of VTK objects: generated surface of DEM
srfsfltSurface = [] # vtkSurfaceReconstructionFilter
cntrfltSurface = [] # vtkContourFilter
rvrsfltSurface = [] # vtkReverseSense
pldtSurface = [] # vtkPolyData
sphrSurface = [] # vtkSphereSource
glphSurface = [] # vtkGlyph3D
mapSurface = [] # vtkPolyDataMapper
actSurface = [] # vtkActor

# Arrays of VTK objects: clipped surface of DEM
clpprClipped = [] # vtkClipPolyData
pldtClipped = [] # vtkPolyData
pntsClipped = [] # vtkPoints
lctrClipped = [] # vtkCellLocator

# Arrays of VTK objects: raster texture on DEM's surface
fltarTexture = [] # vtkFloatArray array of texture coordinates
txtrTexture = [] # vtkTexture
mapTexture = [] # vtkPolyDataMapper
actTexture = [] # vtkActor
strTextureFileName = [] # string

# Arrays of VTK objects: polygonal squares of DEM's surface
pntsSquares_full = vtkPoints()
pntsSquares_only = vtkPoints()
pntsSquares_no = vtkPoints()
pldtSquares = [] # vtkPolyData
plnSquares = [] # vtkPlaneSource
glphSquares = [] # vtkGlyph3D
mapSquares = [] # vtkPolyDataMapper
actSquares = [] # vtkActor

# Arrays of VTK objects: cubes of buildings
pntsVoxels_yes = vtkPoints()
pntsVoxels_no = vtkPoints()
pntsVoxels_industrial = vtkPoints()
pntsVoxels_doorphones_fact = vtkPoints()
pntsVoxels_doorphones_plan = vtkPoints()
pldtVoxels = [] # vtkPolyData
cbVoxels = [] # vtkCubeSource
glphVoxels = [] # vtkGlyph3D
mapVoxels = [] # vtkPolyDataMapper
actVoxels = [] # vtkActor

# Arrays of VTK object: megaphones
pntsMegaphones_buildings_cones = vtkPoints()
pntsMegaphones_standalone_cones = vtkPoints()
pntsMegaphones_spheres = vtkPoints()
pldtMegaphones = [] # vtkPolyData
cnMegaphones = [] # vtkConeSource
sphMegaphones = [] # vtkSphereSource
glphMegaphones = [] # vtkGlyph3D
mapMegaphones = [] # vtkPolyDataMapper
actMegaphones = [] # vtkActor


# Environment initialization (applied for each process)
# ============================================

# Apply selected logging level
logger.remove()
logger.add(lambda msg: tqdm.write(msg, end=""), level=cfg.logLevel, colorize=True)


# ============================================
# Accept three coordinates in meters [lon, lat, height]
# and return three float coordinates of VTK space without rounding [x_vtk, y_vtk, z_vtk]
# ============================================
def coordM2Float(meters):
    floats = []
    floats.append( (float(meters[0])-boundsMin[0]) )
    floats.append( (float(meters[2])-boundsMin[2]) )
    floats.append( (float(boundsMax[1]-meters[1])) )
    return floats

# ============================================
# Accept two pairs of two coordinates in meters (bounding box): lon_min, lon_max, lat_min, lat_max]
# and return two pairs int coordinates of woxel world (bounding box) [x_min, x_max, y_min. y_max]
# ============================================
def boxM2Int(lon_min, lon_max, lat_min, lat_max):
    x_min = math.floor(lon_min/cfg.sizeVoxel)
    x_max = math.ceil(lon_max/cfg.sizeVoxel)
    y_min =math.floor(lat_min/cfg.sizeVoxel)
    y_max = math.ceil(lat_max/cfg.sizeVoxel)
    if ( ( (x_min<0) and (x_max<0) ) or
         ( (x_min>bounds[0]) and (x_max>bounds[0]) ) or
         ( (y_min<0) and (y_max<0) ) or
         ( (y_min>bounds[1]) and (y_max>bounds[1]) ) ):
        return [None, None, None, None]
    if x_min<0:
        x_min = 0
    if x_max>bounds[0]:
        x_max = bounds[0]
    if y_min<0:
        y_min = 0
    if y_max>bounds[1]:
        y_max = bounds[1]
    return [x_min, x_max, y_min, y_max]

# ============================================
# Return number, formatet with using '.' (point) as thousands and millions delimeter
# ============================================
def printLong(number):
    return f'{number:_}'.replace("_", ".")

# ============================================
# Write points to CSV file
# ============================================
def vtkPoints2CSV(filename, points):
    with open(Path('.',cfg.folderOUTPUT, filename), 'w') as file:
        file.write("x,y,z\n")
        for i in range(points.GetNumberOfPoints()):
            point = points.GetPoint(i)
            file.write(f'{point[0]},{point[1]},{point[2]}\n')

# ============================================
# Write to TXT file and log a message with the specified level
# ============================================
def writeStat(message, level="success"):
    with open(Path('.', cfg.folderOUTPUT, 'result.txt'), 'a') as file:
        file.write(message+"\n")
    getattr(logger, level)(message)

# ============================================
# Clear memory from unused GeoPandas GeoDataSet's
# ============================================
def clearMemory():
    logger.info("Clear memory. It may take a few minutes...")

    global gdfCells
    del gdfCells

    global gdfCellsBuildings
    del gdfCellsBuildings

    global gdfBuffersLiving
    del gdfBuffersLiving

    global gdfMegaphones
    del gdfMegaphones

    global gdfCellsMegaphones
    del gdfCellsMegaphones

    global gdfBuffersMegaphonesInt
    del gdfBuffersMegaphonesInt

    global gdfBuffersMegaphonesExt
    del gdfBuffersMegaphonesExt

    gc.collect()
    logger.success("Memory clean. Continue soon...")

