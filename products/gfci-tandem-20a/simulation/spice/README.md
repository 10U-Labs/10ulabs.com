# SPICE Simulations

This directory contains ngspice/LTspice simulation files for validating GFCI circuit behavior.

## Planned Simulations

| File | Purpose |
|------|---------|
| `ct_response.sp` | CT frequency response with various core materials |
| `sense_amplifier.sp` | Sense amplifier gain and filtering |
| `trip_threshold.sp` | Comparator threshold accuracy vs. temperature |
| `trip_driver.sp` | Solenoid driver transient response |
| `power_supply.sp` | Onboard supply startup and load regulation |

## Running Simulations

```bash
ngspice -b ct_response.sp -o ct_response.log
```

## Required Models

- Generic op-amp model (or specific part, TBD)
- MOSFET model for trip driver
- Solenoid coil model (R + L)
