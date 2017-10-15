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
import beltcl # import belt clamp pieces

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

# cube width: 76.2
cube_w = dcube['L']

# in case reference axes wanted to be changed
# citometer axes
cVX = VX
cVY = VY
cVZ = VZ

cVXN = cVX.negative() 
cVYN = cVY.negative()
cVZN = cVZ.negative()


# view from top:
#
#                    Y
#        breadboard  :
#       _____________:____________________
#                    :               :
#                    :               + CUBE_VBBOARD_SEP = 27.5
#    _______      ___:___  ______ ...:
#   |       |    |cen:   ||right |   :
#   | left  |    |tra:...||......|.. : ...........> X     central cube X=0 Y=0 
#   | cube  |    | cube  || cube |   + cube_w
#   |_______|    |_______||______|...:
#   :   :............:.......:   :
#   :   :     +         + CUBE_SEP_R
#   :   :  CUBE_SEP_L        :   :
#   :   :                    :   :
#   :   :.....stroke.........:   :
#   :                            :
#   :....cube_block_l............:

# From the base of the cube to the bottom
H_CUBES = 276.1
# cubes separation, separation between the centers
# 2 of the cubes are very close
#CUBE_SEP_R = math.ceil(cube_w) + 5.   # 76.2 -> 82
CUBE_SEP_R = math.ceil(cube_w) + 12.   # Given by Ivan
# Separation to the left cube larger, to have space to change the beamsplitter
#CUBE_SEP_L = math.ceil(cube_w + 0.7 * cube_w)
CUBE_SEP_L = math.ceil(cube_w + 71.)

file_comps.write('# Space between central al left cube, to introduce ')
file_comps.write('# beam splitter')
file_comps.write( str(CUBE_SEP_L - cube_w) + ' mm \n')
file_comps.write('\n')

stroke = CUBE_SEP_R + CUBE_SEP_L

file_comps.write('# Separation between the centers of right and left cubes, ')
file_comps.write('# stroke: ')
file_comps.write( str(stroke) + ' mm \n')
file_comps.write('\n')

cube_block_l = CUBE_SEP_R + CUBE_SEP_L + cube_w

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
CUBECEN_VBBOARD_SEP = CUBE_VBBOARD_SEP + cube_w/2.

# vertical breadboard
h_vbreadboard = comp_optic.f_breadboard(kcomp_optic.BREAD_BOARD_M,
                                  length = V_BREAD_BOARD_L,
                                  width = V_BREAD_BOARD_W,
                                  cl = 0, cw = 1, ch = 0,
                                  fc_dir_h = VY,
                                  fc_dir_w = VX,
                                  pos = FreeCAD.Vector(0,CUBECEN_VBBOARD_SEP,0),
                                  name = 'vertical_breadboard')


# color of the different objects
OPTIC_COLOR = fcfun.CIAN_08
OPTIC_COLOR_STA = fcfun.GREEN_D07  #Optics that are not moving, static
LED_COLOR = fcfun.CIAN_05
ALU_COLOR = fcfun.YELLOW_05
ALUFRAME_COLOR = fcfun.GREEN_07
ALU_COLOR_STA = (0.8, 0.2, 0.2)
PRINT_COLOR = fcfun.ORANGE


#h_vbreadboard.color(ALU_COLOR)

movegroup_list = []

h_cage_c = comp_optic.f_cagecube(dcube,
                               axis_thru_rods= 'z', axis_thru_hole='x',
                               name = "cube_center")

h_cage_c.BasePlace((0,0,H_CUBES))
h_cage_c.color(OPTIC_COLOR)

h_cage_r = comp_optic.f_cagecube(dcube,
                               axis_thru_rods= 'z', axis_thru_hole='x',
                               name = "cube_right")

h_cage_r.BasePlace((CUBE_SEP_R,0,H_CUBES))
h_cage_r.color(OPTIC_COLOR)

h_cage_l = comp_optic.f_cagecube(dcube,
                               axis_thru_rods= 'z', axis_thru_hole='x',
                               name = "cube_left")

h_cage_l.BasePlace((-CUBE_SEP_L,0,H_CUBES))
h_cage_l.color(OPTIC_COLOR)

movegroup_list.append(h_cage_c.fco)
movegroup_list.append(h_cage_r.fco)
movegroup_list.append(h_cage_l.fco)





# Plate to hold the objective

# dictionary of the dimensions of the plate
#d_obj_plate = kcomp_optic.LB2C_PLATE
#it is the LCP08/M but it has the same dimensions
d_obj_plate = kcomp_optic.LCP01M_PLATE

# separation of the plate from the cubes, it has to be tight, but also leave
# a little bit of room to let the cubes move
OBJ_PLATE_SEP = 1.
# Z position at its top
obj_plate_pos_z = H_CUBES - cube_w/2. - OBJ_PLATE_SEP
obj_plate_pos =  FreeCAD.Vector(0,0,obj_plate_pos_z)
obj_plate_axis_l = VY
h_obj_plate = comp_optic.lcp01m_plate (fc_axis_h = VZN, #bottom is on top
                                       fc_axis_m = VYN,
                                       cm=1,cp=1,ch=0,
                                       pos = obj_plate_pos)
h_obj_plate.color(OPTIC_COLOR_STA)

# Diameter of the objective at the end where it is screwed:
OBJ_D = 69.9
# the objective is at the bottom of the plate, but the plate has been
# drawn upsidedown (it doesnt matter which way), so its top position
# will be its bottom and the objetive will be there
obj_pos = h_obj_plate.topcen_pos



# I don't know the height, what is important is the diameter
fco_objective = fcfun.addCylPos (r= OBJ_D/2., h= 50,
                                 name = "objective",
                                 normal =VZN,
                                 pos=obj_pos)

# direction of the aluminum profile connected to the plate mounting holes
# perpendicular to obj_plate_axis_l
alux_obj_axis = obj_plate_axis_l.cross(VZ)  #it will be X, as alux indicates
alux_obj_axisname = fcfun.get_positive_vecname(
                                fcfun.get_nameofbasevec(alux_obj_axis))

# using a 10mm wide aluminum profile to hold the objective
#alu_obj_w = 10
#d_alu_obj = kcomp.ALU_PROF[alu_obj_w]

