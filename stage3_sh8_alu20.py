# ----------------------------------------------------------------------------
# -- 3 axis stage (XYZ), done with 20mm aluminum extrusion profiles
# -- Python scripts for the small version of the cytometer base
# ----------------------------------------------------------------------------
# -- (c) Felipe Machado
# -- Area of Electronics. Rey Juan Carlos University (urjc.es)
# -- January-2017
# ----------------------------------------------------------------------------
# --- LGPL Licence
# ----------------------------------------------------------------------------

# to execute from the FreeCAD console:
#  execute freecad from the cmd console on the directory
# "C:\Program Files\FreeCAD 0.16\bin\freecad" stage3_20.py

# to excute from command line in windows:
# "C:\Program Files\FreeCAD 0.16\bin\freecadcmd" stage3_20.py

# name of the file
filename = "stage3_sh8_alu20"

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

# to get the components
# In FreeCAD can be added: Preferences->General->Macro->Macro path
sys.path.append(filepath) 
# Either one of these 2 to select the path, inside the tree, copied by
# git subtree, or in its one place
#sys.path.append(filepath + '/' + 'modules/comps'
sys.path.append(filepath + '/' + '../comps')

# where the freecad document is going to be saved
savepath = filepath + "/../../freecad/stage/py/"

import fcfun   # import my functions for freecad. FreeCad Functions
import kstage  # import stage constants
import kcomp   # import material constants and other constants
import comps   # import my CAD components
import parts   # import my CAD components to print
import stageparts # import my CAD pieces to be printed

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
# In this design, the base will be centered on X

