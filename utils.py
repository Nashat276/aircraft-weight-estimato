import numpy as np
import pandas as pd

# ثابتات ونسب مراحل مأخوذة من Homework1rev.pdf (قابلة للتعديل)
PHASE_FRACTIONS_DEFAULT = {
    "phase1_preflight": 0.99,
    "taxi": 0.995,
    "takeoff": 0.995,
    "climb": 0.985,
    "cruise": None,   # يحسب عبر معادلة Breguet
    "loiter": None,   # يحسب عبر معادلة Breguet
    "descent": 0.985,
    "landing": 0.995
}

def breguet_prop_range_fraction(R_sm, Cp, eta_p, L_over_D, V_mph):
    """
    Return weight fraction W_end/W_start for a propeller-driven range segment using:
    W_end/W_start = exp(- R_sm / (375 * (eta_p/Cp) * (L/D) ) )
    Note: R_sm = range in statute miles (sm). If input in NM, convert before calling.
    """
    denom = 375.0 * (eta_p / Cp) * (L_over_D)
    return np.exp(- R_sm / denom)

def breguet_prop_endurance_fraction(E_hr, Cp, eta_p, L_over_D, V_mph):
    """
    For loiter endurance (hours): W_end/W_start = exp(- E / (375 * (1/V_mph) * (eta_p/Cp) * (L/D)))
    Equivalent to exp(- E * V / (375 * (eta_p/Cp) * (L/D)))
    """
    denom = 375.0 * (eta_p / Cp) * (L_over_D)
    # E in hours, V in mph -> multiply E by V to get sm (since denom uses 375)
    return np.exp(- E_hr * V_mph / denom)

def solve_wto_iterative(W_pl, V_cruise_kts, L_over_D_cruise, Cp_cruise, eta_p_cruise,
                        R_nm, V_loiter_kts, L_over_D_loiter, Cp_loiter, eta_p_loiter,
                        E_loiter_hr, A_emp=0.32, B_emp=0.90,
                        tol=1e-3, max_iter=200):
    """
    Iterative solver for WTO:
    - Uses phase fractions from PHASE_FRACTIONS_DEFAULT
    - Computes cruise and loiter fractions via Breguet (converting NM->sm and kts->mph)
    - Uses empirical WE = A * WTO^B to estimate empty weight and iterate until consistent:
      WTO = WE + WF + W_pl
    Returns dictionary with WTO, WE, WF, and used fractions.
    """
    # convert units
    nm_to_sm = 1.15
    V_cruise_mph = V_cruise_kts * 1.15078
    V_loiter_mph = V_loiter_kts * 1.15078
    R_sm = R_nm * nm_to_sm

    # initial guess
    WTO = 48000.0
    for it in range(max_iter):
        # compute phase fractions
        pf = PHASE_FRACTIONS_DEFAULT.copy()
        # cruise fraction (W5/W4)
        cruise_frac = breguet_prop_range_fraction(R_sm, Cp_cruise, eta_p_cruise, L_over_D_cruise, V_cruise_mph)
        pf["cruise"] = cruise_frac
        # loiter fraction (W6/W5)
        loiter_frac = breguet_prop_endurance_fraction(E_loiter_hr, Cp_loiter, eta_p_loiter, L_over_D_loiter, V_loiter_mph)
        pf["loiter"] = loiter_frac

        # total mission weight fraction product (W_final/W_initial)
        # order: phase1 * taxi * takeoff * climb * cruise * loiter * descent * landing
        product = (pf["phase1_preflight"] * pf["taxi"] * pf["takeoff"] * pf["climb"] *
                   pf["cruise"] * pf["loiter"] * pf["descent"] * pf["landing"])

        # fuel fraction used = 1 - product
        Mff = 1.0 - product

        WF = WTO * Mff
        WE_emp = A_emp * (WTO ** B_emp)   # empirical empty weight estimate

        # compute new WTO from balance: WTO_new = WE_emp + WF + W_pl
        WTO_new = WE_emp + WF + W_pl

        # check convergence
        if abs(WTO_new - WTO) < tol:
            WTO = WTO_new
            break
        WTO = 0.5 * (WTO + WTO_new)  # relaxation

    # final recompute
    WF = WTO * Mff
    WE = A_emp * (WTO ** B_emp)

    return {
        "WTO": WTO,
        "WE": WE,
        "WF": WF,
        "Mff": Mff,
        "phase_fractions": pf,
        "iterations": it+1
    }

def sensitivity_analysis(WTO, R_nm, L_over_D, Cp, eta_p):
    """
    Compute partial derivatives (approximate) of WTO with respect to R, Cp, L/D, eta_p
    using formulas from Homework1rev.pdf (table 2.20 / eq 2.45-2.51).
    Returns DataFrame with Parameter and Value (units indicated).
    """
    # helper constants
    # F factor approximated as WTO (this is a simplified approach consistent with the doc)
    F = WTO
    # dWTO/dR (lbs per nm)
    dW_dR = (Cp * F) / (375.0 * eta_p * L_over_D)  # lbs per sm; convert to per nm by dividing by 1.15
    dW_dR_per_nm = dW_dR / 1.15

    # dWTO/dCp
    dW_dCp = (F) / (375.0 * eta_p * L_over_D)

    # dWTO/d(L/D)
    dW_dLD = - (Cp * F) / (375.0 * eta_p * (L_over_D ** 2))

    # dWTO/d(eta_p)
    dW_dnp = - (Cp * F) / (375.0 * (eta_p ** 2) * L_over_D)

    df = pd.DataFrame({
        "Parameter": ["Range (lbs per NM)", "Cp (lbs/lb·hp·hr)", "L/D", "Propeller efficiency ηp"],
        "Value": [dW_dR_per_nm, dW_dCp, dW_dLD, dW_dnp]
    })
    return df

def ws_wp_curve(WTO, wing_area_guess=400.0):
    """
    Generate an illustrative W/S vs W/P curve for design envelope.
    This is illustrative: compute W/S range and corresponding required W/P for cruise power estimate.
    """
    # W/S range (lb/ft^2)
    ws = np.linspace(20, 120, 50)
    # simple power required model: P_req ~ k * W^(3/2) / (sqrt(S))
    # For illustration choose k so values are reasonable
    k = 0.0008
    wp = (k * (WTO ** 1.5)) / np.sqrt(ws)  # lb/hp (approx)
    df = pd.DataFrame({"W/S (lb/ft^2)": ws, "W/P (lb/hp)": wp})
    return df
