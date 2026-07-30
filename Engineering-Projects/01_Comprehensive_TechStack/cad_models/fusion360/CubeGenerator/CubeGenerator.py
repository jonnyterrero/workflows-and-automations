"""Fusion 360 script: generate a parametric solid cube.

Default output is a 3 m x 3 m x 3 m cube, anchored at the origin of a new
component, driven by a single user parameter named ``cube_size``.

Install:
    Copy this folder (CubeGenerator/) into the Fusion scripts directory:
      Windows: %APPDATA%\\Autodesk\\Autodesk Fusion 360\\API\\Scripts
      macOS:   ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts

Run:
    Utilities tab -> ADD-INS -> Scripts and Add-Ins -> Scripts -> CubeGenerator -> Run

Edit the cube afterwards by changing ``cube_size`` in Modify -> Change Parameters;
the sketch and the extrude both reference it, so the cube stays a cube.
"""

import traceback

import adsk.core
import adsk.fusion

# Single source of truth for the cube edge length. Any valid Fusion expression
# works here, e.g. '3 m', '3000 mm', '3 in'. Keep CUBE_SIZE_UNITS in step with
# the unit used in the expression.
CUBE_SIZE_EXPRESSION = '3 m'
CUBE_SIZE_UNITS = 'm'

PARAM_NAME = 'cube_size'
COMPONENT_NAME = 'Cube'
BODY_NAME = 'Cube'


def _upsert_parameter(design: adsk.fusion.Design) -> adsk.fusion.UserParameter:
    """Create the cube_size user parameter, or update it if it already exists."""
    existing = design.userParameters.itemByName(PARAM_NAME)
    if existing:
        existing.expression = CUBE_SIZE_EXPRESSION
        return existing

    return design.userParameters.add(
        PARAM_NAME,
        adsk.core.ValueInput.createByString(CUBE_SIZE_EXPRESSION),
        CUBE_SIZE_UNITS,
        'Edge length of the generated cube',
    )


def _draw_square(component: adsk.fusion.Component, edge_cm: float) -> adsk.fusion.Profile:
    """Sketch a fully constrained square on XY, one corner on the origin."""
    sketch = component.sketches.add(component.xYConstructionPlane)
    sketch.name = 'Cube Base'

    rectangle = sketch.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(edge_cm, edge_cm, 0),
    )

    bottom = rectangle.item(0)
    right = rectangle.item(1)

    # Pin the rectangle to the sketch origin so the body cannot float when the
    # parameter changes.
    sketch.geometricConstraints.addCoincident(bottom.startSketchPoint, sketch.originPoint)

    # Drive both edges off the same parameter -> always a square.
    width = sketch.sketchDimensions.addDistanceDimension(
        bottom.startSketchPoint,
        bottom.endSketchPoint,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        adsk.core.Point3D.create(edge_cm / 2, -edge_cm / 4, 0),
    )
    width.parameter.expression = PARAM_NAME

    height = sketch.sketchDimensions.addDistanceDimension(
        right.startSketchPoint,
        right.endSketchPoint,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        adsk.core.Point3D.create(edge_cm * 1.25, edge_cm / 2, 0),
    )
    height.parameter.expression = PARAM_NAME

    return sketch.profiles.item(0)


def _extrude_cube(component: adsk.fusion.Component, profile: adsk.fusion.Profile) -> adsk.fusion.ExtrudeFeature:
    """Extrude the square by the same parameter to close the cube."""
    extrudes = component.features.extrudeFeatures
    extrude_input = extrudes.createInput(
        profile,
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    distance = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByString(PARAM_NAME)
    )
    extrude_input.setOneSideExtent(
        distance,
        adsk.fusion.ExtentDirections.PositiveExtentDirection,
    )

    extrude = extrudes.add(extrude_input)
    extrude.name = 'Cube Extrude'
    return extrude


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox('No active Fusion design. Open a design and run the script again.')
            return

        # Parametric modeling is required for user parameters and editable features.
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        design.fusionUnitsManager.distanceDisplayUnits = (
            adsk.fusion.DistanceUnits.MeterDistanceUnits
        )

        parameter = _upsert_parameter(design)

        # Fusion's internal length unit is centimeters; convert before creating geometry.
        edge_cm = design.unitsManager.evaluateExpression(
            CUBE_SIZE_EXPRESSION, CUBE_SIZE_UNITS
        )

        occurrence = design.rootComponent.occurrences.addNewComponent(
            adsk.core.Matrix3D.create()
        )
        component = occurrence.component
        component.name = COMPONENT_NAME

        profile = _draw_square(component, edge_cm)
        extrude = _extrude_cube(component, profile)
        extrude.bodies.item(0).name = BODY_NAME

        ui.messageBox(
            'Created a {0} cube.\n\nEdit "{1}" in Modify > Change Parameters to resize it.'.format(
                parameter.expression, PARAM_NAME
            )
        )

    except Exception:
        if ui:
            ui.messageBox('CubeGenerator failed:\n{0}'.format(traceback.format_exc()))
