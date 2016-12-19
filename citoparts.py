# ----------------------------------------------------------------------------
# -- Parts 3D
# -- comps library
# -- Python scripts to create 3D parts models in FreeCAD
# ----------------------------------------------------------------------------
# -- (c) Felipe Machado
# -- Area of Electronics. Rey Juan Carlos University (urjc.es)
# -- October-2016
# ----------------------------------------------------------------------------
# --- LGPL Licence
# ----------------------------------------------------------------------------

# classes that creates objects to be 3D printed

import FreeCAD;
import Part;
import logging
import os
import Draft;
#import copy;
#import Mesh;

# can be taken away after debugging
# directory this file is
filepath = os.getcwd()
import sys
# to get the components
# In FreeCAD can be added: Preferences->General->Macro->Macro path
sys.path.append(filepath)
# Either one of these 2 to select the path, inside the tree, copied by
# git subtree, or in its one place
#sys.path.append(filepath + '/' + 'modules/comps'
sys.path.append(filepath + '/' + '../comps')


import fcfun
import kcomp    # import material constants and other constants
import comps    # import my CAD components
import beltcl   # import my CAD components
import partgroup  # import my CAD components
import kcit

from fcfun import V0, VX, VY, VZ, V0ROT, addBox, addCyl, fillet_len
from fcfun import VXN, VYN, VZN
from fcfun import addBolt, addBoltNut_hole, NutHole
from kcomp import TOL


logging.basicConfig(level=logging.DEBUG)
                    #format='%(%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------- class EndShaftSlider ----------------------------------------
# Creates the slider that goes on a rod and supports the end of another
# rod. The slider runs on 2 linear bearings
# The slider is referenced on the slider axis
# Creates both sides, the upper part and the lower part, it also creates the
# linear bearings

#     slidrod_r : radius of the rod where the slider runs on
#     holdrod_r : radius of the rod that this slider holds
#     holdrod_sep : separation between the rods that are holded
#     holdrod_cen : 1: if the piece is centered on the perpendicular 
#     side        : 'left' or 'right' (slidding on axis Y)
#                 : 'bottom' or 'top' (slidding on axis X)
#
#          Y      axis= 'y'    side='left'
#          |
#          |                                  
#          |
#          |
#      ____|_________
#     |  |   |   ____|
#     |  |   |  |____|
#     |  |   |       |
#     |  |   |       |
#     |  |   |       |---------------- X: holdrod_cen = 1
#     |  |   |       |
#     |  |   |   ____|
#     |  |   |  |____|
#     |__|___|_______|________________ X: holdrod_cen = 0
#
#
#
#      ____|_________ __________________________________________ length
#     |  |   |   ____|
#     |  |   |  |____| ----------------------- holdrod_sep
#     |  |   |       |
#     |  |   |       |                        |
#     |  |   |       |
#     |  |   |       |                        |
#     |  |   |   ____|
#     |  |   |  |____|----- holdrod2end --------
#     |__|___|_______|__________________________________________ 
#
#          |    |
#          |----|----> slide2holdrod (+)
#


# --- Atributes:
# length : length of the slider, on the direction of the slidding axis
# width  : width of the slider, on the direction perpendicular to the slidding
#          axis. On the direction of the holding axis
# partheight : heigth of each part of the slider. So the total height will be
#              twice this height
# holdrod_sep : separation between the 2 rods that are holded and forms the 
#               perpendicular axis movement
# slide2holdrod : distance from the sliding rod (axis) to
#                 the beginning of the hold rod (axis). Positive
# slide2holdrod_sign : distance from the sliding rod (axis) to
#                 the beginning of the hold rod (axis). Positive
#                 or negative depending on the sign
# dent_w  : width of the dent, if no dent is needed, just dent_w = 0
# dent_l  : length of the dent, 
# dent_sl : small dimension of the dent length
# ovdent_w  : width of the dent, including the overlap to make the union
# ovdent_l  : length of the dent, including the overlap to make the union 
# idlepull_axsep : separation between the axis iddle pulleys
# pulley_posx: relative position X of the idle pulleys
# belt_sep : separation between the inner part of the iddle pulleys
#                   that is where the belts are. So it is
#                   idlepull_axsep - 2* radius of the bearing
# idlepulls : FreeCad object of the idle pulleys
# bearings : FreeCad object of the bearings
# top_slide : FreeCad object of the top part of the slider
# bot_slide : FreeCad object of the bottm part of the slider
# base_place: position of the 3 elements: All of them have the same base
#             position.
#             It is (0,0,0) when initialized, it has to be changed using the
#             function Base_Place

class EndShaftSlider (object):

    # Separation from the end of the linear bearing to the end of the piece
    # on the Heigth dimension (Z)
    OUT_SEP_H = 3.0

    # Minimum separation between the bearings, on the slide direction
    MIN_BEAR_SEP = 3.0

    # Ratio between the length of the rod (shaft) that is inserted in the slider
    # and the diameter of the holded shaft
    HOLDROD_INS_RATIO = 2.0

    # Radius to fillet the sides
    FILLT_R = 2.0

    # Space for the sliding rod, to be added to its radius, and to be cut
    SLIDEROD_SPACE = 1.5

    # tolerance on their length for the bearings. Larger because the holes
    # usually are too tight and it doesn't matter how large is the hole
    #TOL_BEARING_L = 2.0 # printed in black and was too loose
    TOL_BEARING_L = 1.0 # reduced

    MTOL = TOL - 0.1 # reducing the tolrances, it was too tolerant :)
    MLTOL = TOL - 0.05 # reducing the tolrances, it was too tolerant :)

    # Bolts to hold the top and bottom parts:
    BOLT_D = 4
    BOLT_HEAD_R = kcomp.D912_HEAD_D[BOLT_D] / 2.0
    BOLT_HEAD_L = kcomp.D912_HEAD_L[BOLT_D] + MTOL
    BOLT_HEAD_R_TOL = BOLT_HEAD_R + MTOL/2.0 
    BOLT_SHANK_R_TOL = BOLT_D / 2.0 + MTOL/2.0
    BOLT_NUT_R = kcomp.NUT_D934_D[BOLT_D] / 2.0
    BOLT_NUT_L = kcomp.NUT_D934_L[BOLT_D] + MTOL
    #  1.5 TOL because diameter values are minimum, so they may be larger
    BOLT_NUT_R_TOL = BOLT_NUT_R + 1.5*MTOL

    # Bolts for the pulleys
    BOLTPUL_D = kcit.BOLTPUL_D
    BOLTPUL_SHANK_R_TOL = BOLTPUL_D / 2.0 + MTOL/2.0
    BOLTPUL_NUT_R = kcomp.NUT_D934_D[BOLTPUL_D] / 2.0
    BOLTPUL_NUT_L = kcomp.NUT_D934_L[BOLTPUL_D] + MTOL
    #  1.5 TOL because diameter values are minimum, so they may be larger
    BOLTPUL_NUT_R_TOL = BOLTPUL_NUT_R + 1.5*MTOL

    def __init__ (self, slidrod_r, holdrod_r, holdrod_sep, 
                  name, holdrod_cen = 1, side = 'left'):

        doc = FreeCAD.ActiveDocument
        self.base_place = (0,0,0)
        self.slidrod_r = slidrod_r
        self.holdrod_r = holdrod_r
        self.holdrod_sep = holdrod_sep
        self.holdrod_cen = holdrod_cen
    
        self.name        = name
        #self.axis        = axis

        # Separation from the end of the linear bearing to the end of the piece
        # on the width dimension (perpendicular to the movement)
        if self.BOLT_D == 3:
            self.OUT_SEP_W = 8.0
            # on the length dimension (parallel to the movement)
            self.OUT_SEP_L = 10.0
        elif self.BOLT_D == 4:
            self.OUT_SEP_W = 10.0
            self.OUT_SEP_L = 14.0
        else:
            print "not defined"

        bearing_l     = kcomp.LMEUU_L[int(2*slidrod_r)] 
        bearing_l_tol = bearing_l + self.TOL_BEARING_L
        bearing_d     = kcomp.LMEUU_D[int(2*slidrod_r)]
        bearing_d_tol = bearing_d + 2.0 * self.MLTOL
        bearing_r     = bearing_d / 2.0
        bearing_r_tol = bearing_r + self.MLTOL

        holdrod_r_tol =  holdrod_r + self.MLTOL/2.0

        holdrod_insert = self.HOLDROD_INS_RATIO * (2*slidrod_r) 

        self.slide2holdrod = bearing_r + self.MIN_BEAR_SEP 
        if side == 'right' or side == 'top':
            # the distance will be negative, either on the X axis (right)
            # or on the Y axis (top)
            self.slide2holdrod_sign = - self.slide2holdrod
        else:
            self.slide2holdrod_sign = self.slide2holdrod
    
        # calculation of the width
        # dimensions should not depend on tolerances
        self.width = (  bearing_d     #bearing_d_tol
                      + self.OUT_SEP_W
                      + holdrod_insert
                      + self.MIN_BEAR_SEP )


        # calculation of the length
        # it can be determined by the holdrod_sep (separation of the hold rods)
        # or by the dimensions of the linear bearings. It will be the largest
        # of these two: 
        # tlen: total length ..
        tlen_holdrod = holdrod_sep + 2 * self.OUT_SEP_L + 2 * holdrod_r
        #tlen_holdrod = holdrod_sep + 2 * self.OUT_SEP_L + 2 * holdrod_r_tol
        #tlen_bearing = (  2 * bearing_l_tol
        tlen_bearing = (  2 * bearing_l
                        + 2* self.OUT_SEP_L
                        + self.MIN_BEAR_SEP)
        if tlen_holdrod > tlen_bearing:
            self.length = tlen_holdrod
            print "length comes from holdrod"
        else:
            self.length = tlen_bearing
            print "length comes from bearing: Check for errors"
       

        self.partheight = (  bearing_r
                           + self.OUT_SEP_H)

        
        # distance from the center of the hold rod to the end on the sliding
        # direction
        self.holdrod2end = (self.length - holdrod_sep)/2

