# ----------------------------------------------------------------------------
# -- Cytometer Base
# -- Python scripts for the cytometer base
# ----------------------------------------------------------------------------
# -- (c) Felipe Machado
# -- Area of Electronics. Rey Juan Carlos University (urjc.es)
# -- July-2017
# ----------------------------------------------------------------------------
# --- LGPL Licence
# ----------------------------------------------------------------------------

# to execute from the FreeCAD console:
#  execute freecad from the cmd console on the directory
# "C:\Program Files\FreeCAD 0.16\bin\freecad" base.py

# to excute from command line in windows:
# "C:\Program Files\FreeCAD 0.16\bin\freecadcmd" base.py

import os
import sys
import FreeCAD;
import FreeCADGui;
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

# where the freecad document is going to be saved
savepath = filepath + "/../../freecad/citometro/py/"

import fcfun   # import my functions for freecad. FreeCad Functions
import kcit    # import citometer constants
import kcomp   # import material constants and other constants
import comps   # import my CAD components
import parts   # import my CAD components to print
import kcomp_optic  # import optic components constants
import comp_optic   # import optic components
import citoparts # import my CAD pieces to be printed

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

Gui.ActiveDocument = Gui.getDocument(doc.Label)
guidoc = Gui.getDocument(doc.Label)

H_CUBES = 250.
CUBE_SEP = 100 # kcomp_optic.CAGE_CUBE_60['L'] = 7.2

cage_c = comp_optic.f_cagecubehalf(kcomp_optic.CAGE_CUBE_HALF_60,
                                   axis_1= 'z', axis_2='-y',
                                   name = "cube45_center")

cage_c.BasePlace((0,0,H_CUBES))

cage_d = comp_optic.f_cagecubehalf(kcomp_optic.CAGE_CUBE_HALF_60,
                                   axis_1= 'z', axis_2='-y',
                                   name = "cube45_right")

cage_d.BasePlace((CUBE_SEP,0,H_CUBES))

cage_l = comp_optic.f_cagecubehalf(kcomp_optic.CAGE_CUBE_HALF_60,
                                   axis_1= 'z', axis_2='-y',
                                   name = "cube45_left")

cage_l.BasePlace((-CUBE_SEP,0,H_CUBES))



guidoc.ActiveView.setAxisCross(True)














