# CuraOpenSCADIntegrationPlugin



# Workflow

Inteded workflow is to export all required OpenSCAD objects (meshes) as individual geometries, as below.

```
/*cura-export 'baseplate()' AS Baseplate */
/*cura-export 'reinforcment(d = 14)' AS Reinforcment100 */
/*cura-export 'reinforcment(d = 24)' AS Reinforcment50*/
/*cura-export 'support()' AS Support */
```

This will place four objects on the build plate. After defining 'Per Model Settings' for each of them, use 'Select All Models', 'Reset All Model Positions' and 'Group Models' to transform them into a single part.

Printing or saving the generated GCode will cause Cura to write all changes back to the OpenSCAD file like below. The difference here is that this is only a single Part made from four meshes with specific settings per mesh.

```
/* cura-export
    'baseplate()' AS Baseplate SETTINGS
        infill_sparse_density = 25
    'reinforcment(d = 14)' AS Reinforcment100 SETTINGS
        infill_mesh = True,
        infill_sparse_density = 100
    'reinforcment(d = 24)' AS Reinforcment50 SETTINGS
        infill_mesh = True,
        infill_sparse_density = 50
    'support()' AS Support SETTINGS
        support_mesh = True
*/
```

Note: You don't need to memorize all the different settings if you follow this workflow.

# Parser syntax

* Each comment section creates one printable object, possibly made from several meshes (grouped), on the build plate.
* Each mesh can have it's own settings, e. g. type of mesh (support, infill etc.), used extruder etc.
* No two meshes must be identical (e.g. 'cube([1, 1, 1])') unless they are given unique names with 'AS ...'.

# Under the hood

Meshes a rendered by creating temporary files and starting openscad in the background to render them. OpenSCAD root modifier (!) is used to ensure that only the required mesh is rendered, e. g.:

```
!baseplate();
include <example.scad>;
```

The downside to this approache is that every mesh has to be render from scratch whenever it is loaded, no caching of geometry between two meshes.