#        if axis == 'x':
#            slid_x = self.length
#            slid_y = self.width
#            slid_z = self.partheight
#        else: # 'y': default
        slid_x = self.width
        slid_y = self.length
        slid_z = self.partheight

        if holdrod_cen == 1:
            # offset if it is centered on the y
            y_offs = - slid_y/2.0
        else:
            y_offs = 0


        slid_posx = - (bearing_r + self.OUT_SEP_W)


        bearing0_pos_y = self.OUT_SEP_L
        # Not bearing_l_tol, because the tol will be added on top and bottom
        # automatically
        bearing1_pos_y = self.length - (self.OUT_SEP_L + bearing_l)
         
        # adding the offset
        bearing0_pos_y = bearing0_pos_y + y_offs
        bearing1_pos_y = bearing1_pos_y + y_offs


        topslid_box = addBox(slid_x, slid_y, slid_z, "topsideslid_box")
        topslid_box.Placement.Base = FreeCAD.Vector(slid_posx, y_offs, 0)

        botslid_box = addBox(slid_x, slid_y, slid_z, "bosidetslid_box")
        botslid_box.Placement.Base = FreeCAD.Vector(slid_posx, y_offs,
                                                    -slid_z)

        topslid_fllt = fillet_len (topslid_box, slid_z, 
                                  self.FILLT_R, "topsideslid_fllt")
        botslid_fllt = fillet_len (botslid_box, slid_z,
                                  self.FILLT_R, "botsideslid_fllt")

        # list of elements that cut:
        cutlist = []

        sliderod = fcfun.addCyl_pos (r = slidrod_r + self.SLIDEROD_SPACE,
                               h = slid_y +2,
                               name = "sliderod",
                               axis = 'y',
                               h_disp = y_offs - 1)

        cutlist.append (sliderod)

        h_lmuu_0 = comps.LinBearing (
                         r_ext = bearing_r,
                         r_int = slidrod_r,
                         h     = bearing_l,
                         name  = "lm" + str(int(2*slidrod_r)) + "uu_0",
                         axis  = 'y',
                         h_disp = bearing0_pos_y,
                         r_tol  = self.MLTOL,
                         h_tol  = self.TOL_BEARING_L)

        cutlist.append (h_lmuu_0.bearing_cont)

        h_lmuu_1 = comps.LinBearingClone (
                                      h_lmuu_0,
                                      "lm" + str(int(2*slidrod_r)) + "uu_1",
                                      namadd = 0)
        h_lmuu_1.BasePlace ((0, bearing1_pos_y - bearing0_pos_y, 0))
        cutlist.append (h_lmuu_1.bearing_cont)


        # ------------ hold rods ----------------

        holdrod_0 = fcfun.addCyl_pos (
                                r = holdrod_r_tol,
                                h = holdrod_insert + 1,
                                name = "holdrod_0",
                                axis = 'x',
                                h_disp = bearing_r + self.MIN_BEAR_SEP )
                                #h_disp = bearing_r_tol + self.MIN_BEAR_SEP )

        holdrod_0.Placement.Base = FreeCAD.Vector(
                                     0,
                                     self.holdrod2end + y_offs,
                                     0)
        cutlist.append (holdrod_0)

        holdrod_1 = fcfun.addCyl_pos (
                                r = holdrod_r_tol,
                                h = holdrod_insert + 1,
                                name = "holdrod_1",
                                axis = 'x',
                                h_disp = bearing_r + self.MIN_BEAR_SEP )
                                #h_disp = bearing_r_tol + self.MIN_BEAR_SEP )

        holdrod_1.Placement.Base = FreeCAD.Vector(
                                       0,
                                       self.length - self.holdrod2end + y_offs,
                                       0)
        cutlist.append (holdrod_1)

        # -------------------- bolts and nuts
        bolt0 = addBoltNut_hole (
                            r_shank   = self.BOLT_SHANK_R_TOL,
                            l_bolt    = 2 * slid_z,
                            r_head    = self.BOLT_HEAD_R_TOL,
                            l_head    = self.BOLT_HEAD_L,
                            r_nut     = self.BOLT_NUT_R_TOL,
                            l_nut     = self.BOLT_NUT_L,
                            hex_head  = 0, extra=1,
                            supp_head = 1, supp_nut=1,
                            headdown  = 0, name="bolt_hole")

        #bolt_left_pos_x =  -(  bearing_r_tol
        bolt_left_pos_x =  -(  bearing_r
                             + self.OUT_SEP_W
                             + sliderod.Base.Radius.Value) / 2.0

        #bolt_right_pos_x =   (  bearing_r_tol
        bolt_right_pos_x =   (  bearing_r
                              + self.MIN_BEAR_SEP
                              + 0.6 * holdrod_insert )

        bolt_low_pos_y =  self.OUT_SEP_L / 2.0 + y_offs
        bolt_high_pos_y =  self.length - self.OUT_SEP_L / 2.0 + y_offs

        bolt_lowmid_pos_y =  1.5 * self.OUT_SEP_L + 2 * holdrod_r + y_offs
        bolt_highmid_pos_y = (  self.length
                             - 1.5 * self.OUT_SEP_L
                             - 2 * holdrod_r  # no _tol
                             + y_offs)

        bolt_pull_pos_x =   (  bearing_r_tol
                              + self.MIN_BEAR_SEP
                              + 0.25 * holdrod_insert )

        self.pulley_posx = bolt_pull_pos_x

        #bolt_pullow_pos_y =  2.5 * self.OUT_SEP_L + 2 * holdrod_r_tol + y_offs
        bolt_pullow_pos_y =  2.5 * self.OUT_SEP_L + 2 * holdrod_r + y_offs
        bolt_pulhigh_pos_y = (  self.length
                             - 2.5 * self.OUT_SEP_L
                             - 2 * holdrod_r  # no _tol
                             + y_offs)

        bolt0.Placement.Base = FreeCAD.Vector (bolt_left_pos_x,
                                               self.length/2 + y_offs,
                                               -slid_z)
        bolt0.Placement.Rotation = FreeCAD.Rotation (VZ, 90)
        cutlist.append (bolt0)

# Naming convention for the bolts
#      ______________ 
#     |lu|   |   _ru_|       right up
#     |  |   |  |____|
#     |  |   |    rmu|       right middle up
#     |  |   | pu    |  pulley up
#     |0 |   | r     | right
#     |  |   | pd    |  pulley down
#     |  |   |   _rmd|       right middle down
#     |  |   |  |____|
#     |ld|___|____rd_|       right down
#       
        # Right
        boltr = Draft.clone(bolt0)
        boltr.Label = "bolt_hole_r"
        boltr.Placement.Base =  FreeCAD.Vector (-bolt_left_pos_x,
                                                self.length/2 + y_offs,
                                               -slid_z)
        boltr.Placement.Rotation = FreeCAD.Rotation (VZ, 30)
        cutlist.append (boltr)


        # Left Up
        boltlu = Draft.clone(bolt0)
        boltlu.Label = "bolt_hole_lu"
        boltlu.Placement.Base =  FreeCAD.Vector (bolt_left_pos_x,
                                                bolt_low_pos_y,
                                               -slid_z)
        boltlu.Placement.Rotation = FreeCAD.Rotation (VZ, 0)
        cutlist.append (boltlu)
        
        # Left Down
        boltld = Draft.clone(bolt0)
        boltld.Label = "bolt_hole_ld"
        boltld.Placement.Base =  FreeCAD.Vector (bolt_left_pos_x,
                                                bolt_high_pos_y,
                                               -slid_z)
        boltld.Placement.Rotation = FreeCAD.Rotation (VZ, 0)
        cutlist.append (boltld)

        # Right Up 
        boltru = Draft.clone(bolt0)
        boltru.Label = "bolt_hole_ru"
        boltru.Placement.Base =  FreeCAD.Vector (bolt_right_pos_x,
                                                bolt_high_pos_y,
                                               -slid_z)
        boltru.Placement.Rotation = FreeCAD.Rotation (VZ, 0)
        cutlist.append (boltru)

        # Right Down
        boltrd = Draft.clone(bolt0)
        boltrd.Label = "bolt_hole_rd"
        boltrd.Placement.Base =  FreeCAD.Vector (bolt_right_pos_x,
                                                bolt_low_pos_y,
                                               -slid_z)
        boltrd.Placement.Rotation = FreeCAD.Rotation (VZ, 0)
        cutlist.append (boltrd)

        # Right Middle Up 
        boltrmu = Draft.clone(bolt0)
        boltrmu.Label = "bolt_hole_rmu"
        boltrmu.Placement.Base =  FreeCAD.Vector (bolt_right_pos_x,
                                                  bolt_highmid_pos_y,
                                                 -slid_z)
        boltrmu.Placement.Rotation = FreeCAD.Rotation (VZ, 0)
        cutlist.append (boltrmu)

        # Right Middle Down
        boltrmd = Draft.clone(bolt0)
        boltrmd.Label = "bolt_hole_rmd"
        boltrmd.Placement.Base =  FreeCAD.Vector (bolt_right_pos_x,
                                                bolt_lowmid_pos_y,
                                               -slid_z)
        boltrmd.Placement.Rotation = FreeCAD.Rotation (VZ, 0)
        cutlist.append (boltrmd)

        # Hole for the upper Pulley bolt       
        boltpull0 = addBolt (
                            r_shank   = self.BOLTPUL_SHANK_R_TOL,
                            l_bolt    = 2 * slid_z,
                            r_head    = self.BOLTPUL_NUT_R_TOL,
                            l_head    = self.BOLTPUL_NUT_L,
                            hex_head  = 1, extra=1,
                            support = 1, 
                            headdown  = 1, name="boltpul_hole")

        boltpull0.Placement.Base =  FreeCAD.Vector (bolt_pull_pos_x,
                                                    bolt_pulhigh_pos_y,
                                                   -slid_z)
        boltpull0.Placement.Rotation = FreeCAD.Rotation (VZ, 30)
        cutlist.append (boltpull0)

        # idlepull_name_list is a list of the components for building
        # an idle pulley out of washers and bearings
        h_idlepull0 = partgroup.BearWashGroup (
                                   holcyl_list = kcomp.idlepull_name_list,
                                   name = 'idlepull_0',
                                   normal = VZ,
                                   pos = boltpull0.Placement.Base + 
                                         FreeCAD.Vector(0,0,2*slid_z))
        idlepull0 = h_idlepull0.fco

        # separation between the axis iddle pulleys
        self.idlepull_axsep = bolt_pulhigh_pos_y - bolt_pullow_pos_y
        # separation between the inner part of the iddle pulleys
        # ie: idlepull_axsep - the diameter of the pulley (bearing)
        # -1 is because the belt is 1.38mm thick. So in each side we can
        # substract 0.5 mm
        self.belt_sep = self.idlepull_axsep - h_idlepull0.d_maxbear - 1

        # Hole for Pulley Down
        boltpull1 = Draft.clone(boltpull0)
        boltpull1.Label = "boltpul_hole_1"
        boltpull1.Placement.Base =  FreeCAD.Vector (bolt_pull_pos_x,
                                                    bolt_pullow_pos_y,
                                                   -slid_z)
        boltpull1.Placement.Rotation = FreeCAD.Rotation (VZ, 30)
        cutlist.append (boltpull1)

        # the other pulley:
        idlepull1 = Draft.clone(idlepull0)
        idlepull1.Label = "idlepull_1"
        idlepull1.Placement.Base.y = bolt_pullow_pos_y - bolt_pulhigh_pos_y

        idlepull_list = [ idlepull0, idlepull1]
        idlepulls = doc.addObject("Part::Compound", "idlepulls")
        idlepulls.Links = idlepull_list

        # --- make a dent in the interior to save plastic
        # points: p dent

        pdent_ur = FreeCAD.Vector ( self.width + slid_posx + 1,
                                    bolt_highmid_pos_y - 1,
                                   -slid_z - 1)
        pdent_ul = FreeCAD.Vector ( bolt_pull_pos_x + 1,
                                    bolt_pulhigh_pos_y - self.OUT_SEP_L ,
                                   -slid_z - 1)
        pdent_dr = FreeCAD.Vector ( self.width + slid_posx + 1,
                                    bolt_lowmid_pos_y +1,
                                   -slid_z - 1)
        pdent_dl = FreeCAD.Vector ( bolt_pull_pos_x + 1,
                                    bolt_pullow_pos_y + self.OUT_SEP_L ,
                                   -slid_z - 1)

        # dent dimensions
        # the length is actually shorter, because it is 1 mm inside.
        #         
        #        ur  ____ ovdent_l
        #         /|                 h_over= (1/ovdent_w)*(ovdent_l-dent_sl)/2.
        #        /_| ___ dent_l      h_over= triang_h_ov / ovdent_w
        #       /| |    
        #      / | |          dent_l = ovdent_l -2*lm
        #     /  | |          
        # ul /___|_| __ dent_sl
        #    |     |
        #    |     |
        #    |     |
        # dl |_____| __
        #    \   | |
        #     \  | |
        #      \ | |
        #       \|_| ___
        #        \ |
        #         \| ____
        #          dr
        #         1
        #    |---|  dent_w
        #    |-----| ovdent_w 
        #
        # the dimensions of the dent overlaped (ov), to make the shape
        self.ovdent_w = abs(pdent_ur.x - pdent_ul.x) # longer width
        self.dent_w   = self.ovdent_w - 1
        self.ovdent_l = abs(pdent_ur.y - pdent_dr.y) # longer  Length 
        self.dent_sl  = abs(pdent_ul.y - pdent_dl.y) # shorter Length 
        # the height of the overlap triangle
        triang_h_ov = abs(pdent_ur.y - pdent_ul.y)
        self.dent_l = ( self.ovdent_l 
                       - 2*(triang_h_ov / self.ovdent_w)) # h_over

        pdent_list = [ pdent_ur, pdent_ul, pdent_dl, pdent_dr]

        dent_plane = doc.addObject("Part::Polygon", "dent_plane")
        dent_plane.Nodes = pdent_list
        dent_plane.Close = True
        dent_plane.ViewObject.Visibility = False
        dent = doc.addObject("Part::Extrusion", "dent")
        dent.Base = dent_plane
        dent.Dir = (0,0, 2*slid_z +2)
        dent.Solid = True
        cutlist.append (dent)

        holes = doc.addObject("Part::MultiFuse", "holes")
        holes.Shapes = cutlist


        if side == 'right':
            holes.Placement.Rotation = FreeCAD.Rotation (VZ, 180)
            idlepulls.Placement.Rotation = FreeCAD.Rotation (VZ, 180)
            topslid_fllt.Placement.Rotation = FreeCAD.Rotation (VZ, 180)
            botslid_fllt.Placement.Rotation = FreeCAD.Rotation (VZ, 180)
            # h_lmuu_0.bearing. bearings stay the same
            if holdrod_cen == False:
                holes.Placement.Base = FreeCAD.Vector (0, self.length,0)
                idlepulls.Placement.Base = FreeCAD.Vector (0, self.length,0)
                topslid_fllt.Placement.Base = FreeCAD.Vector (0, self.length,0)
                botslid_fllt.Placement.Base = FreeCAD.Vector (0, self.length,0)
        elif side == 'bottom':
            holes.Placement.Rotation = FreeCAD.Rotation (VZ, 90)
            idlepulls.Placement.Rotation = FreeCAD.Rotation (VZ, 90)
            topslid_fllt.Placement.Rotation = FreeCAD.Rotation (VZ, 90)
            botslid_fllt.Placement.Rotation = FreeCAD.Rotation (VZ, 90)
            h_lmuu_0.bearing.Placement.Rotation =  FreeCAD.Rotation (VZ, 90)
            # lmuu_1 has relative position to lmuu_0, so if rotating it
            # to the other side and reseting its position will put it in its
            # place
            if holdrod_cen == True:
                h_lmuu_1.bearing.Placement.Rotation = FreeCAD.Rotation (VZ, -90)
                h_lmuu_1.bearing.Placement.Base = FreeCAD.Vector (0,0,0)
            if holdrod_cen == False:
                holes.Placement.Base = FreeCAD.Vector (self.length,0,0)
                idlepulls.Placement.Base = FreeCAD.Vector (self.length,0,0)
                topslid_fllt.Placement.Base = FreeCAD.Vector (self.length,0,0)
                botslid_fllt.Placement.Base = FreeCAD.Vector (self.length,0,0)
                h_lmuu_0.bearing.Placement.Base = FreeCAD.Vector (
                                                          self.length,0,0)
                h_lmuu_1.bearing.Placement.Base = FreeCAD.Vector (
                           self.length - h_lmuu_1.bearing.Placement.Base.y ,0,0)
                h_lmuu_1.bearing.Placement.Rotation =  FreeCAD.Rotation (VZ, 90)
        elif side == 'top':
            holes.Placement.Rotation = FreeCAD.Rotation (VZ, -90)
            idlepulls.Placement.Rotation = FreeCAD.Rotation (VZ, -90)
            topslid_fllt.Placement.Rotation = FreeCAD.Rotation (VZ, -90)
            botslid_fllt.Placement.Rotation = FreeCAD.Rotation (VZ, -90)
            h_lmuu_0.bearing.Placement.Rotation =  FreeCAD.Rotation (VZ, -90)
            # lmuu_1 has relative position to lmuu_0, so if rotating it
            # to the other side and reseting its position will put it in its
            # place
            if holdrod_cen == True:
                h_lmuu_1.bearing.Placement.Rotation =  FreeCAD.Rotation (VZ, 90)
                h_lmuu_1.bearing.Placement.Base = FreeCAD.Vector (0,0,0)
            if holdrod_cen == False:
                #holes.Placement.Base = FreeCAD.Vector (self.length,0,0)
                #topslid_fllt.Placement.Base = FreeCAD.Vector (self.length,0,0)
                #botslid_fllt.Placement.Base = FreeCAD.Vector (self.length,0,0)
                #h_lmuu_0.bearing.Placement.Base = FreeCAD.Vector (
                                                          #self.length,0,0)
                h_lmuu_1.bearing.Placement.Base = FreeCAD.Vector (
                                         h_lmuu_1.bearing.Placement.Base.y ,0,0)
                h_lmuu_1.bearing.Placement.Rotation = FreeCAD.Rotation (VZ, -90)


        # elif side == 'left':
            # don't do anything, default condition

        self.idlepulls = idlepulls

        bearings = doc.addObject("Part::Fuse", name + "_bear")
        bearings.Base = h_lmuu_0.bearing
        bearings.Tool = h_lmuu_1.bearing
        self.bearings = bearings

        top_slide = doc.addObject("Part::Cut", name + "_top")
        top_slide.Base = topslid_fllt 
        top_slide.Tool = holes 
        self.top_slide = top_slide

        bot_slide = doc.addObject("Part::Cut", name + "_bot")
        bot_slide.Base = botslid_fllt 
        bot_slide.Tool = holes 
        self.bot_slide = bot_slide

    # ---- end of __init__  EndShaftSlider

    # move both sliders (top & bottom) and the bearings
    def BasePlace (self, position = (0,0,0)):
        self.base_place = position
        self.idlepulls.Placement.Base = FreeCAD.Vector(position)
        self.bearings.Placement.Base = FreeCAD.Vector(position)
        self.top_slide.Placement.Base = FreeCAD.Vector(position)
        self.bot_slide.Placement.Base = FreeCAD.Vector(position)
        