#alux_obj_len = 100.
#aluy_obj_len = 100.
#h_alux_obj = comps.getaluprof(d_alu_obj, length=alux_obj_len,
#                           axis = alux_obj_axisname,
#                           name = 'alux_obj_y',
#                           cx=1, cy=1, cz=0)
#h_alux_obj.color(ALU_COLOR_STA)
#fco_alux_obj_y = h_alux_obj.fco
#alux_obj_pos_y = obj_plate_pos + FreeCAD.Vector(0,
#                                         h_obj_plate.cbore_hole_sep_l/2.,
#                                         - alu_obj_w)
#fco_alux_obj_y.Placement.Base = alux_obj_pos_y
#fco_alux_obj_ny = Draft.clone(fco_alux_obj_y)
#fco_alux_obj_ny.Label = 'alux_obj_ny'
#fco_alux_obj_ny.Placement.Base.y = (  fco_alux_obj_ny.Placement.Base.y 
#                                    - h_obj_plate.cbore_hole_sep_l)
#fco_alux_obj_ny.ViewObject.ShapeColor = ALU_COLOR_STA
#aluy_obj_axisname = fcfun.get_nameofbasevec(obj_plate_axis_l)
#h_aluy_obj = comps.getaluprof(d_alu_obj, length=aluy_obj_len,
#                           axis = aluy_obj_axisname,
#                           name = 'aluy_obj_x',
#                           cx=1, cy=1, cz=0)
#h_aluy_obj.color(ALU_COLOR_STA)
#fco_aluy_obj_x = h_aluy_obj.fco
#aluy_obj_pos_x = obj_plate_pos + FreeCAD.Vector(
#                                         alux_obj_len/2. + alu_obj_w/2. ,
#                                         (aluy_obj_len-cube_w)/2,
#                                         - alu_obj_w)
#fco_aluy_obj_x.Placement.Base = aluy_obj_pos_x
#fco_aluy_obj_nx = Draft.clone(fco_aluy_obj_x)
#fco_aluy_obj_nx.Label = 'aluy_obj_nx'
#fco_aluy_obj_nx.Placement.Base.x = (  fco_aluy_obj_nx.Placement.Base.x 
#                                    - (alux_obj_len + alu_obj_w))
#fco_aluy_obj_nx.ViewObject.ShapeColor = ALU_COLOR_STA



# SM1 tube lens for the Leds and adapters to SM2 to conect to the cages

pos_tubelens_c = FreeCAD.Vector(0, -cube_w/2. ,H_CUBES)
h_tubelens_c = comp_optic.SM1TubelensSm2 (sm1l_size=20, fc_axis = VYN,
                             ref_sm1 = 0, pos = pos_tubelens_c,
                             ring = 1,
                             name = 'tubelens_c')

h_tubelens_c.color(OPTIC_COLOR)
fco_tubelens_c = h_tubelens_c.fco
movegroup_list.append(fco_tubelens_c)

# the right tubelens
fco_tubelens_r = Draft.clone(fco_tubelens_c)
fco_tubelens_r.Label = 'tubelens_r'
fco_tubelens_r.Placement.Base.x = CUBE_SEP_R
fco_tubelens_r.ViewObject.ShapeColor = OPTIC_COLOR
movegroup_list.append(fco_tubelens_r)

# the left tubelens
fco_tubelens_l = Draft.clone(fco_tubelens_c)
fco_tubelens_l.Label = 'tubelens_l'
fco_tubelens_l.Placement.Base.x = - CUBE_SEP_L
fco_tubelens_l.ViewObject.ShapeColor = OPTIC_COLOR
movegroup_list.append(fco_tubelens_l)

# Leds connected to the tube lens
pos_led_c = (  pos_tubelens_c
             + DraftVecUtils.scaleTo(h_tubelens_c.fc_axis,h_tubelens_c.length))

h_led_c = comp_optic.ThLed30(fc_axis=VY, fc_axis_cable=VZN,
                             pos = pos_led_c, name='led_c')

h_led_c.color(LED_COLOR)
# the freecad object
fco_led_c = h_led_c.fco
movegroup_list.append(fco_led_c)
# clone to the right
fco_led_r = Draft.clone(fco_led_c)
fco_led_r.Label = 'led_r'
fco_led_r.Placement.Base.x = CUBE_SEP_R
fco_led_r.ViewObject.ShapeColor = LED_COLOR
movegroup_list.append(fco_led_r)

# the led on the left is a Prizmatix:

# use scale, and not scaleTo, because the module of VXN is 1
pos_led_l = pos_led_c + DraftVecUtils.scale(VXN, CUBE_SEP_L)

h_led_l = comp_optic.PrizLed(VY, VZ, pos_led_l, name='led_l_prizmatix')
h_led_l.color(LED_COLOR)
movegroup_list.append(h_led_l.fco)



# SM1 tube lens for the Leds and adapters to SM2 to conect to the TOP of
# the cages. For the emission filters, with no locking rings
# they are not on top, but inside, I dont know how much they are inserted
# If cube_w/2, they are just on the edge of the cube, so a little bit less
# than that: 0.9

emitubelens_zpos = cube_w/2 * 0.9

pos_emitubelens_c = FreeCAD.Vector(0, 0, H_CUBES + emitubelens_zpos)
h_emitubelens_c = comp_optic.SM1TubelensSm2 (sm1l_size=20, fc_axis = VZ,
                             ref_sm1 = 0, pos = pos_emitubelens_c,
                             ring = 0,
                             name = 'emitubelens_c')

h_emitubelens_c.color(OPTIC_COLOR)
fco_emitubelens_c = h_emitubelens_c.fco
movegroup_list.append(fco_emitubelens_c)

# the right emission filter tubelens (on top of the cube)
fco_emitubelens_r = Draft.clone(fco_emitubelens_c)
fco_emitubelens_r.Label = 'emitubelens_r'
fco_emitubelens_r.Placement.Base.x = CUBE_SEP_R
fco_emitubelens_r.ViewObject.ShapeColor = OPTIC_COLOR
movegroup_list.append(fco_emitubelens_r)

# the left emission tubelens (on top of the cube)
fco_emitubelens_l = Draft.clone(fco_emitubelens_c)
fco_emitubelens_l.Label = 'emitubelens_l'
fco_emitubelens_l.Placement.Base.x = - CUBE_SEP_L
fco_emitubelens_l.ViewObject.ShapeColor = OPTIC_COLOR
movegroup_list.append(fco_emitubelens_l)


# using a 10mm wide aluminum profile to hold the cubes together
# view from top:
#
#                    Y
#        breadboard  :
#       _____________:____________________
#                    :                   :
#      XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX alux_bb
#                    :                  
#      XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX alux_cubes_y
#           |    |cen:   ||right |
#     left  |    |tra:...||......|...............> X     central cube X=0 Y=0 
#     cube  |    | cube  || cube |
#      XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX alux_cubes_ny
#
#      XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX alux_leds_in
#      XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX alux_leds_out
#

#width of the aluminum profile
alux_cubes_w = 10
#dictionary with the dimensions of the aluminum profile
d_alux_cubes = kcomp.ALU_PROF[alux_cubes_w]
# length of the aluminum profiles
alux_cubes_len = 300
# the extra length of the profiles over the total length of the 3 cubes
alux_cubes_extra = alux_cubes_len - cube_block_l

h_alux_cubes = comps.getaluprof(d_alux_cubes, length=alux_cubes_len,
                           axis = 'x',
                           name = 'alux_cubes_y',
                           cx=1, cy=1, cz=0)
h_alux_cubes.color(ALU_COLOR)

