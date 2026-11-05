# ICON-SuperdropNet

## Prerequisites

- ICON model source code, developed with version 2024.10
- Our additions from https://zenodo.org/records/23665420
    - Patch `icon-superdropnet.patch`
    - Example config `config/dkrz/levante.intel-2021.5.0_ftorch`
    - Run scripts
- FTorch, developed with v1.0.0.

## FTorch

ICON calls SuperdropNet via FTorch. It needs to be available to the user on the target machine.

On Levante: You can use the paths as in `config/dkrz/levante.intel-2021.5.0_ftorch`

Alternative: Follow the installation instructions https://cambridge-iccs.github.io/FTorch/index.html to obtain FTorch. Build for usage on CPU.

## Update code 

Apply the patch to the ICON model source code.

```bash
git apply icon-superdropnet.patch
```

This adds support for
- new namelist `aiparams.nml`
- new module `mo_aiparams.f90`: AI parameterisation forward function
- Calling SuperdropNet in the appropriate places in the two-moment cloud microphysics scheme
- Add times that measure SuperdropNet execution time

If you make changes to SuperdropNet, adapt the unit test case in `/src/configure_model/mo_aiparams_config.f90` accordingly based on SuperdropNet offline results.

## Build ICON

If necessary, adapt paths in the config. Run for configuration:

```bash
./config/dkrz/levante.intel-2021.5.0_ftorch
```

Then build ICON

```bash
make -j8
```

## Run

The main addition to the run file is a block that controls the AI parameterisation namelist

```bash
&aiparams_nml
  aiparams_config%use_superdropnet = .true. ! use superdropnet
  aiparams_config%superdropnet_path = './superdropnet_final.pt' ! actual model path linked above
  aiparams_config%dt_superdropnet = "PT20S" ! time step SuperdropNet uses in its forward pass
/
```

For using e.g. the version of SuperdropNet with a 60 s time step, change `PT20S` to `PT60s`.

Run like any standard ICON simulation.

## Is it working?

Check the log file to see whether the "AIPARAMS" namelist has been considered and the unit test is passing. It should read like this


```bash
  0:  
    0:  Evaluating input to AIPARAMS - Deep Learning emulators for parameterizations
    0:  ============================================================================
    0:  
    0:  Using SuperdropNet for warm rain processes
    0:  SuperdropNet model path: ./superdropnet_final.pt
    0:  
    0:  Test AIPARAMS: SuperdropNet
    0:  
    0:  ----------------------------------------------------------------------------
    0:  
    0:  test_aiparams_superdropnet: Loading SuperdropNet from file: ./superdropnet_final.pt
    0:  test_aiparams_superdropnet: SuperdropNet forward pass
    0:  test_aiparams_superdropnet:  1 1 1 0.00000E+00 0.00000E+00 0.00000E+00
    0:  test_aiparams_superdropnet:  1 1 2 0.00000E+00 0.00000E+00 0.00000E+00
    [...]
     0:  test_aiparams_superdropnet: Finished test. Deleting tensors.
    0:  test_aiparams_superdropnet: SuperdropNet test passed
    0:  
    0:  Test AIPARAMS: SuperdropNet Loop
    0:  
    0:  ----------------------------------------------------------------------------
    0:  
    0:  test_aiparams_superdropnet_loop: Loading SuperdropNet from file: ./superdropnet_final.pt
    0:  test_aiparams_superdropnet_loop: SuperdropNet forward pass: loop with 3 iterations (20s vs 60s)
    0:  test_aiparams_superdropnet_loop:  1 1 1 0.00000E+00 0.00000E+00 0.00000E+00
    0:  test_aiparams_superdropnet_loop:  1 1 2 0.00000E+00 0.00000E+00 0.00000E+00
    0:  test_aiparams_superdropnet_loop:  1 1 3 0.00000E+00 0.00000E+00 0.00000E+00
    [...]
        0:  test_aiparams_superdropnet_loop: 14 1 4 0.83804E+04 0.83804E+04 0.25603E-07
    0:  test_aiparams_superdropnet_loop: SuperdropNet loop test passed

```

Once the run is finished, a Timer report lists the execution time of SuperdropNet, split into "preparation" of input arrays and "forward" application of SuperdropNet via FTorch.

```bash
0:            L interface_cloud_two                      239054400        0.00400s   [5892]         0.29945s        1.3522s   [4415]         1338.677    [7666]               5223.407    [11817]              4371.040    16377   
    0:  
    0:               L phys_2mom_wetgrowth                   1.6E+10          0.00000s   [14]           0.00000s       0.02142s   [2205]            1.455    [6309]                  1.628    [14354]                 1.483    16377   
    0:  
    0:               L phys_2mom_warmrain                    1.6E+10          0.00000s   [0]            0.00442s        1.0119s   [4402]         1292.969    [7666]               5160.824    [11817]              4319.169    16377   
    0:  
    0:                  L AIPARAMS_superdropnet              1.6E+10          0.00000s   [0]            0.00442s        1.0111s   [4402]         1292.743    [7666]               5160.336    [11817]              4318.796    16377   
    0:  
    0:                     L AIPARAMS_superdropnet_prepare   2.4E+10          0.00000s   [0]            0.00000s       0.13608s   [1598]            1.191    [7666]                  4.424    [11817]                 3.305    16377   
    0:  
    0:                     L AIPARAMS_superdropnet_forward   7.9E+09          0.00082s   [1210]         0.00893s        1.0109s   [4402]         1291.050    [7666]               5154.739    [11817]              4314.520    16377   
```

## Common pitfalls

1. Unit test not running: The numbers need to match the ones for SuperdropNet offline application. Check the numbers, adapt if necessary, build and run again.
2. SuperdropNet not called: SuperdropNet only works within two-moment cloud microphysics, this must be enabled.
3. Time step: The timestep passed via `aiparams_config%dt_superdropnet` MUST match the time step that was used in the SuperdropNet torchscript model. ICON-SuperdropNet CANNOT check for this.

