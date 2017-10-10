# ----------------------------------------------------------------------------
# -- Parts to print
# -- comps library
# -- Python FreeCAD functions and classes that groups components
# ----------------------------------------------------------------------------
# -- (c) Felipe Machado
# -- Area of Electronics. Rey Juan Carlos University (urjc.es)
# -- November-2016
# ----------------------------------------------------------------------------
# --- LGPL Licence
# ----------------------------------------------------------------------------

import FreeCAD;
import Part;
import Draft;
import Mesh
import DraftVecUtils
import logging

# ---------------------- can be taken away after debugging
import os
# directory this file is
filepath = os.getcwd()
import sys
# to get the components
# In FreeCAD can be added: Preferences->General->Macro->Macro path
sys.path.append(filepath)
# ---------------------- can be taken away after debugging

import kcomp 
import kcomp_optic
import fcfun
import comps
import kparts

from fcfun import V0, VX, VY, VZ, V0ROT, addBox, addCyl, addCyl_pos, fillet_len
from fcfun import VXN, VYN, VZN
from fcfun import addBolt, addBoltNut_hole, NutHole
from kcomp import TOL



logging.basicConfig(level=logging.DEBUG,
                    format='%(%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ----------- class AluProfBracketPerp -----------------------------------

class AluProfBracketPerp (object):

    """ Bracket to join 2 aluminum profiles that are perpendicular,
        that is, they are not on the same plane

        aluprof_perp (perpendicular to the bracket)   
          /  / /  bracket (not drawn)
         /  / /_____
        /  / /_____/|
       /__/ /______|/ aluprof_lin (it is in line with the bracket)
       |__|/


                     fc_perp_ax (is not the axis of the perpendicular
                       :         profile, but the axis of the bracket
       aluprof_perp    :         attached to the perpendicular profile
                    ___:_             
                   |   |  \ bracket  
                  _|___|____\___ .........> fc_line_ax
     alusize_lin +              aluprof_lin
                 :_______________


                         fc_perp_ax
                          :
                          :br_perp_thick
                          .+.
                      ....:__:
                      :   |  |\
        alusize_perp  +   |  |   \
                      :   |  |______\..
                      :...|_________|..: br_lin_thick .........> fc_lin_ax
                          :.........:
                             
           

    Arguments:
        alusize_lin: width of the aluminum profile on the line
        alusize_perp: width of the perpendicular aluminum profile
        brack_thick: thickness of the bracket
        bolt_d: metric of the bolt 3, 4, ... (integer)
        nbolts_lin: 1: just one bolt on the fc_lin_ax, or two bolts
                   2: two bolts on the fc_lin_ax, or two bolts
        xtr_bolt_head : extra space for the bolt head length,
                        and making a space for it
        xtr_bolt_head_d : extra space for the bolt head diameter,
                          and making a space for it. For the wall bolt
        reinforce = 1,
        fc_perp_ax: axis of the bracket on the perpendicular prof, see picture
        fc_line_ax: axis of the bracket on the aligned profile, see picture
        pos : position of the center of the bracket on the intersection
        wfco: if 1: With FreeCad Object: a freecad object is created
              if 0: only the shape
        name: name of the freecad object, if created
        


    """

    def __init__(self, alusize_lin, alusize_perp,
                 br_perp_thick = 3.,
                 br_lin_thick = 3.,
                 bolt_d = 3, #metric of the bolt
                 nbolts_lin = 1,
                 xtr_bolt_head = 3,
                 xtr_bolt_head_d = 0,
                 reinforce = 1,
                 fc_perp_ax = VZ,
                 fc_lin_ax = VX,
                 pos = V0,
                 wfco=1,
                 name = 'bracket'):

        doc = FreeCAD.ActiveDocument
        self.name = name
        bolt_dict = kcomp.D912[3]
        bolthead_r = bolt_dict['head_r']
        bolthead_r_tol = bolt_dict['head_r_tol']
        boltshank_r_tol = bolt_dict['shank_r_tol']
        bolthead_l = bolt_dict['head_l']
        # normalize axis, just in case:
        axis_perp = DraftVecUtils.scaleTo(fc_perp_ax,1)
        axis_lin = DraftVecUtils.scaleTo(fc_lin_ax,1)
        axis_perp_neg = axis_perp.negative()
        axis_lin_neg = axis_lin.negative()
        axis_wid   = axis_perp.cross(axis_lin)

        #Calculate the length of the brlin_l
        #         br_perp_thick :bolthead_l
        #                  :  : : bolthead_r
        #              ....:__: :  :
        #              :   |  |_   :
        # alusize_perp +   |  |_| _:_
        #              :   |  |__|___|___ 
        #              :...|_____________|
        #                  :.......:
        #                   + boltlin_dist = br_perp_thick+bolthead_l+bolthead_r
        #                          :  :  :
        #                        2 x bolthead_r
        #                  :.............:
        #                      + brlin_l

        boltlin_dist = (  br_perp_thick + bolthead_l + bolthead_r_tol
                        + xtr_bolt_head )

        brlin_l = boltlin_dist + 2 * bolthead_r
        if nbolts_lin > 1:
            # for every new bolt, add 3 times the bolt head radius
            brlin_l = brlin_l + (nbolts_lin-1)* 3 *  bolthead_r

        #              ....:__: :  :           _________
        #              :   |  |_   :          ||       ||
        # alusize_perp +   |  |_| _:_         ||   O   ||
        #              :   |  |__|___|___     ||_______||
        #              :...|_____________|    |___:_:___|......axis_wid
        #                  :.............:    :.........:
        #                    + brlin_l             + alusize_lin

        shp_box = fcfun.shp_box_dir (box_w = alusize_lin,
                                     box_d = brlin_l,
                                     box_h = alusize_perp,
                                     fc_axis_h = axis_perp,
                                     fc_axis_d = axis_lin,
                                     cw = 1, cd = 0, ch = 0,
                                     pos = pos)

        chmf_out_r = min(brlin_l-br_perp_thick, alusize_perp-br_lin_thick)

        chmf_out_pos = (   pos + DraftVecUtils.scaleTo(axis_lin, brlin_l)
                         + DraftVecUtils.scaleTo(axis_perp, alusize_perp))

        shp_box = fcfun.shp_filletchamfer_dirpt(shp_box,
                                                   fc_axis = axis_wid,
                                                   fc_pt = chmf_out_pos,
                                                   fillet = 0,
                                                   radius = chmf_out_r)

        #                                       inside_w
        #                                       ...+...
        #              ....:__: :  :           :_______:
        #              :   |  |_   :          ||       ||
        # alusize_perp +   |  |_| _:_         ||   O   ||
        #              :   |  |__|___|___     ||_______||
        #              :...|_____________|    |___:_:___|
        #                  :.............:    :.........:
        #                    + brlin_l             + alusize_lin
        # cut the box inside
        # Inside width
        # add one, to have it a minimum of one mm
        if reinforce == 1 and (alusize_lin > 2*(bolthead_r + kcomp.TOL) + 1 ):
            inside_w =  2*(bolthead_r + kcomp.TOL)
            print ("inside width " + str(inside_w))
        else:
            #no space for reinforcement, or reinforcement 0
            inside_w = alusize_lin + 2 # +2 to make the cut

        # chamfer of the inside box
        chmf_in_r = alusize_perp/2. - br_lin_thick -bolthead_r_tol
        logger.debug ("chamfer radius" + str(chmf_in_r))

        # inside box:
        insbox_pos = ( pos + DraftVecUtils.scale(axis_lin,br_perp_thick)
                           + DraftVecUtils.scale(axis_perp,br_lin_thick))
        shp_insbox = fcfun.shp_box_dir (box_w = inside_w,
                                     box_d = brlin_l,
                                     box_h = alusize_perp,
                                     fc_axis_h = axis_perp,
                                     fc_axis_d = axis_lin,
                                     cw = 1, cd = 0, ch = 0,
                                     pos = insbox_pos)
        if chmf_in_r > 0 :
            shp_insbox = fcfun.shp_filletchamfer_dirpt(shp_insbox,
                                                     fc_axis = axis_wid,
                                                     fc_pt = insbox_pos,
                                                     fillet = 0,
                                                     radius = chmf_in_r)
        #Part.show(shp_insbox)
        shp_box = shp_box.cut(shp_insbox)

        #pos_boltperp =  pos + DraftVecUtils.scale(axis_perp,alusize_perp/2.) 
        #shp_boltperp= fcfun.shp_cylcenxtr(r=boltshank_r_tol,
        #                    h=brack_thick,
        #                    normal = axis_lin,
        #                    ch = 0, xtr_top = 1, xtr_bot=1,
        #                    pos = pos_boltperp)

        boltholes = []
        pos_boltperp =  (pos + DraftVecUtils.scale(axis_perp,alusize_perp/2.)
                       + DraftVecUtils.scale(axis_lin,br_perp_thick+bolthead_l))
        shp_boltperp = fcfun.shp_bolt_dir(r_shank = boltshank_r_tol,
                            l_bolt = br_perp_thick + bolthead_l,
                            r_head = bolthead_r_tol + xtr_bolt_head_d/2.,
                            l_head = bolthead_l,
                            xtr_head = xtr_bolt_head,
                            xtr_shank = 1,
                            support = 0,
                            fc_normal = axis_lin_neg,
                            fc_verx1 = axis_perp, #it doesnt matter
                            pos = pos_boltperp)
        boltholes.append(shp_boltperp)


        pos_boltlin =  pos + DraftVecUtils.scale(axis_lin,boltlin_dist) 
        shp_boltlin= fcfun.shp_cylcenxtr(r=boltshank_r_tol,
                            h=br_lin_thick,
                            normal = axis_perp,
                            ch = 0, xtr_top = 1, xtr_bot=1,
                            pos = pos_boltlin)
        boltholes.append(shp_boltlin)

        shp_boltfuse = shp_boltlin.fuse(shp_boltperp)

        #if nbolts_lin > 1:
        for ibolt in range (1, nbolts_lin):
            # for every new bolt, add 3 times the bolt head radius
            pos_boltlin = (  pos_boltlin
                           + DraftVecUtils.scale(axis_lin,3 *  bolthead_r)) 
            shp_boltlin= fcfun.shp_cylcenxtr(r=boltshank_r_tol,
                            h=br_lin_thick,
                            normal = axis_perp,
                            ch = 0, xtr_top = 1, xtr_bot=1,
                            pos = pos_boltlin)
            boltholes.append(shp_boltlin)

        shp_boltfuse = fcfun.fuseshplist(boltholes)

        shp_bracket = shp_box.cut(shp_boltfuse)
        doc.recompute()
        shp_bracket =shp_bracket.removeSplitter()

        self.shp = shp_bracket
        self.wfco = wfco
        if wfco == 1:
            # a freeCAD object is created
            fco_bracket = doc.addObject("Part::Feature", name )
            fco_bracket.Shape = shp_bracket
            self.fco = fco_bracket

    def color (self, color = (1,1,1)):
        if self.wfco == 1:
            self.fco.ViewObject.ShapeColor = color
        else:
            logger.debug("Bracket object with no fco")
        
    # exports the shape into stl format
    def export_stl (self, name = ""):
        #filepath = os.getcwd()
        if not name:
            name = self.name
        stlPath = filepath + "/freecad/stl/"
        stlFileName = stlPath + name + ".stl"
        self.shp.exportStl(stlFileName)
       
#doc = FreeCAD.newDocument()

#AluProfBracketPerp ( alusize_lin = 10, alusize_perp = 10,
#                 br_perp_thick = 3.,
#                 br_lin_thick = 3.,
#                 bolt_d = 3,
#                 nbolts_lin = 1,
#                 xtr_bolt_head = 4,
#                 xtr_bolt_head_d = 2*kcomp.TOL, # space for the nut
#                 reinforce = 0,
#                 fc_perp_ax = VZ,
#                 fc_lin_ax = VX,
#                 pos = V0,
#                 wfco=1,
#                 name = 'bracket_lin3_1bolt_noreinfore')


#AluProfBracketPerp ( alusize_lin = 10, alusize_perp = 10,
#                 br_perp_thick = 3.,
#                 br_lin_thick = 3.,
#                 bolt_d = 3,
#                 nbolts_lin = 2,
#                 xtr_bolt_head = 3,
#                 xtr_bolt_head_d = 2*kcomp.TOL, # space for the nut
#                 reinforce = 0,
#                 fc_perp_ax = VZ,
#                 fc_lin_ax = VX,
#                 pos = V0,
#                 wfco=1,
#                 name = 'bracket_lin3_2bolts_noreinfore')


# ----------- class AluProfBracketPerpWide -----------------------------------

class AluProfBracketPerpFlap (object):

    """ Bracket to join 2 aluminum profiles that are perpendicular,
        that is, they are not on the same plane
        It is wide because it has 2 ears/flaps? on the sides, to attach
        to the perpendicular profile

        aluprof_perp (perpendicular to the bracket)   
          /  / /  bracket (not drawn)
         /  / /_____
        /  / /_____/|
       /__/ /______|/ aluprof_lin (it is in line with the bracket)
       |__|/


                     fc_perp_ax (is not the axis of the perpendicular
                       :         profile, but the axis of the bracket
       aluprof_perp    :         attached to the perpendicular profile
                    ___:_             
                   |   |  \ bracket  
                  _|___|____\___ .........> fc_line_ax
     alusize_lin +              aluprof_lin
                 :_______________


                         fc_perp_ax
                          :
                          :br_perp_thick
                          .+.
                      ....:__:
                      :   |  |\
        alusize_perp  +   |  |   \
                      :   |  |______\..
                      :...|__|______|..: br_lin_thick .........> fc_lin_ax
                          :.........:
                             
           

    Arguments:
        alusize_lin: width of the aluminum profile on the line
        alusize_perp: width of the perpendicular aluminum profile
        brack_thick: thickness of the bracket
        bolt_d: metric of the bolt 3, 4, ... (integer)
        nbolts_lin: 1: just one bolt on the fc_lin_ax, or two bolts
                   2: two bolts on the fc_lin_ax, or two bolts
        xtr_bolt_head : extra space for the bolt head on the line to the wall
                        (perpendicular)
        sunk : 1: if the top part is removed,
               0: just drilled
               2: No reinforcement at all
        flap : if it has flaps, if it hasnt flaps, it is kind of useless
               because it is just the middle part without bolts on the
               wall, but it can be used to make an union with other parts
        fc_perp_ax: axis of the bracket on the perpendicular prof, see picture
        fc_line_ax: axis of the bracket on the aligned profile, see picture
        pos : position of the center of the bracket on the intersection
        wfco: if 1: With FreeCad Object: a freecad object is created
              if 0: only the shape
        name: name of the freecad object, if created
        


    """

    def __init__(self, alusize_lin, alusize_perp,
                 br_perp_thick = 3.,
                 br_lin_thick = 3.,
                 bolt_d = 3, #metric of the bolt
                 nbolts_lin = 1,
                 xtr_bolt_head = 1,
                 sunk = 1,
                 flap = 1,
                 fc_perp_ax = VZ,
                 fc_lin_ax = VX,
                 pos = V0,
                 wfco=1,
                 name = 'bracket_flap'):

        doc = FreeCAD.ActiveDocument
        self.name = name
        bolt_dict = kcomp.D912[3]
        bolthead_r = bolt_dict['head_r']
        bolthead_r_tol = bolt_dict['head_r_tol']
        boltshank_r_tol = bolt_dict['shank_r_tol']
        bolthead_l = bolt_dict['head_l']
        # normalize axis, just in case:
        axis_perp = DraftVecUtils.scaleTo(fc_perp_ax,1)
        axis_lin = DraftVecUtils.scaleTo(fc_lin_ax,1)
        axis_perp_neg = axis_perp.negative()
        axis_lin_neg = axis_lin.negative()
        axis_wid   = axis_perp.cross(axis_lin)

        #Calculate the length of the brlin_l
        #                  :+  br_perp_thick :bolthead_l
        #                  :  :+xtr_bolt_head
        #                  :  : : + bolthead_r
        #              ....:__: :  :
        #              :   |  |    :
        # alusize_perp +   |  |   _:_
        #              :   |  |__|___|___ 
        #              :...|_____________|
        #                  :.......:
        #                   +boltlin_dist=br_perp_thick+xtr_bolt_head+bolthead_r
        #                          :  :  :
        #                        2 x bolthead_r
        #                  :.............:
        #                      + brlin_l

        boltlin_dist = br_perp_thick + xtr_bolt_head + bolthead_r 

        brlin_l = boltlin_dist + 2 * bolthead_r
        if nbolts_lin > 1:
            # for every new bolt, add 3 times the bolt head radius
            brlin_l = brlin_l + (nbolts_lin-1)* 3 *  bolthead_r

        #                      1
        #              ....:__: : :        _____________________
        #              :   |  |   :       |     ||       ||     |
        # alusize_perp +   |  |  _:_      |  O  ||       ||  O  |
        #              :   |  |_|___|___  |     ||_______||     |
        #              :...|____________| |_____|___:_:___|_____|..axis_wid
        #                  :............: :     :.........:
        #                    + brlin_l    :     :alusize_lin
        #                                 :.....:
        #                                  oneflap_w:
        #                                  min(4xbolthead_r, alusize_lin)
        #                                 :.....................:
        #                                   totalflap_w

        shp_boxbr = fcfun.shp_box_dir (box_w = alusize_lin,
                                     box_d = brlin_l,
                                     box_h = alusize_perp,
                                     fc_axis_h = axis_perp,
                                     fc_axis_d = axis_lin,
                                     cw = 1, cd = 0, ch = 0,
                                     pos = pos)


        oneflap_w = 0
        if flap == 1:
            oneflap_w = min(4*bolthead_r, alusize_lin)
            totalflap_w = alusize_lin + 2 * oneflap_w
            shp_flap = fcfun.shp_box_dir (box_w = totalflap_w,
                                          box_d = br_perp_thick,
                                          box_h = alusize_perp,
                                          fc_axis_h = axis_perp,
                                          fc_axis_d = axis_lin,
                                          cw = 1, cd = 0, ch = 0,
                                          pos = pos)

            shp_boxbr = shp_boxbr.fuse(shp_flap)


            chmf_pts = []
            for isg in [-0.5,0.5]:
                chmf_pt_pos = (pos
                           + DraftVecUtils.scale(axis_lin, br_perp_thick)
                           + DraftVecUtils.scale(axis_wid, isg * alusize_lin))
                chmf_pts.append(chmf_pt_pos)

            shp_boxbr = fcfun.shp_filletchamfer_dirpts(shp_boxbr,
                                                       fc_axis = axis_perp,
                                                       fc_pts = chmf_pts,
                                                       fillet = 0,
                                                       radius = bolthead_r )

            doc.recompute()
            shp_boxbr =shp_boxbr.removeSplitter()



        chmf_out_r = min(brlin_l-br_perp_thick, alusize_perp-br_lin_thick)

        chmf_out_pos = (   pos + DraftVecUtils.scaleTo(axis_lin, brlin_l)
                         + DraftVecUtils.scaleTo(axis_perp, alusize_perp))

        shp_boxbr = fcfun.shp_filletchamfer_dirpt(shp_boxbr,
                                                   fc_axis = axis_wid,
                                                   fc_pt = chmf_out_pos,
                                                   fillet = 0,
                                                   radius = chmf_out_r)

        #              ....:__: : :        _____________________
        #              :   |  |   :       |     ||       ||     |
        # alusize_perp +   |  |  _:_      |  O  ||       ||  O  |
        #              :   |  |_|___|___  |     ||_______||     |
        #              :...|____________| |_____|___:_:___|_____|..axis_wid
        #                  :.............:       :.........:
        #                    + brlin_l             + alusize_lin

        boltholes = []
        # inside box: (sunk == 1)
        if sunk > 0:
            # cut the box inside
            # Inside width
            # add one, to have it a minimum of one mm
            if (sunk == 1) and (alusize_lin > 2*(bolthead_r + kcomp.TOL) + 1):
                inside_w =  2*(bolthead_r + kcomp.TOL)
                print ("inside width " + str(inside_w))
            else:
                # no space for reinforcement, or no reinforcement (sunk == 2)
                inside_w = alusize_lin + oneflap_w + 2 # +2 to make the cut

            # chamfer of the inside box
            chmf_in_r = alusize_perp/2. - br_lin_thick -bolthead_r_tol
            logger.debug ("chamfer radius" + str(chmf_in_r))

            insbox_pos = ( pos + DraftVecUtils.scale(axis_lin,br_perp_thick)
                           + DraftVecUtils.scale(axis_perp,br_lin_thick))
            shp_insbox = fcfun.shp_box_dir (box_w = inside_w,
                                     box_d = brlin_l,
                                     box_h = alusize_perp,
                                     fc_axis_h = axis_perp,
                                     fc_axis_d = axis_lin,
                                     cw = 1, cd = 0, ch = 0,
                                     pos = insbox_pos)
            if chmf_in_r > 0 :
                shp_insbox = fcfun.shp_filletchamfer_dirpt(shp_insbox,
                                                     fc_axis = axis_wid,
                                                     fc_pt = insbox_pos,
                                                     fillet = 0,
                                                     radius = chmf_in_r)
            shp_boxbr = shp_boxbr.cut(shp_insbox)

            #pos_boltperp = pos +DraftVecUtils.scale(axis_perp,alusize_perp/2.) 
            #shp_boltperp= fcfun.shp_cylcenxtr(r=boltshank_r_tol,
            #                    h=brack_thick,
            #                    normal = axis_lin,
            #                    ch = 0, xtr_top = 1, xtr_bot=1,
            #                    pos = pos_boltperp)

        if flap == 1:
            boltperp_dist_w = (alusize_lin+oneflap_w)/2
            for iboltperp in [-boltperp_dist_w,boltperp_dist_w]:
                pos_boltperp =  (pos
                        + DraftVecUtils.scale(axis_perp,alusize_perp/2.)
                        + DraftVecUtils.scale(axis_lin,br_perp_thick+bolthead_l)
                        + DraftVecUtils.scale(axis_wid, iboltperp))
                shp_boltperp = fcfun.shp_bolt_dir(r_shank = boltshank_r_tol,
                                l_bolt = br_perp_thick + bolthead_l,
                                r_head = bolthead_r_tol + kcomp.TOL, #extra TOL
                                l_head = bolthead_l,
                                xtr_head = 2,
                                xtr_shank = 1,
                                support = 0,
                                fc_normal = axis_lin_neg,
                                fc_verx1 = axis_perp, #it doesnt matter
                                pos = pos_boltperp)
                boltholes.append(shp_boltperp)


        pos_boltlin = ( pos + DraftVecUtils.scale(axis_lin,boltlin_dist) +
                        DraftVecUtils.scale(axis_perp, alusize_perp))
        shp_boltlin = fcfun.shp_bolt_dir(r_shank = boltshank_r_tol,
                            l_bolt = alusize_perp,
                            r_head = bolthead_r_tol + kcomp.TOL/2., #extra TOL
                            l_head = alusize_perp-br_lin_thick,
                            xtr_head = 1,
                            xtr_shank = 1,
                            support = 0,
                            fc_normal = axis_perp_neg,
                            fc_verx1 = axis_lin, #it doesnt matter
                            pos = pos_boltlin)
        boltholes.append(shp_boltlin)

        #if nbolts_lin > 1:
        for ibolt in range (1, nbolts_lin):
            # for every new bolt, add 3 times the bolt head radius
            pos_boltlin = (  pos_boltlin
                           + DraftVecUtils.scale(axis_lin,3 *  bolthead_r)) 
            shp_boltlin = fcfun.shp_bolt_dir(r_shank = boltshank_r_tol,
                            l_bolt = alusize_perp,
                            r_head = bolthead_r_tol + kcomp.TOL/2., #extra TOL
                            l_head = alusize_perp-br_lin_thick,
                            xtr_head = 1,
                            xtr_shank = 1,
                            support = 0,
                            fc_normal = axis_perp_neg,
                            fc_verx1 = axis_lin, #it doesnt matter
                            pos = pos_boltlin)
            boltholes.append(shp_boltlin)

        shp_boltfuse = fcfun.fuseshplist(boltholes)

        shp_bracket = shp_boxbr.cut(shp_boltfuse)
        doc.recompute()
        shp_bracket =shp_bracket.removeSplitter()

        self.shp = shp_bracket
        self.wfco = wfco
        if wfco == 1:
            # a freeCAD object is created
            fco_bracket = doc.addObject("Part::Feature", name )
            fco_bracket.Shape = shp_bracket
            self.fco = fco_bracket

    def color (self, color = (1,1,1)):
        if self.wfco == 1:
            self.fco.ViewObject.ShapeColor = color
        else:
            logger.debug("Bracket object with no fco")
        
    # exports the shape into stl format
    def export_stl (self, name = ""):
        #filepath = os.getcwd()
        if not name:
            name = self.name
        stlPath = filepath + "/freecad/stl/"
        stlFileName = stlPath + name + ".stl"
        self.shp.exportStl(stlFileName)

#doc = FreeCAD.newDocument()

#AluProfBracketPerpFlap ( alusize_lin = 10, alusize_perp = 10,
#                         br_perp_thick = 3.,
#                         br_lin_thick = 3.,
#                         nbolts_lin = 2,
#                         xtr_bolt_head = 1,
#                         sunk = 0,
#                         flap = 1, 
#                         fc_perp_ax = VZ,
#                         fc_lin_ax = VX,
#                         pos = V0,
#                         wfco=1,
#                         name = 'bracket3_flap')

#AluProfBracketPerpFlap ( alusize_lin = 10, alusize_perp = 10,
#                         br_perp_thick = 3.,
#                         br_lin_thick = 3.,
#                         nbolts_lin = 2,
#                         xtr_bolt_head = 1,
#                         sunk = 2,
#                         flap = 1, 
#                         fc_perp_ax = VZ,
#                         fc_lin_ax = VX,
#                         pos = V0,
#                         wfco=1,
#                         name = 'bracket3_flap_sunk')



# ----------- class AluProfBracketPerpTwin -----------------------------------

class AluProfBracketPerpTwin (object):

    """ Bracket to join 3 aluminum profiles that are perpendicular,
        that is, they are not on the same plane
        to the perpendicular profile

        aluprof_perp (perpendicular to the bracket)   
                    . fc_wide_ax
              ___  .
             /  /|.
            /  / /______
           /  / /______/| aluprof_lin (it is in line with the bracket)
          /  / /_______|/-----------
         /  / /_____              . alu_sep
        /  / *_____/|           .
       /__/ /______|/-----------
       |__|/           aluprof_lin (it is in line with the bracket)
             * shows the reference for the position (argument pos)
               the direction of fc_wide_ax indicates where the other
               line of the bracket will be

                     fc_perp_ax (is not the axis of the perpendicular
                       :         profile, but the axis of the bracket
       aluprof_perp    :         attached to the perpendicular profile
                    ___:_             
                   |   |  \ bracket  
                  _|___|____\___ .........> fc_line_ax
     alusize_lin +              aluprof_lin
                 :_______________


                         fc_perp_ax
                          :
                          :br_perp_thick
                          .+.
                      ....:__:
                      :   |  |\
        alusize_perp  +   |  |   \
                      :   |  |______\..
                      :...|_________|..: br_lin_thick .........> fc_lin_ax
                          :.........:

                                             * bolt_perp_line
                                            1: * there is a bolt hole
                                            0: * no bolt hole there
                     ....:__: : :         __________________________
                     :   |  |   :         ||       ||     ||       ||
        alusize_perp +   |  |  _:_        ||   *   ||  O  ||   *   ||
                     :   |  |_|___|___    ||_______||     ||_______||
                     :...|____________|   |___:_:___|_____|___:_:__||..axis_wid
                         :.............:  :.........:..+..:
                           + brlin_l           +     union_w          
                                           alusize_lin         :   
                                               :..alu_sep......:
                             
           

    Arguments:
        alusize_lin: width of the aluminum profile on the line
        alusize_perp: width of the perpendicular aluminum profile
        alu_sep: separation of the 2 paralell profiles, from their centers
        brack_thick: thickness of the bracket
        bolt_d: metric of the bolt 3, 4, ... (integer)
        nbolts_lin: 1: just one bolt on the fc_lin_ax, or two bolts
                   2: two bolts on the fc_lin_ax, or two bolts
        bolt_perp_line: 1: if it has a bolt on the wall (perp) but in line
                   with the line aluminum profiles
                   0: no bolt 
        xtr_bolt_head : extra space for the bolt head, and making a space for it
                   only makes sense if bolt_perp_line == 1
        sunk : 0: No sunk, just drill holes: bolt_perp_line should be 0
               1: sunk, but with reinforcement if possible
               2: no reinforcement
        fc_perp_ax: axis of the bracket on the perpendicular prof, see picture
        fc_line_ax: axis of the bracket on the aligned profile, see picture
        fc_wide_ax: axis of the bracket on wide direction, see picture
           its direction shows where the other aligned profile is
        pos : position of the center of the bracket on the intersection
        wfco: if 1: With FreeCad Object: a freecad object is created
              if 0: only the shape
        name: name of the freecad object, if created
        
    """

    def __init__(self, alusize_lin, alusize_perp,
                 alu_sep,
                 br_perp_thick = 3.,
                 br_lin_thick = 3.,
                 bolt_d = 3, #metric of the bolt
                 nbolts_lin = 1,
                 bolt_perp_line = 0,
                 xtr_bolt_head = 3,
                 sunk = 0,
                 fc_perp_ax = VZ,
                 fc_lin_ax = VX,
                 fc_wide_ax = VY,
                 pos = V0,
                 wfco=1,
                 name = 'bracket_twin'):

        doc = FreeCAD.ActiveDocument
        self.name = name

        bolt_dict = kcomp.D912[3]
        bolthead_r = bolt_dict['head_r']
        bolthead_r_tol = bolt_dict['head_r_tol']
        boltshank_r_tol = bolt_dict['shank_r_tol']
        bolthead_l = bolt_dict['head_l']
        # normalize axis, just in case:
        axis_perp = DraftVecUtils.scaleTo(fc_perp_ax,1)
        axis_lin = DraftVecUtils.scaleTo(fc_lin_ax,1)
        axis_perp_neg = axis_perp.negative()
        axis_lin_neg = axis_lin.negative()
        axis_wid  = DraftVecUtils.scaleTo(fc_wide_ax,1) 

        # position of the other profile
        brlin2_pos = pos + DraftVecUtils.scale(axis_wid, alu_sep)
        if bolt_perp_line == 1: # there is bolt
            if sunk == 2:
                reinforce = 0
            else:
                reinforce = 1
            h_brlin1 = AluProfBracketPerp(alusize_lin = alusize_lin,
                                        alusize_perp = alusize_perp,
                                        br_perp_thick = br_perp_thick,
                                        br_lin_thick = br_lin_thick,
                                        bolt_d = bolt_d,
                                        nbolts_lin = nbolts_lin,
                                        xtr_bolt_head = xtr_bolt_head,
                                        reinforce = reinforce,
                                        fc_perp_ax = axis_perp,
                                        fc_lin_ax = axis_lin,
                                        pos = pos,
                                        wfco = 0)
            h_brlin2 = AluProfBracketPerp(alusize_lin = alusize_lin,
                                        alusize_perp = alusize_perp,
                                        br_perp_thick = br_perp_thick,
                                        br_lin_thick = br_lin_thick,
                                        bolt_d = bolt_d,
                                        nbolts_lin = nbolts_lin,
                                        reinforce = reinforce,
                                        xtr_bolt_head = xtr_bolt_head,
                                        fc_perp_ax = axis_perp,
                                        fc_lin_ax = axis_lin,
                                        pos = brlin2_pos,
                                        wfco = 0)
        else: # no hole:
            h_brlin1 = AluProfBracketPerpFlap (
                                        alusize_lin = alusize_lin,
                                        alusize_perp = alusize_perp,
                                        br_perp_thick = br_perp_thick,
                                        br_lin_thick = br_lin_thick,
                                        nbolts_lin = nbolts_lin,
                                        sunk = sunk,
                                        flap = 0, #no flap
                                        xtr_bolt_head = xtr_bolt_head,
                                        fc_perp_ax = axis_perp,
                                        fc_lin_ax = axis_lin,
                                        pos = pos,
                                        wfco = 0)
            h_brlin2 = AluProfBracketPerpFlap (
                                        alusize_lin = alusize_lin,
                                        alusize_perp = alusize_perp,
                                        br_perp_thick = br_perp_thick,
                                        br_lin_thick = br_lin_thick,
                                        nbolts_lin = nbolts_lin,
                                        sunk = sunk,
                                        xtr_bolt_head = xtr_bolt_head,
                                        flap = 0, #no flap
                                        fc_perp_ax = axis_perp,
                                        fc_lin_ax = axis_lin,
                                        pos = brlin2_pos,
                                        wfco = 0)

        shp_brlin1 = h_brlin1.shp
        shp_brlin2 = h_brlin2.shp

        # center of the 2, to make the union between both
        pos_mid = pos + DraftVecUtils.scale(axis_wid, alu_sep/2.)

        # box_w has +2 to make the union
        union_w = alu_sep-alusize_lin
        shp_union = fcfun.shp_box_dir (box_w = union_w + 2,
                                       box_d = br_perp_thick,
                                       box_h = alusize_perp,
                                       fc_axis_h = axis_perp,
                                       fc_axis_d = axis_lin,
                                       cw = 1, cd = 0, ch = 0,
                                       pos = pos_mid)

        shp_twinbr = fcfun.fuseshplist([shp_brlin1, shp_union, shp_brlin2])
        
        doc.recompute()
        shp_twinbr = shp_twinbr.removeSplitter()

        # chamfer the union 
        chmf_pts = []
        chmf_pt_pos = (pos + DraftVecUtils.scaleTo(axis_lin, br_perp_thick)
                    + DraftVecUtils.scaleTo(axis_wid, alu_sep- alusize_lin/2.))
        chmf_pts.append(chmf_pt_pos)
        chmf_pt_pos = (pos + DraftVecUtils.scaleTo(axis_lin, br_perp_thick)
                         + DraftVecUtils.scaleTo(axis_wid, alusize_lin/2.))
        chmf_pts.append(chmf_pt_pos)


        shp_twinbr = fcfun.shp_filletchamfer_dirpts(shp_twinbr,
                                                    fc_axis = axis_perp,
                                                    fc_pts = chmf_pts,
                                                    fillet = 0,
                                                    radius = bolthead_r )

        doc.recompute()
        shp_twinbr = shp_twinbr.removeSplitter()

        bolthole_list = []
        if bolt_perp_line == 1 or union_w < 8 * bolthead_r:
            # one bolt in the middle
            pos_boltperp =  (pos
                    + DraftVecUtils.scale(axis_perp,alusize_perp/2.)
                    + DraftVecUtils.scale(axis_lin,br_perp_thick+bolthead_l)
                    + DraftVecUtils.scale(axis_wid, alu_sep/2.))
            shp_boltperp = fcfun.shp_bolt_dir(r_shank = boltshank_r_tol,
                            l_bolt = br_perp_thick + bolthead_l,
                            r_head = bolthead_r_tol + kcomp.TOL, #extra TOL
                            l_head = bolthead_l,
                            xtr_head = 2,
                            xtr_shank = 1,
                            support = 0,
                            fc_normal = axis_lin_neg,
                            fc_verx1 = axis_perp, #it doesnt matter
                            pos = pos_boltperp)
            bolthole_list.append(shp_boltperp)
        else:
            # 2 holes:
            boltperp_w_pos1 = alusize_lin/2. + 2* bolthead_r
            boltperp_w_pos2 = alu_sep - alusize_lin/2. - 2* bolthead_r
            for w_pos in [boltperp_w_pos1, boltperp_w_pos2]:
                pos_boltperp =  (pos
                    + DraftVecUtils.scale(axis_perp,alusize_perp/2.)
                    + DraftVecUtils.scale(axis_lin,br_perp_thick+bolthead_l)
                    + DraftVecUtils.scale(axis_wid, w_pos))
                shp_boltperp = fcfun.shp_bolt_dir(r_shank = boltshank_r_tol,
                            l_bolt = br_perp_thick + bolthead_l,
                            r_head = bolthead_r_tol + kcomp.TOL, #extra TOL
                            l_head = bolthead_l,
                            xtr_head = 2,
                            xtr_shank = 1,
                            support = 0,
                            fc_normal = axis_lin_neg,
                            fc_verx1 = axis_perp, #it doesnt matter
                            pos = pos_boltperp)
                bolthole_list.append(shp_boltperp)

        shp_boltperp = fcfun.fuseshplist(bolthole_list)

        shp_twinbr = shp_twinbr.cut(shp_boltperp)
        doc.recompute()
        shp_bracket =shp_twinbr.removeSplitter()

        self.shp = shp_bracket
        self.wfco = wfco
        if wfco == 1:
            # a freeCAD object is created
            fco_bracket = doc.addObject("Part::Feature", name )
            fco_bracket.Shape = shp_bracket
            self.fco = fco_bracket

    def color (self, color = (1,1,1)):
        if self.wfco == 1:
            self.fco.ViewObject.ShapeColor = color
        else:
            logger.debug("Bracket object with no fco")
        
    # exports the shape into stl format
    def export_stl (self, name = ""):
        #filepath = os.getcwd()
        if not name:
            name = self.name
        stlPath = filepath + "/freecad/stl/"
        stlFileName = stlPath + name + ".stl"
        self.shp.exportStl(stlFileName)

    
#doc = FreeCAD.newDocument()

#AluProfBracketPerpTwin ( alusize_lin = 10, alusize_perp = 10,
#                 alu_sep = 40.,
#                 br_perp_thick = 3.,
#                 br_lin_thick = 3.,
#                 bolt_d = 3,
#                 nbolts_lin = 2,
#                 bolt_perp_line = 0,
#                 xtr_bolt_head = 2, 
#                 sunk = 2,
#                 fc_perp_ax = VZ,
#                 fc_lin_ax = VX,
#                 fc_wide_ax = VY,
#                 pos = V0,
#                 wfco=1,
#                 name = 'bracket_twin3')

#AluProfBracketPerpTwin ( alusize_lin = 10, alusize_perp = 10,
#                 alu_sep = 40.,
#                 br_perp_thick = 3.,
#                 br_lin_thick = 3.,
#                 bolt_d = 3,
#                 nbolts_lin = 2,
#                 bolt_perp_line = 1,
#                 xtr_bolt_head = 4, # more extra because of the perp bolt
#                 sunk = 2,
#                 fc_perp_ax = VZ,
#                 fc_lin_ax = VX,
#                 fc_wide_ax = VY,
#                 pos = V0,
#                 wfco=1,
#                 name = 'bracket_twin3_perp')



# ----------- class IdlePulleyHolder ---------------------------
# Creates a holder for a IdlePulley. Usually made of bolts, washers and bearings
# It may include a space for a endstop
# It is centered at the idle pulley, but at the back, and at the profile height
#
#          hole for endstop
#         /   []: hole for the nut
#       ________  ___ 
#      ||__|    |    + above_h
#   ___|     [] |____:__________  Z=0
#      |        |      :         aluminum profile
#      | O    O |      :
#      |________|      + profile_size
#   __________________:________
#
#        O: holes for bolts to attach to the profile
#                 
#               Z 
#               :
#        _______:__ ...
#       /         /|   :
#      /________ / |   :
#      ||__|    |  |   + height
#      |     [] |  |   :
#      |        |  | ..:
#      | O    O | /    
#      |________|/.. + depth 
#      :        :
#      :........:
#          + width
#
#   attach_dir = '-y'  enstop_side= 1     TOP VIEW
#
#
#                Y
#                :                
#                :
#              __:_________
#             |  :   |__| |
#             | (:)       |
#          ...|__:________|..... X
#
# ----- Arguments:
# profile_size: size of the aluminum profile. 20mm, 30mm
# pulleybolt_d: diameter of the bolt used to hold the pulley
# holdbolt_d: diameter of the bolts used to attach this part to the aluminum
#   profile
# above_h: height of this piece above the aluminum profile
# mindepth: If there is a minimum depth. Sometimes needed for the endstop
#            to reach its target
# attach_dir: Normal vector to where the holder is attached:'x','-x','y','-y'
#             NOW ONLY -y IS SUPPORTED. YOU CAN ROTATE IT
# endstop_side: -1, 0, 1. Side where the enstop will be
#                if attach_dir= 'x', this will be referred to the y axis 
#                if 0, there will be no endstop
# endstop_h: height of the endstop. If 0 it will be just on top of the profile
# ----- Attributes:
# depth    : depth of the holder
# width    : depth of the holder
# height    : depth of the holder
# fco      : cad object of the compound

class IdlePulleyHolder (object):

    def __init__ (self, profile_size, pulleybolt_d, holdbolt_d, above_h,
                  mindepth = 0,
                  attach_dir = '-y', endstop_side = 0,
                  endstop_posh = 0,
                  name = "idlepulleyhold"):

        doc = FreeCAD.ActiveDocument

        self.profile_size = profile_size
        self.pulleybolt_d = pulleybolt_d
        self.holdbolt_d   = holdbolt_d
        self.above_h      = above_h

        
        # extra width on each side of the nut
        extra_w = 4.
        # ----------------- Depth calculation
        pulleynut_d = kcomp.NUT_D934_D[int(pulleybolt_d)]
        pulleynut_d_tol = pulleynut_d + 3*TOL
        pulleydepth = pulleynut_d + 2 * extra_w
        depth = max(pulleydepth, mindepth)
        if endstop_side != 0:
            extra_endstop = 3.
            endstop_l =  kcomp.ENDSTOP_B['L']
            endstop_ht =  kcomp.ENDSTOP_B['HT']
            endstop_h =  kcomp.ENDSTOP_B['H']
            endstopdepth = endstop_ht + extra_endstop + extra_w
            depth = max (endstopdepth, depth)
            endstop_boltsep = kcomp.ENDSTOP_B['BOLT_SEP']
            endstop_bolt_h = kcomp.ENDSTOP_B['BOLT_H']
            endstop_bolt_d = kcomp.ENDSTOP_B['BOLT_D']
            # distance of the bolt to the end
            endstop_bolt2lend = (endstop_l - endstop_boltsep)/2.
            # distance of the bolt to the topend
            endstop_bolt2hend = endstop_h - endstop_bolt_h
        self.depth = depth

        # ----------------- Width calculation
        holdbolthead_d = kcomp.D912_HEAD_D[int(holdbolt_d)]
        # the minimum width due to the holding bolts
        minwidth_holdbolt = 2 * holdbolthead_d + 4*extra_w
        # the minimum width due to the endstop
        if endstop_side == 0:
            endstop_l = 0
            endstop_ht = 0
            minwidth_endstop = 0
        else:
            minwidth_endstop = (  endstop_l
                                + 2*TOL
                                + pulleynut_d_tol
                                + 3*extra_w )
        width = max(minwidth_holdbolt, minwidth_endstop)
        self.width = width

        # ----------------- Height calculation
        base_h = .9 * profile_size # no need to go all the way down
        height = base_h + above_h
        self.height = height

#   attach_dir = '-y'  enstop_side= 1
#
#
#                Y
#                :                
#                :
#       p10    __:_________ p11
#             |  :   |__| |
#             | (:)       |        depth
#          ...|__:________|..... X
#           p00          p01 
#                 width
#                :
#      
#                      Y
#                      :
#       p11    ________:__ p01
#             | |__|   :  |
#             |       (:) |        depth
#          ...|________:__|..... X
#           p10          p00 
#                 width


        # Constants to dimensions
        # holding bolts that will be shank in the piece, the rest will be
        # for the head
        bolt_shank = 5.
        
        # holes for the holding bolts
        # separation from the center of the hole to the end
        hbolt_endsep =  extra_w + holdbolthead_d/2.
        # separation between the holding bolts
        hbolt_sep = width - 2 * ( extra_w + holdbolthead_d/2.)
        
        # Nut for the pulley bolt
        pulleynut_h = kcomp.NUT_D934_L[int(pulleybolt_d)]
        pulleynut_hole_h = kcomp.NUT_HOLE_MULT_H * pulleynut_h
        # height inside the piece of the pulley bolt
        # adding 1 to give enough space to the 25mm bolt, it was to tight
        pulleybolt_h = 2 * extra_w + pulleynut_hole_h +1

        if attach_dir == '-y':
            if endstop_side == 0:
                p0x = - width/2.
                p1x = + width/2.
                sg = 1 #sign
            else:
                sg = endstop_side # sign
                p0x = sg * (- pulleynut_d_tol/2. - extra_w)
                p1x =  p0x + sg * width
            p00 = FreeCAD.Vector ( p0x, 0, - base_h)
            p01 = FreeCAD.Vector ( p1x, 0, - base_h)
            p11 = FreeCAD.Vector ( p1x, depth, - base_h)
            p10 = FreeCAD.Vector ( p0x, depth, - base_h)


            shp_wire_base = Part.makePolygon([p00,p01, p11, p10, p00])
            shp_face_base = Part.Face(shp_wire_base)
            shp_box = shp_face_base.extrude(FreeCAD.Vector(0,0,height))



            hbolt_p0x = p0x + sg * hbolt_endsep
            #shank of holding bolt
            pos_shank_hbolt0 = FreeCAD.Vector(hbolt_p0x,
                                              -1,
                                             -profile_size/2.)
            shp_shank_hbolt0 = fcfun.shp_cyl ( r = holdbolt_d/2. + TOL,
                                               h= bolt_shank + 2, normal = VY,
                                               pos = pos_shank_hbolt0)
            if depth > bolt_shank :
                pos_head_hbolt0 = FreeCAD.Vector(hbolt_p0x,
                                                 bolt_shank,
                                                 -profile_size/2.)
                shp_head_hbolt0 = fcfun.shp_cyl (
                                           r = holdbolthead_d/2. + TOL,
                                           h = depth - bolt_shank + 1,
                                           normal = VY,
                                           pos = pos_head_hbolt0)
                shp_hbolt0 = shp_shank_hbolt0.fuse(shp_head_hbolt0)
            else: # no head
                shp_hbolt0 = shp_shank_hbolt0 
            shp_hbolt1 = shp_hbolt0.copy()
            # It is in zero
            shp_hbolt1.Placement.Base.x = sg * hbolt_sep

            # hole for the pulley bolt
            pulleybolt_pos = FreeCAD.Vector (0, depth - pulleydepth/2.,
                                             above_h - pulleybolt_h)
            shp_pulleybolt = fcfun.shp_cyl (r = pulleybolt_d/2. + 0.9*TOL/2,
                                            h = pulleybolt_h + 1,
                                            normal = VZ,
                                            pos = pulleybolt_pos)
                                            
            holes_list = [shp_hbolt0, shp_hbolt1]
            # hole for the nut:

            # hole for the endstop
            if endstop_side != 0:
                #endstopbox_l = endstop_l + 2*TOL
                #endstopbox_w = endstop_ht + extra_endstop + TOL
                endstopbox_l = endstop_l + 2*TOL + extra_w + 1
                endstopbox_w = depth + 2
                #endstop_posx = p1x + sg*(extra_w + endstopbox_l/2.)
                endstop_posx = p1x - sg*(endstopbox_l/2. -1)
                endstop_posy = (depth - endstopbox_w )
                #endstop_posy = (depth - endstopbox_w )
                endstop_posy = -1

                endstop_pos = FreeCAD.Vector(endstop_posx, endstop_posy,
                                             endstop_posh)
                shp_endstop = fcfun.shp_boxcen(x=endstopbox_l,
                                               y=endstopbox_w,
                                               z=above_h-endstop_posh +1,
                                               cx=1,
                                               pos=endstop_pos)
                holes_list.append(shp_endstop)

                # hole for the bolts of the endstop
                endstopbolt0_pos = FreeCAD.Vector(
                                  endstop_posx - endstop_boltsep/2.,
                                  depth - endstop_bolt2hend,
                                  endstop_posh + 1)
                shp_endstopbolt0 = fcfun.shp_cyl (
                                        r= endstop_bolt_d/2. + TOL/2.,
                                        h = extra_w + 1,
                                        normal = fcfun.VZN,
                                        pos=endstopbolt0_pos)
                holes_list.append(shp_endstopbolt0)
                shp_endstopbolt1 = shp_endstopbolt0.copy()
                shp_endstopbolt1.Placement.Base.x = endstop_boltsep
                holes_list.append(shp_endstopbolt1)

            shp_holes = shp_pulleybolt.multiFuse(holes_list)
            shp_pulleyhold = shp_box.cut(shp_holes)

            pulleyhold_aux = doc.addObject("Part::Feature", name + '_aux')
            pulleyhold_aux.Shape = shp_pulleyhold

            # fillet the top part if it has no endstop. So the belt doesnt
            # hit the corner
            if endstop_side == 0:
                fillet_r = (width - pulleynut_d_tol - 2 * extra_w) / 2.
                pulleyhold_aux = fcfun.filletchamfer(
                                       fco = pulleyhold_aux,
                                       e_len = depth,
                                       name = name + '_chmf',
                                       fillet = 1,
                                       radius = fillet_r,
                                       axis = 'y',
                                       zpos_chk = 1,
                                       zpos = above_h)
                                          


            h_nuthole = fcfun.NutHole (nut_r = pulleynut_d_tol/2.,
                                       nut_h = pulleynut_hole_h,
                                       hole_h = pulleydepth/2. + TOL,
                                       name = name + '_nuthole',
                                       extra = 1,
                                       nuthole_x = 0,
                                       cx = 1, cy = 0, holedown = 0)
            nuthole = h_nuthole.fco
            nuthole.Placement.Rotation = FreeCAD.Rotation(VX,-90)
            nuthole.Placement.Base.y = depth - pulleydepth/2. - TOL
            nuthole.Placement.Base.z = above_h - extra_w
            
            pulley_holder = doc.addObject("Part::Cut", name)
            pulley_holder.Base = pulleyhold_aux    
            pulley_holder.Tool = nuthole    

            self.fco = pulley_holder

        doc.recompute()

    def color (self, color = (1,1,1)):
        self.fco.ViewObject.ShapeColor = color

            
            
        

#doc = FreeCAD.newDocument()

#idp = IdlePulleyHolder( profile_size=30.,
#                        pulleybolt_d=3.,
#                        holdbolt_d = 5,
#                        above_h = 47-15-9.5,
#                        mindepth = 0,
#                        attach_dir = '-y',
#                        endstop_side = 0,
#                        endstop_posh = 0,
#                        name = "idlepulleyhold")




# Holder for the endstop to be attached to the rail of SEB15A_R
# Made fast and with hardcoded constants, no parametric


def endstopholder_rail ():

    in_w = kcomp.SEB15A_R['rw']
    add_w = 4.
    #out_w = in_w + 2 * add_w
    out_w = 36.

    ends_d = 6.  #endstop depth
    supp_d = 12.5 # support depth

    total_d = supp_d - ends_d + add_w

    bolt_h = 18.
    extra_h = 5.

    total_h = bolt_h + extra_h + add_w
    obox = fcfun.shp_boxcenfill(out_w, total_d, total_h, 1,
                                cx=1, cy=0, cz=0)


    ibox = fcfun.shp_boxcen(in_w + 1.5 * TOL, add_w + 1, total_h + 2,
                            cx=1, cy=0, cz=0, pos = FreeCAD.Vector(0, -1,-1))


    endsbolt2top = 7. # distance of the endstop bolt to the top
    endsboltsep = 9.6 # distance between endstop bolts
    endsbolt_depth = 5.5 # depth of the holes
    endsbolt_diam = 2.5 # diameter

    ends_bolt_pos0 = FreeCAD.Vector ( endsboltsep/2., total_d +1,
                                      total_h - endsbolt2top)
    ends_bolt0 = fcfun.shp_cyl (r=endsbolt_diam/2.+TOL/2.,
                                h = endsbolt_depth +1,
                                normal = VYN,
                                pos = ends_bolt_pos0) 
    ends_bolt_pos1 = FreeCAD.Vector ( -endsboltsep/2.,
                                       total_d +1,
                                       total_h - endsbolt2top)
    ends_bolt1 = fcfun.shp_cyl (r=endsbolt_diam/2.+TOL/2.,
                                h = endsbolt_depth +1,
                                normal = VYN,
                                pos = ends_bolt_pos1) 

    ends_bolt_pos00 = FreeCAD.Vector ( endsboltsep*1.5,
                                       total_d +1,
                                       total_h - endsbolt2top)
    ends_bolt00 = fcfun.shp_cyl (r=endsbolt_diam/2.+TOL/2.,
                                 h = endsbolt_depth +1,
                                 normal = VYN,
                                 pos = ends_bolt_pos00) 
    ends_bolt_pos11 = FreeCAD.Vector ( -endsboltsep*1.5,
                                        total_d +1,
                                        total_h - endsbolt2top)

    ends_bolt11 = fcfun.shp_cyl (r=endsbolt_diam/2.+TOL/2.,
                                 h = endsbolt_depth +1,
                                 normal = VYN,
                                 pos = ends_bolt_pos11) 



    railbolt_d = 3.

    railbolt = fcfun.shp_boxcenfill ( x=railbolt_d + 0.8*TOL,
                                      y= total_d + 2,
                                      z = railbolt_d + extra_h,
                                      fillrad = railbolt_d/2.,
                                      fx = 0, fy=1, fz=0,
                                      cx=1, cy=0, cz=0,
                                      pos = FreeCAD.Vector(0, -1, add_w))


    railbolthead_d = kcomp.D912_HEAD_D[int(railbolt_d)]

    railbolt_head_pos =  FreeCAD.Vector(
                                     0,
                                     add_w+3,
                                     add_w-railbolthead_d/2. + railbolt_d/2. )

    railbolt_head = fcfun.shp_boxcenfill (x=railbolthead_d + TOL,
                                          y= total_d + 2,
                                          z = railbolthead_d + extra_h,
                                          fillrad = railbolthead_d/2.,
                                          fx = 0, fy=1, fz=0,
                                          cx=1, cy=0, cz=0,
                                          pos = railbolt_head_pos)

    shp_fusecut = ibox.multiFuse([ends_bolt0, ends_bolt1,
                                  ends_bolt00, ends_bolt11,
                                  railbolt, railbolt_head])

    box = obox.cut(shp_fusecut)
    #Part.show (box)
    return (box)
            

# ----------- thin linear bearing housing with one rail to be attached

class ThinLinBearHouse1rail (object):

    """

        Makes a housing for a linear bearing, but it is very thin
        and intented to be attached to one rail, instead of 2
        it has to parts, the lower and the upper part

         ________                           ______________
        | ::...::|                         | ::........:: |
        | ::   ::|    Upper part           |.::        ::.|
        |-::( )::|------                   |.::        ::.|  --> fc_slide_axis
        | ::...::|    Lower part           | ::........:: | 
        |_::___::|                   ______| ::        :: |______
        |_::|_|::|                  |__:_:___::________::__:_:__|
                                                   :
         _________                                 :
        |____O____|                                v
        |  0: :0  |                            fc_bot_axis
        | :     : |
        | :     : |
        | :     : |
        | :.....: |
        |__0:_:0__|
        |____O____|
        
         ________                           ______________
        | ::...::|                         | ::........:: |
        | ::   ::|    Upper part           |.::        ::.|
        |-::( )::|------                   |.::   *axis_center = 1
        | ::...::|    Lower part           | ::........:: | 
        |_::___::|                   ______| ::        :: |______
        |_::|_|::|                  |__:_:___::___*____::__:_:__|
             |                                   axis_center = 0
             |
             V
           always centered in this axis

                                            ______________
        1: axis_center=1                   | ::........:: |
           mid_center =1                   |.::        ::.|
        2: axis_center=0                4  |.::   1 --> fc_slide_axis
           mid_center =1                   | ::........:: | 
        3: axis_center=0             ______| ::        :: |______
           mid_center =0             |_:3:___::___2____::__:_:__|
        4: axis_center=1
           mid_center =0


    Arguments:
        d_lbear: dictionary with the dimensions of the linear bearing
        fc_slide_axis : FreeCAD.Vector with the direction of the slide
        fc_bot_axis: FreCAD.Vector with the direction of the bottom
        axis_center = See picture, indicates the reference point
        mid_center  = See picture, indicates the reference point
        pos = position of the reference point,

    Useful Attributes:
        n1_slide_axis: FreeCAD.Vector
        n1_bot_axis: FreeCAD.Vector
        n1_perp: FreeCAD.Vector
        axis_h: float
        boltcen_axis_dist: float
        boltcen_perp_dist: float
        + --- Dimensions:
        tot_h, tot_w, tot_l
        housing_l, base_h
        + --- FreeCAD objects
        fco_top = top part of the linear bearing housing
        fco_bot = bottom part of the linear bearing housing

           ________                           ______________
          | ::...::|                         | ::........:: |
          | ::   ::|                         |.::        ::.|
          |-::( )::|---:                     |.::        ::.|  --> n1_slide_axis
          | ::...::|   +axis_h               | ::........:: | 
          |_::___::|   :               ______| ::        :: |______
          |_::|_|::|...:              |__:_:___::________::__:_:__|
                                                     :
           _________                                 v
          |____O____|                              n1_bot_axis
          |  0: :0  |
          | :     : |
          | :     : |---+ boltcen_axis_dist ..            --> n1_perp
          | :     : |   :                    :
          | :.....: |   :                    + boltrailcen_dist
          |__0:_:0__|----                    :
          |____O____|------------------------:
             :   :
             :   :
             :...:
               +boltcen_perp_dist
         
                                             ....housing_l..
                                             :              :
           ________....                      :______________:
          | ::...::|   :                     | ::........:: |
          | ::   ::|   :                     |.::        ::.|
          |-::( )::|   :                     |.::        ::.|  --> n1_slide_axis
          | ::...::|   +tot_h                | ::........:: | 
          |_::___::|   :           ... ______| ::        :: |______
          |_::|_|::|...:    base_h ...|__:_:___::________::__:_:__|
          :        :                  :                           :
          :........:                  :...........................:
              +                                      +
             tot_w                                 tot_l       

    """

    MIN_SEP_WALL = 3. # min separation of a wall
    MIN2_SEP_WALL = 2. # min separation of a wall
    OUT_SEP_H = kparts.OUT_SEP_H
    MTOL = kparts.MTOL
    MLTOL = kparts.MLTOL
    TOL_BEARING_L = kparts.TOL_BEARING_L
    # Radius to fillet the sides
    FILLT_R = kparts.FILLT_R

    def __init__(self, d_lbear,
                 fc_slide_axis = VX,
                 fc_bot_axis =VZN,
                 axis_center = 1,
                 mid_center  = 1,
                 pos = V0,
                 name = 'thinlinbearhouse'
                ):

        # normalize, just in case
        n1_slide_axis = DraftVecUtils.scaleTo(fc_slide_axis,1)
        n1_bot_axis = DraftVecUtils.scaleTo(fc_bot_axis,1)
        n1_bot_axis_neg = DraftVecUtils.neg(n1_bot_axis)
        # vector perpendicular to the others
        n1_perp = n1_slide_axis.cross(n1_bot_axis)


        self.rod_r = d_lbear['Di']/2.
        rod_r = self.rod_r
        self.bear_r = d_lbear['Di']
        if rod_r >= 6:
            BOLT_D = 4
        else:
            BOLT_D = 3  # M3 bolts

        doc = FreeCAD.ActiveDocument

        MIN_SEP_WALL = self.MIN_SEP_WALL
        MIN2_SEP_WALL = self.MIN2_SEP_WALL
        OUT_SEP_H = self.OUT_SEP_H
        # bolt dimensions:
        MTOL = self.MTOL
        MLTOL = self.MLTOL
        BOLT_HEAD_R = kcomp.D912_HEAD_D[BOLT_D] / 2.0
        BOLT_HEAD_L = kcomp.D912_HEAD_L[BOLT_D] + MTOL
        BOLT_HEAD_R_TOL = BOLT_HEAD_R + MTOL/2.0 
        BOLT_SHANK_R_TOL = BOLT_D / 2.0 + MTOL/2.0
        BOLT_NUT_R = kcomp.NUT_D934_D[BOLT_D] / 2.0
        BOLT_NUT_L = kcomp.NUT_D934_L[BOLT_D] + MTOL
        #  1.5 TOL because diameter values are minimum, so they may be larger
        BOLT_NUT_R_TOL = BOLT_NUT_R + 1.5*MTOL

        # bearing dimensions:
        bearing_l     = d_lbear['L'] 
        bearing_l_tol = bearing_l + self.TOL_BEARING_L
        bearing_d     = d_lbear['De']
        bearing_d_tol = bearing_d + 2.0 * self.MLTOL
        bearing_r     = bearing_d / 2.0
        bearing_r_tol = bearing_r + self.MLTOL

        #There are two basic pieces: the base and the housing for the linear
        # bearing
        # dimensions of the housing:
        # length on the direction of the sliding rod
        bolt2wall = fcfun.get_bolt_end_sep(BOLT_D, hasnut=1) 
        #housing_l = bearing_l_tol + 2 * (2*BOLT_HEAD_R_TOL + 2* MIN_SEP_WALL)
        housing_l = bearing_l_tol + 2 * (2* bolt2wall)
        print "housing_l: %", housing_l
        # width of the housing (very tight)
        housing_w = max ((bearing_d_tol + 2* MIN_SEP_WALL), 
                         (d_lbear['Di'] + 4* MIN2_SEP_WALL + 2*BOLT_D))
        print "housing_w: %", housing_w

        # dimensions of the base:
        # length on the direction of the sliding rod
        base_l = housing_l +  4* MIN_SEP_WALL + 4 * BOLT_HEAD_R_TOL
        print "base_l: %", base_l
        # width of the base (very tight), the same as the housing
        base_w = housing_w
        print "base_w: %", base_w
        # height of the base (not tight). twice the mininum height
        base_h = 2 * OUT_SEP_H 
        print "base_h: %", base_h

        # height of the housing (not tight, can be large)
        housing_h = base_h +  2* BOLT_HEAD_L + bearing_d_tol
        print "housing_h: %", housing_h


        # distance on the slide_axis from midcenter=0 to midcenter 1.
        # the bolt to join the housing to the rail
        boltrailcen_dist = housing_l/2. + BOLT_HEAD_R_TOL + MIN_SEP_WALL
        # distance on the bot_axis from the rod to the bottom
        # the base and the housing are overlapped.
        # Not taking the tolerance
        #axis_h = bearing_d/2. + 2 * OUT_SEP_H + BOLT_HEAD_L
        axis_h = ( rod_r + kparts.ROD_SPACE_MIN + base_h
                             + 2 * BOLT_HEAD_L)

        #To make the boxes, we take the reference on midcenter=1 and 
        # axis_center = 0. Point 2 on the drawing

        if mid_center == 0:
            # get the vector to the center:
            fc_tomidcenter = DraftVecUtils.scale(n1_slide_axis,boltrailcen_dist)
        else:
            fc_tomidcenter = V0
        if axis_center == 1:
            fc_tobottom = DraftVecUtils.scale(n1_bot_axis,axis_h)
            fc_toaxis = V0
        else:
            fc_tobottom = V0
            fc_toaxis = DraftVecUtils.scale(n1_bot_axis,-axis_h)

        botcenter_pos = pos + fc_tomidcenter + fc_tobottom

        # point 1 on the drawing
        axiscenter_pos = pos + fc_tomidcenter + fc_toaxis

        shp_base = fcfun.shp_box_dir(box_w = base_w,
                                     box_d = base_l, #dir of n1_slide_axis
                                     box_h = base_h,
                                     fc_axis_h = n1_bot_axis_neg,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = botcenter_pos)

        # fillet the base:
        shp_base_fllt = fcfun.shp_filletchamfer_dir(shp_base,
                                                    fc_axis=fc_bot_axis,
                                                    radius=kparts.FILLT_R)


        shp_housing = fcfun.shp_box_dir(box_w = housing_w,
                                     box_d = housing_l, #dir of n1_slide_axis
                                     box_h = housing_h,
                                     fc_axis_h = n1_bot_axis_neg,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = botcenter_pos)
        #Part.show(shp_housing)

        shp_block = shp_base_fllt.fuse(shp_housing)

        # the rod hole
        shp_rod = fcfun.shp_cylcenxtr(r = rod_r + kparts.ROD_SPACE_MIN,
                                      h = base_l,
                                      normal = n1_slide_axis,
                                      ch = 1, xtr_top = 1, xtr_bot=1,
                                      pos = axiscenter_pos)
        # the linear bearing hole
        shp_lbear = fcfun.shp_cylcenxtr(r = bearing_r_tol,
                                        h = bearing_l_tol,
                                        normal = n1_slide_axis,
                                        ch = 1, xtr_top = 1, xtr_bot=1,
                                        pos = axiscenter_pos)
        shp_rodlbear = shp_rod.fuse(shp_lbear)
        shp_block_hole = shp_block.cut(shp_rodlbear)

        # bolts to atach to the support
        
        bolt1_atch_pos = (  botcenter_pos
                          + DraftVecUtils.scale(n1_slide_axis,boltrailcen_dist))
        bolt2_atch_pos = (  botcenter_pos
                         + DraftVecUtils.scale(n1_slide_axis,-boltrailcen_dist))

        shp_bolt1_atch = fcfun.shp_cylcenxtr(r=BOLT_SHANK_R_TOL,
                                             h = base_h,
                                             normal = n1_bot_axis_neg,
                                             ch = 0, xtr_top = 1, xtr_bot = 1,
                                             pos = bolt1_atch_pos)
        shp_bolt2_atch = fcfun.shp_cylcenxtr(r=BOLT_SHANK_R_TOL,
                                             h = base_h,
                                             normal = n1_bot_axis_neg,
                                             ch = 0, xtr_top = 1, xtr_bot = 1,
                                             pos = bolt2_atch_pos)
        bolt_holes = [shp_bolt2_atch]

        # 4 bolts to join the upper and lower parts
        # distance of the bolts to the center, on n1_slide_axis dir
        boltcen_axis_dist = housing_l/2. - bolt2wall
        # distance of the bolts to the center, on n1_perp dir
        boltcen_perp_dist = housing_w/2. - bolt2wall



        for vec_axis in [DraftVecUtils.scale(n1_slide_axis,boltcen_axis_dist),
                         DraftVecUtils.scale(n1_slide_axis,-boltcen_axis_dist)]:
            for vec_perp in [DraftVecUtils.scale(n1_perp,
                                                 boltcen_perp_dist),
                             DraftVecUtils.scale(n1_perp,
                                                 -boltcen_perp_dist)]:
                pos_i = botcenter_pos + vec_axis + vec_perp
                # the nut hole will be on the bottom side,
                
                shp_bolt = fcfun.shp_boltnut_dir_hole (
                                  r_shank = BOLT_SHANK_R_TOL,
                                  l_bolt  = housing_h,
                                  r_head  = BOLT_HEAD_R_TOL,
                                  l_head  = BOLT_HEAD_L,
                                  r_nut  = BOLT_NUT_R_TOL,
                                  # more space, because we want it well inside
                                  l_nut  = 1.5*BOLT_NUT_L,
                                  hex_head = 0,
                                  xtr_head=1,     xtr_nut=1,
                                  supp_head=1,    supp_nut=1,
                                  headstart=0,
                                  fc_normal = n1_bot_axis_neg,
                                  fc_verx1=V0,
                                  pos = pos_i)
                bolt_holes.append(shp_bolt)

        # ----------------- Attributes
        self.n1_slide_axis = n1_slide_axis
        self.n1_bot_axis = n1_bot_axis
        self.n1_perp = n1_perp
        self.axis_h = axis_h
        self.boltcen_axis_dist = boltcen_axis_dist
        self.boltcen_perp_dist = boltcen_perp_dist
        self.tot_h = housing_h
        self.tot_w = housing_w # == base_w
        self.tot_l = base_l
        self.housing_l  = housing_l
        self.base_h = base_h
        
        shp_bolt_holes = shp_bolt1_atch.multiFuse(bolt_holes)       
        shp_lbear_housing = shp_block_hole.cut(shp_bolt_holes)
        doc.recompute()
        # making 2 parts, intersection with 2 boxes:
        shp_box_top = fcfun.shp_box_dir(
                                     box_w = housing_w + 2,
                                     box_d = housing_l + 2, 
                                     box_h = housing_h /2. + 2,
                                     fc_axis_h = n1_bot_axis_neg,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = axiscenter_pos)
        shp_lbear_housing_top = shp_lbear_housing.common(shp_box_top)
        shp_lbear_housing_top = shp_lbear_housing_top.removeSplitter() 
        fco_lbear_top = doc.addObject("Part::Feature", name + '_top') 
        fco_lbear_top.Shape = shp_lbear_housing_top


        shp_box_bot = fcfun.shp_box_dir(
                                     box_w = base_w + 2,
                                     box_d = base_l + 2,
                                     # larger, just in case
                                     box_h = housing_h/2. + base_h + 2,
                                     fc_axis_h = n1_bot_axis,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = axiscenter_pos)
        shp_lbear_housing_bot = shp_lbear_housing.common(shp_box_bot)
        shp_lbear_housing_bot = shp_lbear_housing_bot.removeSplitter()
        fco_lbear_bot = doc.addObject("Part::Feature", name + '_bot') 
        fco_lbear_bot.Shape = shp_lbear_housing_bot

        self.fco_top = fco_lbear_top
        self.fco_bot = fco_lbear_bot

    def color (self, color = (1,1,1)):
        self.fco_top.ViewObject.ShapeColor = color
        self.fco_bot.ViewObject.ShapeColor = color



#doc = FreeCAD.newDocument()
#ThinLinBearHouse (kcomp.LMEUU[10])
#ThinLinBearHouse (kcomp.LMEUU[10], mid_center=0)

# ----------- thin linear bearing housing with one rail to be attached

class ThinLinBearHouse (object):

    """

        Makes a housing for a linear bearing, but it is very thin
        and intented to be attached to 2 rail
        it has to parts, the lower and the upper part

         ________                           ______________
        | ::...::|                         | ::........:: |
        | ::   ::|    Upper part           |.::        ::.|
        |-::( )::|------                   |.::        ::.|  --> fc_slide_axis
        | ::...::|    Lower part           | ::........:: | 
        |_::___::|                         |_::________::_|
                                                   :
                                                   :
         _________                                 v
        |  0: :0  |                            fc_bot_axis
        | :     : |
        | :     : |
        | :     : |--------> fc_perp_axis
        | :     : |
        | :.....: |
        |__0:_:0__|
 
        
         ________                           ______________
        | ::...::|                         | ::........:: |
        | ::   ::|    Upper part           |.::        ::.|
        |-::( )::|------> fc_perp_axis     |.::   *axis_center = 1
        | ::...::|    Lower part           | ::........:: | 
        |_::___::|                         |_::___*____::_|
          |  |                                   axis_center = 0
          |  |
          V  V
          centered in any of these axes

                                            ______________
        1: axis_center=1                   | ::........:: |
           mid_center =1                   |.::        ::.|
        2: axis_center=0                   |.:4   1 --> fc_slide_axis
           mid_center =1                   | ::........:: | 
        3: axis_center=0                   | ::        :: |
           mid_center =0                   |_:3___2____::_|
        4: axis_center=1

        And 8 more posibilities:
        5: bolt_center = 1
        6: bolt_center = 0

          _________              
        |  5:6:   |             
        | :     : |
        | :     : |
        | :     : |--------> fc_perp_axis
        | :     : |
        | :.....: |
        |__0:_:0__|
          mid_center =0


    Arguments:
        d_lbear: dictionary with the dimensions of the linear bearing
        fc_slide_axis : FreeCAD.Vector with the direction of the slide
        fc_bot_axis: FreCAD.Vector with the direction of the bottom
        fc_perp_axis: FreCAD.Vector with the direction of the other
            perpendicular direction. Not useful unless bolt_center == 1
            if = V0 it doesn't matter
        axis_h = distance from the bottom to the rod axis
                0: take the minimum distance
                X: (any value) take that value, if it is smaller than the 
                   minimum it will raise an error and would not take that 
                   value
        axis_center = See picture, indicates the reference point
        mid_center  = See picture, indicates the reference point
        bolt_center  = See picture, indicates the reference point, if it is
                       on the bolt or on the axis
        pos = position of the reference point,

    Useful Attributes:
        n1_slide_axis: FreeCAD.Vector
        n1_bot_axis: FreeCAD.Vector
        n1_perp: FreeCAD.Vector
        axis_h: float
        boltcen_axis_dist: float
        boltcen_perp_dist: float
        + --- Dimensions:
        H, W, L
        + --- FreeCAD objects
        fco_top = top part of the linear bearing housing
        fco_bot = bottom part of the linear bearing housing

           ________                           ______________
          | ::...::|                         | ::........:: |
          | ::   ::|                         |.::        ::.|
          |-::( )::|---:                     |.::        ::.|  --> n1_slide_axis
          | ::...::|   +axis_h               | ::........:: | 
          |_::___::|   :                     | ::        :: |
          |_::___::|...:                     |_::________::_|
                                                     :
                                                     v
           _________                               n1_bot_axis
          |  0: :0  |                  
          | :     : |
          | :     : |........ --> n1_perp
          | :     : |   :
          | :.....: |   + boltcen_axis_dist
          |__0:_:0__|---:
             :   :
             :   :
             :...:
               +boltcen_perp_dist
         
                                             ...... L .......
                                             :              :
           ________....                      :______________:
          | ::...::|   :                     | ::........:: |
          | ::   ::|   :                     |.::        ::.|
          |-::( )::|   :                     |.::        ::.|  --> n1_slide_axis
          | ::...::|   + H                   | ::........:: | 
          |_::___::|...:                     |_::________::_|
          :        :
          :........:
              + 
              W


        bolts_side = 0            bolts_side = 1
         _________                
        |  0: :0  |                ___________ 
        | :     : |               | 0:     :0 |
        | :     : |               |  :     :  |
        | :     : |               |  :     :  |
        | :.....: |               |_0:_____:0_|
        |__0:_:0__|
 

    """

    MIN_SEP_WALL = 3. # min separation of a wall
    MIN2_SEP_WALL = 2. # min separation of a wall
    OUT_SEP_H = kparts.OUT_SEP_H # minimun separation of the linear bearing
    MTOL = kparts.MTOL
    MLTOL = kparts.MLTOL
    TOL_BEARING_L = kparts.TOL_BEARING_L
    # Radius to fillet the sides
    FILLT_R = kparts.FILLT_R

    def __init__(self, d_lbear,
                 fc_slide_axis = VX,
                 fc_bot_axis =VZN,
                 fc_perp_axis = V0,
                 axis_h = 0,
                 bolts_side = 1,
                 axis_center = 1,
                 mid_center  = 1,
                 bolt_center  = 0,
                 pos = V0,
                 name = 'thinlinbearhouse'
                ):

        self.name = name
        self.base_place = (0,0,0)
        # normalize, just in case
        n1_slide_axis = DraftVecUtils.scaleTo(fc_slide_axis,1)
        n1_bot_axis = DraftVecUtils.scaleTo(fc_bot_axis,1)
        n1_bot_axis_neg = DraftVecUtils.neg(n1_bot_axis)
        # vector perpendicular to the others
        v_cross = n1_slide_axis.cross(n1_bot_axis)
        if fc_perp_axis == V0:
            n1_perp = v_cross
        else:
            n1_perp =  DraftVecUtils.scaleTo(fc_perp_axis,1)
            if not fcfun.fc_isparal (v_cross,n1_perp):
                logger.debug("fc_perp_axis not perpendicular")
                n1_perp = v_cross

        self.rod_r = d_lbear['Di']/2.
        rod_r = self.rod_r
        self.bear_r = d_lbear['Di']
        if rod_r >= 6:
            BOLT_D = 4
        else:
            BOLT_D = 3  # M3 bolts

        doc = FreeCAD.ActiveDocument

        MIN_SEP_WALL = self.MIN_SEP_WALL
        MIN2_SEP_WALL = self.MIN2_SEP_WALL
        OUT_SEP_H = self.OUT_SEP_H
        # bolt dimensions:
        MTOL = self.MTOL
        MLTOL = self.MLTOL
        BOLT_HEAD_R = kcomp.D912_HEAD_D[BOLT_D] / 2.0
        BOLT_HEAD_L = kcomp.D912_HEAD_L[BOLT_D] + MTOL
        BOLT_HEAD_R_TOL = BOLT_HEAD_R + MTOL/2.0 
        BOLT_SHANK_R_TOL = BOLT_D / 2.0 + MTOL/2.0

        # bearing dimensions:
        bearing_l     = d_lbear['L'] 
        bearing_l_tol = bearing_l + self.TOL_BEARING_L
        bearing_d     = d_lbear['De']
        bearing_d_tol = bearing_d + 2.0 * self.MLTOL
        bearing_r     = bearing_d / 2.0
        bearing_r_tol = bearing_r + self.MLTOL

        # dimensions of the housing:
        # length on the direction of the sliding rod
        bolt2wall = fcfun.get_bolt_end_sep(BOLT_D, hasnut=0) 
        #housing_l = bearing_l_tol + 2 * (2*BOLT_HEAD_R_TOL + 2* MIN_SEP_WALL)
        if bolts_side == 1:
            # bolts on the side of the linear bearing
            # bolt2axis: distance from the center (axis) to the bolt center
            bolt2axis = fcfun.get_bolt_bearing_sep (BOLT_D, hasnut=0,
                                                    lbearing_r = bearing_r) 
            # it will be shorter (on L), and wider (on W)
            housing_l = bearing_l + 2 * MIN_SEP_WALL
            housing_w = 2 * (bolt2wall + bolt2axis)
        else:
            # bolts after the linear bearing
            # it will be longer (on L), and shorter (on W)
            bolt2axis = fcfun.get_bolt_bearing_sep (BOLT_D, hasnut=0,
                                     lbearing_r = rod_r ) 
                                    #lbearing_r = rod_r + kparts.ROD_SPACE_MIN) 
            housing_l = bearing_l + 4*bolt2wall #bolt_r is included in bolt2wall
            housing_w = max ((bearing_d + 2* MIN_SEP_WALL), 
                              2 * (bolt2wall + bolt2axis))

        print "housing_l: %", housing_l
        print "housing_w: %", housing_w

        # bolt distance
        # distance of the bolts to the center, on n1_slide_axis dir
        boltcen_axis_dist = housing_l/2. - bolt2wall
        # distance of the bolts to the center, on n1_perp dir
        boltcen_perp_dist = bolt2axis

        # minimum height of the housing 
        housing_min_h = bearing_d + 2 * OUT_SEP_H
        axis_min_h = housing_min_h / 2.
        print "min housing_h: %", housing_min_h
        if axis_h == 0:
            # minimum values
            housing_h = housing_min_h
            axis_h = axis_min_h
        elif axis_h >= axis_min_h:
            # the lower part will have longer height: axis_h
            # the upper part will be the minimum: axis_min_h
            housing_h = axis_h + axis_min_h
            axis_h = axis_h
        else: # the argument has an axis_h lower than the minimum possible
            logger.debug("axis_h %s cannot be smaller than %s",
                         str(axis_h), str(axis_min_h))
            housing_h = housing_min_h
            axis_h = axis_min_h

        # Atributes
        self.L = housing_l
        self.W = housing_w
        self.H = housing_h
        self.axis_h = axis_h
        self.boltcen_axis_dist = boltcen_axis_dist
        self.boltcen_perp_dist = boltcen_perp_dist
        self.n1_slide_axis = n1_slide_axis
        self.n1_bot_axis = n1_bot_axis
        self.n1_perp = n1_perp

        #To make the boxes, we take the reference on midcenter=1 and 
        # axis_center = 0. Point 2 on the drawing

        if mid_center == 0:
            # get the vector to the center:
            fc_tomidcenter = DraftVecUtils.scale(n1_slide_axis,
                                                 boltcen_axis_dist)
        else:
            fc_tomidcenter = V0

        if axis_center == 1:
            fc_tobottom = DraftVecUtils.scale(n1_bot_axis,axis_h)
            fc_toaxis = V0
        else:
            fc_tobottom = V0
            fc_toaxis = DraftVecUtils.scale(n1_bot_axis,-axis_h)

        if bolt_center == 1:
            fc_toaxis_perp = DraftVecUtils.scale(n1_perp, boltcen_perp_dist)
        else:
            fc_toaxis_perp = V0

        botcenter_pos = pos + fc_tomidcenter + fc_tobottom + fc_toaxis_perp

        # point 1 on the drawing
        axiscenter_pos = pos + fc_tomidcenter + fc_toaxis + fc_toaxis_perp
        # center on the top
        topcenter_pos = botcenter_pos + DraftVecUtils.scale(n1_bot_axis_neg,
                                                            housing_h)

        shp_housing = fcfun.shp_box_dir(box_w = housing_w,
                                     box_d = housing_l, #dir of n1_slide_axis
                                     box_h = housing_h,
                                     fc_axis_h = n1_bot_axis_neg,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = botcenter_pos)
        # fillet, small
        shp_block = fcfun.shp_filletchamfer_dir(shp_housing,
                                                fc_axis=fc_bot_axis,
                                                radius=2)

        # the rod hole
        shp_rod = fcfun.shp_cylcenxtr(r = rod_r + kparts.ROD_SPACE_MIN,
                                      h = housing_l,
                                      normal = n1_slide_axis,
                                      ch = 1, xtr_top = 1, xtr_bot=1,
                                      pos = axiscenter_pos)
        # the linear bearing hole
        shp_lbear = fcfun.shp_cylcenxtr(r = bearing_r_tol,
                                        h = bearing_l_tol,
                                        normal = n1_slide_axis,
                                        ch = 1, xtr_top = 1, xtr_bot=1,
                                        pos = axiscenter_pos)
        shp_rodlbear = shp_rod.fuse(shp_lbear)

        # 4 bolts 
        
        bolt_holes = []

        for vec_axis in [DraftVecUtils.scale(n1_slide_axis,boltcen_axis_dist),
                         DraftVecUtils.scale(n1_slide_axis,-boltcen_axis_dist)]:
            for vec_perp in [DraftVecUtils.scale(n1_perp,
                                                 boltcen_perp_dist),
                             DraftVecUtils.scale(n1_perp,
                                                 -boltcen_perp_dist)]:
                pos_i = topcenter_pos + vec_axis + vec_perp
                # the nut hole will be on the bottom side,
                
                shp_bolt = fcfun.shp_bolt_dir (
                                  r_shank = BOLT_SHANK_R_TOL,
                                  l_bolt  = housing_h,
                                  r_head  = BOLT_HEAD_R_TOL,
                                  l_head  = BOLT_HEAD_L,
                                  hex_head = 0,
                                  xtr_head=1,     xtr_shank=1,
                                  support=1,
                                  fc_normal = n1_bot_axis,
                                  fc_verx1=V0,
                                  pos = pos_i)
                bolt_holes.append(shp_bolt)

        shp_holes = shp_rodlbear.multiFuse(bolt_holes)       
        shp_lbear_housing = shp_block.cut(shp_holes)
        doc.recompute()
        # making 2 parts, intersection with 2 boxes:
        shp_box_top = fcfun.shp_box_dir(
                                     box_w = housing_w + 2,
                                     box_d = housing_l + 2, 
                                     box_h = housing_h - axis_h + 1,
                                     fc_axis_h = n1_bot_axis_neg,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = axiscenter_pos)
        shp_lbear_housing_top = shp_lbear_housing.common(shp_box_top)
        shp_lbear_housing_top = shp_lbear_housing_top.removeSplitter() 
        fco_lbear_top = doc.addObject("Part::Feature", name + '_top') 
        fco_lbear_top.Shape = shp_lbear_housing_top


        shp_box_bot = fcfun.shp_box_dir(
                                     box_w = housing_w + 2,
                                     box_d = housing_l + 2,
                                     # larger, just in case
                                     box_h = axis_h + 1,
                                     fc_axis_h = n1_bot_axis,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = axiscenter_pos)
        shp_lbear_housing_bot = shp_lbear_housing.common(shp_box_bot)
        shp_lbear_housing_bot = shp_lbear_housing_bot.removeSplitter()
        fco_lbear_bot = doc.addObject("Part::Feature", name + '_bot') 
        fco_lbear_bot.Shape = shp_lbear_housing_bot

        self.fco_top = fco_lbear_top
        self.fco_bot = fco_lbear_bot

    def BasePlace (self, position = (0,0,0)):
        self.base_place = position
        vpos = FreeCAD.Vector(position)
        self.fco_top.Placement.Base = vpos
        self.fco_bot.Placement.Base = vpos

    def color (self, color = (1,1,1)):
        self.fco_top.ViewObject.ShapeColor = color
        self.fco_bot.ViewObject.ShapeColor = color

    def export_stl (self, name = ""):
        #filepath = os.getcwd()
        if not name:
            name = self.name
        stlPath = filepath + "/freecad/stl/"
        stlFileName_top = stlPath + name + "_top" + ".stl"
        # any of these options are valid
        #Mesh.export([self.fco_top], stlFileName_top)
        self.fco_top.Shape.exportStl(stlFileName_top)
        stlFileName_bot = stlPath + name + "_bot" + ".stl"
        #Mesh.export([self.fco_bot], stlFileName_bot)
        self.fco_bot.Shape.exportStl(stlFileName_bot)



#doc = FreeCAD.newDocument()
#ThinLinBearHouse (kcomp.LMEUU[10])
#ThinLinBearHouse (kcomp.LMEUU[10], mid_center=1)
#ThinLinBearHouse (kcomp.LMEUU[10], bolts_side=0, mid_center=1)
#ThinLinBearHouse (kcomp.LMEUU[10], axis_h = 10, bolts_side=0, mid_center=1)
#ThinLinBearHouse (kcomp.LMEUU[10], axis_h = 15, bolts_side=0, mid_center=1)

#ThinLinBearHouse (kcomp.LMEUU[12], axis_h = 0, bolts_side=0, mid_center=1)
#ThinLinBearHouse (kcomp.LMELUU[12], axis_h = 0, bolts_side=0, mid_center=1)
#ThinLinBearHouse (kcomp.LMELUU[12], axis_h = 0, bolts_side=1, mid_center=1)
 
#ThinLinBearHouse (kcomp.LMEUU[12],
#                  fc_slide_axis = VY,
#                  fc_bot_axis = VZN,
#                  fc_perp_axis = VX,
#                  axis_h = 0, bolts_side=0, mid_center=1, bolt_center = 1)
#ThinLinBearHouse (kcomp.LMELUU[12],
#                  fc_slide_axis = VY,
#                  fc_bot_axis = VZN,
#                  fc_perp_axis = VXN,
#                  axis_h = 0, bolts_side=0, mid_center=1, bolt_center = 1)
#ThinLinBearHouse (kcomp.LMELUU[12],
#                  fc_slide_axis = VX,
#                  fc_bot_axis = VZN,
#                  fc_perp_axis = VYN,
#                  axis_h = 0, bolts_side=1,
#                  axis_center=0, mid_center=0, bolt_center = 1)

 

# ----------- Linear bearing housing 

class LinBearHouse (object):

    """
         Makes a housing for a linear bearing takes the dimensions
         from a dictionary, like the one defined in kcomp.py
         it has to parts, the lower and the upper part
 
          _____________                           ______________
         |::   ___   ::|                         |.::........::.|
         |:: /     \ ::|    Upper part           | ::        :: |
         |---|-----|---|------                   | ::        :: |
         |::  \___/  ::|    Lower part           |.::........::.| 
         |::_________::|                         |_::________::_|      
 
          _____________ 
         | 0 :     : 0 |
         |   :     :   |
         |   :     :   |
         |   :     :   |
         |   :     :   |
         |_0_:_____:_0_|
         



                                            ________________
        1: axis_center=1                   | : :........: : |
           mid_center =1                   |.: :        : :.|
        2: axis_center=0                   |.:4:   1 --------->: fc_slide_axis
           mid_center =1                   | : :........:.: | 
        3: axis_center=0                   | : :        : : |
           mid_center =0                   |_:3:___2____:_:_|
        4: axis_center=1
           mid_center =0

    """


    MTOL = kparts.MTOL
    MLTOL = kparts.MLTOL
    TOL_BEARING_L = kparts.TOL_BEARING_L
    # Radius to fillet the sides
    FILLT_R = kparts.FILLT_R


    def __init__(self, d_lbearhousing,
                 fc_slide_axis = VX,
                 fc_bot_axis =VZN,
                 axis_center = 1,
                 mid_center  = 1,
                 pos = V0,
                 name = 'linbearhouse'
                ):

        housing_l = d_lbearhousing['L']
        housing_w = d_lbearhousing['W']
        housing_h = d_lbearhousing['H']
        self.L = housing_l
        self.W = housing_w
        self.H = housing_h
        self.axis_h =  d_lbearhousing['axis_h']
        self.bolt_sep_l =  d_lbearhousing['bolt_sep_l']
        self.bolt_sep_w =  d_lbearhousing['bolt_sep_w']
        self.bolt_d =  d_lbearhousing['bolt_d']
        axis_h = self.axis_h
        self.name = name


        # normalize, just in case they are not
        n1_slide_axis = DraftVecUtils.scaleTo(fc_slide_axis,1)
        n1_bot_axis = DraftVecUtils.scaleTo(fc_bot_axis,1)
        n1_bot_axis_neg = DraftVecUtils.neg(n1_bot_axis)
        # vector perpendicular to the others
        n1_perp = n1_slide_axis.cross(n1_bot_axis)

        # get the linear bearing dictionary
        d_lbear = d_lbearhousing['lbear']
        self.rod_r = d_lbear['Di']/2.
        rod_r = self.rod_r
        self.bear_r = d_lbear['Di']
        bolt_d = d_lbearhousing['bolt_d']

        doc = FreeCAD.ActiveDocument
        # bolt dimensions:
        MTOL = self.MTOL
        MLTOL = self.MLTOL
        BOLT_HEAD_R = kcomp.D912_HEAD_D[bolt_d] / 2.0
        BOLT_HEAD_L = kcomp.D912_HEAD_L[bolt_d] + MTOL
        BOLT_HEAD_R_TOL = BOLT_HEAD_R + MTOL/2.0 
        BOLT_SHANK_R_TOL = bolt_d / 2.0 + MTOL/2.0

        # bearing dimensions:
        bearing_l     = d_lbear['L']
        bearing_l_tol = bearing_l + self.TOL_BEARING_L
        bearing_d     = d_lbear['De']
        bearing_d_tol = bearing_d + 2.0 * self.MLTOL
        bearing_r     = bearing_d / 2.0
        bearing_r_tol = bearing_r + self.MLTOL

        cenbolt_dist_l = d_lbearhousing['bolt_sep_l']/2.
        cenbolt_dist_w = d_lbearhousing['bolt_sep_w']/2.

        #To make the boxes, we take the reference on midcenter=1 and 
        # axis_center = 0. Point 2 on the drawing

        if mid_center == 0:
            # get the vector to the center:
            fc_tomidcenter = DraftVecUtils.scale(n1_slide_axis,cenbolt_dist_l)
        else:
            fc_tomidcenter = V0
        if axis_center == 1:
            fc_tobottom = DraftVecUtils.scale(n1_bot_axis,axis_h)
            fc_toaxis = V0
        else:
            fc_tobottom = V0
            fc_toaxis = DraftVecUtils.scale(n1_bot_axis,-axis_h)

        # point 2 on the drawing
        botcenter_pos = pos + fc_tomidcenter + fc_tobottom

        # point 1 on the drawing
        axiscenter_pos = pos + fc_tomidcenter + fc_toaxis

        # center on top
        topcenter_pos = botcenter_pos + DraftVecUtils.scale(n1_bot_axis_neg,
                                                            housing_h)

        shp_housing = fcfun.shp_box_dir(box_w = housing_w,
                                     box_d = housing_l, #dir of n1_slide_axis
                                     box_h = housing_h,
                                     fc_axis_h = n1_bot_axis_neg,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = botcenter_pos)

        # fillet the base:
        shp_housing_fllt = fcfun.shp_filletchamfer_dir(shp_housing,
                                                    fc_axis=fc_bot_axis,
                                                    radius=2)

        # the rod hole
        shp_rod = fcfun.shp_cylcenxtr(r = rod_r + kparts.ROD_SPACE_MIN,
                                      h = housing_l,
                                      normal = n1_slide_axis,
                                      ch = 1, xtr_top = 1, xtr_bot=1,
                                      pos = axiscenter_pos)
        # the linear bearing hole
        shp_lbear = fcfun.shp_cylcenxtr(r = bearing_r_tol,
                                        h = bearing_l_tol,
                                        normal = n1_slide_axis,
                                        ch = 1, xtr_top = 1, xtr_bot=1,
                                        pos = axiscenter_pos)
        shp_rodlbear = shp_rod.fuse(shp_lbear)

        # 4 bolts to join the upper and lower parts
        # distance of the bolts to the center, on n1_slide_axis dir

        bolt_holes = []

        for vec_axis in [DraftVecUtils.scale(n1_slide_axis,cenbolt_dist_l),
                         DraftVecUtils.scale(n1_slide_axis,-cenbolt_dist_l)]:
            for vec_perp in [DraftVecUtils.scale(n1_perp,
                                                 cenbolt_dist_w),
                             DraftVecUtils.scale(n1_perp,
                                                 -cenbolt_dist_w)]:
                pos_i = topcenter_pos + vec_axis + vec_perp
                # the nut hole will be on the bottom side,
                
                shp_bolt = fcfun.shp_bolt_dir (
                                  r_shank = BOLT_SHANK_R_TOL,
                                  l_bolt  = housing_h,
                                  r_head  = BOLT_HEAD_R_TOL,
                                  l_head  = BOLT_HEAD_L,
                                  hex_head = 0,
                                  xtr_head=1,     xtr_shank=1,
                                  support=1,
                                  fc_normal = n1_bot_axis,
                                  fc_verx1=V0,
                                  pos = pos_i)
                bolt_holes.append(shp_bolt)

        shp_holes = shp_rodlbear.multiFuse(bolt_holes)       
        shp_lbear_housing = shp_housing_fllt.cut(shp_holes)
        #Part.show(shp_lbear_housing)
        doc.recompute()
        # making 2 parts, intersection with 2 boxes:
        shp_box_top = fcfun.shp_box_dir(
                                     box_w = housing_w + 2,
                                     box_d = housing_l + 2, 
                                     box_h = housing_h - axis_h + 2,
                                     fc_axis_h = n1_bot_axis_neg,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = axiscenter_pos)
        shp_lbear_housing_top = shp_lbear_housing.common(shp_box_top)
        shp_lbear_housing_top = shp_lbear_housing_top.removeSplitter() 
        fco_lbear_top = doc.addObject("Part::Feature", name + '_top') 
        fco_lbear_top.Shape = shp_lbear_housing_top

        shp_box_bot = fcfun.shp_box_dir(
                                     box_w = housing_w + 2,
                                     box_d = housing_l + 2,
                                     # larger, just in case
                                     box_h = axis_h + 2,
                                     fc_axis_h = n1_bot_axis,
                                     fc_axis_d = n1_slide_axis,
                                     cw= 1, cd=1, ch=0,
                                     pos = axiscenter_pos)
        shp_lbear_housing_bot = shp_lbear_housing.common(shp_box_bot)
        shp_lbear_housing_bot = shp_lbear_housing_bot.removeSplitter()
        fco_lbear_bot = doc.addObject("Part::Feature", name + '_bot') 
        fco_lbear_bot.Shape = shp_lbear_housing_bot

        self.fco_top = fco_lbear_top
        self.fco_bot = fco_lbear_bot
        doc.recompute()

    def color (self, color = (1,1,1)):
        self.fco_top.ViewObject.ShapeColor = color
        self.fco_bot.ViewObject.ShapeColor = color

    def export_stl (self, name = ""):
        #filepath = os.getcwd()
        if not name:
            name = self.name
        stlPath = filepath + "/freecad/stl/"
        stlFileName_top = stlPath + name + "_top" + ".stl"
        # any of these options are valid
        #Mesh.export([self.fco_top], stlFileName_top)
        self.fco_top.Shape.exportStl(stlFileName_top)
        stlFileName_bot = stlPath + name + "_bot" + ".stl"
        #Mesh.export([self.fco_bot], stlFileName_bot)
        self.fco_bot.Shape.exportStl(stlFileName_bot)


#doc = FreeCAD.newDocument()
#LinBearHouse (kcomp.SCUU[10])
#LinBearHouse (kcomp.SCUU_Pr[10])


# ----------- thin linear bearing housing with asymmetrical distance
# between the bolts

class ThinLinBearHouseAsim (object):

    """
    There are:
        3 axis:          3 planes (normal to axis)   3 distances to plane
        - fc_fro_ax      - fro: front                - D: dep: depth
        - fc_bot_ax      - hor: horizontal)          - H: hei: height
        - fc_sid_ax      - lat: lateral (medial)     - W: wid: width

        The planes are on the center of the slidding rod (height and width),
        and on the middle of the piece (width)

        The 3 axis are perpendicular, but the cross product of 2 vectors may
        result on the other vector or its negative.

        fc_fro_ax points to the front of the figure, but it is symmetrical
           so it can point to the back
        fc_bot_ax points to the bottom of the figure (not symmetrical)
        fc_sid_ax points to the side of the figure. Not symmetrical if
           bolt2cen_wid_n or bolt2cen_wid_p are not zero

        Makes a housing for a linear bearing, but it is very thin
        and intented to be attached to 2 rail
        it has to parts, the lower and the upper part

         ________                           ______________
        | ::...::|                         | ::........:: |
        | ::   ::|    Upper part           |.::        ::.|
        |-::( )::|------ Horizontal plane  |.::        ::.|  --> fc_fro_ax
        | ::...::|    Lower part           | ::........:: | 
        |_::___::|                         |_::________::_|
                                                   :
                                                   :
         _________                                 v
        |  0: :0  |                            fc_bot_axis
        | :     : |
        | :     : |
        | :     : |--------> fc_sid_ax
        | :     : |
        | :.....: |
        |__0:_:0__|
 
        
         ________                           ______________
        | ::...::|                         | ::........:: |
        | ::   ::|    Upper part           |.::        ::.|
        |-::( )::|------> fc_sid_ax        |.::   *refcen_hei = 1
        | ::...::|    Lower part           | ::........:: | 
        |_::___::|                         |_::___*____::_|
          |  |                                   refcen_hei = 0
          |  |
          V  V
          centered in any of these axes
        refcen_hei: reference centered on the height
                  =1: the horizontal plane (height) is on the axis of the rod
                  =0: the horizontal plane is at the bottom 
        refcen_dep: reference centered on the depth
                  =1: the frontal plane (depth) is on the middle of the piece
                  =0: the frontal plane is at the bolts
        refcen_wid=1: reference centered on the width
                      the lateral plane (width) is on the medial axis, dividing
                      the piece on the right and left
                  =0: the lateral plane is at the bolts

                                            ______________
        1: refcen_hei=1                    | ::........:: |
           fro_center =1                   |.::        ::.|
        2: refcen_hei=0                    |.:4   1 --> fc_fro_ax
           fro_center =1                   | ::........:: | 
        3: refcen_hei=0                    | ::        :: |
           fro_center =0                   |_:3___2____::_|
        4: refcen_hei=1

        And 8 more posibilities:
        5: refcen_wid = 0
        6: refcen_wid = 1

          _________              
        |  5:6:   |             
        | :     : |
        | :     : |
        | :     : |--------> fc_sid_ax
        | :     : |
        | :.....: |
        |__0:_:0__|


    Arguments:
        d_lbear: dictionary with the dimensions of the linear bearing
        fc_fro_ax : FreeCAD.Vector with the direction of the slide
        fc_bot_ax: FreCAD.Vector with the direction of the bottom
        fc_sid_ax: FreCAD.Vector with the direction of the other
            perpendicular direction. Not useful unless refcen_wid == 0
            if = V0 it doesn't matter
        axis_h = distance from the bottom to the rod axis
                0: take the minimum distance
                X: (any value) take that value, if it is smaller than the 
                   minimum it will raise an error and would not take that 
                   value
        refcen_hei = See picture, indicates the reference point
        refcen_dep  = See picture, indicates the reference point
        refcen_wid  = See picture, indicates the reference point, if it is
                       on the bolt or on the axis
        pos = position of the reference point,

    Useful Attributes:
        nfro_ax: FreeCAD.Vector normalized fc_fro_ax
        nbot_ax: FreeCAD.Vector normalized fc_bot_ax
        nsid_ax: FreeCAD.Vector
        axis_h: float
        bolt2cen_dep: float
        bolt2cen_wid_n: float
        bolt2cen_wid_p: float
        bolt2bolt_wid: bolt2cen_wid_n + bolt2cen_wid_p
        + --- Dimensions:
        D: housing_d
        W: housing_w
        H: housing_h
        + --- FreeCAD objects
        fco_top = top part of the linear bearing housing
        fco_bot = bottom part of the linear bearing housing

           ________                           ______________
          | ::...::|                         | ::........:: |
          | ::   ::|                         |.::        ::.|
          |-::( )::|---:                     |.::        ::.|  --> nfro_ax
          | ::...::|   +axis_h               | ::........:: | 
          |_::___::|   :                     | ::        :: |
          |_::___::|...:                     |_::________::_|
                                                     :
                                                     v
           _________                               nbot_ax
          |  0: :0  |                  
          | :     : |
          | :     : |........ --> nsid_ax
          | :     : |   :
          | :.....: |   + boltcen_dep
          |__0:_:0__|---:
             : : :
             : : :
             :.:.:
              : + bolt2cen_wid_p: distance form the bolt to the center
              :     on the width dimension. The bolt on the positive side
              + bolt2cen_wid_n: distance form the bolt to the center
             :      on the width dimension. The bolt on the negative side
             :
             + if refcen_wid=0 the reference will be on the bolt2cen_wid_n
         
                                             ...... D .......
                                             :              :
           ________....                      :______________:
          | ::...::|   :                     | ::........:: |
          | ::   ::|   :                     |.::        ::.|
          |-::( )::|   :                     |.::        ::.|  --> nfro_ax
          | ::...::|   + H                   | ::........:: | 
          |_::___::|...:                     |_::________::_|
          :        :
          :........:
              + 
              W


        bolts_side = 0            bolts_side = 1
         _________                
        |  0: :0  |                ___________ 
        | :     : |               | 0:     :0 |
        | :     : |               |  :     :  |
        | :     : |               |  :     :  |
        | :.....: |               |_0:_____:0_|
        |__0:_:0__|
 

    """

    MIN_SEP_WALL = 3. # min separation of a wall
    MIN2_SEP_WALL = 2. # min separation of a wall
    OUT_SEP_H = kparts.OUT_SEP_H # minimun separation of the linear bearing
    MTOL = kparts.MTOL
    MLTOL = kparts.MLTOL
    TOL_BEARING_L = kparts.TOL_BEARING_L
    # Radius to fillet the sides
    FILLT_R = kparts.FILLT_R

    def __init__(self, d_lbear,
                 fc_fro_ax = VX,
                 fc_bot_ax =VZN,
                 fc_sid_ax = V0,
                 axis_h = 0,
                 bolts_side = 1,
                 refcen_hei = 1,
                 refcen_dep  = 1,
                 refcen_wid  = 1,
                 bolt2cen_wid_n = 0,
                 bolt2cen_wid_p = 0,
                 pos = V0,
                 name = 'thinlinbearhouse_asim'
                ):

        self.name = name
        self.base_place = (0,0,0)
        # normalize, just in case
        nfro_ax = DraftVecUtils.scaleTo(fc_fro_ax,1)
        nbot_ax = DraftVecUtils.scaleTo(fc_bot_ax,1)
        nbot_ax_n = DraftVecUtils.neg(nbot_ax)
        # vector perpendicular to the others
        v_cross = nfro_ax.cross(nbot_ax)
        if fc_sid_ax == V0:
            nsid_ax = v_cross
        else:
            nsid_ax =  DraftVecUtils.scaleTo(fc_sid_ax,1)
            if not fcfun.fc_isparal (v_cross,nsid_ax):
                logger.debug("fc_sid_ax not perpendicular")
                nsid_ax = v_cross

        self.rod_r = d_lbear['Di']/2.
        rod_r = self.rod_r
        self.bear_r = d_lbear['Di']
        if rod_r >= 6:
            BOLT_D = 4
        else:
            BOLT_D = 3  # M3 bolts

        doc = FreeCAD.ActiveDocument

        MIN_SEP_WALL = self.MIN_SEP_WALL
        MIN2_SEP_WALL = self.MIN2_SEP_WALL
        OUT_SEP_H = self.OUT_SEP_H
        # bolt dimensions:
        MTOL = self.MTOL
        MLTOL = self.MLTOL
        BOLT_HEAD_R = kcomp.D912_HEAD_D[BOLT_D] / 2.0
        BOLT_HEAD_L = kcomp.D912_HEAD_L[BOLT_D] + MTOL
        BOLT_HEAD_R_TOL = BOLT_HEAD_R + MTOL/2.0 
        BOLT_SHANK_R_TOL = BOLT_D / 2.0 + MTOL/2.0

        # bearing dimensions:
        bearing_l     = d_lbear['L'] 
        bearing_l_tol = bearing_l + self.TOL_BEARING_L
        bearing_d     = d_lbear['De']
        bearing_d_tol = bearing_d + 2.0 * self.MLTOL
        bearing_r     = bearing_d / 2.0
        bearing_r_tol = bearing_r + self.MLTOL

        # dimensions of the housing:
        # length on the direction of the sliding rod
        bolt2wall = fcfun.get_bolt_end_sep(BOLT_D, hasnut=0) 
        #housing_d = bearing_l_tol + 2 * (2*BOLT_HEAD_R_TOL + 2* MIN_SEP_WALL)
        if bolts_side == 1:
            # bolts on the side of the linear bearing
            # bolt2cen_wid: distance from the center (axis) to the bolt center
            bolt2cen_wid = fcfun.get_bolt_bearing_sep (BOLT_D, hasnut=0,
                                                    lbearing_r = bearing_r) 

        else:
            # bolts after the linear bearing (front axis)
            # it will be longer (on D), and shorter (on W)
            bolt2cen_wid = fcfun.get_bolt_bearing_sep (BOLT_D, hasnut=0,
                                     lbearing_r = rod_r ) 
                                    #lbearing_r = rod_r + kparts.ROD_SPACE_MIN) 

        # check if it is going to be wider
        if bolt2cen_wid_n > 0:
            if bolt2cen_wid_n < bolt2cen_wid:
                logger.debug("bolt2cen_wid_n smaller than minimum")
                bolt2cen_wid_n = bolt2cen_wid
            else:
                bolt2cen_wid_n = bolt2cen_wid_n
        else:
            bolt2cen_wid_n = bolt2cen_wid
        if bolt2cen_wid_p > 0:
            if bolt2cen_wid_p < bolt2cen_wid:
                logger.debug("bolt2cen_wid_p smaller than minimum")
                bolt2cen_wid_p = bolt2cen_wid
            else:
                bolt2cen_wid_p = bolt2cen_wid_p
        else:
            bolt2cen_wid_p = bolt2cen_wid

        if bolts_side == 1:
            # it will be shorter (on D), and wider (on W)
            housing_d = bearing_l + 2 * MIN_SEP_WALL
            housing_w = 2 * bolt2wall + bolt2cen_wid_n + bolt2cen_wid_p
        else: 
            housing_d = bearing_l + 4*bolt2wall #bolt_r is included in bolt2wall
            housing_w = max ((bearing_d + 2* MIN_SEP_WALL), 
                              2 * bolt2wall + bolt2cen_wid_n + bolt2cen_wid_p)


        print "housing_d: %", housing_d
        print "housing_w: %", housing_w

        # bolt distance
        # distance of the bolts to the center, on nfro_ax dir
        bolt2cen_dep = housing_d/2. - bolt2wall

        # minimum height of the housing 
        housing_min_h = bearing_d + 2 * OUT_SEP_H
        axis_min_h = housing_min_h / 2.
        print "min housing_h: %", housing_min_h
        if axis_h == 0:
            # minimum values
            housing_h = housing_min_h
            axis_h = axis_min_h
        elif axis_h >= axis_min_h:
            # the lower part will have longer height: axis_h
            # the upper part will be the minimum: axis_min_h
            housing_h = axis_h + axis_min_h
            axis_h = axis_h
        else: # the argument has an axis_h lower than the minimum possible
            logger.debug("axis_h %s cannot be smaller than %s",
                         str(axis_h), str(axis_min_h))
            housing_h = housing_min_h
            axis_h = axis_min_h

        # Atributes
        self.D = housing_d
        self.W = housing_w
        self.H = housing_h
        self.axis_h = axis_h
        self.bolt2cen_dep = bolt2cen_dep
        self.bolt2cen_wid_n = bolt2cen_wid_n
        self.bolt2cen_wid_p = bolt2cen_wid_p
        self.bolt2bolt_wid = bolt2cen_wid_p + bolt2cen_wid_n
        self.nfro_ax = nfro_ax
        self.nbot_ax = nbot_ax
        self.nsid_ax = nsid_ax

        #To make the boxes, we take the reference on midcenter=1 and 
        # refcen_hei = 0. Point 2 on the drawing

        if refcen_dep == 0: #the center is not on frontal plane
            # get the vector from the reference center to the center:
            fc_ref2cen_dep = DraftVecUtils.scale(nfro_ax,
                                                 bolt2cen_dep)
        else:
            fc_ref2cen_dep = V0

        if refcen_hei == 1:
            fc_ref2bot_hei = DraftVecUtils.scale(nbot_ax,axis_h)
            fc_ref2cen_hei = V0
        else:
            fc_ref2bot_hei = V0
            fc_ref2cen_hei = DraftVecUtils.scale(nbot_ax,-axis_h)

        if refcen_wid == 0:
            fc_ref2cen_wid = DraftVecUtils.scale(nsid_ax, bolt2cen_wid_n)
            # since it is not symmetrical the side n and the side p, we
            # another center for the housing, not for the rod
            fc_ref2houscen_wid = DraftVecUtils.scale(nsid_ax,
                                        (bolt2cen_wid_n + bolt2cen_wid_p)/2.)
        else:
            fc_ref2cen_wid = V0
            # since it is not symmetrical the side n and the side p, we
            # another center for the housing, not for the rod
            fc_ref2houscen_wid = DraftVecUtils.scale(nsid_ax,
                                        (bolt2cen_wid_p - bolt2cen_wid_n)/2.)


        botcenter_pos = pos + fc_ref2cen_dep + fc_ref2bot_hei + fc_ref2cen_wid
        bothouscenter_pos =  (  pos + fc_ref2cen_dep + fc_ref2bot_hei
                              + fc_ref2houscen_wid)

        # point 1 on the drawing
        axiscenter_pos = pos + fc_ref2cen_dep + fc_ref2cen_hei + fc_ref2cen_wid
        axishouscenter_pos = (  pos + fc_ref2cen_dep + fc_ref2cen_hei
                              + fc_ref2houscen_wid )
        # center on the top
        topcenter_pos = botcenter_pos + DraftVecUtils.scale(nbot_ax_n,
                                                            housing_h)

        shp_housing = fcfun.shp_box_dir(box_w = housing_w,
                                        box_d = housing_d, #dir of nfro_ax
                                        box_h = housing_h,
                                        fc_axis_h = nbot_ax_n,
                                        fc_axis_d = nfro_ax,
                                        cw= 1, cd=1, ch=0,
                                        pos = bothouscenter_pos)
        # fillet, small
        shp_block = fcfun.shp_filletchamfer_dir(shp_housing,
                                                fc_axis=fc_bot_ax,
                                                radius=2)

        # the rod hole
        shp_rod = fcfun.shp_cylcenxtr(r = rod_r + kparts.ROD_SPACE_MIN,
                                      h = housing_d,
                                      normal = nfro_ax,
                                      ch = 1, xtr_top = 1, xtr_bot=1,
                                      pos = axiscenter_pos)
        # the linear bearing hole
        shp_lbear = fcfun.shp_cylcenxtr(r = bearing_r_tol,
                                        h = bearing_l_tol,
                                        normal = nfro_ax,
                                        ch = 1, xtr_top = 1, xtr_bot=1,
                                        pos = axiscenter_pos)
        shp_rodlbear = shp_rod.fuse(shp_lbear)

        # 4 bolts 
        
        bolt_holes = []

        for vec_axis in [DraftVecUtils.scale(nfro_ax,bolt2cen_dep),
                         DraftVecUtils.scale(nfro_ax,-bolt2cen_dep)]:
            for vec_perp in [DraftVecUtils.scale(nsid_ax,
                                                 bolt2cen_wid_p),
                             DraftVecUtils.scale(nsid_ax,
                                                 -bolt2cen_wid_n)]:
                pos_i = topcenter_pos + vec_axis + vec_perp
                # the nut hole will be on the bottom side,
                
                shp_bolt = fcfun.shp_bolt_dir (
                                  r_shank = BOLT_SHANK_R_TOL,
                                  l_bolt  = housing_h,
                                  r_head  = BOLT_HEAD_R_TOL,
                                  l_head  = BOLT_HEAD_L,
                                  hex_head = 0,
                                  xtr_head=1,     xtr_shank=1,
                                  support=1,
                                  fc_normal = nbot_ax,
                                  fc_verx1=V0,
                                  pos = pos_i)
                bolt_holes.append(shp_bolt)

        shp_holes = shp_rodlbear.multiFuse(bolt_holes)       
        shp_lbear_housing = shp_block.cut(shp_holes)
        doc.recompute()
        # making 2 parts, intersection with 2 boxes:
        shp_box_top = fcfun.shp_box_dir(
                                     box_w = housing_w + 2,
                                     box_d = housing_d + 2, 
                                     box_h = housing_h - axis_h + 1,
                                     fc_axis_h = nbot_ax_n,
                                     fc_axis_d = nfro_ax,
                                     cw= 1, cd=1, ch=0,
                                     pos = axishouscenter_pos)
        shp_lbear_housing_top = shp_lbear_housing.common(shp_box_top)
        shp_lbear_housing_top = shp_lbear_housing_top.removeSplitter() 
        fco_lbear_top = doc.addObject("Part::Feature", name + '_top') 
        fco_lbear_top.Shape = shp_lbear_housing_top


        shp_box_bot = fcfun.shp_box_dir(
                                     box_w = housing_w + 2,
                                     box_d = housing_d + 2,
                                     # larger, just in case
                                     box_h = axis_h + 1,
                                     fc_axis_h = nbot_ax,
                                     fc_axis_d = nfro_ax,
                                     cw= 1, cd=1, ch=0,
                                     pos = axishouscenter_pos)
        shp_lbear_housing_bot = shp_lbear_housing.common(shp_box_bot)
        shp_lbear_housing_bot = shp_lbear_housing_bot.removeSplitter()
        fco_lbear_bot = doc.addObject("Part::Feature", name + '_bot') 
        fco_lbear_bot.Shape = shp_lbear_housing_bot

        self.fco_top = fco_lbear_top
        self.fco_bot = fco_lbear_bot

    def BasePlace (self, position = (0,0,0)):
        self.base_place = position
        vpos = FreeCAD.Vector(position)
        self.fco_top.Placement.Base = vpos
        self.fco_bot.Placement.Base = vpos

    def color (self, color = (1,1,1)):
        self.fco_top.ViewObject.ShapeColor = color
        self.fco_bot.ViewObject.ShapeColor = color

    def export_stl (self, name = ""):
        #filepath = os.getcwd()
        if not name:
            name = self.name
        stlPath = filepath + "/freecad/stl/"
        stlFileName_top = stlPath + name + "_top" + ".stl"
        self.fco_top.Shape.exportStl(stlFileName_top)
        stlFileName_bot = stlPath + name + "_bot" + ".stl"
        self.fco_bot.Shape.exportStl(stlFileName_bot)


#doc = FreeCAD.newDocument()
#ThinLinBearHouseAsim (kcomp.LMELUU[12],
#                  fc_fro_ax = VX,
#                  fc_bot_ax = VZN,
#                  fc_sid_ax = VYN,
#                  axis_h = 0, bolts_side=0,
#                  refcen_hei=1, refcen_dep=1, refcen_wid = 1,
#                  bolt2cen_wid_n = 0,
#                  bolt2cen_wid_p = 25)



# ----------- NemaMotorHolder

class NemaMotorHolder (object):

    """



         __________________
        ||                ||
        || O     __     O ||
        ||    /      \    ||
        ||   |   1    |   ||
        ||    \      /    ||
        || O     __     O ||
        ||________________|| .....
        ||_______2________|| ..... wall_thick



         ________3_________        3_________________ ....
        |  ::  :    :  ::  |       |      :     :    |    + motor_thick
        |__::__:_1__:__::__|       2......:..1..:....|....:..........> fc_axis_n
        ||                ||       | :              /
        || ||          || ||       | :           /
        || ||          || ||       | :        /
        || ||          || ||       | :      /
        || ||          || ||       | :   /
        ||________________||       |_: /
        ::                         :                 :
         + reinf_thick             :....tot_d........:


                fc_axis_h
                 :
         ________:_________ ..................................
        |  ::  :    :  ::  |                                  :
        |__::__:_1__:__::__|....................              :
        ||                ||....+ motor_min_h  :              :
        || ||          || ||                   :              +tot_h
        || ||          || ||                   + motor_max_h  :
        || ||          || ||                   :              :
        || ||          || ||...................:              :
        ||________________||..................................:
        :                  :
        :.....tot_w........:

        
       1: ref_axis = 1 & ref_bolt = 0 
       2: ref_axis = 0 & ref_bolt = 0 
       --3: ref_axis = 0 & ref_bolt = 0 

    """

    def __init__ (self,
                  nema_size = 17,
                  wall_thick = 4.,
                  motor_thick = 4.,
                  reinf_thick = 4.,
                  motor_max_h = 5.,
                  motor_min_h =10.,
                  motor_xtr_space = 2., # counting on one side
                  bolt_wall_d = 4.,
                  chmf_r = 1.,
                  fc_axis_h = VZ,
                  fc_axis_n = VX,
                  #fc_axis_p = VY,
                  ref_axis = 1, 
                  #ref_bolt = 0,
                  pos = V0,
                  wfco = 1,
                  name = 'nema_holder'):

               doc = FreeCAD.ActiveDocument

        # normalize de axis
        axis_h = DraftVecUtils.scaleTo(fc_axis_h,1)
        axis_n = DraftVecUtils.scaleTo(fc_axis_n,1)
        #axis_p = axis_h.cross(axis_n) #perpendicular
        axis_n_n = axis_n.negative()
        axis_h_n = axis_h.negative()

        motor_w = kcomp.NEMA_W[nema_size]

        self.axis_h = axis_h
        self.axis_n = axis_n
        self.pos = pos

        bolthead_l = kcomp.D912[bolt_wall_d]['head_l']
        washer_thick = kcomp.WASH_D125_T[bolt_wall_d]

        # making the big box that will contain everything and will be cut
        tot_h = motor_thick + motor_max_h + 2 * bolt_wall_d
        tot_w = 2* reinf_thick + motor_w + 2 * motor_xtr_space
        tot_d = (   wall_thick + motor_w + motor_xtr_space
                  + bolthead_l + washer_thick)

        # getting the offset of the reference
        # distance of the motor axis to de wall
        motax2wall_dist = (wall_thick + motor_w/2. + motor_xtr_space
                               + bolthead_l + washer_thick)
        if ref_axis == 1:
            ref2motax = V0  #point 1
            ref2motaxwall = DraftVecUtils.scale(axis_n_n, motax2wall_dist) 
        else:
            ref2motax = DraftVecUtils.scale(axis_n, motax2wall_dist)
            ref2motaxwall = V0 # point 2

        # point centered on the symmetrical plane, on top of axis_h and
        # on the wall (pint 3)
        ref2topwallcent = (  ref2motaxwall
                             + DraftVecUtils.scale(axis_h, motor_thick))
        topwallcent_pos = pos + ref2topwallcent

        # make the whole box:
        shp_box = fcfun.shp_box_dir (box_w = tot_w,
                                     box_d = tot_d,
                                     box_h = tot_h,
                                     fc_axis_h = axis_h_n,
                                     fc_axis_d = axis_n,
                                     cw=1, cd=0, ch=0, pos = topwallcent_pos)

        # chamfer of the box to make a 'triangular' reinforcement
        chmf_reinf_r = min(tot_d- wall_thick, tot_h-motor_thick)
        shp_box = fcfun.shp_filletchamfer_dir(shp_box, axis_p, fillet=0,
                                              radius = chmf_reinf_r)
        doc.recompute()
 

        shp_box = shp_motorholder
        if wfco == 1:
            # a freeCAD object is created
            fco_motorholder = doc.addObject("Part::Feature", name )
            fco_motorholder.Shape = shp_motorholder
            self.fco = fco_motorholder




doc = FreeCAD.newDocument()
NemaMotorHolder ( self,
                  nema_size = 17,
                  wall_thick = 4.,
                  motor_thick = 4.,
                  reinf_thick = 4.,
                  motor_max_h = 5.,
                  motor_min_h =10.,
                  motor_xtr_space = 2., # counting on one side
                  bolt_wall_d = 4.,
                  chmf_r = 1.,
                  fc_axis_h = VZ,
                  fc_axis_n = VX,
                  #fc_axis_p = VY,
                  ref_axis = 1, 
                  #ref_bolt = 0,
                  pos = V0,
                  wfco = 1,
                  name = 'nema_holder'):


# ----------- Linear bearing housing 

class Plate3CageCubes (object):

    """
    Creates a plate to join 3 Cage Cubes

                          fc_top_ax   fc_fro_ax
                               :      /
        _______________________:_____/__________..............
       | O            O        :  O /         O |--top_h/2   + top_h
       |..........  ____  .....:..... ..........|..:.........:
       |o  ___  o: |SQR | :o  _:_ /o: :o  ___  o|
       |  /   \  : |____| :  / :.\..:.:. /...\..|..... fc_sid_ax
       |  \___/  :        :  \___/  : :  \___/  |
       |o_______o:________:o_______o:_:o_______o|
          :   :    :....:
          :. .:      + sqr_w
            + hole_d
                             fc_fro_ax
                               :
       ___________        _____:_____ __________ 
       |o  ___  o|        |o  _:_ /o| |o  ___  o|  --> cage cubes
       |  /   \  |        |  / : \  | |  /   \  |
       |  \___/  |        |  \_:_/  | |  \___/  |
       |o_______o|________|____:___ |_|o_______o|........... fc_sid_ax
       |  :   :              :   :       :   :  |  + thick
       |__:___:______________:___:_______:___:__|..:
            :                  :           :
            :.... cube_dist_n..:...........:
                                     + cube_dist_p



    Thruholes of the bolts are not drawn

    The position of the plate: pos, is referenced to the center of the
    hole of the middle plate.

    There are 3 axes:
        - fc_fro_ax: FreeCAD.Vector pointing to the direction of the cage
          cubes, and it is on the surface touching the cubes
        - fc_top_ax: FreeCAD.Vector pointing to the top, where there is an
          extra length (top_h) to hold an aluminum profile
        - fc_sid_ax: FreeCAD.Vector pointing to the side p (positive)

        ________________________________________
       | O            O           O           O |
       |..........        ........... ..........|
       |o  ___  o:        :o  ___  o: :o  ___  o|
       |  /   \  :        :  /   \  : :  /   \  |
       |  \___/  :        :  \___/  : :  \___/  |
       |o_______o:________:_________:_:o_______o|
            :                  :           :
            :.... cube_dist_n..:           :

    Arguments:
        d_cagecube: dictionary with the dimensions of the cage cube
        thick: thickness of the plate, in mm
        cube_dist_n: distance from center to center of the middle cage cube
               to the cube in opposite direction (negative) of fc_sid_ax
        cube_dist_p: distance from center to center of the middle cage cube
               to the cube in the same direction (positive) of fc_sid_ax
        top_h: length of the extra part on top of the plate to hold a
               aluminum profile or whatever
        cube_face: indicates which face of the cube is facing the plate.
               There are 3 possible faces (defined in kparts.py):
               THRUHOLE (1) : the big hole is a thruhole without threads
               THRURODS (2) : the face has 4 thruholes for the rods
               RODSCREWS(3): the face has 4 tapped holes for screwing the
                            end of the rods
        hole_d: diameter of the central thruhole facing the plate.
               0: take the value of the cagecube hole
               X: take this value, since there may be something attached,
                  such as a tubelens, which may have a ring that makes
                  necesary to have larger diameter hole
               -1: no hole
        boltatt_n: number of bolt holes on the extra top side
        boltatt_d: diameter of the bolt holes on the top side
        sqr_h: height of the square hole done if there is space between cubes
               if 0: no rectangle.
               The rectangle only will be on the larger space between cubes
        sqr_w: width of the square(rectangle) hole done if there is space
               between cubes. It is made in line with the top of the cubes
               centered on the width space
               if 0: takes all the space of the space
        fc_fro_ax: FreeCAD.Vector pointing to the direction of the cage
               cubes, and it is on the surface touching the cubes
        fc_top_ax: FreeCAD.Vector pointing to the top, where there is an
               extra length (top_h) to hold an aluminum profile
        fc_sid_ax: FreeCAD.Vector pointing to the side p (positive)
        fillet_r: radius of the fillet of the corners, if 0, no fillet
        holes_tol : Add tolerance for the holes, it seems that even when milled
                it is needed
        moreboltholes : if more bolt holes are made to attach things
        pos: FreeCAD.Vector with the position of the reference. 
               Center of the hole of the middle plate, on the face touching
               the cagecube
        name: str with the name of the FreeCAD.Object

    """

    ROD_SCREWS = kcomp_optic.ROD_SCREWS
    THRU_RODS = kcomp_optic.THRU_RODS
    THRU_HOLE = kcomp_optic.THRU_HOLE

    def __init__(self,
                 d_cagecube,
                 thick,
                 cube_dist_n,
                 cube_dist_p,
                 top_h = 10,
                 #which side of the cube faces the plate
                 cube_face = kcomp_optic.ROD_SCREWS,
                 hole_d = 0, 
                 boltatt_n = 6, 
                 boltatt_d = 3, 
                 sqr_h = 0,
                 sqr_w = 0,
                 fc_fro_ax = VX,
                 fc_top_ax = VZ,
                 fc_sid_ax = VY,
                 fillet_r = 1.,
                 holes_tol = 0,
                 moreboltholes = 0,
                 pos = V0,
                 name = 'Plate3CageCubes'
                ):

        self.d_cagecube = d_cagecube
        self.name = name
        cage_w = d_cagecube['L']

        #get normalized vectors
        nfro_ax = DraftVecUtils.scaleTo(fc_fro_ax,1)
        nfro_ax_n = nfro_ax.negative()
        ntop_ax = DraftVecUtils.scaleTo(fc_top_ax,1)
        nsid_ax = DraftVecUtils.scaleTo(fc_sid_ax,1)

        # calculate the plate dimensions
        # and its center
        #  ________________________________________.............
        # | O            O           O           O |  + top_h  :
        # |..........        ........... ..........|..:        :
        # |o  ___  o:        :o  _ _  o: :o  ___  o|  :        + plate_h
        # |  /   \  :        :  / : \  : :  /   \  |  + cage_w :
        # |  \___/  :        :  \___/  : :  \___/  |  :        :
        # |o_______o:________:o_______o:_:o_______o|..:........:
        # :    :                  :           :    :
        # :    :.... cube_dist_n..:...........:    :
        # :                          +cube_dist_p  :
        # :......plate_w...........................: 


        plate_w = cube_dist_n + cube_dist_p + cage_w
        plate_h = cage_w + top_h



        # the center of the plate on the fc_top_ax and tc_sid_ax vectors
        platecen_pos = ( pos
                  + DraftVecUtils.scale(ntop_ax,top_h/2.)
                  + DraftVecUtils.scale(nsid_ax,(cube_dist_p-cube_dist_n)/2.))

        shp_box = fcfun.shp_box_dir (box_w = plate_w,
                                     box_d = plate_h,
                                     box_h = thick,
                                     fc_axis_h = nfro_ax_n,
                                     fc_axis_d = ntop_ax,
                                     cw=1, cd=1, ch=0,
                                     pos = platecen_pos)

        if fillet_r > 0:
            # fillet the four corners
            shp_box = fcfun.shp_filletchamfer_dir(shp_box, fc_axis = fc_fro_ax,
                                              fillet = 1, radius = fillet_r)

        # diameter of the holes of the cubes:
        if cube_face == self.ROD_SCREWS:
            cube_hole_d = d_cagecube['thru_thread_d'] + holes_tol
            bolt_d = d_cagecube['rod_thread_d'] + holes_tol
        elif cube_face == self.THRU_RODS:
            cube_hole_d = d_cagecube['thru_thread_d'] + holes_tol
            bolt_d = d_cagecube['thru_rod_d'] + holes_tol
        elif cube_face == self.THRU_HOLE:
            cube_hole_d = d_cagecube['thru_hole_d'] + holes_tol
            bolt_d = d_cagecube['rod_thread_d'] + holes_tol
        else:
            logger.debug("cube_face not supported %s", cube_face)
            cube_hole_d = d_cagecube['thru_thread_d'] + holes_tol
            bolt_d = d_cagecube['rod_thread_d'] + holes_tol

        bolt_r = bolt_d/2.

        # position of the cage on the positive and negative sides:
        pos_cage_p = pos + DraftVecUtils.scale(nsid_ax,cube_dist_p)
        pos_cage_n = pos + DraftVecUtils.scale(nsid_ax,-cube_dist_n)
        holes_list = []
        if hole_d >= 0: #if <0: no hole
            if hole_d == 0:
                hole_d = cube_hole_d
            # check if the diameter is larger than the cage diameter
            elif hole_d < cube_hole_d:
                logger.debug("hole_d smaller than cube hole"); 
                logger.debug("taking the minimum %s", cube_hole_d)
                hole_d = cube_hole_d
            else:
                hole_d = hole_d

            hole_r = hole_d/2.
            # central big hole (it is on pos)
            shp_bighole_cen = fcfun.shp_cylcenxtr (r= hole_r, h = thick,
                                                   normal = nfro_ax_n,
                                                   ch=0, xtr_top=1, xtr_bot=1,
                                                   pos = pos)

            shp_bighole_p = fcfun.shp_cylcenxtr (r= hole_r, h = thick,
                                                 normal = nfro_ax_n,
                                                 ch=0, xtr_top=1, xtr_bot=1,
                                                 pos = pos_cage_p)

            shp_bighole_n = fcfun.shp_cylcenxtr (r= hole_r, h = thick,
                                                 normal = nfro_ax_n,
                                                 ch=0, xtr_top=1, xtr_bot=1,
                                                 pos = pos_cage_n)
            # add the large holes to the list
            holes_list.extend([shp_bighole_cen, shp_bighole_p,
                               shp_bighole_n])

        ################

        cagebolt_sep = d_cagecube['thru_rod_sep']
        cagebolt2cen = cagebolt_sep /2.
        bolt_pos_top_p = DraftVecUtils.scale(ntop_ax, cagebolt2cen)
        bolt_pos_top_n = DraftVecUtils.scale(ntop_ax, -cagebolt2cen)
        bolt_pos_sid_p = DraftVecUtils.scale(nsid_ax, cagebolt2cen)
        bolt_pos_sid_n = DraftVecUtils.scale(nsid_ax, -cagebolt2cen)

        for pos_i in [pos, pos_cage_p, pos_cage_n]:
            for top_add in [bolt_pos_top_p, bolt_pos_top_n]:
                for sid_add in [bolt_pos_sid_p, bolt_pos_sid_n]:
                    pos_boltcage = pos_i + top_add + sid_add
                    shp_boltcage = fcfun.shp_cylcenxtr (r= bolt_r, h = thick,
                                             normal = nfro_ax_n,
                                             ch=0, xtr_top=1, xtr_bot=1,
                                             pos = pos_boltcage)
                    holes_list.append(shp_boltcage)

        # bolts to attach the aluminum profile:
        if boltatt_n < 2:
            boltatt_n = 2
        # the first and the last bolt will be at the same fc_sid_ax as the
        # cage bols.
        # the distance between the first and the last is:
        boltatt_dist =  cube_dist_n + cube_dist_p + cagebolt_sep
        boltatt_sep = boltatt_dist / (boltatt_n - 1)
        vec_boltatt_add = DraftVecUtils.scale(nsid_ax, boltatt_sep)
        #The first bolt will be:
        boltatt_pos = (   pos_cage_n
                        + DraftVecUtils.scale(nsid_ax, -cagebolt2cen)
                        + DraftVecUtils.scale(ntop_ax, cage_w/2. + top_h/2.))
        boltatt_r = boltatt_d/2.
        for it_boltatt in range(boltatt_n):
            shp_boltatt = fcfun.shp_cylcenxtr (r= boltatt_r, h = thick,
                                             normal = nfro_ax_n,
                                             ch=0, xtr_top=1, xtr_bot=1,
                                             pos = boltatt_pos)
            boltatt_pos = boltatt_pos + vec_boltatt_add
            holes_list.append(shp_boltatt)

        if cube_dist_n > cube_dist_p :
            # large space central vector
            larg_sp_c_vec = DraftVecUtils.scale(nsid_ax,-cube_dist_n/2.)
            shor_sp_c_vec = DraftVecUtils.scale(nsid_ax,cube_dist_p/2.)
            # width of the large space
            larg_sp_w = cube_dist_n - cage_w
            shor_sp_w = cube_dist_p - cage_w
        else:
            larg_sp_c_vec = DraftVecUtils.scale(nsid_ax,cube_dist_p/2.)
            shor_sp_c_vec = DraftVecUtils.scale(nsid_ax,-cube_dist_n/2.)
            # width of the large space
            larg_sp_w = cube_dist_p - cage_w
            shor_sp_w = cube_dist_n - cage_w

        # square (rectangle holes):
        #  a rectangle on the larger distance between the cubes
        if sqr_h > 0: 
            #  ________________________________________
            # | O            O           O           O |
            # |.......... _____                ........|
            # |o  ___  o: |_:_| larg_sp_c_pos    ___  o|
            # |  /   \  :   :<--------: \  : :  /   \  |
            # |  \___/  :        :  \___/  : :  \___/  |
            # |o_______o:________:o_______o:_:o_______o|
            # vector of the distance from the center to the square

            pos_sqr = (pos + larg_sp_c_vec +
                             DraftVecUtils.scale(ntop_ax,cage_w/2. - sqr_h/2.))
            if sqr_w == 0: # square width will be the total distance
                sqr_w = larg_sp_w

            # since in dont have shp_box_dir_extr, I put extra depth
            # double thick because we need extra and I havent brought it back
            # then a little more to cut the other
            # 1 mm tolerance. 0.5 on each side
            shp_sqr = fcfun.shp_box_dir (box_w = sqr_w + 1., # 1mm tolerance
                                         box_d = 2.1 * thick,
                                         box_h = sqr_h + 1.,
                                         fc_axis_h = ntop_ax,
                                         fc_axis_d = nfro_ax_n,
                                         cw=1, cd=1, ch=1, pos= pos_sqr)
            holes_list.append(shp_sqr)
            

        # more bolt holes ( holes):
        if moreboltholes == 1: 
            #  ________________________________________
            # | O            O           O           O |
            # |........................................|
            # |o  ___  o:                  : :o  ___  o|
            # |  /   \  :   :<--------: \  : :  /   \  |
            # |  \___/  : O    O :  \___/  : :  \___/  |
            # |o_______o:________:o_______o:_:o_______o|

            # holes on the shorter side
            pos_bolt = pos + bolt_pos_top_n + shor_sp_c_vec
            shp_bolt = fcfun.shp_cylcenxtr (r= bolt_r, h = thick,
                                                normal = nfro_ax_n,
                                                ch=0, xtr_top=1, xtr_bot=1,
                                                pos = pos_bolt)
            holes_list.append(shp_bolt)
            pos_bolt = ( pos + bolt_pos_top_n + shor_sp_c_vec +
                             DraftVecUtils.scale(ntop_ax,20))
            shp_bolt = fcfun.shp_cylcenxtr (r= bolt_r, h = thick,
                                                normal = nfro_ax_n,
                                                ch=0, xtr_top=1, xtr_bot=1,
                                                pos = pos_bolt)
            holes_list.append(shp_bolt)

            # holes on the larger side
 
            pos_bolt = pos + bolt_pos_top_n + larg_sp_c_vec
            shp_bolt = fcfun.shp_cylcenxtr (r= bolt_r, h = thick,
                                                normal = nfro_ax_n,
                                                ch=0, xtr_top=1, xtr_bot=1,
                                                pos = pos_bolt)
            holes_list.append(shp_bolt)
            pos_bolt = ( pos + bolt_pos_top_n + larg_sp_c_vec +
                             DraftVecUtils.scale(ntop_ax,20))
            shp_bolt = fcfun.shp_cylcenxtr (r= bolt_r, h = thick,
                                                normal = nfro_ax_n,
                                                ch=0, xtr_top=1, xtr_bot=1,
                                                pos = pos_bolt)
            holes_list.append(shp_bolt)
            # holes on the larger side
                                                
            pos_bolt = (pos + bolt_pos_top_n + larg_sp_c_vec +
                             DraftVecUtils.scale(nsid_ax,20))
            shp_bolt = fcfun.shp_cylcenxtr (r= bolt_r, h = thick,
                                                normal = nfro_ax_n,
                                                ch=0, xtr_top=1, xtr_bot=1,
                                                pos = pos_bolt)
            holes_list.append(shp_bolt)
            pos_bolt = ( pos + bolt_pos_top_n + larg_sp_c_vec +
                             DraftVecUtils.scale(nsid_ax,20) +
                             DraftVecUtils.scale(ntop_ax,20))
            shp_bolt = fcfun.shp_cylcenxtr (r= bolt_r, h = thick,
                                                normal = nfro_ax_n,
                                                ch=0, xtr_top=1, xtr_bot=1,
                                                pos = pos_bolt)
            holes_list.append(shp_bolt)


            # holes on the larger side
                                                
            pos_bolt = (pos + bolt_pos_top_n + larg_sp_c_vec +
                             DraftVecUtils.scale(nsid_ax,-15))
            shp_bolt = fcfun.shp_cylcenxtr (r= bolt_r, h = thick,
                                                normal = nfro_ax_n,
                                                ch=0, xtr_top=1, xtr_bot=1,
                                                pos = pos_bolt)
            holes_list.append(shp_bolt)
            pos_bolt = ( pos + bolt_pos_top_n + larg_sp_c_vec +
                             DraftVecUtils.scale(nsid_ax,-15) +
                             DraftVecUtils.scale(ntop_ax,20))
            shp_bolt = fcfun.shp_cylcenxtr (r= bolt_r, h = thick,
                                                normal = nfro_ax_n,
                                                ch=0, xtr_top=1, xtr_bot=1,
                                                pos = pos_bolt)
            holes_list.append(shp_bolt)


            

        
            

        shp_holes = fcfun.fuseshplist(holes_list)
        shp_plate = shp_box.cut(shp_holes)


        doc = FreeCAD.ActiveDocument
        fco_plate =  doc.addObject("Part::Feature", name) 
        fco_plate.Shape = shp_plate
        self.fco = fco_plate

    def color (self, color = (1,1,1)):
        self.fco.ViewObject.ShapeColor = color

    # exports the shape to STL format
    def export_stl (self, name = ""):
        if not name:
            name = self.name
        stlPath = filepath + "/freecad/stl/"
        stlFileName = stlPath + name + ".stl"
        self.fco.Shape.exportStl(stlFileName)

                           

#doc = FreeCAD.newDocument()
#Plate3CageCubes(d_cagecube = kcomp_optic.CAGE_CUBE_60,
#                thick = 5,
#                cube_dist_n = 120,
#                cube_dist_p = 80,
#                top_h = 10,
#                cube_face = 'rodscrews',#which side of the cube faces the plate
#                hole_d = 0, 
#                boltatt_n = 6,
#                boltatt_d = 3+TOL,
#                fc_fro_ax = VX,
#                fc_top_ax = VZ,
#                fc_sid_ax = VY,
#                pos = V0,
#                name = 'Plate3CageCubes')