#the freecad object of the aluminum profile
fco_alux_cubes_y = h_alux_cubes.fco
# Since the X position is referred to the center, to get the x position of 
# the profile center we do:
alux_cubes_pos_x = -alux_cubes_len*(0.5-(CUBE_SEP_R+ cube_w/2.)/cube_block_l)
alux_cubes_pos_z =  H_CUBES +  cube_w /2.
# Y position of the 2 aluminum profiles attached to the cages:
alux_cubes_y_pos_y =   (cube_w - alux_cubes_w)/2.
alux_cubes_ny_pos_y = - alux_cubes_y_pos_y
# These 2 aluminum profile will hold a normal linear bearing housing

# There rods can be different in size, so we have the rod on the led side
# and the other on the breadboard side
# rod diameter for the linear bearing
rod_bb_d = 10.
rod_bb_r = rod_bb_d/2.
rod_led_d = 12.
rod_led_r = rod_led_d/2.
# dictionary of the linear bearing:
d_lbearing_bb = kcomp.LMEUU[rod_bb_d]
d_lbearing_led = kcomp.LMEUU[rod_led_d]



# Set the position on X and Z of the aluminum profiles
# position Y will be different for the 4 of them (they are parallel)
fco_alux_cubes_y.Placement.Base.x = alux_cubes_pos_x
fco_alux_cubes_y.Placement.Base.z = alux_cubes_pos_z

## Plates to hold the cagecubes together

plate3cubes_thick = 4.

cubefaceplate = h_cage_c.vec_face(VY)

#plate3cubes_cenhole_d = h_tubelens_c.ring_d + TOL

print h_tubelens_c.ring_d + TOL
file_comps.write('hole tublens ' + str( h_tubelens_c.ring_d + TOL) +'\n')
file_comps.write('vs 57\n')
plate3cubes_cenhole_d = 57. # 56 given by ivan

# plate on the side of the leds

h_plate3cagecubes_led = parts.Plate3CageCubes (d_cagecube = dcube,
                                           thick = plate3cubes_thick,
                                           cube_dist_n = CUBE_SEP_L, 
                                           cube_dist_p = CUBE_SEP_R, 
                                           top_h = alux_cubes_w,
                                           cube_face = cubefaceplate,
                                           hole_d = plate3cubes_cenhole_d,
                                           boltatt_n = 12,
                                           boltatt_d = 3,
                                           sqr_h = 0,
                                           sqr_w = 0,
                                           fc_fro_ax = VY,
                                           fc_top_ax = VZ,
                                           fc_sid_ax = VX,
                                           fillet_r = 2.,
                                           holes_tol = TOL,
                                           pos = pos_tubelens_c,
                                           name = 'Plate3CubesLeds')

h_plate3cagecubes_led.color(PRINT_COLOR)
h_plate3cagecubes_led.export_stl()
                                           
movegroup_list.append(h_plate3cagecubes_led.fco)



# the other linear bearing housing, not so thin: bolts_side = 1

# First, set the Y position of this rod, on the middle of the sm1 tubelens:
sm1_l = h_tubelens_c.sm1_l

# alux_leds_in, will be after the sm2 ring of the SM1 to SM2 tube lens adapter
sm2_l = h_tubelens_c.sm2_l + h_tubelens_c.ring_l

rod_led_pos_y = (- cube_w/2. - sm2_l - sm1_l/2.)

# This will be the same position for the housing, having it centered on its
# axis: bolt_center = 0

lbear1_pos_x = -(CUBE_SEP_L-cube_w/2.)
lbear2_pos_x = CUBE_SEP_R/2.
lbear_cpos_y = rod_led_pos_y #cpos, because it is centered

lbear_pos_z = alux_cubes_pos_z
lbear1_pos = FreeCAD.Vector(lbear1_pos_x, 
                            lbear_cpos_y,
                            lbear_pos_z)
h_lbear1_led = parts.ThinLinBearHouse(d_lbearing_led, 
                                      fc_slide_axis = VX,
                                      fc_bot_axis = VZ,
                                      fc_perp_axis = VYN,
                                      bolts_side = 1,
                                      axis_center = 0,
                                      mid_center = 1, #centered on slide_axis
                                      bolt_center = 0,
                                      pos = lbear1_pos,
                                      name = 'linbearhouse_led1')

h_lbear1_led.color(PRINT_COLOR)
# maybe better to just make an object with the 2
movegroup_list.append(h_lbear1_led.fco_top)
movegroup_list.append(h_lbear1_led.fco_bot)

lbear2_pos = FreeCAD.Vector(lbear2_pos_x, 
                            lbear_cpos_y,
                            lbear_pos_z)
h_lbear2_led = parts.ThinLinBearHouse(d_lbearing_led, 
                                      fc_slide_axis = VX,
                                      fc_bot_axis = VZ,
                                      fc_perp_axis = VYN,
                                      bolts_side = 1,
                                      axis_center = 0,
                                      mid_center = 1,
                                      bolt_center = 0,
                                      pos = lbear2_pos,
                                      name = 'linbearhouse_led2')
h_lbear2_led.color(PRINT_COLOR)
h_lbear2_led.export_stl(name='linearbearing_house')
movegroup_list.append(h_lbear2_led.fco_top)
movegroup_list.append(h_lbear2_led.fco_bot)

lbear_l = h_lbear1_led.L

# Get the distance from the base of the linear bearing to the rod
lbear_led_rod_h = h_lbear1_led.axis_h
file_comps.write('sym linearbearing rod to base: ' + str(lbear_led_rod_h))
file_comps.write('\n')

## Thin Linear bearing housing (on the breadboard side)

lbear_bb_pos_x = -((CUBE_SEP_L-cube_w)/2.+cube_w/2.)
lbear_bb_pos_y = alux_cubes_y_pos_y #reference on the bolt->alux_cubes_y_pos_y

lbear_bb_pos = FreeCAD.Vector(lbear_bb_pos_x, 
                             lbear_bb_pos_y,
                             lbear_pos_z)
# distance from the bolt attached to the alux_cubes_y to the rod:
# half of the width of the aluminum profile + radius of the rod
# + separation of the axis to the cubes (depends on the cube cover: 3mm?
sep_rod2cube = 6  # ----------------> CHECK with Ivan ****************
sep_rod2alu = rod_bb_r + alux_cubes_w/2. + sep_rod2cube

# shaft holders for the rods:
d_sh_bb = kcomp.SK[int(rod_bb_d)]
d_sh_led = kcomp.SK[int(rod_led_d)]
# the distance of the shaft to the shaft holder base 
sh_led_h = d_sh_led['h']
sh_bb_h = d_sh_bb['h']

# difference in height of the shaft centers:
sh_h_dif = sh_led_h - sh_bb_h

#                 lbear_bb                 lbear_led
#          ....  ___________               __________ ....
#          :    |                          _____     |    :
# lbear_bb_rod_h|   _____                 |     |    |    + lbear_led_rod_h
#          :    |  |     |    ----------- |  O  |---- ....:
#          :...  --|  O  |----- sh_h_dif  |     |
#                __|     |__            __|     |__
#               |___________|          |___________|
#

lbear_bb_rod_h = lbear_led_rod_h + sh_h_dif 