"""

    # Move the bearing and its container
    def BasePlace (self, position = (0,0,0)):
        self.base_place = position
        self.bearing.Placement.Base = FreeCAD.Vector(position)
        self.bearing_cont.Placement.Base = FreeCAD.Vector(position)
"""


# ---------- class CentralSlider ----------------------------------------
# Creates the central slider that moves on the X axis
# The slider runs on 1 or 2 pairs of linear bearings.
# The slider is referenced on its center
# Creates both sides, the upper part and the lower part, it also creates the
# linear bearings
# Arguments:
#     rod_r   : radius of the rods where the slider runs on
#     rod_sep : separation between the rods 
#     belt_sep: separation between the belt
#     dent_w  : width of the dent, if no dent is needed, just dent_w = 0
#     dent_l  : length of the dent, 
#     dent_sl : small dimension of the dent length
#     motortype : the Nema motor used: 17, 14, ..
#     dlg_y    : dictionary of the linear guide on the positive Y end. 0 if none
#     dlg_ny   : dictionary of the linear guide on the negative Y end. 0 if none
#     dlg_x    : dictionary of the linear guide on the positive X end. 0 if none
#     dlg_nx   : dictionary of the linear guide on the negative X end. 0 if none
#     
#
#           Y   
#           |
#      _____|_____     ______________________           
#     |  _______  |
#     |_|       |_| -------------
#     |_         _|
#     | |_______| |
#     |           | ---------
#     |           |
#     |           |----X
#     |           |
#     |  _______  | --------- belt_sep
#     |_|       |_|
#     |_         _|
#     | |_______| | ------------- rod_sep
#     |___________|__________________________ length
#
#     |__ width __|

#               Y   
#               |
#          _____|_____     ______________________           
#         |  _______  |
#         |_|       |_| -------------
#         |_         _|
#         | |_______| |  __________________
#        /             \
#       /               \   __________
#      |                 |
#      |                 |
#      |                 |  __________ dent_sl
#       \               /
#        \   _______   /___________________ dent_l
#         |_|       |_|
#         |_         _|
#         | |_______| | ------------- rod_sep
#         |___________|__________________________ length
#      |--|dent_w

      #
        #          ___ ovdent_l
        #        /|\
        #       /_|_\   __ dent_l
        #      /| | |\
        #     / | | | \           dent_l = (dent_w/ovdent_w)*ovdent_l
        #    /  | | |  \
        #   /___|_|_|___\
        #          1

# --- Atributes:
# length : length of the slider, direction perpendicular to the slidding axis.
#          on Y direction
# width  : width of the slider, on the direction of the slidding
#          axis (X) 
# partheight : heigth of each part of the slider. So the total height will be
#              twice this height
# rod_sep : separation between the 2 rods that are holded and forms the 
#               perpendicular axis movement
# belt_sep: separation between the belt
# dent_w  : width of the dent, if no dent is needed, just dent_w = 0
# dent_l  : length of the dent, 
# dent_sl : small dimension of the dent length
# dent_sl : small dimension of the dent length
# ovdent_w  : width of the dent including 1 mm of overlap
# ovdent_l  : length of the dent including the overlap 

# totwidth: the width including the dent
# h_motor: the motor used, the object comps.NemaMotor
# parts : list of FreeCad objects that the slider contains
# idlepulls : FreeCad object of the idle pulleys
# bearings : FreeCad object of the bearings
# top_slide : FreeCad object of the top part of the slider
# bot_slide : FreeCad object of the bottm part of the slider
# base_place: position of the 3 elements: All of them have the same base
#             position.
#             It is (0,0,0) when initialized, it has to be changed using the
#             function BasePlace

# if posx or posy are zero, there is no linear guide on that end:
# lg_nx_posx: end of the linear guide support, where the linear guide
#             is going to be attached
# lg_nx_posz: z of the bottom bolt of the linear guide
# lg_x_posx: end of the linear guide support
# lg_x_posz: z of the bottom bolt of the linear guide
# lg_ny_posy: end of the linear guide support
# lg_ny_posz: z of the bottom bolt of the linear guide
# lg_y_posy: end of the linear guide support
# lg_y_posz: z of the bottom bolt of the linear guide

