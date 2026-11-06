#!/bin/bash
#SBATCH --job-name=mergetime         # Job name
#SBATCH --partition=interactive       # Partition name
#SBATCH --mem=100G                      # Memory per node
#SBATCH --time=00:30:00               # Time limit (hh:mm:ss)
#SBATCH --output=../log/job_%j.out           # Standard output log
#SBATCH --error=../log/job_%j.err            # Standard error log
#SBATCH --account=ka1176     # Account name

# --- THINGS TO ADAPT
var=${var:-qg,qr,qni,qnr,qnc}   # radtiation: rlds,rlus,rlut,rsds,rsdt,rsus,rsut. Use * for all vars, only recommended for 2D daily means
stream=${stream:-atm_3d_P1D_3} # also: atm_3d_P1D_X or atm_2d_PT20M, atm_2d_P1D
var_string=${var_string:-moments} # string to use in output file name

# ---

# exp dir:
# /work/ka1176/caroline/gitlab/icon-ml/keep_reference_experiments or
# /work/ka1176/paul/icon-ml/experiments
data_dir=${data_dir:-/work/ka1176/paul/icon-ml/experiments}
# List of experiment names to process
exp_names=("${exp:-iconml_amip_superdropnet_sharma25_60s_single_2ndtry}") 
# Experiment overview in experiment_overview.md

# Load necessary modules
module purge
module load cdo/2.5.0-gcc-11.2.0

# Loop over experiment names
for exp_name in "${exp_names[@]}"; do
    echo "Processing experiment: $exp_name"
    temp_dir="../data/temp_selvar_${exp_name}_${var_string}_${stream}"
    mkdir -p $temp_dir

    # Apply selvar to each file
    for file in ${data_dir}/${exp_name}/${exp_name}_${stream}_*.nc; do
        base_name=$(basename $file)
        cdo selvar,${var} $file $temp_dir/$base_name
    done

    # Merge the processed files
    cdo mergetime $temp_dir/*.nc ../data/${exp_name}_${stream}_${var_string}_mergetime.nc

    # Clean up temporary files
    rm -r $temp_dir
done

# copy grid file if not yet done for later interpolation:
if [ ! -f ../data/icon_grid_0054_R02B08_G.nc ]; then
    cp ${data_dir}/${exp_name}/icon_grid_0054_R02B08_G.nc ../data/icon_grid_0054_R02B08_G.nc
fi

