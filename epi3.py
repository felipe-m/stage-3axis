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
import math
import FreeCAD;
import FreeCADGui;
import Part;
import Draft;
import logging  # to avoid using print statements
#import copy;
#import Mesh;
import DraftVecUtils;


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
from fcfun import VXN, VYN, VZN
from fcfun import addBolt, addBoltNut_hole, NutHole
from kcomp import TOL

# Taking the same axis as the 3D printer:
#
#    Z   Y
#    | /               USING THIS ONE
#    |/___ X
# 
# centered on the cubes and the vertical line of the camera and the objective
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


# file to save the components and their dimensions. Kind of a BOM,
# bill of materials
file_comps = open ('epi_bom.txt', 'w')

# dictionary with dimensions of the cubes
dcube = kcomp_optic.CAGE_CUBE_60

H_CUBES = 250.
# cubes separation, separation between the centers
# 2 of the cubes are very close
CUBE_SEP_R = math.ceil(dcube['L']) + 5.   # 76.2 -> 82
# Separation to the left cube larger, to have space to change the beamsplitter
CUBE_SEP_L = math.ceil(1.8 * CUBE_SEP_R)

file_comps.write('# Separation between the centers of right and left cubes: ')
file_comps.write( str(CUBE_SEP_R + CUBE_SEP_L) + ' mm \n')
file_comps.write('\n')

cube_block_l = CUBE_SEP_R + CUBE_SEP_L + dcube['L']

file_comps.write('# Length of the whole block: 3 cages in total: ')
file_comps.write( str(cube_block_l) + ' mm \n')
file_comps.write('\n')



# Vertical bread board
V_BREAD_BOARD_L = 900.  # it has 36 holes on the length: 36x25
V_BREAD_BOARD_W = 300.  # it has 12 holes on the width: 12x25

# Separation of the cube from the vertical breaboard
# on y axis
CUBE_VBBOARD_SEP = 27.5
# Separation of the center of the cube from the vertical breaboard
# so this is the Y of the breadboard, plus its width
CUBECEN_VBBOARD_SEP = CUBE_VBBOARD_SEP + dcube['L']/2.

# vertical breadboard
#vbreadboard = comp_optic.f_breadboard(kcomp_optic.BREAD_BOARD_M,
#                                 length = V_BREAD_BOARD_L,
#                                 width = V_BREAD_BOARD_W,
#                                 cl = 0, cw = 1, ch = 0,
#                                 fc_dir_h = VY,
#                                 fc_dir_w = VX,
#                                 pos = FreeCAD.Vector(0,CUBECEN_VBBOARD_SEP,0),
#                                 name = 'vertical_breadboard')

cage_c = comp_optic.f_cagecube(dcube,
                               axis_thru_rods= 'z', axis_thru_hole='x',
                               name = "cube_center")

cage_c.BasePlace((0,0,H_CUBES))

cage_r = comp_optic.f_cagecube(dcube,
                               axis_thru_rods= 'z', axis_thru_hole='x',
                               name = "cube_right")

cage_r.BasePlace((CUBE_SEP_R,0,H_CUBES))

cage_l = comp_optic.f_cagecube(dcube,
                               axis_thru_rods= 'z', axis_thru_hole='x',
                               name = "cube_left")

cage_l.BasePlace((-CUBE_SEP_L,0,H_CUBES))

# using a 10mm wide aluminum profile to hold the cubes together
alux_cubes_w = 10
d_alux_cubes = kcomp.ALU_PROF[alux_cubes_w]
alux_cubes_len = 300
# the extra length of the profiles over the total set of cubes
alux_cubes_extra = alux_cubes_len - cube_block_l

h_alux_cubes = comps.getaluprof(d_alux_cubes, length=alux_cubes_len,
                           axis = 'x',
                           name = 'alux_cubes_y',
                           cx=1, cy=1, cz=0)

fco_alux_cubes_y = h_alux_cubes.fco
# Since the X position is referred to the center, to get the x position of 
# the profile center we do:
#      alux_cubes_len*(0.5-(CUBE_SEP_R + dcube['L']/2.)/cube_block_l)
alux_cubes_pos_z =  H_CUBES +  dcube['L'] /2.
alux_cubes_pos = FreeCAD.Vector(
            -alux_cubes_len*(0.5-(CUBE_SEP_R+ dcube['L']/2.)/cube_block_l) ,
                           (dcube['L'] - alux_cubes_w)/2.,
                            alux_cubes_pos_z)