class CentralSlider (object):

    # Separation from the end of the linear bearing to the end of the piece
    # on the Heigth dimension (Z)
    OUT_SEP_H = 2.0  # smaller to test 3.0

    # Minimum separation between the bearings, on the slide direction
    MIN_BEAR_SEP = 2.0  # smaller to test 3.0

    # Radius to fillet the sides
    FILLT_R = 3.0 # larger to 2.0

    # Space for the sliding rod, to be added to its radius, and to be cut
    ROD_SPACE = 1.5

    # tolerance on their length for the bearings. Larger because the holes
    # usually are too tight and it doesn't matter how large is the hole
    #TOL_BEARING_L = 2.0 # printed in black and was too loose
    TOL_BEARING_L = 1.0 # reduced, good

    MTOL = TOL - 0.1 # reducing the tolrances, it was too tolerant :)
    MLTOL = TOL - 0.05 # reducing the tolrances, it was too tolerant :)

    # Bolts to hold the top and bottom parts:
    BOLT_D = 4
    BOLT_HEAD_R = kcomp.D912_HEAD_D[BOLT_D] / 2.0
    BOLT_HEAD_L = kcomp.D912_HEAD_L[BOLT_D] + MTOL
    BOLT_HEAD_R_TOL = BOLT_HEAD_R + MTOL/2.0 
    BOLT_SHANK_R_TOL = BOLT_D / 2.0 + MTOL/2.0
    BOLT_NUT_R = kcomp.NUT_D934_D[BOLT_D] / 2.0
    BOLT_NUT_L = kcomp.NUT_D934_L[BOLT_D] + MTOL
    #  1.5 TOL because diameter values are minimum, so they may be larger
    BOLT_NUT_R_TOL = BOLT_NUT_R + 1.5*MTOL

    def __init__ (self, rod_r, rod_sep, name, belt_sep,
                  dent_w, dent_l, dent_sl, motortype=17,
                  dlg_y=0, dlg_ny=0, dlg_x=0, dlg_nx=0):

        doc = FreeCAD.ActiveDocument
        self.base_place = (0,0,0)
        self.rod_r      = rod_r
        self.rod_sep    = rod_sep
        self.name       = name
        self.belt_sep   = belt_sep
        self.dent_w     = dent_w
        self.motortype  = motortype
        self.dlg_y       = dlg_y
        self.dlg_ny      = dlg_ny
        self.dlg_x       = dlg_x
        self.dlg_nx      = dlg_nx
        if dent_w == 0:
            self.dent_l     = 0
            self.dent_sl    = 0
            self.ovdent_w   = 0
            self.ovdent_l   = 0
        else:
            self.dent_l     = dent_l
            self.dent_sl    = dent_sl
            self.ovdent_w   = dent_w + 1
            ovdent_w        = self.ovdent_w

        bearing_l     = kcomp.LMEUU_L[int(2*rod_r)] 
        bearing_l_tol = bearing_l + self.TOL_BEARING_L
        bearing_d     = kcomp.LMEUU_D[int(2*rod_r)]
        bearing_d_tol = bearing_d + 2.0 * self.MLTOL
        bearing_r     = bearing_d / 2.0
        bearing_r_tol = bearing_r + self.MLTOL
        #
        #    |  _____  |
        #    |_|     |_|
        #    |_       _|
        #    | |_____| | ___
        #    |_________| ___ OUT_SEP_MOVPP: separation perpendicular to movement
        #      
        #    | |-----| bearing_l (+ MLTOL)
        #    |-| OUT_SEP_MOV : separacion on the direction of the movement
        #    |---------| length
        #   
        # separation from the end of the linear bearing to the end
        self.SEP = 3.
        #self.OUT_SEP_MOV = 4.0
        #if self.BOLT_D == 3:
        #    self.OUT_SEP_MOVPP = 10.0
        #elif self.BOLT_D == 4:
        #    self.OUT_SEP_MOVPP = 10.0
        #else:
        #    print "Bolt Size not defined in CentralSlider"

        # the thickness of the support for the linear guide
        lg_sup_t = 6

        # length: rod separation
        # + twice(both sides) of radius of bearing, bolts and separation)
        self.length = ( rod_sep
                    + 2 *(bearing_r + 2 * self.SEP + 2 * self.BOLT_NUT_R_TOL))
        # linear guides on the Y ends
        lg_y_w = 0
        lg_ny_w = 0
        tot_lg_y_w = 0
        tot_lg_ny_w = 0
        if dlg_y != 0:
            lg_y_w = dlg_y['rail']['rw']
            # total width including the bolts and space between them and
            # linear guide 
            tot_lg_y_w = lg_y_w +  2 * self.BOLT_NUT_R_TOL + 4 * self.SEP
        if dlg_ny !=0:
            lg_ny_w = dlg_ny['rail']['rw']
            tot_lg_ny_w = lg_ny_w +  2 * self.BOLT_NUT_R_TOL + 4 * self.SEP
        if dlg_y != 0 or dlg_ny != 0:
            # add space for the support and the nut
            self.length = self.length + lg_sup_t 
        if dlg_y == 0 and dlg_ny == 0 and dlg_x ==0 and dlg_nx == 0:
            # No support for linear guides:
            with_lg = 0
        else:
            with_lg = 1

       
        # check the max value of the linearguides, and then, the max
        # value of the bearing compared with the linear guide
        self.width  = (max([bearing_l,tot_lg_y_w,tot_lg_ny_w])
                       + 2 * self.SEP )
        self.partheight  = bearing_r + self.OUT_SEP_H
        self.totwidth  = self.width + 2*self.dent_w

        slid_x = self.width
        slid_y = self.length
        slid_z = self.partheight

        topcenslid_box = fcfun.addBox_cen (slid_x, slid_y, slid_z,
                                  "topcenslid_box",
                                  cx=True, cy=True, cz= False)
        #logger.debug('topcenslid_box %s ' % str(topcenslid_box.Shape))
        botcenslid_box = fcfun.addBox_cen (slid_x, slid_y, slid_z,
                                 "botcenslid_box",
                                  cx=True, cy=True, cz= False)
        botcenslid_box.Placement.Base = FreeCAD.Vector(0, 0, -slid_z)

        # fillet
        topcenslid_fllt = fillet_len (box = topcenslid_box,
                                      e_len = slid_z,
                                      radius = self.FILLT_R,
                                      name = "topcenslid_fllt")
        botcenslid_fllt = fillet_len (botcenslid_box, slid_z, self.FILLT_R,
                                     "botcenslid_fllt")

        # list of elements to cut:
        cutlist = []
        # List to add to the bottom slider
        addbotlist = []
        # list of objects to be added to the top slider
        addtoplist = []
        # ----------------------------- outward dent
        #               t                         y
        #           tl ___ tr  (top right)        |_ x
        #         lt  /   \  rt (right top)
        #       lb   |     | rb (right bottom) r
        #             \   /
        #        bl    --- br  (bottom right)

        # we have dent_l, dent_w and ovdent_w (dent_w + 1)
        #         
        #     tr  ____ ovdent_l
        #    |\                 h_over = triang_h/dent_w
        #    | \  _  ___ dent_l
        #    | |\                triang_h
        #    | | \                    
        #    | |  \ rt    
        # ul |_|___\ __ dent_sl
        #    |     |
        #    |     |
        #    |     |
        # dl |_____| __
        #    | |   / rb
        #    | |  / 
        #    | | /  
        #    | |/    ___
        #    | /    
        #    |/      ____
        #     br
        #     1
        #      |---|  dent_w
        #    |-----| ovdent_w 
        #
        # the dimensions of the dent overlaped (ov), to make the shape
        # height of the triangle (no overlaped)
        if dent_w != 0:
            triang_h = (dent_l - dent_sl) / 2.
            h_over = triang_h / dent_w
            ovdent_l = dent_l + 2 * h_over
            self.ovdent_l = ovdent_l

            # slid_x-1 because the dent was calculated with 1mm of superposition
            # points:
            #p_dent_t  = FreeCAD.Vector(  0            , dent_l/2.0, 0)
            p_dent_tr = FreeCAD.Vector(  slid_x/2. -1 , ovdent_l/2., 0)
            p_dent_rt = FreeCAD.Vector(  slid_x/2. + dent_w , dent_sl/2., 0)
            #p_dent_r  = FreeCAD.Vector(  slid_x/2. -1 + dent_w , 0 , 0)
            dentwire = fcfun.wire_sim_xy([p_dent_tr, p_dent_rt])
            dentface = Part.Face(dentwire)
            shp_topdent = dentface.extrude(FreeCAD.Vector(0,0, slid_z))
            shp_botdent = dentface.extrude(FreeCAD.Vector(0,0,-slid_z))
            topdent = doc.addObject("Part::Feature", "topcenslidedent")
            topdent.Shape = shp_topdent
            botdent = doc.addObject("Part::Feature", "botcenslidedent")
            botdent.Shape = shp_botdent

            topcenslid_dent = doc.addObject("Part::Fuse","topcenslid_dent")
            topcenslid_dent.Base = topcenslid_fllt
            topcenslid_dent.Tool = topdent

            addtoplist.append (topcenslid_dent)

            botcenslid_dent = doc.addObject("Part::Fuse","botcenslid_dent")
            botcenslid_dent.Base = botcenslid_fllt
            botcenslid_dent.Tool = botdent
        
            addbotlist.append (botcenslid_dent)

        # --------------------- Hole for the rods ---------------
        toprod = fcfun.addCyl_pos ( r = rod_r + self.ROD_SPACE,
                                    h = slid_x +2,
                                    name = "toprod",
                                    axis = 'x',
                                    h_disp = -slid_x/2.0 - 1)
        toprod.Placement.Base.y = rod_sep /2.0
        cutlist.append (toprod)

        botrod = fcfun.addCyl_pos ( r = rod_r + self.ROD_SPACE,
                                    h = slid_x +2,
                                    name = "botrod",
                                    axis = 'x',
                                    h_disp = -slid_x/2.0 - 1)
        botrod.Placement.Base.y = -rod_sep /2.0
        cutlist.append (botrod)

        # --------------------- Fixed belt clamps (fbcl)
        # the width of the belt_clamp (on the X axis):
        fbcl_w = beltcl.Gt2BeltClamp.CB_IW + 2*beltcl.Gt2BeltClamp.CB_W 
        # the length of the belt_clamp (on the Y axis):
        fbcl_l = beltcl.Gt2BeltClamp.CBASE_L
    
        # top (positive Y)
        # Y position:
        fbclt_pos_y = ( self.belt_sep /2.0 -1 )
        # X position will be on the intersection of the border of the slider
        # with the Y position (fbclt_po_y)
        # There are 3 parts:
        # above the dent: fbclt_pos_y > dent_l/2. 
        # on the dent: dent_l/2. > fbclt_pos_y > dent_sl/.2
        # below the dent: fbclt_pos_y < dent_sl/.2
        # the position is related to the center of the belt clamp. So we
        # have to substract fbcl_w/2.
        if fbclt_pos_y >= dent_l/2. :
            fbclt_pos_x = slid_x/2. - fbcl_w/2. 
        elif fbclt_pos_y <= dent_sl/2. :
            fbclt_pos_x = self.totwidth/2. - fbcl_w/2. 
        else:
            # calculate the intersection of the line with the fbclt_pos_y:
            #a triangle calculation: b/h = B/H
            h = fbclt_pos_y - dent_sl/2.
            b = h * (dent_w/triang_h)
            fbclt_pos_x =  self.totwidth/2. - fbcl_w/2. - b
        fbclt_pos = FreeCAD.Vector(fbclt_pos_x,
                                   fbclt_pos_y,
                                   slid_z )
        #fco_fbclt = beltcl.fco_topbeltclamp (railaxis = '-y', bot_norm = '-z',
        #                 pos = fbclt_pos, extra = 1, name = "fbclt")
        shp_fbclt = beltcl.shp_topbeltclamp (railaxis = '-y', bot_norm = '-z',
                         pos = fbclt_pos, extra = 1)

        fbcl_xmin = fbclt_pos_x - fbcl_w/2. 

        fbcl_xmax = self.totwidth/2. + 1

        fbcl_ymax = dent_l / 2.
        fbcl_ymin = fbclt_pos_y - beltcl.Gt2BeltClamp.CBASE_L 

        doc.recompute()

        # base to add to the lower slider:
        bs_fbclt_p0 = FreeCAD.Vector (fbcl_xmin, fbcl_ymin, -1)
        bs_fbclt_p1 = FreeCAD.Vector (fbcl_xmax, fbcl_ymin, -1)
        bs_fbclt_p2 = FreeCAD.Vector (fbcl_xmax, fbcl_ymax, -1)
        bs_fbclt_p3 = FreeCAD.Vector (fbcl_xmin, fbcl_ymax, -1)
        bs_fbclt_wire = Part.makePolygon([bs_fbclt_p0,bs_fbclt_p1,
                                          bs_fbclt_p2,bs_fbclt_p3,
                                          bs_fbclt_p0])
        bs_fbclt_face = Part.Face(bs_fbclt_wire)
        shp_bs_fbclt_box = bs_fbclt_face.extrude(
                                     FreeCAD.Vector(0,0,slid_z+1))
        shp_bs_fbclt = shp_bs_fbclt_box.common(topcenslid_dent.Shape)
        #all: base with the beltclt
        shp_afbclt = shp_bs_fbclt.fuse(shp_fbclt)
        afbclt = doc.addObject("Part::Feature", "fbclt")
        afbclt.Shape = shp_afbclt
        addbotlist.append (afbclt)
        afbclt.Placement.Base.z = -0.1

        # base to cut to the lower slider:
        cbs_fbclt_p0 = FreeCAD.Vector (fbcl_xmin -kcomp.TOL,
                                       fbcl_ymin -kcomp.TOL, -1)
        cbs_fbclt_p1 = FreeCAD.Vector (fbcl_xmax,
                                       fbcl_ymin -kcomp.TOL, -1)
        cbs_fbclt_p2 = FreeCAD.Vector (fbcl_xmax,
                                       fbcl_ymax +kcomp.TOL, -1)
        cbs_fbclt_p3 = FreeCAD.Vector (fbcl_xmin -kcomp.TOL,
                                       fbcl_ymax +kcomp.TOL, -1)
        cbs_fbclt_wire = Part.makePolygon([cbs_fbclt_p0,cbs_fbclt_p1,
                                          cbs_fbclt_p2,cbs_fbclt_p3,
                                          cbs_fbclt_p0])
        cbs_fbclt_face = Part.Face(cbs_fbclt_wire)
        shp_cbs_fbclt = cbs_fbclt_face.extrude(
                                     FreeCAD.Vector(0,0,slid_z+2))
        cbs_fbclt = doc.addObject("Part::Feature", "cbs_cfbclt")
        cbs_fbclt.Shape = shp_cbs_fbclt

        cuttoplist = []
        cuttoplist.append (cbs_fbclt)

        # bottom belt clamp
        fbclb_pos = FreeCAD.Vector( fbclt_pos_x,
                                   -fbclt_pos_y,
                                   slid_z )
        shp_fbclb = beltcl.shp_topbeltclamp (railaxis = 'y', bot_norm = '-z',
                         pos = fbclb_pos, extra = 1)

        # base to add to the lower slider:
        bs_fbclb_p0 = FreeCAD.Vector (fbcl_xmin,-fbcl_ymin, -1)
        bs_fbclb_p1 = FreeCAD.Vector (fbcl_xmax,-fbcl_ymin, -1)
        bs_fbclb_p2 = FreeCAD.Vector (fbcl_xmax,-fbcl_ymax, -1)
        bs_fbclb_p3 = FreeCAD.Vector (fbcl_xmin,-fbcl_ymax, -1)
        bs_fbclb_wire = Part.makePolygon([bs_fbclb_p0,bs_fbclb_p1,
                                          bs_fbclb_p2,bs_fbclb_p3,
                                          bs_fbclb_p0])
        bs_fbclb_face = Part.Face(bs_fbclb_wire)
        shp_bs_fbclb_box = bs_fbclb_face.extrude(
                                     FreeCAD.Vector(0,0,slid_z+1))
        shp_bs_fbclb = shp_bs_fbclb_box.common(topcenslid_dent.Shape)
        #all: base with the beltclt
        shp_afbclb = shp_bs_fbclb.fuse(shp_fbclb)
        afbclb = doc.addObject("Part::Feature", "fbclb")
        afbclb.Shape = shp_afbclb
        addbotlist.append (afbclb)
        afbclb.Placement.Base.z = -0.2
        doc.recompute()

        # base to cut to the lower slider:
        cbs_fbclb_p0 = FreeCAD.Vector (fbcl_xmin -kcomp.TOL,
                                       -(fbcl_ymin -kcomp.TOL), -1)
        cbs_fbclb_p1 = FreeCAD.Vector (fbcl_xmax,
                                       -(fbcl_ymin -kcomp.TOL), -1)
        cbs_fbclb_p2 = FreeCAD.Vector (fbcl_xmax,
                                       -(fbcl_ymax +kcomp.TOL), -1)
        cbs_fbclb_p3 = FreeCAD.Vector (fbcl_xmin -kcomp.TOL,
                                       -(fbcl_ymax +kcomp.TOL), -1)
        cbs_fbclb_wire = Part.makePolygon([cbs_fbclb_p0,cbs_fbclb_p1,
                                          cbs_fbclb_p2,cbs_fbclb_p3,
                                          cbs_fbclb_p0])
        cbs_fbclb_face = Part.Face(cbs_fbclb_wire)
        shp_cbs_fbclb = cbs_fbclb_face.extrude(
                                     FreeCAD.Vector(0,0,slid_z+2))
        cbs_fbclb = doc.addObject("Part::Feature", "cbs_cfbclb")
        cbs_fbclb.Shape = shp_cbs_fbclb

        cuttoplist.append (cbs_fbclb)

        doc.recompute()

        parts_list = []
        # --------------------- Idle Pulley
        # idlepull_name_list is a list of the components for building
        # an idle pulley out of washers and bearings
        # we dont have enough information for the position yet
