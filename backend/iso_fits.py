
# ISO 286-2 Simplified Lookup Table (Metric, Nominal sizes up to 500mm)
# Structure: { "ToleranceClass": { (min_dia, max_dia): (lower_limit_microns, upper_limit_microns) } }

ISO_FITS = {
    "H7": {
        (0, 3): (0, 10),
        (3, 6): (0, 12),
        (6, 10): (0, 15),
        (10, 18): (0, 18),
        (18, 30): (0, 21),
        (30, 50): (0, 25),
        (50, 80): (0, 30),
        (80, 120): (0, 35),
        (120, 180): (0, 40),
        (180, 250): (0, 46),
        (250, 315): (0, 52),
        (315, 400): (0, 57),
        (400, 500): (0, 63),
    },
    "g6": {
        (0, 3): (-8, -2),
        (3, 6): (-12, -4),
        (6, 10): (-14, -5),
        (10, 18): (-17, -6),
        (18, 30): (-20, -7),
        (30, 50): (-25, -9),
        (50, 80): (-29, -10),
        (80, 120): (-34, -12),
        (120, 180): (-39, -14),
    },
    "f7": {
        (0, 3): (-16, -6),
        (3, 6): (-22, -10),
        (6, 10): (-28, -13),
        (10, 18): (-34, -16),
        (18, 30): (-41, -20),
        (30, 50): (-50, -25),
        (50, 80): (-60, -30),
    }
    # Add more as needed
}

def calculate_iso_limits(nominal_value, tolerance_code):
    """
    Calculates the numerical limits for a given nominal diameter and ISO tolerance code.
    Returns a string: "+0.015 / -0.000" or None if not found.
    """
    try:
        nominal = float(nominal_value)
        code = tolerance_code.strip()
        
        # Check if code exists in our library
        if code not in ISO_FITS:
            return None
            
        # Find the range
        lookup = ISO_FITS[code]
        limits = None
        
        for (min_dia, max_dia), vals in lookup.items():
            if min_dia < nominal <= max_dia:
                limits = vals
                break
                
        if not limits:
            return None
            
        lower_mu, upper_mu = limits
        
        # Convert microns to mm
        lower_mm = lower_mu / 1000.0
        upper_mm = upper_mu / 1000.0
        
        # Format explicitly with sign
        return f"{upper_mm:+.3f} / {lower_mm:+.3f}"
        
    except Exception:
        return None
