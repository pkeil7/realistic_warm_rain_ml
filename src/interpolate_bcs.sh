#!/bin/bash
#SBATCH --job-name=interpolate         # Job name
#SBATCH --partition=interactive       # Partition name
#SBATCH --mem=100G                      # Memory per node
#SBATCH --time=00:30:00               # Time limit (hh:mm:ss)
#SBATCH --output=../log/job_%j.out           # Standard output log
#SBATCH --error=../log/job_%j.err            # Standard error log
#SBATCH --account=ka1176     # Account name

module purge
module load cdo/2.5.0-gcc-11.2.0

grid_file="..data/icon_grid_0054_R02B08_G.nc"
infile="../data/sst_bc_4xCO2.nc"
outfile="../data/sst_bc_int_4xCO2.nc"
weightfile_sst="wgtdis_MPI-ESM_to_r2b8_sst.nc"

cdo -f nc4 gendis,$grid_file $infile $weightfile_sst

cdo -f nc4 remap,${grid_file},${weightfile_sst} $infile $outfile

#cdo -f nc remapcon,${grid_file} $infile $outfile

infile="../data/sea_ice_bc_4xCO2.nc"
outfile="../data/sea_ice_bc_int_4xCO2.nc"
weightfile_sic="wgtdis_MPI-ESM_to_r2b8_sic.nc"

cdo -f nc4 gendis,$grid_file $infile $weightfile_sic

cdo -f nc4 remap,${grid_file},${weightfile_sic} $infile $outfile

#cdo -f nc remapcon,${grid_file} $infile $outfile
