# Signal-processing specification

The electrical rate is 10,000 samples/s/channel; six channels yield 60,000 scalar values/s. Supported windows are 0.1, 0.2, 0.5, 1, 2 and 5 seconds. The library supports overlap in [0,1); benchmark studies enforce zero overlap so raw samples cannot cross partitions.

| Window seconds | Samples/channel | FFT bin spacing Hz |
|---:|---:|---:|
| 0.1 | 1,000 | 10 |
| 0.2 | 2,000 | 5 |
| 0.5 | 5,000 | 2 |
| 1 | 10,000 | 1 |
| 2 | 20,000 | 0.5 |
| 5 | 50,000 | 0.2 |

RMS is sqrt(mean(x²)); peak is max(abs(x)); crest is peak/RMS. RMS imbalance is maximum deviation from the three-phase mean divided by that mean, in percent. This is an amplitude statistic, not a universal fault diagnosis.

Periodic Hann FFT amplitudes are coherent-gain corrected; DC/Nyquist scaling is handled separately. Fundamental search is near nominal supply frequency. Harmonics use nearest frequency bins, up to order 40 or Nyquist. THD is harmonic RMS norm divided by fundamental RMS. **Off-bin frequency, leakage and short windows can bias harmonic/phase estimates**; current tests primarily establish bin-centered 50/60 Hz behavior. Welch PSD uses at most 2,048 samples per segment and its own lower spectral resolution.

Verified phase-to-neutral paired channels permit total active power sum(mean(v·i)), apparent power sum(Vrms·Irms), true power factor P/S and fundamental reactive power from fundamental amplitudes and phase angles. The reactive value excludes distortion power. Other wiring conventions return unavailable power.

Butterworth low/high/band-pass, notch, detrending and median smoothing are optional. Original arrays are copied, configuration is retained and filtered results warn about edge artifacts. Synthetic generation does not verify real anti-alias hardware. MCSA requires supplied pole count and speed, and sideband separation of at least two FFT bins before exploratory amplitude extraction.
