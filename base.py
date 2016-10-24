# ----------------------------------------------------------------------------
# -- Cytometer Base
# -- Python scripts for the cytometer base
# ----------------------------------------------------------------------------
# -- (c) Felipe Machado
# -- Area of Electronics. Rey Juan Carlos University (urjc.es)
# -- October-2016
# ----------------------------------------------------------------------------
# --- LGPL Licence
# ----------------------------------------------------------------------------

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
#import mat_cte  # name changed to kcomp
import kcomp   # import material constants and other constants
import comps   # import my CAD components
import parts3d # import my CAD pieces to be printed

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



# Aluminum profiles for the citometer base

#  ------------- X alum profiles
# fb: front (y=0) bottom (z=0)
h_alu_x_fb = comps.MisumiAlu30s6w8 (kcit.CIT_X -2 * kcit.ALU_W,
                                    "alu_x_fb", axis= 'x', cx=1, cy=1, cz=0)
alu_x_fb = h_alu_x_fb.fco   # the FreeCad Object

# bb: back (y=0) bottom (z=0)
alu_x_bb = Draft.clone(alu_x_fb)
alu_x_bb.Label = "alu_x_bb"
alu_x_bb.Placement.Base = (FreeCAD.Vector( 0, kcit.CIT_Y - kcit.ALU_W,0)) 

# Temporary middle aluminun profile
# Now I have a ROD_Y of 550 mm (ROD_Y_L), so I need to make the Y length
# smaller. The availabe length of the rod from the center of the alum profile
# is  ROD_Y_L - TotD - 2.   # (TotD/ 2) * 2 (each side) and then about 1mm 
#  standing out

# bm: bottom, middle

# rod outside of the rod holder, just 1 mm
rod_y_out = 1
# the length of the rod that is off the rod holder center (SK)
rod_y_off =  kcomp.SK12['L']/2.0 + rod_y_out 
alu_x_bm_ypos = (   (kcit.CIT_Y - kcit.ALU_W)
                  - (kcit.ROD_Y_L - 2 * (rod_y_off)))

alu_x_bm = Draft.clone(alu_x_fb)
alu_x_bm.Label = "alu_x_bmid"
alu_x_bm.Placement.Base = ( FreeCAD.Vector ( 0, alu_x_bm_ypos,0)) 

"""

   ____________
      _____
     |     |   
     |_____|     
   ____________    

"""


#  ------------- Y alum profiles
# lb: left (x=-) bottom (z=0)

h_alu_y_lb = comps.MisumiAlu30s6w8 (kcit.CIT_Y -  kcit.ALU_W,
                                    "alu_y_fb", axis= 'y', cx=1, cy=0, cz=0)
alu_y_lb = h_alu_y_lb.fco   # the FreeCad Object
alu_y_lb.Placement.Base = FreeCAD.Vector(-(kcit.CIT_X/2.0 -kcit.ALU_W/2.0),
                                         -kcit.ALU_W/2.0,
                                         0)

# rb: right (x=+) bottom (z=0)
alu_y_rb = Draft.clone(alu_y_lb)
alu_y_rb.Label = "alu_y_rb"
alu_y_rb.Placement.Base = FreeCAD.Vector( kcit.CIT_X/2.0 -kcit.ALU_W/2.0,
                                         -kcit.ALU_W/2.0,
                                         0)


# ------------------- X End Slider, just this one becuase I needed the
# slid2holdrod distance is needed

h_xendslid_l = parts3d.EndShaftSlider(slidrod_r = kcit.ROD_R,
                                   holdrod_r = kcit.ROD_R,
                                   holdrod_sep = kcit.ROD_X_SEP,
                                   name          = "slider_left",
                                   holdrod_cen = 1,
                                   side = 'left')