fco_alux_cubes_y.Placement.Base = alux_cubes_pos
fco_alux_cubes_ny = Draft.clone(fco_alux_cubes_y)
fco_alux_cubes_ny.Label = 'alux_cubes_ny'
fco_alux_cubes_ny.Placement.Base.y = ( fco_alux_cubes_y.Placement.Base.y 
                                      - (dcube['L'] - alux_cubes_w))

# aluminum profiles to hold the linear bearings.
# Perpendicular to the previous

aluy_cubes_w = 15 # maybe 15 is better than 10
aluy_cubes_len = 150.
d_aluy_cubes = kcomp.ALU_PROF[aluy_cubes_w]

h_aluy_cubes = comps.getaluprof(d_aluy_cubes, length=aluy_cubes_len,
                           axis = 'y',
                           name = 'aluy_cubes_x',
                           cx=1, cy=0, cz=0)

# just 2 mm away from the breadboard

aluy_cubes_vboard_sep = 2.5
aluy_cubes_pos_y = -aluy_cubes_len + CUBECEN_VBBOARD_SEP - aluy_cubes_vboard_sep
fco_aluy_cubes_x = h_aluy_cubes.fco

aluy_cubes_pos_z = alux_cubes_pos_z +  alux_cubes_w
aluy_cubes_pos_x = dcube['L']/2.
# X will be set afterwards
fco_aluy_cubes_x.Placement.Base = FreeCAD.Vector(0, 
                                                  aluy_cubes_pos_y,
                                                  aluy_cubes_pos_z)
fco_aluy_cubes_nx = Draft.clone(fco_aluy_cubes_x)
aluy_cubes_pos_nx = - CUBE_SEP_L + dcube['L']/2.
fco_aluy_cubes_nx.Label = 'aluy_cubes_nx'
fco_aluy_cubes_nx.Placement.Base.x = aluy_cubes_pos_nx
fco_aluy_cubes_x.Placement.Base.x = aluy_cubes_pos_x
       







# Plate to hold the objective

# dictionary of the dimensions of the plate
d_obj_plate = kcomp_optic.LB2C_PLATE

# separation of the plate from the cubes, it has to be tight, but also leave
# a little bit of room to let the cubes move
OBJ_PLATE_SEP = 1.
obj_plate_h = H_CUBES - dcube['L']/2. - d_obj_plate['thick'] - OBJ_PLATE_SEP
obj_plate_pos =  FreeCAD.Vector(0,0,obj_plate_h)
obj_plate_axis_l = VY
h_obj_plate = comp_optic.Lb2cPlate (fc_axis_h = VZ,
                                    fc_axis_l = obj_plate_axis_l,
                                    cl=1,cw=1,ch=0,
                                    pos = obj_plate_pos)

# direction of the aluminum profile connected to the plate mounting holes
# perpendicular to obj_plate_axis_l
alux_obj_axis = obj_plate_axis_l.cross(VZ)  #it will be X, as alux indicates
alux_obj_axisname = fcfun.get_positive_vecname(
                                fcfun.get_nameofbasevec(alux_obj_axis))

# using a 10mm wide aluminum profile to hold the objective
alu_obj_w = 10
d_alu_obj = kcomp.ALU_PROF[alu_obj_w]


alux_obj_len = 100.
aluy_obj_len = 100.

h_alux_obj = comps.getaluprof(d_alu_obj, length=alux_obj_len,
                           axis = alux_obj_axisname,
                           name = 'alux_obj_y',
                           cx=1, cy=1, cz=0)

fco_alux_obj_y = h_alux_obj.fco
alux_obj_pos_y = obj_plate_pos + FreeCAD.Vector(0,
                                         h_obj_plate.cbore_hole_sep_l/2.,
                                         - alu_obj_w)
fco_alux_obj_y.Placement.Base = alux_obj_pos_y
fco_alux_obj_ny = Draft.clone(fco_alux_obj_y)
fco_alux_obj_ny.Label = 'alux_obj_ny'
fco_alux_obj_ny.Placement.Base.y = (  fco_alux_obj_ny.Placement.Base.y 
                                    - h_obj_plate.cbore_hole_sep_l)