h_lbear_bb = parts.ThinLinBearHouseAsim(d_lbearing_bb,
                                   fc_fro_ax = VX,
                                   fc_bot_ax = VZ,
                                   fc_sid_ax = VY,
                                   axis_h = lbear_bb_rod_h,
                                   bolts_side = 0,
                                   refcen_hei = 0,
                                   refcen_dep = 1,
                                   refcen_wid = 0, #ref on the bolt
                                   bolt2cen_wid_n = sep_rod2alu,
                                   pos = lbear_bb_pos,
                                   name = 'thin_linbearhouse_asym_bboard')

h_lbear_bb.color(PRINT_COLOR)
h_lbear_bb.export_stl(name='asym_linearbearing_house')

movegroup_list.append(h_lbear_bb.fco_top)
movegroup_list.append(h_lbear_bb.fco_bot)

# Z position of the rods

rod_bb_pos_z = lbear_pos_z - lbear_bb_rod_h
rod_led_pos_z = lbear_pos_z - lbear_led_rod_h

rod2lbearbolt_dist_y = h_lbear1_led.boltcen_perp_dist
# Position of the aluminum profile to hold the linear bearing
alux_leds_in_pos_y = rod_led_pos_y + rod2lbearbolt_dist_y
# Position of the aluminum profile to hold the linear bearing,
# closest to the leds
alux_leds_out_pos_y = rod_led_pos_y - rod2lbearbolt_dist_y

# distance from the rod to the bolt that attachs the linear bearing
# house to the aluminum profile alux_cubes_y. On the Y axis
# there are 2 distances because it is asymmetrical, the shorter one
rod2lbearbolt_small_dist_y = h_lbear_bb.bolt2cen_wid_p
rod2lbearbolt_large_dist_y = h_lbear_bb.bolt2cen_wid_n

# Y position of the rod (axis) on the side of the breadboard
rod_bb_pos_y = lbear_bb_pos_y + rod2lbearbolt_large_dist_y
# Position of the aluminum profile closest to the breadboard
alux_bb_pos_y = rod_bb_pos_y + rod2lbearbolt_small_dist_y


#clone the aluminum profiles, with the X and Y position, and in Y=0
fco_alux_cubes_ny = Draft.clone(fco_alux_cubes_y)
fco_alux_cubes_ny.Label = 'alux_cubes_ny'
fco_alux_cubes_ny.Placement.Base.y = alux_cubes_ny_pos_y
fco_alux_cubes_ny.ViewObject.ShapeColor = ALU_COLOR
movegroup_list.append(fco_alux_cubes_ny)

fco_alux_bb = Draft.clone(fco_alux_cubes_y)
fco_alux_bb.Label = 'alux_bboard'
fco_alux_bb.Placement.Base.y = alux_bb_pos_y
fco_alux_bb.ViewObject.ShapeColor = ALU_COLOR
movegroup_list.append(fco_alux_bb)

fco_alux_leds_in = Draft.clone(fco_alux_cubes_y)
fco_alux_leds_in.Label = 'alux_leds_in'
fco_alux_leds_in.Placement.Base.y = alux_leds_in_pos_y
fco_alux_leds_in.ViewObject.ShapeColor = ALU_COLOR
movegroup_list.append(fco_alux_leds_in)

fco_alux_leds_out = Draft.clone(fco_alux_cubes_y)
fco_alux_leds_out.Label = 'alux_leds_out'
fco_alux_leds_out.Placement.Base.y = alux_leds_out_pos_y
fco_alux_leds_out.ViewObject.ShapeColor = ALU_COLOR
movegroup_list.append(fco_alux_leds_out)

# and set the original aluminun profile position on Y
fco_alux_cubes_y.Placement.Base.y = alux_cubes_y_pos_y
movegroup_list.append(fco_alux_cubes_y)



# plate on the side of the breadboard

plate_sqr_w = h_lbear_bb.D + 2 # tolerance 
plate_sqr_h = h_lbear_bb.H + 5 # tolerance to have space to introduce it
pos_plate_bb = FreeCAD.Vector(0, cube_w/2. ,H_CUBES)

h_plate3cagecubes_bb = parts.Plate3CageCubes (d_cagecube = dcube,
                                           thick = plate3cubes_thick,
                                           cube_dist_n = CUBE_SEP_L, 
                                           cube_dist_p = CUBE_SEP_R, 
                                           top_h = alux_cubes_w,
                                           cube_face = cubefaceplate,
                                           hole_d = -1, #no big holes
                                           boltatt_n = 12,
                                           boltatt_d = 3,
                                           sqr_h = plate_sqr_h,
                                           sqr_w = plate_sqr_w,
                                           fc_fro_ax = VYN,
                                           fc_top_ax = VZ,
                                           fc_sid_ax = VX,
                                           fillet_r = 2.,
                                           holes_tol = TOL,
                                           moreboltholes = 1,
                                           pos = pos_plate_bb,
                                           name = 'Plate3CubesBB')

h_plate3cagecubes_bb.color(PRINT_COLOR)
h_plate3cagecubes_bb.export_stl()
movegroup_list.append(h_plate3cagecubes_bb.fco)





# Belt clamps:

bclamp_p_pos_x = lbear2_pos_x + lbear_l/2.
bclamp_n_pos_x = lbear1_pos_x - lbear_l/2.
bclamp_pos_y = alux_leds_in_pos_y
bclamp_pos_z = lbear_pos_z

beltclamp_p_pos = FreeCAD.Vector(bclamp_p_pos_x, bclamp_pos_y, bclamp_pos_z)
beltclamp_n_pos = FreeCAD.Vector(bclamp_n_pos_x, bclamp_pos_y, bclamp_pos_z)

h_beltclamp_p = beltcl.BeltClamp (fc_fro_ax = VX,
                                  fc_top_ax = VZN,
                                  base_h = 0,
                                  base_l = 0,
                                  base_w = 0,
                                  bolt_d = 3, #M3 bolts
                                  bolt_csunk = 1,
                                  ref = 6, #position at the end: backbase
                                  pos = beltclamp_p_pos,
                                  extra = 0,
                                  wfco = 1,
                                  intol = 0.2, #added 0.2, belt didnt fit
                                  name = 'bclamp_p')
                       
h_beltclamp_p.color(PRINT_COLOR)
h_beltclamp_p.export_stl(name = 'belt_clamp')
movegroup_list.append(h_beltclamp_p.fco)

h_beltclamp_n = beltcl.BeltClamp (fc_fro_ax = VXN,
                                  fc_top_ax = VZN,
                                  base_h = 0,
                                  base_l = 0,
                                  base_w = 0,
                                  bolt_d = 3, #M3 bolts
                                  bolt_csunk = 1,
                                  ref = 6, #position at the end: backbase
                                  pos = beltclamp_n_pos,
                                  extra = 0,
                                  wfco = 1,
                                  intol = 0.2,
                                  name = 'bclamp_n')
h_beltclamp_n.color(PRINT_COLOR)
movegroup_list.append(h_beltclamp_n.fco)

                   