# ------------------ Shaft holders SK12 ------------------------------
# f= front; r: right. hole_x = 0 -> hole facing Y axis
h_sk12_fr = comps.Sk(size=12, name="sk12_fr", hole_x = 0, cx=1, cy=1)
sk12_fr = h_sk12_fr.fco   # the FreeCad Object
# rod_y_sep is the separation of the Y RODs
rod_y_sep = kcit.ROD_X_L + 2.0 * h_xendslid_l.slide2holdrod + 2 * TOL
sk12_fr.Placement.Base = FreeCAD.Vector (rod_y_sep/2.0,
                                         alu_x_bm_ypos, # 0
                                         kcit.ALU_W)
# f= front; l: left
sk12_fl = Draft.clone(sk12_fr)
sk12_fl.Label = "sk12_fl"
sk12_fl.Placement.Base = FreeCAD.Vector (-rod_y_sep/2.0,
                                          alu_x_bm_ypos, # 0
                                          kcit.ALU_W)

# b= back; r: right
sk12_br = Draft.clone(sk12_fr)
sk12_br.Label = "sk12_br"
sk12_br.Placement.Base = FreeCAD.Vector ( rod_y_sep/2.0,
                                          kcit.CIT_Y - kcit.ALU_W,
                                          kcit.ALU_W)

# b= back; l: left
sk12_bl = Draft.clone(sk12_fr)
sk12_bl.Label = "sk12_bl"
sk12_bl.Placement.Base = FreeCAD.Vector (-rod_y_sep/2.0,
                                          kcit.CIT_Y - kcit.ALU_W,
                                          kcit.ALU_W)


# ------------------ Y Shafts --------------------------------------
# rod_y_off is defined abover

# the length of the rod inside the rod holders
rod_y_use = 2*rod_y_off + kcomp.SK12['L']

# the height of the Y rod
rod_y_pos_h = sk12_fr.Placement.Base.z + h_sk12_fr.HoleH

rod_y_l = addCyl(r= kcit.ROD_D/2.0, h=kcit.ROD_Y_L, name= "rod_y_l")
rod_y_l.Placement.Base = FreeCAD.Vector (-rod_y_sep/2.0,
                                            alu_x_bm_ypos - rod_y_off,
                                            rod_y_pos_h)
rod_y_l.Placement.Rotation = FreeCAD.Rotation (VX,-90)
                                            
rod_y_r = addCyl(r= kcit.ROD_D/2.0, h=kcit.ROD_Y_L, name= "rod_y_r")
rod_y_r.Placement.Base = FreeCAD.Vector ( rod_y_sep/2.0,
                                            alu_x_bm_ypos - rod_y_off,
                                            rod_y_pos_h)
rod_y_r.Placement.Rotation = FreeCAD.Rotation (VX,-90)
                                            
                                            
# ------------------ Base of the portas ----------------------------

portabase = addBox (x = kcit.PORTABASE_W,
                    y = kcit.PORTABASE_L,
                    z = kcit.PORTABASE_H,
                    name = "portabase",
                    cx = 1, cy= 0)

portabase_pos_y = (   kcit.CIT_Y 
                    - (1.5 * kcit.ALU_W)
                    - portabase.Width.Value)

portabase.Placement.Base.y = portabase_pos_y
#portabase.Placement.Base.z = 250

portahold_box = addBox (x = portabase.Length,
                        y = portabase.Width,
                        z = kcit.PORTA_H,
                        name = "portahold_box",
                        cx = 1, cy= 0)

portahold_box.Placement.Base.z = portabase.Height
#portahold_box.Placement.Base.z = portabase.Height.Value + 250


portahole_list = []
for i in xrange(kcit.N_PORTA):
    portahole_i = addBox (x = kcit.PORTA_L + TOL,
                        y = kcit.PORTA_W + TOL,
                        z = kcit.PORTA_H + 2,  # +2 to cut
                        name = "portahole_" + str(i),
                        cx = 1, cy= 0)
    portahole_pos_y =  (i+1)*kcit.PORTAS_SEP + i *kcit.PORTA_W - TOL/2.0
    # portabase.Height is a quantity, so cannot be added to a value.
    # so I have to take its value
    portahole_pos = FreeCAD.Vector(0,
                                   portahole_pos_y,
                                   portabase.Height.Value - 1) 
    # add its position to make it relative
    portahole_i.Placement.Base = portahole_pos + portahole_i.Placement.Base
    portahole_list.append(portahole_i)

