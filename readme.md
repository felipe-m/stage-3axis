# Cytometer script files

## `kcit.py`

Constants and dimensions for the cytometer

## `base.py`

Python script for the cytometer base.
It uses functions and classes from other folders:

Directory structure:

```
cad/
  +-- frecad                  # FreeCAD designs
      +-- comps
          +-- misumi_profile_hfs_series_w8_30x30.FCStd
  +-- py_freecad              # python scripts for FreeCAD
      +-- citometro             # citometer scripts
          +-- base.py             # citometer base
          +-- kcit.py             # citometer constants
      +-- comps               # library of components
          +-- comps.py            # components
          +-- kcomp.py            # constants about components
          +-- fcfun.py            # library of functions
      +-- corexy              # python scripts for coreXY printer
          +-- carriage.py         # carriage of the 3D printer 
```

  