# This is not valid because the block cannot go all the way until the 
# linear bearing, becuase it will hit the led/tubelens
#Length of the cart (the part between the linear bearings) to calculate the
# length of the rods, having the stroke
#lbear_length = h_lbear2_led.L
#cart_length = lbear2_pos_x - lbear1_pos_x + lbear_length

#file_comps.write('# Length of the "cart" block, from the linear bearings: ')
#file_comps.write( str(cart_length) + ' mm \n')
#file_comps.write('\n')

# dictionary of the shaft holder
#d_sh = kcomp.SK[rod_d]

sh_led_depth = d_sh_led['L']
sh_bb_depth = d_sh_bb['L']

sh_depth_max = max(sh_led_depth, sh_bb_depth)
extra_rod = 2.

#min_rod_l = stroke + cart_length + 40
# 2* the depth of the shaft holder and a little bit extra room to hold it
min_rod_l = stroke + cube_block_l + 2*sh_depth_max + 2*extra_rod

file_comps.write('# Min rod length: stroke + cart length + shaft holder: ')
file_comps.write( str(min_rod_l) + ' mm \n')
file_comps.write('\n')

# list of rods length we have:
rod_list_10 = [600, 575, 550, 525, 500, 475, 450]
rod_list_12 = [700, 675, 650, 600, 550, 525, 500, 475, 450]
d_rod_l = { 10 : rod_list_10,
          12 : rod_list_12 }

rod_bb_l = 0
for rodlen in d_rod_l[int(rod_bb_d)]:
    if min_rod_l > rodlen:
        break
    else:
        rod_bb_l = rodlen

rod_led_l = 0
for rodlen in d_rod_l[int(rod_led_d)]:
    if min_rod_l > rodlen:
        break
    else:
        rod_led_l = rodlen

file_comps.write('# Final rod length:')
file_comps.write( str(rod_bb_l) + ' mm \n')
file_comps.write('\n')
if rod_bb_l != rod_led_l:
    logger.debug ("rod length are not equal: " + str(rod_l_cand)
                  + str(rod_l_cand_2))
    file_comps.write('# Final rod length for led side:')
    file_comps.write( str(rod_led_l) + ' mm \n')
    file_comps.write('\n')
    




# From the center to the left side we have:

#
#                              Y
#          breadboard          :
#         _____________________:____________
#                              :       :
#                              :       + CUBE_VBBOARD_SEP = 27.5
#      _______      _______  __:___ ...:
#     |       |    |cen:   ||right |   :
#     | left  |    |tra:...||..:...|.. : ...........> X   
#     | cube  |    | cube  || cube |   + cube_w
#     |_______|    |_______||______|...:
#                              :
#   SH=========================:==== rod_led
#  :  :   :                    :   :    
#  :  :   :                    :   :
#  :  :   :                    :   :
#  :  :...:.....stroke.........:   :
#  :  : +cube_w/2                  :
#  :  :....cube_block_l............:
#  :..:
#    + sh_depth_max + extra_rod 


#
#                              Y
#          breadboard          :
#         _____________________:____________
#                              :       :
#                              :       + CUBE_VBBOARD_SEP = 27.5
#                           ___:___      _______  ______ ...:
#                          |       |    |cen:   ||right |   :
#                          | left  |    |tra:...||..:...|.. : ...........> X   
#                          | cube  |    | cube  || cube |   + cube_w
#                          |_______|    |_______||______|...:
#                              :
#   SH=========================:=========================SH
#                          :   :                     :  :  :
#                          :   :      CUBE_SEP_L     :  :  :
#                          :   :                     :  :  :
#                          :   :.........stroke......:..:  :
#                          :                 cube_w/2 + :  :
#                          :........cube_block_l........:..:
#                                                         + sh_depth + extra_rod
# so the total length of the rod is:
# 2 * extra_rod + 2*sh_depth  + 2*stroke + cube_w
# since: cube_block = stroke + cube_w, then
# 2*extra_rod + 2*sh_depth + stroke + cube_block_l
# having it centered on Y=0

rod_led_pos = FreeCAD.Vector(0, rod_led_pos_y, rod_led_pos_z)
shp_rod_led = fcfun.shp_cylcenxtr(r= rod_led_r, h=rod_led_l, normal= VX,
                                  pos = rod_led_pos)
fco_rod_led = doc.addObject("Part::Feature", 'rod_led')
fco_rod_led.Shape = shp_rod_led

rod_bb_pos = FreeCAD.Vector(0, rod_bb_pos_y, rod_bb_pos_z)
shp_rod_bb = fcfun.shp_cylcenxtr(r= rod_bb_r, h=rod_bb_l, normal= VX,
                                     pos = rod_bb_pos)
fco_rod_bb = doc.addObject("Part::Feature", 'rod_bboard')
fco_rod_bb.Shape = shp_rod_bb

# Shaft holders are on Aluminum profiles



# sh_depth/2 because referenced at the middle
sh_pos_x = min(rod_bb_l, rod_led_l)/2. - sh_depth_max/2. - extra_rod


h_sh_bb_list = []
h_sh_led_list = []
for sufix, sh_pos_xi in zip(['n', 'p'], [-sh_pos_x, sh_pos_x]):
    sh_bb_pos = FreeCAD.Vector(sh_pos_xi, rod_bb_pos_y, rod_bb_pos_z)
    name_sh = 'sh_holder_bb_' + sufix
    h_sh_bb = comps.Sk_dir (size = int(rod_bb_d),
                                fc_axis_h = VZ,
                                fc_axis_d = VX,
                                ref_hr = 1, #ref at the rod
                                ref_wc = 1, #ref at the symmetry axis
                                ref_dc = 1, #ref at center
                                pos = sh_bb_pos,
                                name = name_sh)
    h_sh_bb_list.append(h_sh_bb)
    sh_led_pos = FreeCAD.Vector(sh_pos_xi, rod_led_pos_y,
                                    rod_led_pos_z)
    name_sh = 'sh_holder_led_' + sufix
    h_sh_led = comps.Sk_dir (size = int(rod_led_d),
                                fc_axis_h = VZ,
                                fc_axis_d = VX,
                                ref_hr = 1, #ref at the rod
                                ref_wc = 1, #ref at the symmetry axis
                                ref_dc = 1, #ref at center
                                pos = sh_led_pos,
                                name = name_sh)
    h_sh_led_list.append(h_sh_led)

 







# aluminum profiles to hold the linear bearings.
# Perpendicular to the previous

aluy_cubes_w = 10 # maybe 15 is better than 10
aluy_cubes_len = 150.
d_aluy_cubes = kcomp.ALU_PROF[aluy_cubes_w]

h_aluy_cubes = comps.getaluprof(d_aluy_cubes, length=aluy_cubes_len,
                           axis = 'y',
                           name = 'aluy_cubes_x',
                           cx=1, cy=0, cz=0)
h_aluy_cubes.color(ALU_COLOR)