#        h_csidlepull0 = partgroup.BearWashGroup (
#                                   holcyl_list = kcomp.idlepull_name_list,
#                                   name = 'csidlepull_0',
#                                   normal = VZ,
#                                   pos = FreeCAD.Vector(0,0,slid_z))
#        csidlepull0 = h_csidlepull0.fco
#        # 0.5 is for the thickness of the belt
#        bolt_pull_pos_y = self.belt_sep /2.0 - h_csidlepull0.r_maxbear -0.5 
#        csidlepull0.Placement.Base = FreeCAD.Vector(
#                                                  -slid_x/2.,
#                                                   bolt_pull_pos_y,
#                                                   0)
#        csidlepull1 = Draft.clone(csidlepull0)
#        csidlepull1.Label = "cisidlepull_1"
#        csidlepull1.Placement.Base = FreeCAD.Vector(
#                                                   slid_x/2.,
#                                                   bolt_pull_pos_y,
#                                                   0)
#
#        csidlepull_list = [ csidlepull0, csidlepull1]
#        csidlepulls = doc.addObject("Part::Compound", "csidlepulls")
#        csidlepulls.Links = csidlepull_list
#
#        # list of parts of the central slider, any part that is a FreeCad
#        # Object
#        parts_list.append (csidlepulls)
#
#        # Hole for the Idle Pulley bolt       
#        csboltpull0 = addBolt (
#                            r_shank   = EndShaftSlider.BOLTPUL_SHANK_R_TOL,
#                            l_bolt    = 2 * slid_z,
#                            r_head    = EndShaftSlider.BOLTPUL_NUT_R_TOL,
#                            l_head    = EndShaftSlider.BOLTPUL_NUT_L,
#                            hex_head  = 1, extra=1,
#                            support = 1, 
#                            headdown  = 1, name="csboltpul_hole")
#
#        csboltpull0.Placement.Base =  FreeCAD.Vector (
#                                                   slid_x/2.,
#                                                   bolt_pull_pos_y,
#                                                   -slid_z)
#        csboltpull0.Placement.Rotation = FreeCAD.Rotation (VZ, 30)
#
#        cutlist.append (csboltpull0)
#        # the other Idle Pulley bolt hole
#        csboltpull1 = Draft.clone(csboltpull0)
#        csboltpull1.Label = "csboltpul_hole_1"
#        csboltpull1.Placement.Base =  FreeCAD.Vector (
#                                                   -slid_x/2.,
#                                                   bolt_pull_pos_y,
#                                                   -slid_z)
#        csboltpull1.Placement.Rotation = FreeCAD.Rotation (VZ, 30)
#        cutlist.append (csboltpull1)

        # --------------------- Linear Bearings -------------------
        h_lmuu_0 = comps.LinBearing (
                         r_ext = bearing_r,
                         r_int = rod_r,
                         h     = bearing_l,
                         name  = "cen_lm" + str(int(2*rod_r)) + "uu_0",
                         axis  = 'x',
                         h_disp = - bearing_l/2.0,
                         r_tol  = self.MLTOL,
                         h_tol  = self.TOL_BEARING_L)
        h_lmuu_0.BasePlace ((0, rod_sep / 2.0, 0))
        cutlist.append (h_lmuu_0.bearing_cont)

        h_lmuu_1 = comps.LinBearingClone (
                                      h_lmuu_0,
                                      "cen_lm" + str(int(2*rod_r)) + "uu_1",
                                      namadd = 0)
        h_lmuu_1.BasePlace ((0, - rod_sep / 2.0, 0))
        cutlist.append (h_lmuu_1.bearing_cont)

        # ---------- Belt tensioner

        h_bclten0 =  beltcl.Gt2BeltClamp (base_h = slid_z,
                                          midblock =0, name="bclten0")
        bclten0 = h_bclten0.fco   # the FreeCad Object
        parts_list.append(bclten0)
        bclten0_cont = h_bclten0.fco_cont   # the container
        # It is not centered. being one corner in (0,0,0)
        # the width is h_gt2clamp0.CBASE_W + 2 * h_gt2clamp0.extind
        #     _________
        #    |         |
        #   /           \ 
        #  |             |
        #   \           /
        #    |_________|
        #
        #  |_ 0 is here: I have to change it to be centered, and able to 
        #                rotate
      
        beltclamp_w = h_bclten0.CBASE_W + 2 * h_bclten0.extind
        #h_bclten0.BasePlace ((    -(self.width/2. +self.dent_w) 
        #                            + h_bclten0.CBASE_L ,

        h_bc_nuthole0 = NutHole (nut_r  = kcomp.M3_NUT_R_TOL,
                           nut_h  = kcomp.M3NUT_HOLE_H,
                           # + TOL to have a little bit more room for the nut
                           hole_h = slid_z/2. + TOL, 
                           name   = "bccr_nuthole0",
                           extra  = 1,
                           # the height of the nut on the X axis
                           nuthole_x = 1,
                           cx = 0, # not centered on x
                           cy = 1, # centered on y, on the center of the hexagon
                           holedown = 0)

        # fbcl_xmin is the x where the other clamp starts
        # the x min, of the nut hole
        bc_nuthole_x = (  fbcl_xmin
                        - h_bclten0.NUT_HOLE_EDGSEP
                        - h_bc_nuthole0.nut_h)
        # the end of the carriage
        bc_car_xend = bc_nuthole_x - h_bclten0.NUT_HOLE_EDGSEP

        bc_nuthole0 = h_bc_nuthole0.fco # the FreeCad Object
        bc_nuthole0.Placement.Base = FreeCAD.Vector(
                                             bc_nuthole_x,
                                             fbclt_pos_y,
                                             slid_z/2.)
        h_bclten0.BasePlace ((    bc_car_xend,
                                  fbclt_pos_y+ beltclamp_w/ 2.,
                                  0))
        bclten0.Placement.Rotation = FreeCAD.Rotation(VZ,180)
        bclten0_cont.Placement.Rotation = FreeCAD.Rotation(VZ,180)
        bclten0_cont_l =    bc_car_xend + self.width/2. +self.dent_w 
        bclten0_cont.Dir = (  bclten0_cont_l, 0,0)
        beltholes_l = []
        beltholes_l.append(bc_nuthole0)
        beltholes_l.append(bclten0_cont)

        # hole for the leadscrew of the belt clamp
        bcl_leads_h = ( self.width/2. + self.dent_w - bc_car_xend + 1)
        bcl_leads0 = fcfun.addCylPos (
                             r=kcomp.M3_SHANK_R_TOL,
                             h= bcl_leads_h,
                             name = "bcl_leads0",
                             normal = VX,
                             pos = FreeCAD.Vector (bc_car_xend-1,
                                                   fbclt_pos_y,
                                                   slid_z/2.))
        beltholes_l.append(bcl_leads0)
        # add a hole to see below
        shp_box_pos = FreeCAD.Vector (-slid_x/2., fbclt_pos_y, -slid_z-1)
        shp_boxb = fcfun.shp_boxcenfill( x= slid_x/2.+bc_car_xend -2,
                                         y= kcomp.M3_2APOT_TOL,
                                         z= slid_z + 2,
                                         fillrad = 2,
                                         fx=0, fy=0, fz=1,
                                         cx=0, cy=1, cz=0,
                                           pos = shp_box_pos)

        boxb = doc.addObject("Part::Feature", "boxb0")
        boxb.Shape = shp_boxb
        beltholes_l.append(boxb)

        beltholes_t = doc.addObject("Part::MultiFuse", "beltholes_t")
        beltholes_t.Shapes = beltholes_l
        doc.recompute()

        bclten1 = Draft.clone(bclten0)
        bclten1.Label = 'bclten1'
        bclten1.Placement.Base.x = 0 # just to move it a little bit
        bclten1.Placement.Base.y = - fbclt_pos_y + beltclamp_w/ 2.
        parts_list.append(bclten1)

        beltholes_b = Draft.clone(beltholes_t)
        beltholes_b.Label = 'beltholes_b'
        beltholes_b.Placement.Base.y = - 2* fbclt_pos_y

        doc.recompute()
        cutlist.append (beltholes_t)
        cutlist.append (beltholes_b)

        # --------------------- Motor -------------------
        h_nema14 = comps.NemaMotor(size=14, length=26.0, shaft_l=24.,
               circle_r = 0, circle_h=2.,
               name="nema14_my5602", chmf=2., rshaft_l = 0,
               bolt_depth = 3.5, bolt_out = 2 + slid_z/2.,
               normal= FreeCAD.Vector(0,0,1),
               #pos = FreeCAD.Vector(0,0,-slid_z))
               pos = FreeCAD.Vector(0,0,slid_z/2.))

        parts_list.append (h_nema14.fco)
        shp_contnema14 = h_nema14.shp_cont  # this is a shape, not a fco

        h_nema17 = comps.NemaMotor(size=17, length=33.5, shaft_l=24.,
               circle_r = 12., circle_h=2.,
               name="nema17_ST4209S1006B", chmf=2., rshaft_l = 10.,
               bolt_depth = 4.5, bolt_out = 2 + slid_z/2.,
               normal= FreeCAD.Vector(0,0,1),
               #pos = FreeCAD.Vector(0,0,-slid_z))
               pos = FreeCAD.Vector(0,0,slid_z/2.))

        parts_list.append (h_nema17.fco)
        shp_contnema17 = h_nema17.shp_cont  # this is a shape, not a fco
        shp_contmotors = shp_contnema17.fuse(shp_contnema14)

        contmotors = doc.addObject("Part::Feature", "contmotors")
        contmotors.Shape = shp_contmotors
        cutlist.append (contmotors)

        if motortype == 17:
            self.h_motor = h_nema17
        elif motortype == 14:
            self.h_motor = h_nema14
        else: #if motortype == 14:
            self.h_motor = h_nema14
            logger.error('motor not defined')

        # ------ the small motor Nanotec STF2818X0504-A -- just the bolt holes
        mtol = kcomp.TOL - 0.1
        nanostf28_boltsep = 34.1
        bhole_motorstf0 = addBolt (
            r_shank =  1.5  + mtol/2., # nemabolt_d/2. + mtol/2.,
            l_bolt = 2 + slid_z/2.,
            r_head = kcomp.D912_HEAD_D[3]/2. + mtol/2.,
            l_head = kcomp.D912_HEAD_L[3] + mtol,
            hex_head = 0, extra =1, support=1, headdown = 0,
            name ="bhole_notorstf0")

        bhole_motorstf1 = Draft.clone(bhole_motorstf0)
        bhole_motorstf1.Label = "bhole_notorstf1"

        bhole_motorstf0.Placement.Base = FreeCAD.Vector(
                                                -nanostf28_boltsep/2.,
                                                 0,
                                                 slid_z/2.)
        bhole_motorstf1.Placement.Base = FreeCAD.Vector(
                                                 nanostf28_boltsep/2.,
                                                 0,
                                                 slid_z/2.)
        bholes_motorstf = doc.addObject("Part::Fuse", "bholes_motorstf")
        bholes_motorstf.Base = bhole_motorstf0
        bholes_motorstf.Tool = bhole_motorstf1

        cutlist.append (bholes_motorstf)

        # -------------------- Middle Bolts -------------------------
        # Bolts on the middle of the slider to attach one side to
        # the other. They will be placed between the belt tensioner and
        # the motor
        motor_posy =  h_nema17.width/2.
        boltmid_posy = ((fbclt_pos_y- beltclamp_w/2.) + motor_posy)/2.

        # head down in case we want to have a larger bolt up to 
        # the end of the leadscrew
        boltmid0 = addBoltNut_hole (
                            r_shank   = self.BOLT_SHANK_R_TOL,
                            l_bolt    = 2 * slid_z,
                            r_head    = self.BOLT_HEAD_R_TOL,
                            l_head    = self.BOLT_HEAD_L,
                            r_nut     = self.BOLT_NUT_R_TOL,
                            l_nut     = self.BOLT_NUT_L,
                            hex_head  = 0, extra=1,
                            supp_head = 1, supp_nut=1,
                            headdown  = 1, name="boltmid0")
        boltmid0.Placement.Base = FreeCAD.Vector(0, - boltmid_posy, -slid_z)
        boltmid1 = Draft.clone (boltmid0)
        boltmid1.Label = 'boltmid1'
        boltmid1.Placement.Base.y = boltmid_posy
        cutlist.append(boltmid0)
        cutlist.append(boltmid1)

        # -------------------- End Bolts -------------------------
        # Bolts on the end of the slider to attach one side to the other. 
        boltend_posx = slid_x/2. - self.SEP - self.BOLT_NUT_R_TOL
        boltend_posy = slid_y/2. - self.SEP - self.BOLT_NUT_R_TOL

        boltend00 = addBoltNut_hole (
                            r_shank   = self.BOLT_SHANK_R_TOL,
                            l_bolt    = 2 * slid_z,
                            r_head    = self.BOLT_HEAD_R_TOL,
                            l_head    = self.BOLT_HEAD_L,
                            r_nut     = self.BOLT_NUT_R_TOL,
                            l_nut     = self.BOLT_NUT_L,
                            hex_head  = 0, extra=1,
                            supp_head = 1, supp_nut=1,
                            headdown  = 0, name="boltend00")
        boltend00.Placement.Base = FreeCAD.Vector(-boltend_posx,
                                                  -boltend_posy,
                                                  -slid_z)
        boltend10 = Draft.clone (boltend00)
        boltend10.Label = 'boltend10'
        boltend10.Placement.Base.x = boltend_posx
        boltend01 = Draft.clone (boltend00)
        boltend01.Label = 'boltend01'
        boltend01.Placement.Base.y = boltend_posy
        boltend11 = Draft.clone (boltend01)
        boltend11.Label = 'boltend11'
        boltend11.Placement.Base.x = boltend_posx

        cutlist.append(boltend00)
        cutlist.append(boltend10)
        cutlist.append(boltend01)
        cutlist.append(boltend11)
        doc.recompute()

        # ------ Linear guide supports for the vertical movement
        #
        #              self.totwidth/2
        #            |------------------------|------
        #            :   lg_posx_c
        #            : |----------------------|
        #            : :   lgsup_posx
        #            : : |--------------------|
        #            : : :    lgsup_posx_c
        #            : : :  |-----------------|
        #            : : :  :   lgsup_nuthole_posx
        #            : : :  : |---------------|
        #            : : :  :     lgsup_nuthole_posx_c
        #            : : :  :   |-------------|
        #            : :
        #                lgsup_t
        #    lg_hole_in  |----| lgnuthole_h
        #            |---|    |---|
        #             ________________________........
        #            |   |    |   |
        #            |   |    |   |
        #        __  |___|    |   |
        #       |    |   |    |   |
        #     lg_w   |   |    |   |
        #       |    |   |    |   |
        #       |    |   |    |   |
        #       |__  |___|    |   |
        #            |
        #            |
        #            |

        # list of objects to be cut to the bottom slider
        cutbotlist = []

        self.lg_nx_posx = 0 # 0 if there is no linear guide
        self.lg_nx_posz = 0
        self.lg_x_posx = 0
        self.lg_x_posz = 0

        # Linear Guides on X side. sg is the sign (positive or negative side)
        for sg, lg in (-1, dlg_nx), (1, dlg_x):
            if lg != 0:
                lg_b = lg['block']
                lg_r = lg['rail']
                if sg == -1:
                    suf = 'nx' # sufix for the names
                else:
                    suf = 'x' # sufix for the names
                # Making a hole just the size of:
                # the total linear guide height - block height - TOL 
                lg_hole_in = lg_b['lh'] - lg_b['bh'] - TOL
                # the width of the linear guide
                lg_w = lg_r['rw']
                #lg_hole_w = lgx_r['rw'] + 1.5*TOL # both sides: 1.5 TOL
                # Position of the center of the linear guide hole
                lg_posx_c = sg * (self.totwidth/2 - lg_hole_in/2.)
                lg_pos_c = FreeCAD.Vector(lg_posx_c, 0,0)
                if sg == -1:
                    xtr_nx = 1
                    xtr_x  = 0
                else:
                    xtr_nx = 0
                    xtr_x  = 1
                shp_lg_hole = fcfun.shp_boxcenxtr (
                                       lg_hole_in, lg_w, 2*slid_z,
                                       cx=1, cy=1, cz=1,
                                       xtr_nx = xtr_nx,  xtr_x = xtr_x,
                                       xtr_ny = .8 * TOL, xtr_y = .8 * TOL,
                                       xtr_nz = 1, xtr_z = 1,
                                       pos=lg_pos_c)
                fco_lg_hole=doc.addObject("Part::Feature", 'lg_hole_'+suf)
                fco_lg_hole.Shape = shp_lg_hole
                cutlist.append(fco_lg_hole)

                #Making the support on the top slider, supports goes down
                lgsup_posx = sg * (self.totwidth/2 - lg_hole_in)
                lgsup_posx_c = lgsup_posx - sg * lg_sup_t/2.
                lgsup_pos_c = FreeCAD.Vector(lgsup_posx_c,
                                             0,
                                             -lg_r['boltlsep'])
                shp_lgsup = fcfun.shp_boxcenxtr(lg_sup_t,
                                                lg_w,
                                                lg_r['boltlsep'],
                                                cx=1, cy=1, cz=0,
                                                xtr_z = 1,
                                                pos=lgsup_pos_c)
                fco_lgsup = doc.addObject("Part::Feature", 'lgsup_'+suf)
                fco_lgsup.Shape = shp_lgsup
                addtoplist.append(fco_lgsup)
                # bolt holes on the support
                lg_bolt_list = []
                # bolt on top, negative Y, or centered if only one
                lgbolt_t0_pos_c = FreeCAD.Vector(lgsup_posx_c,
                                              -lg_r['boltwsep']/2.,
                                               slid_z/2.)
                lgbolt_t0 = fcfun.shp_cylcenxtr (
                                           r=lg_r['boltd']/2.,
                                           h = lg_sup_t, 
                                           normal = VX,  ch=1,
                                           xtr_top=1, xtr_bot=1,
                                           pos= lgbolt_t0_pos_c)
                # bolt at bottom, negative Y, or centered if only one
                lgbolt_b0_pos_c = FreeCAD.Vector(lgsup_posx_c,
                                              -lg_r['boltwsep']/2.,
                                              slid_z/2. - lg_r['boltlsep'])
                lgbolt_b0 = fcfun.shp_cylcenxtr (
                                           r=lg_r['boltd']/2.,
                                           h = lg_sup_t, 
                                           normal = VX,  ch=1,
                                           xtr_top=1, xtr_bot=1,
                                           pos= lgbolt_b0_pos_c)


                lgbolt0 = lgbolt_t0.fuse(lgbolt_b0)
                # nut hole to introduce the nut
                lgbolt_d = lg_r['boltd']
                lgbolt_d_int = int(lgbolt_d)
                lgnut_d = kcomp.NUT_D934_D[lgbolt_d_int]
                lgnut_l = kcomp.NUT_D934_L[lgbolt_d_int]
                lgnut_r_tol = lgnut_d/2. + 1.5*TOL
                lgnut_2apot_tol = 2* lgnut_r_tol * kcomp.APOT_R
                lgnuthole_h = lgnut_l * 1.5
                h_lgnuthole0 = fcfun.NutHole(nut_r = lgnut_r_tol,
                                         nut_h = lgnuthole_h,
                                         hole_h = slid_z /2. + TOL,
                                         name = 'lgnuthole0_' + suf,
                                         extra = 1,
                                         nuthole_x = 1,
                                         cx = 1,
                                         cy = 1,
                                         holedown = 0)
                doc.recompute()
                lgnuthole0 = h_lgnuthole0.fco
                lgsup_nuthole_posx = lgsup_posx - sg * lg_sup_t
                lgsup_nuthole_posx_c = lgsup_nuthole_posx - sg * lgnuthole_h/2.
                lgnuthole0.Placement.Base = FreeCAD.Vector(
                                                    lgsup_nuthole_posx_c,
                                                    lgbolt_t0_pos_c.y ,
                                                    lgbolt_t0_pos_c.z-TOL)
                doc.recompute()
                cuttoplist.append(lgnuthole0)
                if lg_r['boltwsep'] != 0: # there are 2 bolts in a row
                    lgbolt1 = lgbolt0.copy()
                    lgbolt1.Placement.Base.y = lg_r['boltwsep']
                    lgbolts = lgbolt0.fuse(lgbolt1)
                    # clone the nut hole
                    lgnuthole1 = Draft.clone(lgnuthole0)
                    lgnuthole1.Label = 'lgnuthole1' + suf
                    lgnuthole1.Placement.Base.y = lg_r['boltwsep']/2.
                    cuttoplist.append(lgnuthole1)
                else:
                    lgbolts = lgbolt0

                fco_lgbolts = doc.addObject("Part::Feature", 'lgbolts'+suf)
                fco_lgbolts.Shape = lgbolts
                cuttoplist.append(fco_lgbolts)
                # the hole on the bottom slide to make space for the support
                # that is on the top slide and goes down
                lgsuphole_pos = FreeCAD.Vector(lgsup_posx_c, 0,-slid_z)
                if sg == -1:
                    xtr_nx = 1;
                    xtr_x  = TOL
                else:
                    xtr_nx = TOL
                    xtr_x  = 1
                shp_lgsuphole = fcfun.shp_boxcenxtr(
                                             lg_sup_t,
                                             lg_w,
                                             slid_z,
                                             cx=1, cy=1, cz=0,
                                             xtr_nx = xtr_nx, xtr_x = xtr_x,
                                             xtr_ny = TOL, xtr_y = TOL,
                                             xtr_nz = 1, xtr_z = 1,
                                             pos=lgsuphole_pos)
                fco_lgsuphole = doc.addObject("Part::Feature",'lgsuphole_'+ suf)
                fco_lgsuphole.Shape = shp_lgsuphole
                cutbotlist.append(fco_lgsuphole)
                # attribute values to know where the linear guide is 
                if sg == -1:
                    self.lg_nx_posx = lgsup_posx 
                    self.lg_nx_posz = lgbolt_b0_pos_c.z
                else:
                    self.lg_x_posx = lgsup_posx 
                    self.lg_x_posz = lgbolt_b0_pos_c.z
            

        # Linear Guides on Y side. sg is the sign (positive or negative side)
        self.lg_ny_posy = 0 # 0 if there is no linear guide
        self.lg_ny_posz = 0
        self.lg_y_posy = 0
        self.lg_y_posz = 0
        for sg, lg in (-1, dlg_ny), (1, dlg_y):
            if lg != 0:
                lg_b = lg['block']
                lg_r = lg['rail']
                if sg == -1:
                    suf = 'ny' # sufix for the names
                else:
                    suf = 'y' # sufix for the names
                # Making a hole just the size of:
                # the total linear guide height - block height - TOL 
                lg_hole_in = lg_b['lh'] - lg_b['bh'] - TOL
                # the width of the linear guide
                lg_w = lg_r['rw']
                #lg_hole_w = lg_r['rw'] + 1.5*TOL # both sides: 1.5 TOL
                # Position of the center of the linear guide hole
                lg_posy_c = sg * (self.length/2 - lg_hole_in/2.)
                lg_pos_c = FreeCAD.Vector(0,lg_posy_c,0)
                if sg == -1:
                    xtr_ny = 1
                    xtr_y  = 0
                else:
                    xtr_ny = 0
                    xtr_y  = 1
                shp_lg_hole = fcfun.shp_boxcenxtr (
                                       lg_w, lg_hole_in, 2*slid_z,
                                       cx=1, cy=1, cz=1,
                                       xtr_nx = .8 * TOL, xtr_x = .8 * TOL,
                                       xtr_ny = xtr_ny,  xtr_y = xtr_y,
                                       xtr_nz = 1, xtr_z = 1,
                                       pos=lg_pos_c)
                fco_lg_hole=doc.addObject("Part::Feature", 'lgy_hole_'+suf)
                fco_lg_hole.Shape = shp_lg_hole
                cutlist.append(fco_lg_hole)

                #Making the support on the top slider, supports goes down
                lgsup_posy = sg * (self.length/2 - lg_hole_in)
                lgsup_posy_c = lgsup_posy - sg * lg_sup_t/2.
                lgsup_pos_c = FreeCAD.Vector(0, lgsup_posy_c,
                                             -lg_r['boltlsep'])
                shp_lgsup = fcfun.shp_boxcenxtr(
                                                lg_w,
                                                lg_sup_t,
                                                lg_r['boltlsep'],
                                                cx=1, cy=1, cz=0,
                                                xtr_z = 1,
                                                pos=lgsup_pos_c)
                fco_lgsup = doc.addObject("Part::Feature", 'lgysup_'+suf)
                fco_lgsup.Shape = shp_lgsup
                addtoplist.append(fco_lgsup)
                # bolt holes on the support
                lg_bolt_list = []
                # bolt on top, negative Y, or centered if only one
                lgbolt_t0_pos_c = FreeCAD.Vector(
                                              -lg_r['boltwsep']/2.,
                                              lgsup_posy_c,
                                               slid_z/2.)
                lgbolt_t0 = fcfun.shp_cylcenxtr (
                                           r=lg_r['boltd']/2.,
                                           h = lg_sup_t, 
                                           normal = VY,  ch=1,
                                           xtr_top=1, xtr_bot=1,
                                           pos= lgbolt_t0_pos_c)
                # bolt at bottom, negative Y, or centered if only one
                lgbolt_b0_pos_c = FreeCAD.Vector(
                                              -lg_r['boltwsep']/2.,
                                              lgsup_posy_c,
                                              slid_z/2. - lg_r['boltlsep'])
                lgbolt_b0 = fcfun.shp_cylcenxtr (
                                           r=lg_r['boltd']/2.,
                                           h = lg_sup_t, 
                                           normal = VY,  ch=1,
                                           xtr_top=1, xtr_bot=1,
                                           pos= lgbolt_b0_pos_c)

                lgbolt0 = lgbolt_t0.fuse(lgbolt_b0)
                # nut hole to introduce the nut
                lgbolt_d = lg_r['boltd']
                lgbolt_d_int = int(lgbolt_d)
                lgnut_d = kcomp.NUT_D934_D[lgbolt_d_int]
                lgnut_l = kcomp.NUT_D934_L[lgbolt_d_int]
                lgnut_r_tol = lgnut_d/2. + 1.5*TOL
                lgnut_2apot_tol = 2* lgnut_r_tol * kcomp.APOT_R
                lgnuthole_h = lgnut_l * 1.5
                h_lgnuthole0 = fcfun.NutHole(nut_r = lgnut_r_tol,
                                         nut_h = lgnuthole_h,
                                         hole_h = slid_z /2. + TOL,
                                         name = 'lgynuthole0_' + suf,
                                         extra = 1,
                                         nuthole_x = 0,
                                         cx = 1,
                                         cy = 1,
                                         holedown = 0)
                doc.recompute()
                lgnuthole0 = h_lgnuthole0.fco
                lgsup_nuthole_posy = lgsup_posy - sg * lg_sup_t
                lgsup_nuthole_posy_c = lgsup_nuthole_posy - sg * lgnuthole_h/2.
                lgnuthole0.Placement.Base = FreeCAD.Vector(
                                                    lgbolt_t0_pos_c.x ,
                                                    lgsup_nuthole_posy_c,
                                                    lgbolt_t0_pos_c.z-TOL)
                doc.recompute()
                cuttoplist.append(lgnuthole0)
                if lg_r['boltwsep'] != 0: # there are 2 bolts in a row
                    lgbolt1 = lgbolt0.copy()
                    lgbolt1.Placement.Base.x = lg_r['boltwsep']
                    lgbolts = lgbolt0.fuse(lgbolt1)
                    # clone the nut hole
                    lgnuthole1 = Draft.clone(lgnuthole0)
                    lgnuthole1.Label = 'lgynuthole1' + suf
                    lgnuthole1.Placement.Base.x = lg_r['boltwsep']/2.
                    cuttoplist.append(lgnuthole1)
                else:
                    lgbolts = lgbolt0

                fco_lgbolts = doc.addObject("Part::Feature", 'lgybolts'+suf)
                fco_lgbolts.Shape = lgbolts
                cuttoplist.append(fco_lgbolts)
                # the hole on the bottom slide to make space for the support
                # that is on the top slide and goes down
                lgsuphole_pos = FreeCAD.Vector(0,lgsup_posy_c,-slid_z)
                if sg == -1:
                    xtr_ny = 1;
                    xtr_y  = TOL
                else:
                    xtr_ny = TOL
                    xtr_y  = 1
                shp_lgsuphole = fcfun.shp_boxcenxtr(
                                             lg_w,
                                             lg_sup_t,
                                             slid_z,
                                             cx=1, cy=1, cz=0,
                                             xtr_nx = TOL, xtr_x = TOL,
                                             xtr_ny = xtr_ny, xtr_y = xtr_y,
                                             xtr_nz = 1, xtr_z = 1,
                                             pos=lgsuphole_pos)
                fco_lgsuphole = doc.addObject("Part::Feature",
                                              'lgysuphole_'+ suf)
                fco_lgsuphole.Shape = shp_lgsuphole
                cutbotlist.append(fco_lgsuphole)
                # attribute values to know where the linear guide is 
                if sg == -1:
                    self.lg_ny_posy = lgsup_posy 
                    self.lg_ny_posz = lgbolt_b0_pos_c.z
                else:
                    self.lg_y_posy = lgsup_posy 
                    self.lg_y_posz = lgbolt_b0_pos_c.z



        # ----------- final fusion of holes
        #holes = doc.addObject("Part::MultiFuse", "censlid_holes")
        #holes.Shapes = cutlist

        holes_top = doc.addObject("Part::MultiFuse", "censlid_topholes")
        holes_top.Shapes = cutlist + cuttoplist

        holes_bot = doc.addObject("Part::MultiFuse", "censlid_botholes")
        holes_bot.Shapes = cutlist + cutbotlist

        self.parts = parts_list

        doc.recompute()

        # bearings fusion:
        bearings = doc.addObject("Part::Fuse", name + "_bear")
        bearings.Base = h_lmuu_0.bearing
        bearings.Tool = h_lmuu_1.bearing
        self.bearings = bearings

        # ----- adding the supports to the top slider:
        if with_lg == 1:
            topcenslid_sup = doc.addObject("Part::MultiFuse", name + "_bot_sup")
            topcenslid_sup.Shapes = addtoplist

        doc.recompute()

        # ----- adding the belt clamps to the bottom slider:
        botcenslid_cl = doc.addObject("Part::MultiFuse", name + "_bot_cl")
        botcenslid_cl.Shapes = addbotlist

        doc.recompute()
        # ----------- final cut
        topcenslid = doc.addObject("Part::Cut", name + "_top")
        if with_lg == 1:
            topcenslid.Base = topcenslid_sup
        else:
            topcenslid.Base = topcenslid_dent
        topcenslid.Tool = holes_top
        self.top_slide = topcenslid

        botcenslid = doc.addObject("Part::Cut", name + "_bot")
        botcenslid.Base = botcenslid_cl
        botcenslid.Tool = holes_bot

        doc.recompute()
        #botcenslid.Shape = botcenslid.Shape.removeSplitter()

        self.bot_slide = botcenslid

        doc.recompute()


    # move both sliders (top & bottom) and the bearings
    def BasePlace (self, position = (0,0,0)):
        self.base_place = position
        vpos = FreeCAD.Vector(position)
        for part in self.parts:
            part.Placement.Base = part.Placement.Base + vpos
            #part.Placement = ( 
            #       FreeCAD.Placement(vpos,V0ROT,V0).multiply(part.Placement))
        self.bearings.Placement.Base = vpos
        self.top_slide.Placement.Base = vpos
        self.bot_slide.Placement.Base = vpos