# Union of all the portaholes:
portahold_holes = doc.addObject("Part::MultiFuse", "portahold_holes")
portahold_holes.Shapes = portahole_list

# Cut the holes from portahold_box
portahold = doc.addObject("Part::Cut", "portahold")
portahold.Base = portahold_box
portahold.Tool = portahold_holes

portahold.Placement.Base.y = portabase_pos_y
#portahold.Placement.Base.z = 250


doc.recompute()
# this changes the color, but doesn't show it on the gui
portahold.ViewObject.ShapeColor = fcfun.RED
"""
guidoc.getObject(portahold.Label).ShapeColor = fcfun.BLACK
guidoc.portahold.ShapeColor = fcfun.RED
guidoc.portahold.ShapeColor = fcfun.RED
"""

"""
lm_bearing = fcfun.addCylHole (r_ext = kcomp.LMEUU_D[kcit.ROD_Di]/2.0,
                               r_int = kcit.ROD_D/2.0,
                               h= kcomp.LMEUU_L[kcit.ROD_Di],
                               name = "lm" + str(kcit.ROD_Di) + "uu",
                               axis = 'y',
                               h_disp = -kcomp.LMEUU_L[kcit.ROD_Di]/2)

lm_bearing = fcfun.addCylHole (r_ext = kcomp.LMEUU_D[kcit.ROD_Di]/2.0,
                               r_int = kcit.ROD_D/2.0,
                               h= kcomp.LMEUU_L[kcit.ROD_Di],
                               name = "lm" + str(kcit.ROD_Di) + "uu",
                               axis = 'x',
                               h_disp = 0)

lm_bearing = fcfun.addCylHole (r_ext = kcomp.LMEUU_D[kcit.ROD_Di]/2.0,
                               r_int = kcit.ROD_D/2.0,
                               h= kcomp.LMEUU_L[kcit.ROD_Di],
                               name = "lm" + str(kcit.ROD_Di) + "uu",
                               axis = 'z',
                               h_disp = TOL)
"""


# ------------------- X End Slider
# This has been moved up, because the slid2holdrod distance is needed
#h_xendslid_l = parts3d.EndShaftSlider(slidrod_r = kcit.ROD_R,
#                                   holdrod_r = kcit.ROD_R,
#                                   holdrod_sep = kcit.ROD_X_SEP,
#                                   name          = "slider_left",
#                                   holdrod_cen = 1,
#                                   side = 'left')

h_xendslid_l.BasePlace ((-rod_y_sep/2.0, portabase_pos_y, rod_y_pos_h))



h_xendslid_r = parts3d.EndShaftSlider(slidrod_r = kcit.ROD_R,
                                   holdrod_r    = kcit.ROD_R,
                                   holdrod_sep  = kcit.ROD_X_SEP,
                                   name         = "slider_right",
                                   holdrod_cen  = 1,
                                   side = 'right')

h_xendslid_r.BasePlace ((rod_y_sep/2.0, portabase_pos_y, rod_y_pos_h))

# ------------------- Central Slider

print "h_zendslid_r.dent_w " + str(h_xendslid_r.dent_w)
print "h_zendslid_r.dent_w " + str(h_xendslid_r.dent_l)
print "h_zendslid_r.dent_w " + str(h_xendslid_r.dent_sl)

h_censlid = parts3d.CentralSlider (rod_r   = kcit.ROD_R,
                                   rod_sep = kcit.ROD_X_SEP,
                                   name    = "central_slider",
                                   dent_w  = h_xendslid_r.dent_w,
                                   dent_l  = h_xendslid_r.dent_l,
                                   dent_sl = h_xendslid_r.dent_sl)