aluy_cubes_vboard_sep = 2.5
aluy_cubes_pos_y = ( - aluy_cubes_len
                     + CUBECEN_VBBOARD_SEP
                     - aluy_cubes_vboard_sep
                     + aluy_cubes_w)

aluy_cubes_pos_y = (   alux_bb_pos_y
                     - aluy_cubes_len
                     + alux_cubes_w/2.)
fco_aluy_cubes_x = h_aluy_cubes.fco

aluy_cubes_pos_z = alux_cubes_pos_z +  alux_cubes_w
aluy_cubes_pos_x = cube_w/2.
# X will be set afterwards
fco_aluy_cubes_x.Placement.Base = FreeCAD.Vector(0, 
                                                  aluy_cubes_pos_y,
                                                  aluy_cubes_pos_z)
fco_aluy_cubes_nx = Draft.clone(fco_aluy_cubes_x)
fco_aluy_cubes_nx.ViewObject.ShapeColor = ALU_COLOR
aluy_cubes_pos_nx = - CUBE_SEP_L + cube_w/2.
fco_aluy_cubes_nx.Label = 'aluy_cubes_nx'
fco_aluy_cubes_nx.Placement.Base.x = aluy_cubes_pos_nx
fco_aluy_cubes_x.Placement.Base.x = aluy_cubes_pos_x
movegroup_list.append(fco_aluy_cubes_nx)
movegroup_list.append(fco_aluy_cubes_x)


#------ brackets to screw alux and aluy aluminum profiles:

#------ brackets on top of the symmetrical rail (leds' side)
#aluy_cubes_pos_z are referenced to the lowest point
br_alu_pos_z = aluy_cubes_pos_z 
#alux_leds_out_pos_y is centered on y
br_alu_pos_y = alux_leds_out_pos_y
br_alu_pos_nx = aluy_cubes_pos_nx + aluy_cubes_w/2
br_alu_pos_x = aluy_cubes_pos_x - aluy_cubes_w/2

br_alu_nx_pos = FreeCAD.Vector(br_alu_pos_nx, br_alu_pos_y, br_alu_pos_z)
br_alu_x_pos = FreeCAD.Vector(br_alu_pos_x, br_alu_pos_y, br_alu_pos_z)

alu_led_linbear_sep = 2 * rod2lbearbolt_dist_y

h_br_led_nx = parts.AluProfBracketPerpTwin ( alusize_lin = aluy_cubes_w,
                 alusize_perp = aluy_cubes_w,
                 alu_sep = alu_led_linbear_sep,
                 br_perp_thick = 3.,
                 br_lin_thick = 3.,
                 bolt_lin_d = 3,
                 nbolts_lin = 2,
                 bolt_perp_line = 0,
                 xtr_bolt_head = 2, 
                 sunk = 2,
                 fc_perp_ax = VZ,
                 fc_lin_ax = VX,
                 fc_wide_ax = VY,
                 pos = br_alu_nx_pos,
                 wfco=1,
                 name = 'bracket_twin_led_nx')
h_br_led_nx.color(PRINT_COLOR)
h_br_led_nx.export_stl()
movegroup_list.append(h_br_led_nx.fco)


h_br_led_x = parts.AluProfBracketPerpTwin ( alusize_lin = aluy_cubes_w,
                 alusize_perp = aluy_cubes_w,
                 alu_sep = alu_led_linbear_sep,
                 br_perp_thick = 3.,
                 br_lin_thick = 3.,
                 bolt_lin_d = 3,
                 nbolts_lin = 2,
                 bolt_perp_line = 1,
                 xtr_bolt_head = 4, 
                 sunk = 2,
                 fc_perp_ax = VZ,
                 fc_lin_ax = VXN,
                 fc_wide_ax = VY,
                 pos = br_alu_x_pos,
                 wfco=1,
                 name = 'bracket_twin_led_x')


h_br_led_x.color(PRINT_COLOR)
h_br_led_x.export_stl()
movegroup_list.append(h_br_led_x.fco)

print("alu_led_sep: " + str(alu_led_linbear_sep))


#------ brackets on top of the asymmetrical rail (bb breadboard side)

#alux_leds_out_pos_y is centered on y
br_alu_bb_pos_y = alux_cubes_y_pos_y

br_alu_bb_nx_pos = FreeCAD.Vector(br_alu_pos_nx,
                                    br_alu_bb_pos_y,
                                    br_alu_pos_z)
br_alu_bb_x_pos = FreeCAD.Vector(br_alu_pos_x,
                                   br_alu_bb_pos_y,
                                   br_alu_pos_z)

alu_bb_linbear_sep = h_lbear_bb.bolt2bolt_wid

h_br_bb_nx = parts.AluProfBracketPerpTwin ( alusize_lin = aluy_cubes_w,
                 alusize_perp = aluy_cubes_w,
                 alu_sep = alu_bb_linbear_sep,
                 br_perp_thick = 3.,
                 br_lin_thick = 3.,
                 bolt_lin_d = 3,
                 nbolts_lin = 2,
                 bolt_perp_line = 0,
                 xtr_bolt_head = 2, 
                 sunk = 2,
                 fc_perp_ax = VZ,
                 fc_lin_ax = VX,
                 fc_wide_ax = VY,
                 pos = br_alu_bb_nx_pos,
                 wfco=1,
                 name = 'bracket_twin_bb_nx')
h_br_bb_nx.color(PRINT_COLOR)
h_br_bb_nx.export_stl()
movegroup_list.append(h_br_bb_nx.fco)

h_br_bb_x = parts.AluProfBracketPerpTwin ( alusize_lin = aluy_cubes_w,
                 alusize_perp = aluy_cubes_w,
                 alu_sep = alu_bb_linbear_sep,
                 br_perp_thick = 3.,
                 br_lin_thick = 3.,
                 bolt_lin_d = 3,
                 nbolts_lin = 2,
                 bolt_perp_line = 1,
                 xtr_bolt_head = 4, 
                 sunk = 2,
                 fc_perp_ax = VZ,
                 fc_lin_ax = VXN,
                 fc_wide_ax = VY,
                 pos = br_alu_bb_x_pos,
                 wfco=1,
                 name = 'bracket_twin_bb_x')

h_br_bb_x.color(PRINT_COLOR)
h_br_bb_x.export_stl()
movegroup_list.append(h_br_bb_x.fco)


# ------------------ Aluminum profiles for the big frame
# size of the aluminum profiles for the rods structure
aluframe_w = 20
d_aluframe = kcomp.ALU_PROF[aluframe_w]

# position of rod center the breadboard shaft holder on the negative side of X:
# (-sh_pos_x, rob_bb_pos_y, rod_bb_pos_z)
# or
h_sh_bb_n = h_sh_bb_list[0]
h_sh_led_n = h_sh_led_list[0]

# so the corner bottom point, y_pos will be larger and z pos minimum:
# and will be the z_pos for the top face of the alu profile
#
#    bboard
#     ||                                        Z  
#     ||    ___               ___            Y _|
#     ||   | 0 |             | 0 |------
#     || __|   |__         __|   |__   + sh_led_h
#       |_________|_______|_________|..:
#       1                            2
#            aluframey
#       3____________________________4
#       :                             :
#       :........min_aluframey_l......:
#