aluy_obj_axisname = fcfun.get_nameofbasevec(obj_plate_axis_l)
h_aluy_obj = comps.getaluprof(d_alu_obj, length=aluy_obj_len,
                           axis = aluy_obj_axisname,
                           name = 'aluy_obj_x',
                           cx=1, cy=1, cz=0)
fco_aluy_obj_x = h_aluy_obj.fco

aluy_obj_pos_x = obj_plate_pos + FreeCAD.Vector(
                                         alux_obj_len/2. + alu_obj_w/2. ,
                                         (aluy_obj_len-dcube['L'])/2,
                                         - alu_obj_w)
fco_aluy_obj_x.Placement.Base = aluy_obj_pos_x

fco_aluy_obj_nx = Draft.clone(fco_aluy_obj_x)
fco_aluy_obj_nx.Label = 'aluy_obj_nx'
fco_aluy_obj_nx.Placement.Base.x = (  fco_aluy_obj_nx.Placement.Base.x 
                                    - (alux_obj_len + alu_obj_w))



# SM1 tube lens for the Leds and adapters to SM2 to conect to the cages

pos_tubelens_c = FreeCAD.Vector(0, -dcube['L']/2. ,H_CUBES)
h_tubelens_c = comp_optic.SM1TubelensSm2 (sm1l_size=20, fc_axis = VYN,
                             ref_sm1 = 0, pos = pos_tubelens_c,
                             ring = 1,
                             name = 'tubelens_c')

fco_tubelens_c = h_tubelens_c.fco

# the right tubelens
fco_tubelens_r = Draft.clone(fco_tubelens_c)
fco_tubelens_r.Label = 'tubelens_r'
fco_tubelens_r.Placement.Base.x = CUBE_SEP_R

# the left tubelens
fco_tubelens_l = Draft.clone(fco_tubelens_c)
fco_tubelens_l.Label = 'tubelens_l'
fco_tubelens_l.Placement.Base.x = - CUBE_SEP_L

# Leds connected to the tube lens
pos_led_c = (  pos_tubelens_c
             + DraftVecUtils.scaleTo(h_tubelens_c.fc_axis,h_tubelens_c.length))

h_led_c = comp_optic.ThLed30(fc_axis=VY, fc_axis_cable=VZN,
                             pos = pos_led_c, name='led_c')

# the freecad object
fco_led_c = h_led_c.fco
# clone to the right
fco_led_r = Draft.clone(fco_led_c)
fco_led_r.Label = 'led_r'
fco_led_r.Placement.Base.x = CUBE_SEP_R

# the led on the left is a Prizmatix:

# use scale, and not scaleTo, because the module of VXN is 1
pos_led_l = pos_led_c + DraftVecUtils.scale(VXN, CUBE_SEP_L)

h_led_l = comp_optic.PrizLed(VY, VZ, pos_led_l, name='led_l_prizmatix')



# SM1 tube lens for the Leds and adapters to SM2 to conect to the TOP of
# the cages. For the emission filters, with no locking rings
# they are not on top, but inside, I dont know how much they are inserted
# If dcube['L']/2, they are just on the edge of the cube, so a little bit less
# than that: 0.9

emitubelens_zpos = dcube['L']/2 * 0.9

pos_emitubelens_c = FreeCAD.Vector(0, 0, H_CUBES + emitubelens_zpos)
h_emitubelens_c = comp_optic.SM1TubelensSm2 (sm1l_size=20, fc_axis = VZ,
                             ref_sm1 = 0, pos = pos_emitubelens_c,
                             ring = 0,
                             name = 'emitubelens_c')

fco_emitubelens_c = h_emitubelens_c.fco

# the right emission filter tubelens (on top of the cube)
fco_emitubelens_r = Draft.clone(fco_emitubelens_c)
fco_emitubelens_r.Label = 'emitubelens_r'
fco_emitubelens_r.Placement.Base.x = CUBE_SEP_R

# the left emission tubelens (on top of the cube)
fco_emitubelens_l = Draft.clone(fco_emitubelens_c)
fco_emitubelens_l.Label = 'emitubelens_l'
fco_emitubelens_l.Placement.Base.x = - CUBE_SEP_L




file_comps.close()

doc.recompute()

guidoc.ActiveView.setAxisCross(True)














