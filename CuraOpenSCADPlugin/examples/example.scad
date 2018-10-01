/*
  Inteded workflow is to export all required OpenSCAD objects (meshes)
  as individual geometries, as below.
*/

/*cura-export 'baseplate()' AS Baseplate */
/*cura-export 'reinforcment(d = 14)' AS Reinforcment100 */
/*cura-export 'reinforcment(d = 24)' AS Reinforcment50*/
/*cura-export 'support()' AS Support */

/*
  This will place four objects on the build plate. After defining
  'Per Model Settings' for each of them, use 'Select All Models',
  'Reset All Model Positions' and 'Group Models' to transform them
  into a single part.

  (not implemented yet) Printing or saving the generated GCode will
  cause Cura to write all changes back to the OpenSCAD file like below.
  The difference ist here is that this is only a single Part made from
  four meshes with specific settings per mesh.
*/

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

module relief(ri = 10, ro = 12, h = 3) {
   difference() {
       cylinder(r = ro, h = h);
       translate([0, 0, -0.01]) cylinder(r = ri, h = h + 0.02);
   }    
}

module centers(x, y, z = 0) {
   for(tx = [-x/2, x/2], ty = [-y/2, y/2])
       translate([tx, ty, z]) children();
}

module reinforcment(x = 50, y = 50, d = 8, h = 10) {
  centers(x, y) cylinder(r = d/2, h = h); 
}

module support(x = 50, y = 50) {
   translate([0, 0, 2.5]) {
     cube([x - 10, 10, 5.01], center = true);
     cube([10, y - 10, 5.01], center = true);
   }
}

module nosupport(x = 50, y = 50, d = 8) {
   centers(x, y, -0.01) relief(ri = d/2 + 4, ro = d/2 + 6);
}

module baseplate(x = 50, y = 50, d = 8, h = 10) {
   difference() {
       hull() centers(x, y) cylinder(r = 2 * d, h = h);
       centers(x, y, -0.01) cylinder(r = d/2, h = h + 0.02);
       support(x, y, d);
       nosupport(x, y);
   }
}

baseplate();
%color([0.5, 0, 0, 0.75]) reinforcment(d = 14, h = 10.2);
%color([0.5, 0.25, 0.25, 0.75]) reinforcment(d = 24, h = 10.1);
%color([0.75, 0.75, 1.0, 0.5]) support();