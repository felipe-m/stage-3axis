# ----------------------------------------------------------------------------
# -- Citometer Constants
# ----------------------------------------------------------------------------
# -- (c) Felipe Machado
# -- Area of Electronics. Rey Juan Carlos University (urjc.es)
# -- October-2016
# ----------------------------------------------------------------------------
# --- LGPL Licence
# ----------------------------------------------------------------------------


# Taking the same axis as the 3D printer:
#
#    Z   Y
#    | /               
#    |/___ X
#


""" we don't need it because it has been already loaded
import os
import sys
filepath = os.getcwd()
sys.path.append(filepath + '/' + '../components')
"""
import kcomp

# Aluminum profile width
ALU_W = 30.0
# total citometer dimensions
CIT_X = 460.0
CIT_Y = 850.0
CIT_Z = 700.0

# Rod diameter
ROD_Di = 12
ROD_D = float(ROD_Di)
ROD_R = ROD_D/2.0
# Rods' length
# X ROD
ROD_X_L = 165.0
# Y ROD (we can change this, but this is what we have now, those I bought
# for the Indimension
ROD_Y_L = 550.0

# This is the space between the end of rod X and the center of rod Y
ROD_X2Y = kcomp.LMEUU_D[ROD_Di]/2.0 + 4
# separation between the centers of the Y rods (the long ones)
ROD_Y_SEP = ROD_X_L + 2 * ROD_X2Y
# separation between the centers of the X rods (the short ones)
ROD_X_SEP = 150.0

# Microscope slides (portas) dimensions:
PORTA_L = 75.0
PORTA_W = 25.0
PORTA_H = 1.0 #actually, from 0.9 to 1.1

# Number of Portas:
N_PORTA = 8

# separation between 2 portas, and from the porta to the end of the base
PORTA_SEP = 5.

# Porta's base

PORTABASE_L = (N_PORTA * PORTA_W) + (N_PORTA + 1) * PORTA_SEP
PORTABASE_W = PORTA_L + 2 * PORTA_SEP
PORTABASE_H = 4. 

#  ---------------- Y-slider dimensions ------------------------
# The 2 sliders that go along the Y axis. They are also the X end


#YSLIDER_Y = PORTABASE_L - 2 * (PORTA_W + PORTAS_SEP)


# Carriage Position
# moving this position, we would move the portas

CAR_POS_X = 0
CAR_POS_Y = 0


# Vertical movement.

# Diameter of the leadscrew
ZLEADS_D = 8
# Length of the leadscrew
ZLEADS_L = 100


# Idle pulleys made with bolts
BOLTPUL_D = 4

