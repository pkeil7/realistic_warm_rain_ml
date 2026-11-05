using Pkg
Pkg.add(["CloudMicrophysics", "ClimaParams", "CSV", "DataFrames"])

using CloudMicrophysics
import CloudMicrophysics.Parameters as CMP
import CloudMicrophysics.Microphysics2M as CM2
using CSV, DataFrames

FT = Float64
scheme = CMP.SB2006(FT)   # Seifert & Beheng 2006, standard parameters

# --- Air density ---
ρ = FT(1.2)               # air density [kg/m^3]

# --- Initial conditions (q_liq0 in kg/m^3, converted to kg/kg below) ---
q_liq0_vol = FT[1e-3, 1e-3, 2.5e-3]   # cloud water content [kg/m^3]
N_liq0     = FT[1e8, 6e8, 1e8]        # cloud droplet number density [1/m^3]

# --- Time stepping ---
dt = FT(20.0)              # time step length [s]
t_end = FT(600*dt)       # total simulated time [s]
n_steps = Int(round(t_end / dt))

function integrate(q_liq0, N_liq0)
    q_liq = q_liq0
    N_liq = N_liq0
    q_rai = FT(0.0)
    N_rai = FT(0.0)

    t_out     = Float64[0.0]
    q_liq_out = Float64[q_liq]
    N_liq_out = Float64[N_liq]
    q_rai_out = Float64[q_rai]
    N_rai_out = Float64[N_rai]

    for step in 1:n_steps
        # Autoconversion: cloud droplets colliding to form rain
        au = CM2.autoconversion(scheme.acnv, q_liq, q_rai, ρ, N_liq)

        # Accretion: raindrops collecting cloud droplets
        acc = CM2.accretion(scheme, q_liq, q_rai, ρ, N_liq)

        # Liquid self-collection: cloud droplets merging into larger cloud droplets
        dN_liq_sc = CM2.liquid_self_collection(scheme.acnv, q_liq, ρ, au.dN_liq_dt)

        # Rain self-collection and breakup: raindrops merging / breaking up
        rain = CM2.rain_self_collection_and_breakup(scheme, q_rai, ρ, N_rai)

        # Total tendencies
        dq_liq_dt = au.dq_liq_dt + acc.dq_liq_dt
        dq_rai_dt = au.dq_rai_dt + acc.dq_rai_dt
        dN_liq_dt = au.dN_liq_dt + acc.dN_liq_dt + dN_liq_sc
        dN_rai_dt = au.dN_rai_dt + acc.dN_rai_dt + rain.sc + rain.br

        # Forward Euler update (clamp to physically valid, non-negative values)
        q_liq = max(FT(0), q_liq + dq_liq_dt * dt)
        q_rai = max(FT(0), q_rai + dq_rai_dt * dt)
        N_liq = max(FT(0), N_liq + dN_liq_dt * dt)
        N_rai = max(FT(0), N_rai + dN_rai_dt * dt)

        push!(t_out, step * dt)
        push!(q_liq_out, q_liq)
        push!(N_liq_out, N_liq)
        push!(q_rai_out, q_rai)
        push!(N_rai_out, N_rai)
    end

    # convert q_liq, q_rai back to kg/m^3
    return DataFrame(t=t_out, q_liq=q_liq_out .* ρ, N_liq=N_liq_out, q_rai=q_rai_out .* ρ, N_rai=N_rai_out)
end

for i in eachindex(q_liq0_vol)
    q_liq0 = q_liq0_vol[i] / ρ   # convert kg/m^3 -> kg/kg
    df = integrate(q_liq0, N_liq0[i])
    fname = "warm_rain_moments_$(i).csv"
    CSV.write(fname, df)
    println("case $i: q_liq0=$(q_liq0) kg/kg, N_liq0=$(N_liq0[i]) 1/m^3 -> wrote $fname with $(nrow(df)) rows")
end