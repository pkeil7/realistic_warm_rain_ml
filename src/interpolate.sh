#!/bin/bash
#SBATCH --job-name=interpolate         # Job name
#SBATCH --partition=interactive       # Partition name
#SBATCH --mem=100G                      # Memory per node
#SBATCH --time=00:30:00               # Time limit (hh:mm:ss)
#SBATCH --output=../log/job_%j.out           # Standard output log
#SBATCH --error=../log/job_%j.err            # Standard error log
#SBATCH --account=ka1176     # Account name


# Only works for one file. Consider using mergetime.sh first.
# Can also be run interactively for small files. 1 day of 2min precip r2b8 takes less than 1 min


# List of experiment names to process
# Experiment overview in experiment_overview.md
exp_names=("${exp:-iconml_amip_superdropnet_sharma25_60s_single_2ndtry}")
stream=${stream:-atm_3d_P1D_3} # also: atm_3d_P1D_X or atm_2d_PT20M, atm_2d_P1D
var=${var:-moments} # corresponds to var_string in mergetime.sh
res=${res:-1} # 1 or 01 (1 degree or 0.1 degree)
horizontal_interpolation=true
generate_weightfile=false
vertical_interpolation=${vertical_interpolation:-true} # for 3d vars. Only works if you have interpolated pressure (pfull) already horizontally, adapt pfull_file below if needed

grid_file="../data/icon_grid_0054_R02B08_G.nc"

# Loop over experiment names
for exp in "${exp_names[@]}"; do
    infile="../data/${exp}_${stream}_${var}_mergetime.nc"
    outfile="../data/${exp}_${stream}_${var}_${res}deg.nc"
    grid_description="grid_file_${res}deg.txt"
    weightfile="../data/weightfile_rb02b08_to_${res}x${res}deg.nc"
    outfile_vert_int="../data/${exp}_${stream}_${var}_${res}deg_pl.nc"
    pfull_file="../data/${exp}_atm_3d_P1D_4_ta_tend_ta_${res}deg.nc"

# Load necessary modules
# Older cdo module fails!
    module purge
    module load cdo/2.5.0-gcc-11.2.0

    if [ "$horizontal_interpolation" = true ]; then
        if [ "$generate_weightfile" = true ]; then
            echo "Generating weight file for $exp..."
            cdo gendis,${grid_description} ${infile} ${weightfile}
        fi

        cdo -remap,${grid_description},${weightfile} $infile $outfile
    fi

    if [ "$vertical_interpolation" = true ]; then
        tempfile="../data/temp_${exp}.nc"
        if [ "$var" != "ta_tend_ta" ]; then # if pfull not in file get it
            echo "Fetching pressure for $exp from file $pfull_file"
            cdo merge $outfile -selvar,pfull $pfull_file $tempfile
        else
            cp $outfile $tempfile
        fi

        echo "Applying vertical interpolation for $exp..."
        cdo ap2pl,92500,85000,70000,60000,50000,40000,30000,20000,15000,10000 $tempfile $outfile_vert_int
    
        rm $tempfile
    fi
done
