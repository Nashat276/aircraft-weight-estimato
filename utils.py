import numpy as np
import pandas as pd

def calculate_weights(payload, crew, range_nm, ld_ratio, cp, eta_p):
    # مثال مبسط باستخدام معادلة بريغيه
    Wto_guess = 48550
    Mff = 0.764
    WF = Wto_guess * (1 - Mff)
    WE = Wto_guess - WF - payload - crew
    return {"WTO": Wto_guess, "WF": WF, "WE": WE}

def sensitivity_analysis(WTO, range_nm, ld_ratio, cp, eta_p):
    dWTO_dR = (cp * WTO) / (375 * eta_p * ld_ratio)
    dWTO_dCp = WTO / (375 * eta_p * ld_ratio)
    dWTO_dLD = - (cp * WTO) / (375 * eta_p * (ld_ratio**2))

    data = {
        "Parameter": ["Range", "Cp", "L/D"],
        "Sensitivity": [dWTO_dR, dWTO_dCp, dWTO_dLD]
    }
    return pd.DataFrame(data)
