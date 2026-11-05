# This is for SST. For sea ice and CO2 check ../notebooks/get_bc_4xCO2.ipynb

module purge
module load cdo/2.5.0-gcc-11.2.0

cdo addc,4 /pool/data/ICON/grids/public/mpim/0054/sst_and_seaice/r0100/bc_sst_2019-2021.nc data/bc_sst_2019-2021+uniform4K.nc