# --------------------- class portabase -------------
# base where the portas will be
# It has a structure to attach it to the nut of the leadscrew and some others
# to the linear guides
        
# Microscope slides (portas) dimensions (see kcit.py)
# porta_l : length of the porta
# porta_w : width of the porta
# n_porta : number of portas
# portas_sep : separation between portas, and from the porta to the end
# portabase_h: height of the base, where the portas will be
# portabase2nut: distance from the bottom of the portabase to the flange of
#         the nut of the leadscrew.
# nutshank_d : diameter of the shank of the leadscrew nut
# nutshank_l : length of the shank of the leadscrew nut
# nutflange_d : diameter of the flange of the leadscrew nut
# nutbolt_d : diameter of the bolt hole to attach the nut. It probably
#             has tolerance, to be sure, it is converted to nutbolt_d_tol
# nutbolt_pos : distance from the center to the bolt hole
# dlgy: dictionary (kcomp.) of the linear guide on Y, both sides the same
# lgy_posy: Position on Y of the linear guide
# lgybl_posz_c_bot: Postion on Z of the center of the linear guide block on its
#                   lower position
# lgy_posz_top: Z position of the top part of the rail

# Attributes:
# all the arguments and:
# portabase_l: length of the base where the portas are
# portabase_w: width of the base where the portas are
# nutbolt_d_tol: diameter of the nut bolts, with tolerances

