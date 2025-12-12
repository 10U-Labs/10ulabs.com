# Volume Comparison from Datasheets

## Full-size Siemens 1-pole 20A GFCI (QF120A)

| Dimension | Value |
|-----------|-------|
| Height | 3.0" (76.2 mm) |
| Width | 1.0" (25.4 mm) |
| Depth | 3.1" (78.7 mm) |

**Approximate volume (rectangular):** 3.0 × 1.0 × 3.1 = **9.3 in³** (~152 cm³)

---

## Siemens 2-circuit Tandem Breaker (like my AFCI tandem, Q2020AFC)

| Dimension | Value |
|-----------|-------|
| Height | 3.25" (82.6 mm) |
| Width | 0.75" (19.1 mm) |
| Depth | 2.75" (69.9 mm) |

**Approximate volume (rectangular):** 3.25 × 0.75 × 2.75 = **6.7 in³** (~110 cm³)

---

## Comparison

- **tandem_volume / gfci_volume ≈ 6.7 / 9.3 ≈ 0.72**
- Alternatively, **two GFCI volumes / one tandem volume ≈ 18.6 / 6.7 ≈ 2.8**

Therefore, purely from outer volume, it looks physically plausible to fit two GFCI channels inside a tandem envelope, pending detailed internal layout. The tandem form factor provides roughly 70% of the volume of a single full-size GFCI, suggesting that aggressive miniaturization of the GFCI sensing/trip circuitry will be required to achieve a 2-channel design within the tandem envelope.
