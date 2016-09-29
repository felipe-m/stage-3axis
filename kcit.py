# file with the citometer constants 

# Taking the same axis as the 3D printer:
#
#    Z   Y
#    | /               
#    |/___ X
#


# to get the components

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
# Rods' length
# X ROD
ROD_X_L = 165.0
# Y ROD (we can change this, but this is what we have now, those I bought
# for the Indimension
ROD_Y_L = 550.0

# This is the space between the end of rod X and the center of rod Y
ROD_X2Y = kcomp.LMEUU_BEARING_D[ROD_Di]/2.0 + 4
# separation between the centers of the Y rods (the long ones)
ROD_Y_SEP = ROD_X_L + 2 * ROD_X2Y


