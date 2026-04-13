# ============================================
# Module: Generate lights for 3D-visualization
# ============================================

import vtk # Use other 3D-visualization features
import modules.environment as env # Environment defenition

def PrepareLights(renderer):

    # Calculate scene bounds to position lights appropriately
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
    env.lights.append(ambient_light)

    # Add main directional light from above (like sun)
    sun_light = vtk.vtkLight()
    sun_light.SetLightTypeToSceneLight()
    sun_light.SetPosition(scene_center[0], y_max + scene_depth * 2, scene_center[2])
    sun_light.SetFocalPoint(scene_center[0], scene_center[1], scene_center[2])
    sun_light.SetColor(1, 1, 1)
    sun_light.SetIntensity(0.7)
    env.lights.append(sun_light)

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
    env.lights.append(corner1)

    # Front-right corner
    corner2 = vtk.vtkLight()
    corner2.SetLightTypeToSceneLight()
    corner2.SetPosition(x_max + scene_width * 0.3, corner_height, z_max + scene_height * 0.3)
    corner2.SetFocalPoint(scene_center[0], y_min, scene_center[2])
    corner2.SetColor(1, 1, 1)
    corner2.SetIntensity(corner_intensity)
    env.lights.append(corner2)

    # Back-left corner
    corner3 = vtk.vtkLight()
    corner3.SetLightTypeToSceneLight()
    corner3.SetPosition(x_min - scene_width * 0.3, corner_height, z_min - scene_height * 0.3)
    corner3.SetFocalPoint(scene_center[0], y_min, scene_center[2])
    corner3.SetColor(1, 1, 1)
    corner3.SetIntensity(corner_intensity)
    env.lights.append(corner3)

    # Back-right corner
    corner4 = vtk.vtkLight()
    corner4.SetLightTypeToSceneLight()
    corner4.SetPosition(x_max + scene_width * 0.3, corner_height, z_min - scene_height * 0.3)
    corner4.SetFocalPoint(scene_center[0], y_min, scene_center[2])
    corner4.SetColor(1, 1, 1)
    corner4.SetIntensity(corner_intensity)
    env.lights.append(corner4)

    # Add side lights at mid-height for building sides
    side_height = scene_center[1] + scene_depth * 0.3

    # Left side
    left_light = vtk.vtkLight()
    left_light.SetLightTypeToSceneLight()
    left_light.SetPosition(x_min - scene_width, side_height, scene_center[2])
    left_light.SetFocalPoint(scene_center[0], scene_center[1], scene_center[2])
    left_light.SetColor(1, 1, 1)
    left_light.SetIntensity(0.3)
    env.lights.append(left_light)

    # Right side
    right_light = vtk.vtkLight()
    right_light.SetLightTypeToSceneLight()
    right_light.SetPosition(x_max + scene_width, side_height, scene_center[2])
    right_light.SetFocalPoint(scene_center[0], scene_center[1], scene_center[2])
    right_light.SetColor(1, 1, 1)
    right_light.SetIntensity(0.3)
    env.lights.append(right_light)