h_censlid.BasePlace ((0, portabase_pos_y, rod_y_pos_h))


# -------- X rods (shaft)

# the one on the front:
xrod_x_pos = - rod_y_sep/2.0 + h_xendslid_l.slide2holdrod + TOL
xrod_f = fcfun.addCyl_pos ( r= kcit.ROD_R, h = kcit.ROD_X_L, name="rod_x_f",
                      axis = 'x', h_disp = xrod_x_pos)

xrod_f.Placement.Base = FreeCAD.Vector (0, 
                            portabase_pos_y - h_xendslid_l.holdrod_sep/2.0,
                            rod_y_pos_h)

xrod_b = fcfun.addCyl_pos ( r= kcit.ROD_R, h = kcit.ROD_X_L, name="rod_x_f",
                      axis = 'x', h_disp = xrod_x_pos)

xrod_b.Placement.Base = FreeCAD.Vector (0, 
                            portabase_pos_y + h_xendslid_l.holdrod_sep/2.0,
                            rod_y_pos_h)

# ----- bearings of the X axis:

#xbearing_sep = 1.5

#h_lmuu_xfl = comps.LinBearing (r_ext = kcomp.LMEUU_D[kcit.ROD_Di]/2.0,
#                         r_int = kcit.ROD_D/2.0,
#                         h= kcomp.LMEUU_L[kcit.ROD_Di],
#                         name = "lm" + str(kcit.ROD_Di) + "uu" ,
#                         axis = 'x',
#                         #h_disp = -kcomp.LMEUU_L[kcit.ROD_Di]/2,
#                         h_disp = 0,
#                         r_tol  = TOL,
#                         h_tol  = 2.0)

#h_lmuu_xfl.BasePlace ((xbearing_sep/2.0,
#                     portabase_pos_y - h_xendslid_l.holdrod_sep/2.0,
#                     rod_y_pos_h))

#h_lmuu_xfr = comps.LinBearingClone(h_lmuu_xfl, "_xfr", namadd=1)

#h_lmuu_xfr.BasePlace ((-xbearing_sep/2.0 - h_lmuu_xfr.h,
#                     portabase_pos_y - h_xendslid_l.holdrod_sep/2.0,
#                     rod_y_pos_h))

# recompute before coloring:
doc.recompute()
h_xendslid_l.top_slide.ViewObject.ShapeColor = fcfun.BLUE_05
h_xendslid_l.bot_slide.ViewObject.ShapeColor = fcfun.BLUE_05
h_xendslid_r.top_slide.ViewObject.ShapeColor = fcfun.BLUE_05
h_xendslid_r.bot_slide.ViewObject.ShapeColor = fcfun.BLUE_05
h_censlid.top_slide.ViewObject.ShapeColor = fcfun.BLUE_05
h_censlid.bot_slide.ViewObject.ShapeColor = fcfun.BLUE_05



# ----------- T8 Nut and housing for the vertical movement -----------

h_nutT8house = comps.T8NutHousing (name="T8NutHousing", nutaxis='z',
                         screwface_axis ='-x', cx=1, cy = 1, cz=0)
h_nutT8 = comps.T8Nut("nutt8", nutaxis = 'z' )

h_nutT8house.fco.Placement.Base = FreeCAD.Vector(0,
                                                    portabase_pos_y,
                                                    rod_y_pos_h)

h_nutT8.fco.Placement.Base = FreeCAD.Vector(0,
                                           portabase_pos_y,
                                           rod_y_pos_h + h_nutT8house.Length)

doc.recompute()




# otherwise I have problems with Gui.ActiveDocument
"""
doc = FreeCAD.ActiveDocument
guidoc = Gui.getDocument(doc.Label)
"""
guidoc.ActiveView.setAxisCross(True)
"""
Gui.ActiveDocument = Gui.getDocument(doc.Label)
Gui.ActiveDocument.ActiveView.setAxisCross(True)
"""

doc.saveAs (savepath + filename + ".FCStd")