# position of point 1
sh_bot_pos_z = h_sh_bb_n.pos.z - sh_bb_h
sh_bb_bot_py_pos_y = h_sh_bb_n.pos.y + h_sh_bb_n.tot_w/2
# Z position of point 3
aluframeybot_pos_z = sh_bot_pos_z - aluframe_w

# position of point 2, z is the same (different values to get it)
#sh_bot_pos_z = h_sh_led.pos.z + DraftVecUtils.scale(VZN, sh_led_h)
sh_led_bot_ny_pos_y = h_sh_led_n.pos.y - h_sh_led_n.tot_w/2

min_aluframey_l = abs(sh_bb_bot_py_pos_y - sh_led_bot_ny_pos_y) + 2*aluframe_w

file_comps.write('# Min length of aluframey: ')
file_comps.write( str(min_aluframey_l) + ' mm \n')

# 20x20 alu profiles we have
alu_list_20 = [670, 500, 400, 360, 350,  340, 330, 320, 300, 280, 260, 240,
               220, 180, 160, 54]

d_alu_l = { 20 : alu_list_20 }

aluframey_l = 0
for alulen in d_alu_l[aluframe_w]:
    if min_aluframey_l > alulen:
        break
    else:
        aluframey_l = alulen

file_comps.write('# Length of aluframey: ')
file_comps.write( str(aluframey_l) + ' mm \n')

aluframey_nx_pos = FreeCAD.Vector(-sh_pos_x,
                                  (sh_bb_bot_py_pos_y+sh_led_bot_ny_pos_y)/2.,
                                  sh_bot_pos_z)
h_aluframey_nx = comps.getaluprof_dir(d_aluframe, aluframey_l,
                                  fc_axis_l = cVY,
                                  fc_axis_w = cVZN,
                                  ref_l = 1, # centered
                                  ref_w = 2, # looking down
                                  # ref_p = 1, # centered
                                  pos = aluframey_nx_pos,
                                  name = 'aluframey_nx')
h_aluframey_nx.color(ALUFRAME_COLOR)

aluframey_x_pos = aluframey_nx_pos
aluframey_x_pos.x = sh_pos_x
h_aluframey_x = comps.getaluprof_dir(d_aluframe, aluframey_l,
                                 fc_axis_l = cVY,
                                 fc_axis_w = cVZN,
                                 ref_l = 1, # centered
                                 ref_w = 2, # looking down
                                 pos = aluframey_x_pos,
                                 name = 'aluframey_x')
h_aluframey_x.color(ALUFRAME_COLOR)

#    bboard
#     ||                                        Z  
#     ||    ___               ___            Y _|
#     ||   | 0 |             | 0 |------
#     || __|   |__         __|   |__   + sh_led_h
#     |||_________|_______|_________|..:
#     ||1                            2
#     ||     aluframey
#     ||3____________________________4  aluframeybot_pos_z 
#     || \/ |
#     | >  < aluframex_y
#     ||_/\_| 
#     ||
#      y_pos=CUBECEN_VBBOARD_SEP

# the minimum length is the distance of the shaft holders + 2*aluframe_w/2
#
#       Shaft holder
#       ___                                        Z
#      |   |__________________                     |_ X
#      |   |__________________                     
#      |___|
#     _|___|_
#    |  \ /  |                           |  \ /  | 
#     >     <  aluframey_nx               >     <  aluframey_x
#    |__/_\__|___________________________|__/ \__|
#    |   :                                   :   |
#    |   :      aluframex_y                  :   |
#    |   :                                   :   |
#    |___:___________________________________:___|
#    :   :                                   :
#    :. .:...........2 * sh_pos_x ...........:
#      + aluframe_w/2.
#
#
min_aluframex_l = 2*sh_pos_x + aluframe_w
aluframex_l = 0
for alulen in d_alu_l[aluframe_w]:
    if min_aluframex_l > alulen:
        break
    else:
        aluframex_l = alulen

file_comps.write('# Minimum aluframex (along the rods: ')
file_comps.write( str(min_aluframex_l) + ' mm \n')
file_comps.write('# Length of aluframex: ')
file_comps.write( str(aluframex_l) + ' mm \n')

aluframex_y_pos = FreeCAD.Vector(0, CUBECEN_VBBOARD_SEP, aluframeybot_pos_z)
h_aluframex_y = comps.getaluprof_dir(d_aluframe, aluframex_l,
                                 fc_axis_l = cVX,
                                 fc_axis_w = cVZN,
                                 fc_axis_p = cVYN,
                                 ref_l = 1, # centered
                                 ref_w = 2, # looking down
                                 ref_p = 2, # looking cVYN
                                 pos = aluframex_y_pos,
                                 name = 'aluframex_y')
h_aluframex_y.color(ALUFRAME_COLOR)

aluframex_ny_pos = FreeCAD.Vector(0, rod_led_pos_y, aluframeybot_pos_z)
h_aluframex_ny = comps.getaluprof_dir(d_aluframe, aluframex_l,
                                 fc_axis_l = cVX,
                                 fc_axis_w = cVZN,
                                 ref_l = 1, # centered
                                 ref_w = 2, # looking down
                                 ref_p = 1, # centered on y
                                 pos = aluframex_ny_pos,
                                 name = 'aluframex_ny')
h_aluframex_ny.color(ALUFRAME_COLOR)

aluframex_nz_y_pos = FreeCAD.Vector(0, CUBECEN_VBBOARD_SEP, 0)
h_aluframex_nz_y = comps.getaluprof_dir(d_aluframe, aluframex_l,
                                 fc_axis_l = cVX,
                                 fc_axis_w = cVZ,
                                 fc_axis_p = cVYN,
                                 ref_l = 1, # centered
                                 ref_w = 2, # looking up
                                 ref_p = 2, # looking cVYN
                                 pos = aluframex_nz_y_pos,
                                 name = 'aluframex_nz_y')
h_aluframex_nz_y.color(ALUFRAME_COLOR)

aluframex_nz_ny_pos = FreeCAD.Vector(0, rod_led_pos_y, 0)
h_aluframex_nz_ny = comps.getaluprof_dir(d_aluframe, aluframex_l,
                                 fc_axis_l = cVX,
                                 fc_axis_w = cVZ,
                                 fc_axis_p = cVYN,
                                 ref_l = 1, # centered
                                 ref_w = 2, # looking up
                                 ref_p = 1, # centered on y
                                 pos = aluframex_nz_ny_pos,
                                 name = 'aluframex_nz_ny')
h_aluframex_nz_ny.color(ALUFRAME_COLOR)

# ---------------------- FRAME 1 --------------------------------
frame1_list = []

# profiles at the bottom on axis y
aluframey_nz_nx_pos = FreeCAD.Vector(-sh_pos_x - aluframe_w ,
                                  (sh_bb_bot_py_pos_y+sh_led_bot_ny_pos_y)/2.,
                                   aluframe_w)
