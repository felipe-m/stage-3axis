# to execute from the FreeCAD console:
#  execute freecad from the cmd console on the directory
# "C:\Program Files\FreeCAD 0.16\bin\freecad" base.py

# to excute from command line in windows:
# "C:\Program Files\FreeCAD 0.16\bin\freecadcmd" base.py


# name of the file
filename = "base"

import os
import sys
import FreeCAD;
import Part;
import Draft;
import logging  # to avoid using print statements
#import copy;
#import Mesh;


# to get the current directory. Freecad has to be executed from the same
# directory this file is
filepath = os.getcwd()
#filepath = "./"
#filepath = "F/urjc/proyectos/2016_platform_cell/device/planos/python/"
#filepath = "C:/Users/felipe/urjc/proyectos/2016_platform_cell/device/planos/python/"

# to get the components
# In FreeCAD can be added: Preferences->General->Macro->Macro path
sys.path.append(filepath) 
# Either one of these 2 to select the path, inside the tree, copied by
# git subtree, or in its one place
#sys.path.append(filepath + '/' + 'modules/comps'
sys.path.append(filepath + '/' + '../comps')

import fcfun   # import my functions for freecad. FreeCad Functions
import kcit    # import citometer constants
#import mat_cte  # name changed to kcomp
import kcomp   # import material constants and other constants
import comps   # import my CAD components

from fcfun import V0, VX, VY, VZ, V0ROT, addBox, addCyl, fillet_len
from fcfun import addBolt, addBoltNut_hole, NutHole
from kcomp import TOL

# Taking the same axis as the 3D printer:
#
#    Z   Y
#    | /               USING THIS ONE
#    |/___ X
#
# as seen from the front
# be careful because at the beginning I was considering:
#      Z
#      |
#      |___ Y       NOT USING THIS ONE
#     /
#    / X
#
# In this design, the bas will be centered on X

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

doc = FreeCAD.newDocument()

"""
alumprof30_nam = ("misumi_profile_hfs_serie6_w8_30x30.FCStd")
doc_alumprof = FreeCAD.openDocument(alumprof30_nam)


list_obj_alumprofile = []
for obj in doc_alumprof.Objects:
    if (hasattr(obj,'ViewObject') and obj.ViewObject.isVisible()
        and hasattr(obj,'Shape') and len(obj.Shape.Faces) > 0 ):
       # len(obj.Shape.Faces) > 0 to avoid sketches
        list_obj_alumprofile.append(obj)
    if len(obj.Shape.Faces) == 0:
        orig_alumsk = obj
logging.debug("%s", list_obj_alumprofile)

FreeCAD.ActiveDocument = doc
alu_sk = doc.addObject("Sketcher::SketchObject", "alu_sk")
alu_sk.Geometry = orig_alumsk.Geometry
alu_sk.Constraints = orig_alumsk.Constraints
#alu_sk.Visibility = False
#alu_sk.Placement.Base = FreeCAD.Vector( kcit.ALU_W/2.0,  kcit.ALU_W/2.0, 0)

FreeCAD.closeDocument(doc_alumprof.Name)
FreeCAD.ActiveDocument = doc #otherwise, clone will not work
"""
"""

# Aluminum profiles for the citometer base

#  ------------- X alum profiles
# fb: front (y=0) bottom (z=0)
"""
h_alu_x_fb = comps.MisumiAlu30s6w8 (kcit.CIT_X -2 * kcit.ALU_W,
                                  "alu_x_fb", axis= 'x', cx=1, cy=1, cz=0)
alu_x_fb = h_alu_x_fb.CadObj
"""
alu_x_fb.Dir = (0,0,kcit.CIT_X - 2 * kcit.ALU_W)
alu_x_fb.Solid = True

# the base position of the X aluminum extrusion. 
alu_x_basepos =  FreeCAD.Vector ( -(alu_x_fb.Dir.Length)/2.0,
                                    kcit.ALU_W/2.0,
                                    kcit.ALU_W/2.0)
alu_x_fb.Placement.Base = alu_x_basepos
alu_x_fb.Placement.Rotation = FreeCAD.Rotation (VY, 90)
"""