#
#      _________________________________________________ .........
#     |  ___   ___   ___   ___   ___   ___   ___   ___  | ..      :
#     | |   | |   | |   | |   | |   | |   | |   | |   | |   :     :
#     | |   | |   | |   | |   | |   | |   | |   | |   | |   +porta_l
#     | |   | |   | |   | |   | |   | |   | |   | |   | |   :     :
#     | |___| |___| |___| |___| |___| |___| |___| |___| | ..:     +portabase_w
#     |_________________________________________________| ........:
#     : :   :                 : :                       :
#     : :...:                 :.:                       :
#     :   + porta_w            + portas_sep             :
#     :                                                 :
#     : ................. portabase_l ..................:


#       This is the base for the portas
#    _________________________________________________
#    _________________________________________________| portabase_h
#                               /            /            :
#                              /           /              :
#                      H      /          /                :
#                      H     /         /                  + portabase2nut
#  leadscrew(H)        H    /        /                    :
#                      H   /       /                      :
#                      H  /      /                        :
#              ___     H /     /                          :
#  nutshank_l  +      | |    /                            :
#              :__  __| |__/ _____________________________:
#  nut             |___ ___|    
#                  :   U   :
#                  :   H   :
#                  :   H   :
#                  :  : :  :
#                  :   +-> nutshank_d
#                  :       : 
#                  :---+--- 
#                      nutflange_d