h_aluframey_nz_nx = comps.getaluprof_dir(d_aluframe, aluframey_l,
                                  fc_axis_l = cVY,
                                  fc_axis_w = cVZ,
                                  ref_l = 1, # centered
                                  ref_w = 2, # looking up
                                  # ref_p = 1, # centered
                                  pos = aluframey_nz_nx_pos,
                                  name = 'aluframe1y_nz_nx')
h_aluframey_nz_nx.color(ALUFRAME_COLOR)
frame1_list.append(h_aluframey_nz_nx.fco)

# doing this you make both vector being the same!!!
# it seems to work on pointers
#aluframey_nz_x_pos = aluframey_nz_nx_pos
aluframey_nz_x_pos = FreeCAD.Vector(aluframey_nz_nx_pos)
aluframey_nz_x_pos.x = - aluframey_nz_nx_pos.x
h_aluframey_nz_x = comps.getaluprof_dir(d_aluframe, aluframey_l,
                                 fc_axis_l = cVY,
                                 fc_axis_w = cVZ,
                                 ref_l = 1, # centered
                                 ref_w = 2, # looking up
                                 pos = aluframey_nz_x_pos,
                                 name = 'aluframe1y_nz_x')
h_aluframey_nz_x.color(ALUFRAME_COLOR)
frame1_list.append(h_aluframey_nz_x.fco)

# vertical profiles for the frame
min_aluframez_l = sh_bot_pos_z - 2 * aluframe_w
aluframez_l = 0
for alulen in d_alu_l[aluframe_w]:
    if min_aluframez_l > alulen:
        break
    else:
        aluframez_l = alulen

file_comps.write('# Minimum aluframez (vertical) for frame_1: ')
file_comps.write( str(min_aluframez_l) + ' mm \n')
file_comps.write('# Length of aluframez for frame_1: ')
file_comps.write( str(aluframez_l) + ' mm \n')

h_aluframe1z_dict = {}
for x_sufi, x_posi in zip(['nx', 'x'],
                      [aluframey_nz_nx_pos.x, aluframey_nz_x_pos.x]):
    for y_sufi, y_posi in zip(['_ny', '_y'],
                       [aluframex_nz_ny_pos.y - aluframe_w, 
                   # because aluframex_nz_y_pos was not centered and
                   # pointing to the opposite way
                    aluframex_nz_y_pos.y + aluframe_w/2.]):
        aluframez_pos_i = FreeCAD.Vector(x_posi, y_posi, 2*aluframe_w)
        name_i = 'aluframe1z_' + x_sufi + y_sufi
        h_aluframez = comps.getaluprof_dir(d_aluframe, aluframez_l,
                             fc_axis_l = cVZ,
                             fc_axis_w = cVY,
                             ref_l = 2, # looking up
                             ref_w = 1, # centered on y, like aluframex_nz_y
                             pos = aluframez_pos_i,
                             name = name_i)
        h_aluframez.color(ALUFRAME_COLOR)
        frame1_list.append(h_aluframez.fco)
        h_aluframe1z_dict[(x_sufi+y_sufi)] = h_aluframez


frame_1_group = doc.addObject("Part::Compound","frame_1")
frame_1_group.Links = frame1_list


# ---------------------- FRAME 2 --------------------------------
frame2_list = []

# vertical profiles for the frame
min_aluframez_l = sh_bot_pos_z -  aluframe_w
aluframez_l = 0
for alulen in d_alu_l[aluframe_w]:
    if min_aluframez_l > alulen:
        break
    else:
        aluframez_l = alulen

file_comps.write('# Minimum aluframez (vertical) for frame_2: ')
file_comps.write( str(min_aluframez_l) + ' mm \n')
file_comps.write('# Length of aluframez for frame_2: ')
file_comps.write( str(aluframez_l) + ' mm \n')

h_aluframey_dict = {}
h_aluframe2z_dict = {}
x_posi_abs = aluframex_l/2. + aluframe_w/2.
for x_sufi, x_sigi in zip(['nx', 'x'], [-1, 1]):
    # profiles at the bottom on axis y
    pos_i = FreeCAD.Vector( x_sigi * x_posi_abs,
                           (sh_bb_bot_py_pos_y+sh_led_bot_ny_pos_y)/2.,
                            0)
    name_i = 'aluframe2y_' + x_sufi
    h_aluframey_nz = comps.getaluprof_dir(d_aluframe, aluframey_l,
                                  fc_axis_l = cVY,
                                  fc_axis_w = cVZ,
                                  ref_l = 1, # centered
                                  ref_w = 2, # looking up
                                  # ref_p = 1, # centered
                                  pos = pos_i,
                                  name = name_i)
    h_aluframey_nz.color(ALUFRAME_COLOR)
    frame2_list.append(h_aluframey_nz.fco)
    h_aluframey_dict[(x_sufi+y_sufi)] = h_aluframey_nz

    # vertical profiles
    for y_sufi, y_posi in zip(['_ny', '_y'],
                       [aluframex_nz_ny_pos.y, 
                   # because aluframex_nz_y_pos was not centered and
                   # pointing to the opposite way
                    aluframex_nz_y_pos.y - aluframe_w/2.]):
        pos_i = FreeCAD.Vector(x_sigi * x_posi_abs, y_posi, aluframe_w)
        name_i = 'aluframe2z_' + x_sufi + y_sufi
        h_aluframez = comps.getaluprof_dir(d_aluframe, aluframez_l,
                             fc_axis_l = cVZ,
                             fc_axis_w = cVY,
                             ref_l = 2, # looking up
                             ref_w = 1, # centered on y, like aluframex_nz_y
                             pos = pos_i,
                             name = name_i)
        h_aluframez.color(ALUFRAME_COLOR)
        frame2_list.append(h_aluframez.fco)
        h_aluframe2z_dict[(x_sufi+y_sufi)] = h_aluframez


frame_2_group = doc.addObject("Part::Compound","frame_2")
frame_2_group.Links = frame2_list

# ------------------- end frame 2

view_frame_1 = 2

if view_frame_1 == 1:
    frame_1_group.ViewObject.Visibility=True
    frame_2_group.ViewObject.Visibility=False
else:
    frame_1_group.ViewObject.Visibility=False
    frame_2_group.ViewObject.Visibility=True


n_movegr = len(movegroup_list)
mvgroup_l = list(set(movegroup_list))
n_cl_movegr = len(mvgroup_l)
# to check if any element has been take twice
print ("movegroup elements: " + str(n_movegr) + " - " + str(n_cl_movegr))


movegroup = doc.addObject("Part::Compound","movegroup")
movegroup.Links = mvgroup_l
# movement range: 3 positions
movegroup.Placement.Base = FreeCAD.Vector(CUBE_SEP_L,0,0)
movegroup.Placement.Base = FreeCAD.Vector(-CUBE_SEP_R,0,0)
#movegroup.Placement.Base = FreeCAD.Vector(0,0,0)


file_comps.close()

doc.recompute()

guidoc.ActiveView.setAxisCross(True)














