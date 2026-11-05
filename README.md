
# Repository for "Realisitc Emulation of Warming Rain Microphysics in the ICON-A Model"
The README is stucutured in 3 main parts:
- preparing SuperdropNet for use in ICON, as well as brief offline evaluation
- Running SuperdropNet in ICON
- Processing ICON output for analysis and Figures

# Prepare SuperdropNet
Go to superdropnet folder:

- model class with constraints in defined in `superdropnet.py`
- run `create_torchscript.ipynb` to create torchscript if you change weights or constraints
- Calculate 2moment behaviour for reference in `calculate_2moment.jl`
- Evaluate offline behaviour in `SDN_offline_behaviour.ipynb`

# Run ICON with SuperdropNet
Check out `ICON-superdropNet.md`


# Processing ICON data for figures
Use `src/mergetime.sh` and `src/interpolate.sh` for preprocessing raw ICON output. Check `experiment_overview.md` for experiments.

## Recipie

Use mergetime and interpolate scripts for all experiments. For horizontal interpolation, you need to create a weightfile once in the beginning for both target resolutions (0.1 and 1deg)

- Precipiation:
    - `var=pr`
    - daily values: `stream=atm_2d_P1D`
    - 20min values: `steam=atm_2d_PT20M`
    - 0.1 degree target resolution: `res=01`
- Radiaiton:
    - `var=rlds,rlus,rlut,rsds,rsdt,rsus,rsut`, `var_string=radiation`
    - daily values: `stream=atm_2d_P1D`
    - 0.1 degree target resolution: `res=01`
- all 2d daily varibles in 1 degree resolution:
    - `var=*`, `var_string=all`
    - daily values: `stream=atm_2d_P1D`
    - 1 degree target resolution: `res=1`  
- Temperature, pressure, and temperature tendencies:
    - `var=ta,pfull,tend_ta_two`, `var_string=ta_tend_ta`
    - daily values: `stream=atm_3d_P1D_4`
    - 1 degree target resolution: `res=1`
    - `vertical_interpolation=true`
    - do this before the other 3d variables, then you have pressure for the vertical interpolation ready.
- Specific Humidity, cloud water content, cloud ice content:
    - `var=hus,clw,cli`, `var_string=hus_clw_cli`
    - daily values: `stream=atm_3d_P1D_2`
    - 1 degree target resolution: `res=1`,
    - `vertical_interpolation=true`
- Moments:
    - `var=qg,qr,qni,qnr,qnc`, `var_string=moments`
    - daily values: `stream=atm_3d_P1D_3`
    - 1 degree target resolution: `res=1`
    - `vertical_interpolation=true`


## IMERG observations

IMERG can be downloaded here: https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGHH_07/summary?keywords=%22IMERG%20final%22. However, you need to create an account and follow a couple of annoying steps. Data is currently stored under `/work/ka1176/paul/realistic-superdropnet/data/IMERG`. There you will also find the `create_netrc_IMERG.py` and `create_urs_cookie_IMERG.py` which are necessary for download. More information here: https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHH.07/2020/