logging.basicConfig(level=logging.DEBUG,
                    format='%(%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

doc = FreeCAD.newDocument()

Gui.ActiveDocument = Gui.getDocument(doc.Label)
guidoc = Gui.getDocument(doc.Label)

# file to save the components and their dimensions. Kind of a BOM,
# bill of materials
file_comps = open ('stage_bom.txt', 'w')

# we want to move 2 portas
# constants defined in kstage
#
#       _______________................
#      |  ___________  |              :
#      | |           | |              :
#      | |___________|.|...           + PORTABASE_L
#      |  ___________ .|...PORTA_SEP  :
#      | |           | |  + PORTA_W   :
#      | |___________|.|..:           :              Y
#      |_______________|..............:              |_ X
#      : :           : :
#      : :..PORTA_L..: :
#      :               :
#      :..PORTABASE_W..:
#

# Aluminum profile dimensions
ALU_Wi = 20
ALU_W = float(ALU_Wi)

file_comps.write('# Aluminum profile width: ' + str(ALU_Wi) + ' mm \n')
file_comps.write('\n')

# Rod diameter on Y direction
RODY_Di = 8  # integer
RODY_D  = float(RODY_Di)  # float
RODY_R  = RODY_D/2.
file_comps.write('# Shaft diameter: ' + str(RODY_Di) + ' mm \n')
file_comps.write('\n')
RODX_Di = RODY_Di
RODX_D  = float(RODX_Di)  # float
RODX_R  = RODX_D/2.



aluprof_dict = kcomp.ALU_PROF.get(ALU_Wi)
if aluprof_dict == None:
    logger.error('Aluminum extrusion width %d not yet defined', ALU_Wi)

# We are having the stage centered on X 
# The origin (0,0,0) will be on the X-Y shafts. On the center of the sliders


# --------------- Y slider, the one on the end of X, on the negative side
# we need some of its dimensions, so we create it here, and then, it will be
# positioned

rodx_sep = kstage.PORTABASE_L  # calculate

h_yslid_nx = stageparts.EndShaftSlider(slidrod_r = RODY_R,
                                        holdrod_r = RODY_R,
                                        holdrod_sep = rodx_sep,
                                        name          = "yslider_nx",
                                        holdrod_cen = 1,
                                        side = 'left')


# Dimensions of the stage
STAGE_X = 2.5 * kstage.PORTABASE_W
STAGE_Y = kstage.PORTABASE_L + h_yslid_nx.length + 2*ALU_W

file_comps.write('# Stage Dimensions X: '+ str(STAGE_X) + ' mm \n')
file_comps.write('# Stage Dimensions Y: '+ str(STAGE_Y) + ' mm \n')


# Y positions: From the front aluminum profile
#
#                 Y
#                 :
#       ______________________
#       |____________________|
#       ||        :         ||
#       ||        :         ||
#       ||        :         ||
#      _||_       :        _||_
#     |    |      :       |    |     The y center is on the center of y slider
#     |    |      : - - - | - -| - - - - X 
#     |____|______________|____|....+ h_yslid_nx.length/2 ............
#       |____________________|......+ ALU_W
#
#

# ALU_W/2. because the aluminum profile is centered
y_off = ALU_W/2. + h_yslid_nx.length/2.
alux_pos_ny = - y_off
alux_pos_y  = alux_pos_ny + STAGE_Y - ALU_W
yslid_pos_y = alux_pos_ny +  ALU_W/2. +  h_yslid_nx.length/2. # + y_rail_l/2
rodx_pos_ny = yslid_pos_y - rodx_sep/2.
rodx_pos_y  = yslid_pos_y + rodx_sep/2.


# Z positions: From the bottom aluminum profile
#        _____
#       |     |
#       | ( ) |- - - - - - -  Z ORIGIN
#      _|     |_       +  kcomp.SK[RODY_Di]['h']
#    _|_________!__ ...:
#                      + ALU_W
#    ______________ ...:
#

# Offset, now is on the XY-shafts, but it could be changed
z_off = ALU_W + kcomp.SK[RODY_Di]['h'] # Z Origin
alu_pos_z  = - z_off
sky_pos_z  = ALU_W + alu_pos_z
rody_pos_z = sky_pos_z + kcomp.SK[RODY_Di]['h'] #h_sky.HoleH
rodx_pos_z = rody_pos_z
    


#  ------------- X alum profiles
h_alux = comps.getaluprof (aludict= aluprof_dict,
                               length = STAGE_X,
                               axis = 'x',
                               name = "alux_y0",
                               cx=1, cy=1, cz=0)

file_comps.write('# 2 Aluminum Profile X axis: Width: '+ str(ALU_Wi))
file_comps.write(' Length  '+ str(STAGE_X) + ' mm \n')
file_comps.write('\n')

#  the profile on negative Y (or y=0, depends on the offset)
alux_ny = h_alux.fco   # the FreeCad Object
alux_ny.Placement.Base.z = alu_pos_z
alux_ny.Placement.Base.y = alux_pos_ny

# the profile on y positive: y
alux_y = Draft.clone(alux_ny)
alux_y.Label = "alux_y"
alux_y.Placement.Base.y = alux_pos_y
alux_y.Placement.Base.z = alu_pos_z


#  ------------- Y alum profiles
# the one on x positive

aluy_len = STAGE_Y - 2 * ALU_W # length of the aluminum profile
h_aluy = comps.getaluprof (aludict = aluprof_dict,
                           length = aluy_len,
                           axis = 'y',
                           name = "aluy_x",
                           cx=1, cy=0, cz=0)

file_comps.write('# 2 Aluminum Profile Y axis: Width: '+ str(ALU_Wi))
file_comps.write(' Length  '+ str(aluy_len) + ' mm \n')
file_comps.write('\n')

aluy_x = h_aluy.fco   # the FreeCad Object
aluy_pos_x = STAGE_X/2. - ALU_W/2.

# the profile on x positive: x
aluy_x.Placement.Base = FreeCAD.Vector(aluy_pos_x,
                                       alux_pos_ny + ALU_W/2.,
                                       alu_pos_z)

# the profile on x negative: nx
aluy_nx = Draft.clone(aluy_x)
aluy_nx.Label = "aluy_nx"
aluy_nx.Placement.Base = FreeCAD.Vector(-aluy_pos_x,
                                         alux_pos_ny + ALU_W/2.,
                                         alu_pos_z)


# ------------------ Shaft holders SK of Y ------------------------------
# f= front; r: right. hole_x = 0 -> hole facing Y axis
h_sky = comps.Sk(size=RODY_Di, name="sky_x_y0", hole_x = 0, cx=1, cy=1)
sky_pos_x = STAGE_X/2. -  h_sky.TotW/2.
# rod_y_sep: separation between the Y shafts
rod_y_sep = 2 + sky_pos_x

file_comps.write('# 4 Shaft Holders, SK'+ str(RODY_Di) + ' \n')
file_comps.write('\n')

# SK on X postive and Y=0
sky_x_y0 = h_sky.fco   # the FreeCad Object
sky_x_y0.Placement.Base = FreeCAD.Vector (sky_pos_x,
                                          alux_pos_ny,
                                          sky_pos_z)
# SK on X negative and Y=0
sky_nx_y0 = Draft.clone(sky_x_y0)
sky_nx_y0.Label = "sky_nx_y0"
sky_nx_y0.Placement.Base.x = -sky_pos_x

# SK on X positive and Y positive
sky_x_y = Draft.clone(sky_x_y0)
sky_x_y.Label = "sky_x_y"
sky_x_y.Placement.Base.y = alux_pos_y

# SK on X negative and Y positive
sky_nx_y = Draft.clone(sky_x_y0)
sky_nx_y.Label = "sky_nx_y"
sky_nx_y.Placement.Base.x = -sky_pos_x
sky_nx_y.Placement.Base.y = alux_pos_y

# rod outside of the rod holder, just 1 mm
rody_out = 1
# the length of the rod that is off the rod holder center (SK)
rody_off =  h_sky.TotD/2. + rody_out 

# the total length of the rod
rody_l = STAGE_Y - ALU_W + 2 * rody_off

file_comps.write('# 2 Shafts, Y axis, Diameter '+ str(RODY_Di) )
file_comps.write('  Length: '+ str(rody_l) + '\n' )
file_comps.write('\n')

# ------------------ Y Shafts --------------------------------------

rody_pos_x = sky_pos_x
rody_sep = 2 * rody_pos_x #separation between the y rods
rody_pos_y = -rody_off + alux_pos_ny


v_rody_x = FreeCAD.Vector(rody_pos_x, rody_pos_y, rody_pos_z)
rody_x = fcfun.addCylPos(r= RODY_R, h=rody_l, name= "rody_x",
                         normal = VY, 
                         pos = v_rody_x)
                                            
v_rody_nx = FreeCAD.Vector(-rody_pos_x, rody_pos_y, rody_pos_z)
rody_nx = fcfun.addCylPos(r= RODY_R, h=rody_l, name= "rody_nx",
                         normal = VY, 
                         pos = v_rody_nx)



# --------------- Y sliders --------------------------------------

# the length of the y rail, just the lenght of the rod taking away the part
# that is over the aluminum extrusion
y_rail_l = STAGE_Y - 2 * ALU_W
# the stroke: the length of the rail minus the length of the slider
y_stroke = y_rail_l - h_yslid_nx.length

h_yslid_nx.BasePlace ((-rody_sep/2., yslid_pos_y, rody_pos_z))

# --------------- Y slider, the one on the end of X, on the negative side
h_yslid_x = stageparts.EndShaftSlider(slidrod_r = RODY_R,
                                      holdrod_r = RODX_R,
                                      holdrod_sep = rodx_sep,
                                      name          = "yslider_x",
                                      holdrod_cen = 1,
                                      side = 'right')

h_yslid_x.BasePlace ((rody_sep/2., yslid_pos_y, rody_pos_z))

file_comps.write('# 2 Y sliders \n')
file_comps.write('# Y Slider Dimensions length (Y): ')
file_comps.write(str(h_yslid_x.length) + ' mm \n')
file_comps.write('# Y Slider Dimensions width (X): ')
file_comps.write(str(h_yslid_x.width) + ' mm \n')
file_comps.write('# Y Slider Dimensions height (Z): ')
file_comps.write(str(2*h_yslid_x.partheight) + ' mm \n')
file_comps.write('\n')


# -------- X rods (shafts)

# the one on the front:
rodx_pos_x = - sky_pos_x + h_yslid_x.slide2holdrod + TOL
rodx_l = - 2* rodx_pos_x

file_comps.write('# 2 Shafts, X axis, Diameter '+ str(RODX_Di) )
file_comps.write('  Length: '+ str(rodx_l) )
file_comps.write('\n')

rodx_ny = fcfun.addCyl_pos ( r= RODX_R, h = rodx_l, name="rod_x_ny",
                      axis = 'x', h_disp = rodx_pos_x)

rodx_ny.Placement.Base = FreeCAD.Vector(0, rodx_pos_ny, rodx_pos_z)

rodx_y = fcfun.addCyl_pos ( r= RODX_R, h = rodx_l, name="rod_x_y",
                      axis = 'x', h_disp = rodx_pos_x)

rodx_y.Placement.Base = FreeCAD.Vector(0, rodx_pos_y, rodx_pos_z)

# --------------- Central Slider, with inner hole

h_censlid = stageparts.CentralSliderHole (
                                   rod_r   = RODX_R,
                                   rod_sep = rodx_sep,
                                   name    = "central_slider",
                                   belt_sep = h_yslid_x.belt_sep,
                                   dent_w  = h_yslid_x.dent_w,
                                   dent_l  = h_yslid_x.dent_l,
                                   dent_sl = h_yslid_x.dent_sl,
                                   dlg_nx = kcomp.SEBWM16,
                                   dlg_x = kcomp.SEBWM16,
                                   dlg_ny = kcomp.SEB15A,
                                   dlg_y = kcomp.SEB15A
                                 )
#h_censlid.BasePlace ((0, portabase_pos_y, rod_y_pos_z))


h_portatrayhole = stageparts.PortaTrayHole(
                         porta_l = kstage.PORTA_L,
                         porta_w = kstage.PORTA_W,
                         porta_h = kstage.PORTA_H,
                         n_porta = 2,
                         porta_sep = 5.,
                         sep_ext = 10.,
                         tray_h = 8.,
                         toplimit = 1,
                         extraporta_l = 3,
                         clamp = -1,
                         axis_portas = 'x',
                         handhole = 1,
                         fco = 1,
                         name = 'portatray',
                         pos_z = 20)


# Nut for the vertical Leadscrew


h_vlscrew_nut = comps.get_mis_min_lscrnut (kcomp.MIS_LSCRNUT_C_L1_T4, 
                                           nutaxis = '-z',
                                           cutaxis = 'y',
                                           name = 'vertical_lscrew_nut',
                                           axis_pos = 20-8) 

file_comps.close()

doc.recompute()

h_yslid_nx.top_slide.ViewObject.ShapeColor = fcfun.BLUE_05
h_yslid_nx.bot_slide.ViewObject.ShapeColor = fcfun.BLUE_05
h_yslid_x.top_slide.ViewObject.ShapeColor = fcfun.BLUE_05
h_yslid_x.bot_slide.ViewObject.ShapeColor = fcfun.BLUE_05

h_portatrayhole.fco.ViewObject.ShapeColor = fcfun.YELLOW_05
h_portatrayhole.fco_clamp_group.ViewObject.ShapeColor = fcfun.ORANGE

doc.recompute()



