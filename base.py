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
import kcomp   # import material constants and other constants
import comps   # import my CAD components
import parts   # import my CAD components to print
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

h_xendslid_l = citoparts.EndShaftSlider(slidrod_r = kcit.ROD_R,
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
rod_y_pos_z = sk12_fr.Placement.Base.z + h_sk12_fr.HoleH

rod_y_l = addCyl(r= kcit.ROD_D/2.0, h=kcit.ROD_Y_L, name= "rod_y_l")
rod_y_l.Placement.Base = FreeCAD.Vector (-rod_y_sep/2.0,
                                            alu_x_bm_ypos - rod_y_off,
                                            rod_y_pos_z)
rod_y_l.Placement.Rotation = FreeCAD.Rotation (VX,-90)
                                            
rod_y_r = addCyl(r= kcit.ROD_D/2.0, h=kcit.ROD_Y_L, name= "rod_y_r")
rod_y_r.Placement.Base = FreeCAD.Vector ( rod_y_sep/2.0,
                                            alu_x_bm_ypos - rod_y_off,
                                            rod_y_pos_z)
rod_y_r.Placement.Rotation = FreeCAD.Rotation (VX,-90)
                                            

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

portabase_pos_y = (   kcit.CIT_Y
                    - (1.5 * kcit.ALU_W)
                    - kcit.PORTABASE_L)


# ------------------- X End Slider
# This has been moved up, because the slid2holdrod distance is needed
#h_xendslid_l = citoparts.EndShaftSlider(slidrod_r = kcit.ROD_R,
#                                   holdrod_r = kcit.ROD_R,
#                                   holdrod_sep = kcit.ROD_X_SEP,
#                                   name          = "slider_left",
#                                   holdrod_cen = 1,
#                                   side = 'left')

h_xendslid_l.BasePlace ((-rod_y_sep/2.0, portabase_pos_y, rod_y_pos_z))



h_xendslid_r = citoparts.EndShaftSlider(slidrod_r = kcit.ROD_R,
                                   holdrod_r    = kcit.ROD_R,
                                   holdrod_sep  = kcit.ROD_X_SEP,
                                   name         = "slider_right",
                                   holdrod_cen  = 1,
                                   side = 'right')

h_xendslid_r.BasePlace ((rod_y_sep/2.0, portabase_pos_y, rod_y_pos_z))

# ------------------- Central Slider

print "h_zendslid_r.dent_w " + str(h_xendslid_r.dent_w)
print "h_zendslid_r.dent_w " + str(h_xendslid_r.dent_l)
print "h_zendslid_r.dent_w " + str(h_xendslid_r.dent_sl)

h_censlid = citoparts.CentralSlider (rod_r   = kcit.ROD_R,
                                   rod_sep = kcit.ROD_X_SEP,
                                   name    = "central_slider",
                                   belt_sep = h_xendslid_r.belt_sep,
                                   dent_w  = h_xendslid_r.dent_w,
                                   dent_l  = h_xendslid_r.dent_l,
                                   dent_sl = h_xendslid_r.dent_sl,
                                   dlg_nx = kcomp.SEBWM16,
                                   dlg_x = kcomp.SEBWM16,
                                   dlg_ny = kcomp.SEB15A,
                                   dlg_y = kcomp.SEB15A
                                 )

h_censlid.BasePlace ((0, portabase_pos_y, rod_y_pos_z))


# -------- X rods (shaft)

# the one on the front:
xrod_x_pos = - rod_y_sep/2.0 + h_xendslid_l.slide2holdrod + TOL
xrod_f = fcfun.addCyl_pos ( r= kcit.ROD_R, h = kcit.ROD_X_L, name="rod_x_f",
                      axis = 'x', h_disp = xrod_x_pos)

xrod_f.Placement.Base = FreeCAD.Vector (0, 
                            portabase_pos_y - h_xendslid_l.holdrod_sep/2.0,
                            rod_y_pos_z)

xrod_b = fcfun.addCyl_pos ( r= kcit.ROD_R, h = kcit.ROD_X_L, name="rod_x_f",
                      axis = 'x', h_disp = xrod_x_pos)

xrod_b.Placement.Base = FreeCAD.Vector (0, 
                            portabase_pos_y + h_xendslid_l.holdrod_sep/2.0,
                            rod_y_pos_z)

# ----- bearings of the X axis: (they are made in the central slider)

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
#                     rod_y_pos_z))

#h_lmuu_xfr = comps.LinBearingClone(h_lmuu_xfl, "_xfr", namadd=1)

#h_lmuu_xfr.BasePlace ((-xbearing_sep/2.0 - h_lmuu_xfr.h,
#                     portabase_pos_y - h_xendslid_l.holdrod_sep/2.0,
#                     rod_y_pos_z))

# recompute before coloring:
doc.recompute()
h_xendslid_l.top_slide.ViewObject.ShapeColor = fcfun.BLUE_05
h_xendslid_l.bot_slide.ViewObject.ShapeColor = fcfun.BLUE_05
h_xendslid_r.top_slide.ViewObject.ShapeColor = fcfun.BLUE_05
h_xendslid_r.bot_slide.ViewObject.ShapeColor = fcfun.BLUE_05
h_censlid.top_slide.ViewObject.ShapeColor = fcfun.BLUE_05
h_censlid.bot_slide.ViewObject.ShapeColor = fcfun.BLUE_05

# ----------- Motor coupler for the vertical movement (Z)
# The motor is already with the central slider
# Motor handler:
h_motorz = h_censlid.h_motor

# end of the motor shaft

# rod_y_pos_z:      Position of the slider
# h_motorz.pos.z:   Position of the motor referenced to the slider
# h_motorz.shaft_l: Position of the tip of the shaft, referenced to the motor
# 0.5: Just some tolerance
coupmotz_pos_z = rod_y_pos_z + h_motorz.pos.z + h_motorz.shaft_l + 0.5
# motor shaft diameter
motzsh_d = h_motorz.shaft_d


# larg_neg = 0 => The large diameter (ZLEADS_D==8) is not on the negative side
#                 It's looking upwards
h_coupler = comps.FlexCoupling (ds=motzsh_d, dl=kcit.ZLEADS_D, ctype='rb',
                                name='zflexcoupling', axis ='z', center=1,
                                larg_neg = 0)
                                

h_coupler.fco.Placement.Base = (0, portabase_pos_y, coupmotz_pos_z)


# ----------- T8 Nut and housing for the vertical movement -----------

# T8 Leadscrew
# adding .5 tolerance
t8lead_posz = coupmotz_pos_z + .5
t8lead_pos = FreeCAD.Vector(0,portabase_pos_y, coupmotz_pos_z + .5)
t8lead = fcfun.addCylPos (r= kcit.ZLEADS_D/2., h= kcit.ZLEADS_L,
                          name="t8leadscrew", normal=VZ, pos=t8lead_pos)

h_nutT8house = comps.T8NutHousing (name="T8NutHousing", nutaxis='-z',
                         screwface_axis ='-x', cx=1, cy = 1, cz=0)
h_nutT8 = comps.T8Nut("nutt8", nutaxis = '-z' )


# lower position of the nut (not considering the height of the bolts
# to attach it
nutT8_posz_min = (  coupmotz_pos_z
                  + h_coupler.length/2.
                  # whatever is larger, the shaft out or the head of the bolt
                  # probably the head of the bolt
                  + max(h_nutT8.ShaftOut,
                    kcomp.D912_HEAD_L[h_nutT8.FlangeBoltDmetric]))

t8lead_end_posz = t8lead_posz + kcit.ZLEADS_L

nutT8_posz_max = t8lead_end_posz - (h_nutT8.NutL - h_nutT8.ShaftOut)

# Just to draw it around the middle of the leadscrew
#nutT8_posz = (nutT8_posz_max + nutT8_posz_min )/2.
# At the bottom:
#nutT8_posz =  nutT8_posz_min
# At the top:
nutT8_posz =  nutT8_posz_max

h_nutT8house.fco.Placement.Base = FreeCAD.Vector(0, portabase_pos_y,
                                   nutT8_posz )

h_nutT8.fco.Placement.Base = FreeCAD.Vector(0,
                                           portabase_pos_y,
                                           nutT8_posz)




doc.recompute()

# ----------- Linear Guides for vertical movement -----------

boltend_sep = 8.
boltend_sep15 = 14.

bl_pos = 0.8

lg_nx = comps.LinGuide (136., kcomp.SEBWM16, axis_l = 'z', axis_b='x',
                    boltend_sep = boltend_sep, bl_pos=bl_pos, name='lg_nx')

lg_nx.BasePlace((h_censlid.lg_nx_posx,
                 portabase_pos_y,
                 rod_y_pos_z +  h_censlid.lg_nx_posz - boltend_sep))

lg_y = comps.LinGuide (150., kcomp.SEB15A, axis_l = 'z', axis_b='-y',
                    boltend_sep = boltend_sep15, bl_pos=bl_pos, name='lg_y')
                    #boltend_sep = boltend_sep15, bl_pos=0.8, name='lg_y')

lg_y.BasePlace(( 0,
                 portabase_pos_y + h_censlid.lg_y_posy,
                 rod_y_pos_z +  h_censlid.lg_ny_posz - boltend_sep15))


lg_ny = comps.LinGuide (150., kcomp.SEB15A, axis_l = 'z', axis_b='y',
                    boltend_sep = boltend_sep15, bl_pos=bl_pos, name='lg_ny')
                    #boltend_sep = boltend_sep15, bl_pos=0.8, name='lg_ny')

lg_ny.BasePlace(( 0,
                 portabase_pos_y - h_censlid.lg_y_posy,
                 rod_y_pos_z +  h_censlid.lg_ny_posz - boltend_sep15))

print 'h_censlid.lg_y_posy: ' + str(h_censlid.lg_y_posy)

doc.recompute()


                                            
# --------- Base of the portas and attachment to the leadscrew nut --------
#

#                 H 
#                 H 
#                 H 
#                 H 
# leadscrew(H)    H 
#                 H 
# leadscrew      | |   
#   nut        __| |__  ____ portabase_nut_pos_z
#             |_______|      h_nutT8.FlangeL +  } nutT8_base_h
#                 U     ____ h_nutT8.ShaftOut   }
#                 H    
#  leadscrew(H)   H     
#                _H_        { t8lead_posz (absolute pos)
#  motor        | H | ___ /_{ coupmotz_pos_z (absolute position)
#  coupler      |_:_|
#               __|__  ___ h_motorz.pos.z (relative to rod_y_pos_z)
#              |     |
#              |Motor|  ________ reference: rod_y_pos_z


#       This is the base for the portas
#    _________________________________________________ t8lead_end_posz
# leadscrew      |H|                                 |
#   nut        __|H|__  ___ portabase_nut_posz_max   |
#             |___H___|                              |
#                 U                                  |
#                 H                                  |
#                 H                                  |
#                 H                                  + portabase2nut_h
#                 H                                  |
# leadscrew(H)    H                                  |
#                 H                                  |
# leadscrew      | |                                 |
#   nut        __| |__  ___ portabase_nut_posz_min __|
#             |_______|    
#                _U_   ___  
#  motor        | H |     + h_coupler.length 
#  coupler      |_:_|  ___|
#               __|__  ___ 
#              |     |
#              |Motor|  ________ 



nutT8_base_h = h_nutT8.FlangeL + h_nutT8.ShaftOut



# The position of portabase_posz can be in any position between its 
# minimum and maximum position

portabase_nut_posz_min = nutT8_posz_min +  h_nutT8.FlangeL


portabase2nut_h = t8lead_end_posz - portabase_nut_posz_min
print 'portabase2nut_h : ' + str(portabase2nut_h)

portabase_nut_posz_max =  nutT8_posz_max +  h_nutT8.FlangeL

# this is the stroke
t8lead_stroke = portabase_nut_posz_max - portabase_nut_posz_min
print 'Z stroke : ' + str(t8lead_stroke)


nutT8shank_l = h_nutT8.NutL - nutT8_base_h

# assuming the Linear guides on Y

# The upper position of the block. Measured on the middle of the block
lgybl_posz_c_max = (
                            # position of the bottom hole of the rail
                            rod_y_pos_z +  h_censlid.lg_y_posz
                            # add 2 more holes
                          + 2 * h_censlid.dlg_y['rail']['boltlsep'] 
                            # substract the half of the length of the block
                          - .5 * h_censlid.dlg_y['block']['bl'] )

lgybl_posz_c_min = (
                            # position of the bootm hole of the rail
                            rod_y_pos_z +  h_censlid.lg_y_posz
                            # add the half of the length of the block
                          + .5 * h_censlid.dlg_y['block']['bl'] )

# position of the top end of the rail
lg_posz_top = (  rod_y_pos_z +  h_censlid.lg_y_posz 
                 # add 2 more bolt holes
               + 3 * h_censlid.dlg_y['rail']['boltlsep'] 
                 # add the separation from the last hole to the end
               + boltend_sep15)



# making them relative
portabase_nut_posz = nutT8_posz +  h_nutT8.FlangeL
portabase_nut_posz_min = nutT8_posz_min +  h_nutT8.FlangeL
# calculate relative to one position (min)
lg_posz_top_rel = lg_posz_top  - portabase_nut_posz_min
# make it 15 smaller (+15 because is negative), because the guides are
# longer than the leadscrew
lgybl_posz_c_min_rel = lgybl_posz_c_min - portabase_nut_posz_min +15
#lgybl_posz_c_max_rel = lgybl_posz_c_max - portabase_nut_posz
print 'lg_posz_top_rel: '  + str(lg_posz_top_rel)
print 'lgybl_posz_c_min_rel: '  + str(lgybl_posz_c_min_rel)

h_portabase = citoparts.PortaBase (
                       porta_l = kcit.PORTA_L,
                       porta_w = kcit.PORTA_W,
                       n_porta = kcit.N_PORTA,
                       porta_sep = kcit.PORTA_SEP,
                       portabase_h = kcit.PORTABASE_H,
                       portabase2nut = portabase2nut_h,
                       nutshank_d = h_nutT8.ShaftD,
                       nutshank_l = nutT8shank_l,
                       nutflange_d = h_nutT8.FlangeD,
                       nutbolt_d = h_nutT8.FlangeBoltHoleD,
                       nutbolt_pos = h_nutT8.FlangeBoltPosD/2.,
                       # attachment to the linear guide
                       dlgy = lg_y.dlg,
                       lgy_posy = h_censlid.lg_y_posy,
                       # position relative to the nut
                       lgybl_posz_c_bot = lgybl_posz_c_min_rel,
                       lgy_posz_top = lg_posz_top_rel
                       )

h_portabase.BasePlace((0,portabase_pos_y, portabase_nut_posz))

doc.recompute()

# this is the length of the portabase.
portabase_l = h_portabase.portabase_l

# this is the length of the end slider
endslider_l = h_xendslid_l.length

# the half of its difference will be the amount that the central slider
# (including the portabase) exceeds each end of the endslider.
# That will be the depth dimension of the endstop. That will also have
# one idle pulley
endstop_d = (portabase_l - endslider_l) / 2.

endslider_posz_top = rod_y_pos_z + h_xendslid_l.partheight
endslider_posz_bot = rod_y_pos_z - h_xendslid_l.partheight

h_idlepulleyhold_lowends_nx = parts.IdlePulleyHolder (
                           profile_size =  kcit.ALU_W,
                           pulleybolt_d = kcit.BOLTPUL_D,
                           holdbolt_d = 5,
                           # height above the profile (relative):
                           above_h = endslider_posz_top - kcit.ALU_W,
                           mindepth = endstop_d,
                           endstop_side = 1,
                           # 2mm below to avoid touching with the rod
                           endstop_posh = endslider_posz_bot - kcit.ALU_W -2,
                           name = 'idlpulhold_lowends_nx')


idlepulleyhold_lowends_nx = h_idlepulleyhold_lowends_nx.fco
idlepulleyhold_lowends_nx.Placement.Rotation = FreeCAD.Rotation (VZ, 180)
idlepulleyhold_lowends_nx.Placement.Base = FreeCAD.Vector(
                                     -rod_y_sep/2.0 + h_xendslid_l.pulley_posx,
                                     kcit.CIT_Y - 1.5*kcit.ALU_W,
                                     kcit.ALU_W)

idlepull_h = 8.
pulley_d = 13.


h_idlepulleyhold_highends_x = parts.IdlePulleyHolder (
                         profile_size =  kcit.ALU_W,
                         pulleybolt_d = kcit.BOLTPUL_D,
                         holdbolt_d = 5,
                         # height above the profile (relative):
                         above_h = endslider_posz_top - kcit.ALU_W + idlepull_h,
                         mindepth = endstop_d,
                         endstop_side = -1,
                         # 2mm below to avoid touching with the rod
                         endstop_posh = endslider_posz_bot - kcit.ALU_W -2,
                         name = 'idlpulhold_highends_x')


idlepulleyhold_highends_x = h_idlepulleyhold_highends_x.fco
idlepulleyhold_highends_x.Placement.Rotation = FreeCAD.Rotation (VZ, 180)
idlepulleyhold_highends_x.Placement.Base = FreeCAD.Vector(
                                     rod_y_sep/2.0 - h_xendslid_l.pulley_posx,
                                     kcit.CIT_Y - 1.5*kcit.ALU_W,
                                     kcit.ALU_W)


                                       
h_idlepulleyhold_low_x = parts.IdlePulleyHolder (
                        profile_size =  kcit.ALU_W,
                        pulleybolt_d = kcit.BOLTPUL_D,
                        holdbolt_d = 5,
                        # height above the profile (relative):
                        above_h = endslider_posz_top - kcit.ALU_W,
                        mindepth = 0,
                        endstop_side = 0,
                        # 2mm below to avoid touching with the rod
                        endstop_posh = 0,
                        name = 'idlpulhold_low_x')

idlepulleyhold_low_x = h_idlepulleyhold_low_x.fco
idlepulleyhold_low_x.Placement.Base = FreeCAD.Vector(
                        rod_y_sep/2.0 - h_xendslid_l.pulley_posx + 1.5*pulley_d,
                        kcit.CIT_Y - 0.5 * kcit.ALU_W,
                        kcit.ALU_W)

                                       
h_idlepulleyhold_high_nx = parts.IdlePulleyHolder (
                        profile_size =  kcit.ALU_W,
                        pulleybolt_d = kcit.BOLTPUL_D,
                        holdbolt_d = 5,
                        # height above the profile (relative):
                        above_h = endslider_posz_top - kcit.ALU_W + idlepull_h,
                        mindepth = 0,
                        endstop_side = 0,
                        # 2mm below to avoid touching with the rod
                        endstop_posh = 0,
                        name = 'idlpulhold_high_nx')

idlepulleyhold_high_nx = h_idlepulleyhold_high_nx.fco
idlepulleyhold_high_nx.Placement.Base = FreeCAD.Vector(
                       -rod_y_sep/2.0 + h_xendslid_l.pulley_posx - 1.5*pulley_d,
                        kcit.CIT_Y - 0.5 * kcit.ALU_W,
                        kcit.ALU_W)


 


doc.recompute()
h_idlepulleyhold_lowends_nx.fco.ViewObject.ShapeColor = fcfun.ORANGE
h_idlepulleyhold_highends_x.fco.ViewObject.ShapeColor = fcfun.ORANGE
h_idlepulleyhold_low_x.fco.ViewObject.ShapeColor = fcfun.ORANGE
h_idlepulleyhold_high_nx.fco.ViewObject.ShapeColor = fcfun.ORANGE

# this changes the color, but doesn't show it on the gui
#portahold.ViewObject.ShapeColor = fcfun.RED
"""
guidoc.getObject(portahold.Label).ShapeColor = fcfun.BLACK
guidoc.portahold.ShapeColor = fcfun.RED
guidoc.portahold.ShapeColor = fcfun.RED
"""


guidoc.ActiveView.setAxisCross(True)

doc.saveAs (savepath + filename + ".FCStd")