class PortaBase (object):

    def __init__ (self, porta_l, porta_w, n_porta, porta_sep, 
                  portabase_h,
                  portabase2nut, nutshank_d, nutshank_l, nutflange_d,
                  nutbolt_d, nutbolt_pos,
                  dlgy,
                  lgy_posy,
                  lgybl_posz_c_bot,
                  lgy_posz_top,
                 ):

        doc = FreeCAD.ActiveDocument

        self.base_place  = (0,0,0)
        self.porta_l     = porta_l
        self.porta_w     = porta_w
        self.n_porta     = n_porta
        self.porta_sep   = porta_sep
        self.portabase_h = portabase_h
        self.portabase2nut = portabase2nut
        self.nutshank_d  = nutshank_d
        self.nutshank_l  = nutshank_l
        self.nutflange_d = nutflange_d
        self.nutbolt_d   = nutbolt_d
        self.dlgy        = dlgy
        self.lgy_posy    = lgy_posy
        self.lgybl_posz_bot = lgybl_posz_c_bot
        self.lgy_posz_top = lgy_posz_top
        # probably nutbolt_d already has tolerances, so just in case, convert
        # to integer (metric) and add tol
        nutbolt_d_metric = int(nutbolt_d) 
        nutbolt_d_tol = nutbolt_d_metric + 1.5*TOL 
        self.nutbolt_d_tol = nutbolt_d_tol
        self.nutbolt_pos = nutbolt_pos

        portabase_l = (n_porta * porta_w) + (n_porta +1) * porta_sep
        self.portabase_l = portabase_l
        portabase_w = porta_l + 2 * porta_sep

        # ------------------- Porta base -------------------

        fillrad = 2.
        shp_portabase_box = fcfun.shp_boxcenfill (
                                   x= portabase_w,
                                   y= portabase_l,
                                   z= portabase_h,
                                   fillrad = fillrad,
                                   fx=0, fy=0, fz=1,
                                   cx=1, cy=1, cz=0,
                                   pos = FreeCAD.Vector(0,0,portabase2nut))

        portabase_box = doc.addObject("Part::Feature", "portabase_box")
        portabase_box.Shape = shp_portabase_box

        # Making drawings of the portas
        portahole_list = []
        for ind in xrange(n_porta):
            h_porta = comps.RectRndBar (Base = porta_l,
                                        Height = porta_w,
                                        Length = 2.,
                                        Radius = 0,
                                        Thick= 1.,
                                        inrad_same= 1,
                                        axis = 'z',
                                        baseaxis = 'x',
                                        name = 'porta_' + str(ind),
                                        cx = 1, cy=0, cz=1)
            portahole_pos_y = -portabase_l/2. + (ind+1)*porta_sep + ind *porta_w

            portahole_pos = FreeCAD.Vector(0,
                                           portahole_pos_y,
                                           portabase2nut + portabase_h)
            # add its position to make it relative
            h_porta.fco.Placement.Base = portahole_pos 
            portahole_list.append(h_porta.fco)
        
        # Union of all the portaholes:
        portaholes = doc.addObject("Part::MultiFuse", "portaholes")
        portaholes.Shapes = portahole_list

        portabase = doc.addObject("Part::Cut", "portabase")
        portabase.Base = portabase_box
        portabase.Tool = portaholes

        doc.recompute()

        portabase.ViewObject.ShapeColor = fcfun.RED_05

        # ------------------- Attachment to the nut -------------------

        shp_extcone = Part.makeCone(nutflange_d/2., #r1
                                    #portabase2nut + nutflange_d/2.,  #r2
                                    0.7*portabase2nut,  #r2
                                    portabase2nut +1)  #height

        shp_intcone = Part.makeCone(nutshank_d/2. + TOL, #r1
                                    #portabase2nut/2., #r2
                                    0.5*portabase2nut, #r2
                                    portabase2nut - nutshank_l +2,  #height
                                    FreeCAD.Vector(0,0,nutshank_l))

        shp_nutcyl = Part.makeCylinder(nutshank_d/2. + TOL, # r
                                       nutshank_l + 2, # h
                                       FreeCAD.Vector (0,0,-1))

        # 4 bolts
        # to see, 3 will not be thru-hole, so the tolerances are smaller
        shp_nutbolt0 = Part.makeCylinder(nutbolt_d_tol/2. -TOL/2, # r
                                    0.7 * nutshank_l, # not thru-hole
                                    FreeCAD.Vector (nutbolt_pos,0,-1))


        shp_nutbolt1 = Part.makeCylinder(nutbolt_d_tol/2. -TOL/2, # r
                                    0.7 * nutshank_l, # not thru-hole
                                    FreeCAD.Vector (-nutbolt_pos,0,-1))

        #shp_nutbolt2 = Part.makeCylinder(nutbolt_d_tol/2. -TOL/2, # r
        #                            nutshank_l, # not thru-hole
        #                            FreeCAD.Vector (0,-nutbolt_pos,-1))

        #shp_nutbolt3 = Part.makeCylinder(nutbolt_d_tol/2., # r
        #                            portabase2nut/2., # large enough
        #                            FreeCAD.Vector (0,nutbolt_pos,-1))

        shp_conecyl = shp_intcone.multiFuse([shp_nutcyl, shp_nutbolt0,
                                                         shp_nutbolt1])
                                                         #shp_nutbolt2])
        #Part.show(shp_conecyl)
        shp_conecut = shp_extcone.cut(shp_conecyl)

        shp_boxcom = fcfun.shp_boxcen(nutflange_d, portabase_l, portabase2nut+3,
                            cx=1, cy=1, cz=0,
                            pos=FreeCAD.Vector(0,0,-1))
        shp_support = shp_conecut.common(shp_boxcom)
     
        portabase_sup0 = doc.addObject("Part::Feature", 'portabase_support0')
        portabase_sup0.Shape = shp_support
        doc.recompute()

        # I will need to have addBolt in shape, but meanwhile, I have to do
        # it at the end
        fco_nutbolt2 = fcfun.addBolt (r_shank = nutbolt_d_tol/2.,
                   l_bolt=portabase2nut/3., # large enough
                   r_head =kcomp.D912_HEAD_D[nutbolt_d_metric]/2. + TOL/3.,
                   l_head = portabase2nut/3. - nutshank_l -4,
                   hex_head = 0, extra=1, support=1, headdown=0,
                   name='nutboltthru2')
        fco_nutbolt2.Placement.Base.y = -nutbolt_pos
        fco_nutbolt3 = fcfun.addBolt (r_shank = nutbolt_d_tol/2.,
                   l_bolt=portabase2nut/3., # large enough
                   r_head =kcomp.D912_HEAD_D[nutbolt_d_metric]/2. + TOL/3.,
                   l_head = portabase2nut/3. - nutshank_l -4,
                   hex_head = 0, extra=1, support=1, headdown=0,
                   name='nutboltthru3')
        fco_nutbolt3.Placement.Base.y = nutbolt_pos

        portabase_nutthru = doc.addObject("Part::MultiFuse",'portabase_nutthru')
        portabase_nutthru.Shapes = [fco_nutbolt2, fco_nutbolt3] 
        doc.recompute()


        portabase_sup = doc.addObject("Part::Cut", 'portabase_support')
        portabase_sup.Base = portabase_sup0 
        portabase_sup.Tool = portabase_nutthru
        doc.recompute()


        doc.recompute()

        # Tab to attach to the Y-end linear guides
        lgtab_posy = lgy_posy + dlgy['block']['lh'] + TOL/2.
        if lgtab_posy > portabase_l/2.:
            print 'citoparts: portabase too small'
            portabase_tot = doc.addObject("Part::Fuse", 'portabase_tot')
            portabase_tot.Base = portabase
            portabase_tot.Tool = portabase_sup
        else:
            # position of the lower bolts of the block
            lgbl_boltbot_posz = lgybl_posz_c_bot - dlgy['block']['boltlsep']/2.
            lgbl_bolttop_posz = lgybl_posz_c_bot + dlgy['block']['boltlsep']/2.
            lgtab_w = dlgy['block']['bw'] + 8
            lgtab_z = portabase2nut - lgbl_boltbot_posz + 8.
            lgtab_t =  portabase_l/2.- lgtab_posy #thickness
            shp_lgtab_y = fcfun.shp_boxcen (
                                      x = lgtab_w,
                                      y = lgtab_t,
                                      z = lgtab_z +1,
                                      cx = 1, cy= 0, cz=0,
                        pos = FreeCAD.Vector(0,lgtab_posy,lgbl_boltbot_posz-8))
            lgbl_boltwsep = dlgy['block']['boltwsep']
            shp_lgbolt00 = fcfun.shp_cyl(
                                      r = (dlgy['block']['boltd']+TOL)/2.,
                                      h = lgtab_t + 2,
                                      normal = VY,
                                      pos = FreeCAD.Vector(-lgbl_boltwsep/2,
                                                           lgtab_posy-1,
                                                           lgbl_boltbot_posz))
            shp_lgbolt01 = fcfun.shp_cyl(
                                      r = (dlgy['block']['boltd']+TOL)/2.,
                                      h = lgtab_t + 2,
                                      normal = VY,
                                      pos = FreeCAD.Vector(lgbl_boltwsep/2,
                                                           lgtab_posy-1,
                                                           lgbl_boltbot_posz))
            shp_lgbolt10 = fcfun.shp_cyl(
                                      r = (dlgy['block']['boltd']+TOL)/2.,
                                      h = lgtab_t + 2,
                                      normal = VY,
                                      pos = FreeCAD.Vector(-lgbl_boltwsep/2,
                                                           lgtab_posy-1,
                                                           lgbl_bolttop_posz))
            shp_lgbolt11 = fcfun.shp_cyl(
                                      r = (dlgy['block']['boltd']+TOL)/2.,
                                      h = lgtab_t + 2,
                                      normal = VY,
                                      pos = FreeCAD.Vector(lgbl_boltwsep/2,
                                                           lgtab_posy-1,
                                                           lgbl_bolttop_posz))

            shp_lgbolts = shp_lgbolt00.multiFuse([
                                                  shp_lgbolt01,
                                                  shp_lgbolt10,
                                                  shp_lgbolt11])

            shp_lgtab_y_hole = shp_lgtab_y.cut(shp_lgbolts)
            shp_lgtab_ny_hole = shp_lgtab_y_hole.copy()
            shp_lgtab_ny_hole.Placement.Base.y = -2*lgtab_posy -  lgtab_t

            shp_lgytabs = shp_lgtab_ny_hole.fuse(shp_lgtab_y_hole)

            lgytabs = doc.addObject("Part::Feature", 'lgytabs')
            lgytabs.Shape = shp_lgytabs

            portabase_tabs = doc.addObject("Part::MultiFuse", 'portabase_tabs')
            # not including the support because the chamfer may touch it
            #portabase_tot.Shapes = [portabase, portabase_sup, lgytabs]
            portabase_tabs.Shapes = [portabase, lgytabs]

            # making a chamfer:
            chmf_rad = portabase2nut - lgy_posz_top
            doc.recompute()
            portabase_chmf = fcfun.filletchamfer(portabase_tabs,
                                                 e_len = lgtab_w,
                                                 name = 'portabase_chmf',
                                                 fillet = 0,
                                                 radius = chmf_rad,
                                                 axis = 'x',
                                                 zpos_chk = 1,
                                                 zpos = portabase2nut)
            # reinforcement
            rfm_z = 5.
            rfm_t = 5. # thickness
            h_portabase_rfm = comps.RectRndBar(Base = portabase_l,
                                           Height = portabase_w,
                                           Length = rfm_z + 1,
                                           Radius = fillrad,
                                           Thick = rfm_t,
                                           inrad_same = 1,
                                           axis = 'z',
                                           baseaxis = 'y',
                                           name = 'portabase_rfm',
                                           cx=1, cy=1, cz=0)

            portabase_rfm = h_portabase_rfm.fco
            portabase_rfm.Placement.Base.z = portabase2nut - rfm_z 

            portabase_tot = doc.addObject("Part::MultiFuse", 'portabase_tot')
            portabase_tot.Shapes = [portabase_chmf, portabase_sup,portabase_rfm]

        self.fco = portabase_tot


        doc.recompute()
 
                                         

    # move both sliders (top & bottom) and the bearings
    def BasePlace (self, position = (0,0,0)):
        self.base_place = position
        vpos = FreeCAD.Vector(position)
        self.fco.Placement.Base = vpos

#doc = FreeCAD.newDocument()

#nutshank_l = kcomp.T8N_L - kcomp.T8N_FLAN_L - kcomp.T8N_SHAFT_OUT
#h_portabase = PortaBase (
#                         porta_l = 75.,
#                         porta_w = 25.,
#                         n_porta = 8,
#                         porta_sep = 5.,
#                         portabase_h = 4.,
#                         portabase2nut = 83.,
#                         nutshank_d = kcomp.T8N_D_SHAFT_EXT,
#                         nutshank_l = nutshank_l,
#                         nutflange_d = kcomp.T8N_D_FLAN,
#                         nutbolt_d = kcomp.T8N_BOLT_D,
#                         nutbolt_pos = kcomp.T8N_D_BOLT_POS/2.,
#                         dlgy = kcomp.SEB15A,
#                         lgy_posy = 99.96,
#                         # position relative to the nut
#                         lgybl_posz_c_bot = -62.5,
#                         lgy_posz_top = 50.5
#                         )













## ------------------ Base of the portas ----------------------------
#
#portabase = addBox (x = kcit.PORTABASE_W,
#                    y = kcit.PORTABASE_L,
#                    z = kcit.PORTABASE_H,
#                    name = "portabase",
#                    cx = 1, cy= 0)
#
#portabase_pos_y = (   kcit.CIT_Y
#                    - (1.5 * kcit.ALU_W)
#                    - portabase.Width.Value)
#
#portabase.Placement.Base.y = portabase_pos_y
##portabase.Placement.Base.z = 250
#
#portahold_box = addBox (x = portabase.Length,
#                        y = portabase.Width,
#                        z = kcit.PORTA_H,
#                        name = "portahold_box",
#                        cx = 1, cy= 0)
#
#portahold_box.Placement.Base.z = portabase.Height
##portahold_box.Placement.Base.z = portabase.Height.Value + 250
#
#
#portahole_list = []
#for i in xrange(kcit.N_PORTA):
#    portahole_i = addBox (x = kcit.PORTA_L + TOL,
#                        y = kcit.PORTA_W + TOL,
#                        z = kcit.PORTA_H + 2,  # +2 to cut
#                        name = "portahole_" + str(i),
#                        cx = 1, cy= 0)
#    portahole_pos_y =  (i+1)*kcit.PORTAS_SEP + i *kcit.PORTA_W - TOL/2.0
#    # portabase.Height is a quantity, so cannot be added to a value.
#    # so I have to take its value
#    portahole_pos = FreeCAD.Vector(0,
#                                   portahole_pos_y,
#                                   portabase.Height.Value - 1)
#    # add its position to make it relative
#    portahole_i.Placement.Base = portahole_pos + portahole_i.Placement.Base
#    portahole_list.append(portahole_i)
#
## Union of all the portaholes:
#portahold_holes = doc.addObject("Part::MultiFuse", "portahold_holes")
#portahold_holes.Shapes = portahole_list
#
## Cut the holes from portahold_box
#portahold = doc.addObject("Part::Cut", "portahold")
#portahold.Base = portahold_box
#portahold.Tool = portahold_holes
#
#portahold.Placement.Base.y = portabase_pos_y
##portahold.Placement.Base.z = 250
#
#
#doc.recompute()
## this changes the color, but doesn't show it on the gui
#portahold.ViewObject.ShapeColor = fcfun.RED
#"""
#guidoc.getObject(portahold.Label).ShapeColor = fcfun.BLACK
#guidoc.portahold.ShapeColor = fcfun.RED
#guidoc.portahold.ShapeColor = fcfun.RED




















                  


#doc = FreeCAD.newDocument()
#CentralSlider (rod_r = kcit.ROD_R, rod_sep = 150.0, name="central_slider")
#cs = CentralSlider (rod_r = 6, rod_sep = 200.0, name="central_slider",



#cs = CentralSlider (rod_r = 6, rod_sep = 150.0, name="central_slider",
#                    belt_sep = 100,  # check value
#                    dent_w = 18,
#                    #dent_w = 30,
#                    dent_l = 122,
#                    dent_sl = 68,
#                    dlg_nx = kcomp.SEBWM16,
#                    dlg_x = kcomp.SEBWM16,
#                    #dlg_x = kcomp.SEB15A,
#                    #dlg_ny = kcomp.SEBWM16,
#                    dlg_ny = kcomp.SEB15A,
#                    dlg_y = kcomp.SEB15A )