# bb: back (y=0) bottom (z=0)
alu_x_bb = Draft.clone(alu_x_fb)
alu_x_bb.Label = "alu_x_bb"
alu_x_bb.Placement.Base = ( FreeCAD.Vector ( 0, kcit.CIT_Y - kcit.ALU_W,0)) 
"""

#  ------------- Y alum profiles
# lb: left (x=-) bottom (z=0)
alu_y_lb = doc.addObject("Part::Extrusion", "alu_y_lb")
alu_y_lb.Base = alu_sk
# the sketch is on XY, extrusion direction on Z. Centered on XY
# substracting the width of the aluminum profile
alu_y_lb.Dir = (0,0,kcit.CIT_Y - kcit.ALU_W)
alu_y_lb.Solid = True

# the base position of the Y aluminum extrusion (centered on X)
alu_y_basepos =  FreeCAD.Vector ( 0, 0,
                                  kcit.ALU_W/2.0)
# the position to the right end. taking away half of the aluminum extrusion
# width. So relative to the center, but since the aluminum extrusion is also
# centered, it is its position
alu_y_xendpos = FreeCAD.Vector(kcit.CIT_X/2.0 - kcit.ALU_W/2.0, 0, 0)

alu_y_lb.Placement.Base = alu_y_basepos - alu_y_xendpos
alu_y_lb.Placement.Rotation = FreeCAD.Rotation (VX, -90)

# rb: right (x=-) bottom (z=0)
alu_y_rb = Draft.clone(alu_y_lb)
alu_y_rb.Label = "alu_y_rb"
alu_y_lb.Placement.Base = alu_y_basepos + alu_y_xendpos
alu_y_lb.Placement.Rotation = FreeCAD.Rotation (VX, -90)
"""

# ------------------ Shaft holders SK12 ------------------------------
# f= f; r: right. hole_x = 0 -> hole facing Y axis
h_sk12_fr = comps.Sk(size=12, name="sk12_fr", hole_x = 0, cx=1, cy=1)
sk12_fr = h_sk12_fr.CadObj
# ROD_Y_SEP is the separation of the Y RODs
sk12_fr.Placement.Base = FreeCAD.Vector (kcit.ROD_Y_SEP/2.0,
                                         kcit.ALU_W/2.0,
                                         kcit.ALU_W)
# f= front; l: left
sk12_fl = Draft.clone(sk12_fr)
sk12_fl.Label = "sk12_fl"
sk12_fl.Placement.Base = FreeCAD.Vector (-kcit.ROD_Y_SEP/2.0,
                                          kcit.ALU_W/2.0,
                                          kcit.ALU_W)
#alu_y_lb.Placement.Base = alu_y_basepos + alu_y_xendpos

#sk12_fl = comps.Sk(size=12, name="sk12_000", hole_x = 0, cx=0, cy=0)
# b= back; l: left
#sk12_bl = comps.Sk(size=12, name="sk12_000", hole_x = 0, cx=0, cy=0)

# the shaft support on the left back
"""
sk12_000 = comps.Sk(size=12, name="sk12_000", hole_x = 0, cx=0, cy=0)
sk12_001 = comps.Sk(size=12, name="sk12_001", hole_x = 0,  cx=0, cy=1)
sk12_100 = comps.Sk(size=12, name="sk12_100", hole_x = 1,  cx=0, cy=0)
sk12_101 = comps.Sk(size=12, name="sk12_101", hole_x = 1,  cx=0, cy=1)
sk12_110 = comps.Sk(size=12, name="sk12_110", hole_x = 1,  cx=1, cy=0)
sk12_111 = comps.Sk(size=12, name="sk12_111", hole_x = 1,  cx=1, cy=1)
mi = comps.MisumiAlu30s6w8 (30, "x_000", axis= 'x')
mi = comps.MisumiAlu30s6w8 (30, "y_000", axis= 'y')
mi = comps.MisumiAlu30s6w8 (30, "z_000", axis= 'z')
mi = comps.MisumiAlu30s6w8 (30, "x_111", axis= 'x', cx=1, cy=1, cz=1)
mi = comps.MisumiAlu30s6w8 (30, "y_111", axis= 'y', cx=1, cy=1, cz=1)
mi = comps.MisumiAlu30s6w8 (30, "z_111", axis= 'z', cx=1, cy=1, cz=1)
mi = comps.MisumiAlu30s6w8 (30, "x_110", axis= 'x', cx=1, cy=1, cz=0)
mi = comps.MisumiAlu30s6w8 (30, "y_101", axis= 'y', cx=1, cy=0, cz=1)
mi = comps.MisumiAlu30s6w8 (30, "z_011", axis= 'z', cx=0, cy=1, cz=1)
"""

doc.recompute()













