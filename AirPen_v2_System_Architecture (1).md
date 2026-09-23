# AirPen v2 — Complete System Architecture & Workflow
*Group 11 · K. J. Somaiya Institute of Technology · Working reference document*

---

## 1. What AirPen Is, In One Paragraph

AirPen is a pen-grip (primary) or wrist-strapped (secondary) ESP32 + MPU6050 device that recognizes characters written in the air and sends them to any Bluetooth-paired computer as standard keyboard keystrokes (BLE HID). It requires **no host-side software** — to the OS, it is indistinguishable from a Bluetooth keyboard. This is not a pointing device (like a stylus or laser pointer); it performs **discrete symbol recognition → text output**, not continuous cursor control. The defensible novelty is the *combination* of on-device edge inference + universal HID output + per-user personalization — no single piece of that is novel alone.

---

## 2. System Boundary — What's On the Device vs. What's Not

```
┌─────────────────────────────────────────────────────────────┐
│                      AIRPEN DEVICE (self-contained)          │
│                                                                │
│   MPU6050 → filtering → segmentation → CNN+GRU/DTW →         │
│   personalization match → autocorrect → BLE HID keystrokes   │
│                                                                │
└──────────────────────────┬─────────────────────────────────┘
                            │  BLE HID (standard keyboard profile)
                            ▼
              ┌─────────────────────────────┐
              │   ANY HOST — no app needed   │
              │  (laptop, phone, AR/VR HMD)  │
              │  Text just appears wherever  │
              │  the cursor/focus already is │
              └─────────────────────────────┘

   OPTIONAL, NOT REQUIRED FOR OPERATION:
   ┌─────────────────────────────┐
   │  Companion calibration app   │  ← only for: personalization
   │  (dev tool, not a product    │    setup, data collection,
   │   requirement)                │    debugging/visualization
   └─────────────────────────────┘
```

**Design rule to protect the core claim:** nothing required for normal text-entry operation may depend on a host-side app. The companion app (if built) is a *development and calibration tool*, never a runtime dependency.

### 2.1 Two nuances worth being explicit about

**The cursor/pointer stretch goal would make AirPen behave like a stylus/laser pointer — but only optionally, and only for that one add-on mode.** The core product (Section 5's CNN+GRU/DTW pipeline) does discrete symbol recognition, not continuous pointing. The stretch goal (Section 8) is a *separate* composite HID keyboard+mouse mode using rate-controlled cursor mapping from wrist rotation. It reuses existing trigger/DEADZONE/BLE infrastructure but is explicitly NOT one of the two headline claims (edge AI + BLE HID; CNN/GRU + personalization) — it's a visible, easy-to-demo addition for non-technical audiences, pursued only after the core is stable, and never a requirement for the disability or AR/VR text-entry claims to hold.

**A lightweight companion app is useful, but only as a dev/calibration tool — never a product requirement.** Its jobs: (a) give some confirmation during personalization calibration that a sample was actually captured correctly (there's no other way to know that without a screen), and (b) support the team's own data collection tooling. Keep this mentally separate from "the product" at all times — if a decision ever makes the companion app required for AirPen to function normally for an end user, that decision has broken the core "no host software" claim and should be reconsidered.

---

## 3. Hardware Architecture

### 3.1 Bill of Materials
| Component | Role |
|---|---|
| ESP32 DevKit V1 (38-pin) | Main MCU — sensor read, inference, BLE HID |
| MPU6050 (GY-521 breakout) | 6-axis IMU: 3-axis accel + 3-axis gyro |
| Push button (GPIO4) | Toggle: start/stop a character/word |
| Pen-grip enclosure (3D printed) | Primary form factor |
| Strap loop (same enclosure) | Secondary wrist-worn mode |
| USB / small powerbank | Power (never connect anything to VIN) |

### 3.2 Wiring
```
MPU6050          ESP32
------           -----
VCC       ---->  3.3V
GND       ---->  GND
SDA       ---->  GPIO21
SCL       ---->  GPIO22
(no external pull-ups needed — GY-521 board has them)

Button    ---->  GPIO4  (other leg to GND)

⚠ NEVER connect anything to VIN.
⚠ Always unplug before rewiring.
⚠ Stage-by-stage bring-up: Blink → sensor test → button test → full firmware.
```

### 3.3 I2C access strategy
Raw `Wire.h` register access is used instead of the Adafruit MPU6050 library — this was forced by clone-chip init failures, but turned out to be the better approach for tight embedded firmware (more control, smaller footprint).

### 3.4 Known firmware gap
The MPU6050 hardware **DLPF** (Digital Low-Pass Filter) is not currently configured. It lives in the `CONFIG` register (`0x1A`), bits `2:0` (`DLPF_CFG`), values 0–6 trading off bandwidth vs. delay (0 ≈ 260 Hz/minimal filtering, 6 ≈ 5 Hz/heavy filtering). For air-writing motion (a few Hz of real signal), a mid-range setting (~21–44 Hz bandwidth) is a reasonable starting point — cuts high-frequency sensor noise essentially for free, before your three software filtering stages even run.

---

## 4. On-Device Signal Pipeline (the full path from motion to keystroke)

```
1. RAW SENSOR READ
   MPU6050 registers → ax, ay, az, gx, gy, gz  @ sample rate

2. NOISE REDUCTION (3 real stages — tremor-preserving, not tremor-removing)
   a. Bias calibration     — per-session, pen held still at start
   b. Deadzone thresholding — 1.8°/s, ignores true sensor-noise-level jitter
   c. EMA smoothing         — α = 0.25
   [+ planned: hardware DLPF as a 4th, free pre-filter stage]

   IMPORTANT FRAMING: these remove SENSOR NOISE, not TREMOR.
   Tremor is physiological signal and is deliberately preserved —
   it's the entire reason personalization (Section 6) exists.

3. SEGMENTATION
   Toggle-button press = stroke/character start
   ~2 second pen-up (no motion) = auto-finalize
   Multi-stroke characters (e.g. "A", "T") grouped under one character
   sample via a stroke-boundary marker channel.

4. TRAJECTORY RECONSTRUCTION (parallel path, DTW/visualization only)
   Gyro integration: x += gy·sensitivity·dt ; y += -gx·sensitivity·dt
   NOT fed to the CNN/GRU — the model consumes raw multi-channel
   sequences directly, this path exists only for DTW template matching
   and any visual debugging.

5. PREPROCESSING (see preprocess_airpen_data.py — already built & tested)
   Flatten strokes → resample to fixed T timesteps (linear interpolation)
   → per-sample z-score normalize → (T, 7) tensor
   [ax, ay, az, gx, gy, gz, stroke_boundary]

6. RECOGNITION (two-tier, confidence-routed)
   ┌─────────────────────┐        ┌──────────────────────┐
   │  PRIMARY: CNN+GRU    │        │  FALLBACK: DTW        │
   │  (learned, personal- │  low   │  (Sakoe-Chiba banded, │
   │  izable)              │──────►│  direction-reversal   │
   │                       │ conf. │  tolerant, shape-     │
   │                       │       │  feature tiebreaker)  │
   └─────────────────────┘        └──────────────────────┘
   Routing needs empirical validation that confidence scores actually
   separate correct/incorrect predictions (open checkpoint).

7. PERSONALIZATION (core research contribution)
   Dense(64) embedding layer (penultimate layer of the CNN+GRU) doubles
   as a feature extractor. New user provides 5–10 calibration samples/
   character → embedded → stored as personal reference set. Inference
   time: nearest-neighbor match (cosine/Euclidean) against the user's
   OWN references instead of the generic softmax head.
   [Future: Siamese/prototypical network training + ECHWR contrastive
   pretraining for better embedding quality.]

8. AUTOCORRECT (on-device, invisible — see Section 7 for full design)
   Buffered per-word, dictionary/edit-distance check, silent no-op if
   ambiguous. No autocomplete (no display to show suggestions on) —
   named as future work with "no display" as the explicit constraint.

9. BLE HID OUTPUT
   Character(s) sent as standard keyboard keystroke reports.
   [Stretch goal, not committed: composite keyboard+mouse HID for a
   rate-controlled cursor mode — separate from the two headline claims.]
```

---

## 5. Recognition Model — Exact Specification

**Input:** `(T, 7)` tensor — T fixed timesteps × [ax, ay, az, gx, gy, gz, stroke_boundary]

```
Conv1D(64 filters,  kernel=5, ReLU) → BatchNorm → MaxPool(2)
Conv1D(128 filters, kernel=3, ReLU) → BatchNorm → MaxPool(2)
Conv1D(128 filters, kernel=3, ReLU) → BatchNorm
GRU(64 units) → final hidden state
Dense(64, ReLU)      ← ALSO the personalization embedding layer
Dropout(0.3)
Dense(36, softmax)   ← A–Z, 0–9 vocabulary
```
Loss: categorical cross-entropy · Optimizer: Adam · Early stopping on val loss.

**Why CNN+GRU over CNN-alone:** Wehbi et al. (2021, STABILO Digipen) directly compared the two on comparable IMU pen data — CNN-alone had roughly double the character error rate of CNN+recurrent (35.9% vs 17.97% CER in their CLDNN). This is the load-bearing citation for the architecture choice.

**Full variant comparison (already in the paper draft):**

| Variant | Status | Why |
|---|---|---|
| Handcrafted features (mean/var/FFT) + SVM/RF | Benchmark baseline only | Fast, interpretable, cheap; no temporal modeling |
| 1D-CNN only | Rejected as primary | ~2x error rate of CNN+recurrent (Wehbi et al.) |
| **1D-CNN + GRU** | **SELECTED** | Best accuracy/complexity trade-off for our scale + ESP32 target |
| 1D-CNN + LSTM/BLSTM | Alternate, not selected | Similar benefit, heavier — worse edge-deployment cost |
| DTW | Retained as fallback | No training needed, robust with little data, doesn't improve with more data |

**Edge deployment:** INT8 post-training quantization → TensorFlow Lite Micro → ESP32 (fall back to ESP32-S3 if flash/RAM too tight).

---

## 6. Data Architecture

### 6.1 Raw sample format (on-device recording output)
```json
{
  "contributor": "alice",
  "character": "A",
  "n_strokes": 2,
  "strokes": [
    [ {"t_ms": .., "ax": .., "ay": .., "az": .., "gx": .., "gy": .., "gz": ..}, ... ],
    [ ... ]
  ]
}
```
Path convention: `data/<contributor>/<character>/<timestamp>.json`

### 6.2 Datasets in play

| Dataset | Role | Notes |
|---|---|---|
| **Own recordings** | Final reported results, always | Split-by-contributor; A–D done, continuing to full A-Z/0-9 |
| **6DMG** | Pretraining / architecture validation | Best match for pen-grip mode; 62 classes, hybrid inertial+optical capture — use `load_6dmg.py` (built this session) to convert to our tensor format |
| **ImAiR** | Reserved for wristband-secondary mode | Wrist-worn IMU, matches secondary form factor |
| **uWave** | Pipeline/DTW validation only | Narrow vocabulary, not full letters |
| Own v1 `gesture_templates.json` | Zero-effort proxy data | Small, mouse-drawn |

**Rule: public datasets pretrain/validate architecture only — final reported accuracy numbers always come from your own hardware + held-out test contributors.**

### 6.3 Data schema note
A `"mode": "pen" | "wrist"` field is needed once wristband-pilot data collection starts, since `DEADZONE`/`SENSITIVITY` firmware constants are tuned separately per mode.

### 6.4 Evaluation methodology
- Leave-one-contributor-out cross-validation (cross-user generalization)
- Before/after-calibration comparison (personalization gain)
- Paired statistical tests (t-test / Wilcoxon), metrics pre-registered before running studies

---

## 7. Autocorrect Design (built this session — `autocorrect_prototype.py`)

**Core constraint driving the design:** no screen exists anywhere in the system, so no suggestion can ever be shown for the user to accept/reject. This rules out conventional autocomplete UX and shapes autocorrect to be fully silent and conservative.

```
Character-by-character:
   CNN+GRU/DTW recognizes a char → sent to host IMMEDIATELY (stays responsive)
   → buffered into "current word"

At word boundary (space / punctuation / pause-timeout):
   IF buffered word is an exact dictionary hit        → do nothing
   IF exactly ONE dictionary word is within edit-      → erase it:
     distance ≤ 2 of the buffered word                   send BACKSPACE × N
                                                           retype corrected word
   IF ambiguous (multiple equal-distance candidates)   → leave as-is
   OR nothing close enough                               (silent no-op — safer
                                                           than a wrong guess
                                                           nobody can catch)
```

**Why backspace-and-retype instead of buffering the whole word before sending:** sending immediately per-character preserves the "feels like typing" responsiveness that's part of the product's appeal; the correction cost is paid only on the minority of words that need it, and only as a brief visible flicker — the same trade-off phone keyboards make.

**Demo finding (from this session's test run):** with a small ~130-word dictionary, "friend" (not in the dictionary) was wrongly corrected to "find" — a real illustration of the false-positive risk. A larger, well-chosen dictionary reduces this but never eliminates it; this is worth stating plainly in the paper as a known limitation, not glossed over.

**Firmware porting path:** dictionary → flash-resident sorted word list (via `export_trie_for_firmware()` in the prototype) with binary search for exact match; the bounded Damerau-Levenshtein routine is ~30 lines and translates directly to C, no libraries needed.

**Explicitly deferred to future work:** predictive autocomplete (word completion before the word is finished) — stated reason: no display exists to show candidates for the user to select.

---

## 8. BLE HID Layer

- Standard BLE HID keyboard profile — Just Works pairing, same as any Bluetooth mouse/keyboard (no password expected, this is normal).
- Single-active-BLE-connection constraint (documented in README).
- **Known risk area:** prior unresolved laptop pairing issue. Suspected causes in priority order: stale bonding cache after reflash (fix: unpair on OS + NVS erase + re-pair), single-connection conflict, Windows HID enumeration delay, Just-Works vs. passkey mismatch.
- **Rule:** get keyboard-only HID rock-solid (3× repeatable clean pair/re-pair) before building anything else on top — composite keyboard+mouse (cursor stretch goal) is more fragile and should stay a fallback-able optional branch, not the default.

---

## 9. Application Framing (guide-facing, literature-grounded)

| Framing | Scope | Key citation |
|---|---|---|
| **Primary: AR/VR controller-free text entry** | Short-form only (names, tags, codes, short replies) — NOT long-form typing. Two contexts: (a) training/simulation (hands-free, pen mode), (b) hands-busy field-service (wristband mode) | — |
| **Secondary: assistive text entry** | Users with hand tremor (essential/early-moderate Parkinson's) who retain gross wrist mobility but lack fine precision — explicitly NOT full paralysis | Tironi et al. 2025 (pen-grip clinical precedent); Rovini, Maremmani & Cavallo 2017 (IMU sensing for Parkinson's, literature-grounded) |

**Known tension (proactively disclosed to guide, not hidden):** AR/VR hands-busy scenarios want wristband; disability's primary mode is pen-grip. Resolved by splitting AR/VR into the two sub-cases above rather than claiming one form factor covers everything.

**Population-size reassurance:** essential tremor affects ~1% of the general population, ~4–6% of people over 65 — tens of millions worldwide, more than Parkinson's alone (~10M worldwide). Narrow ≠ small.

**"Is this really gesture recognition without a camera?" rebuttal:** gesture recognition is defined by the task (classify body motion → meaningful category), not the sensor. Zero-camera precedent: uWave (accelerometer), WiDraw (WiFi), Soli (radar), NNTrak (IMU) — all treated as legitimate gesture-recognition work in the field's own literature.

---

## 10. Research Framing (the Minor-project "this isn't just an app" case)

- **RQ1 (primary):** Does per-user few-shot personalization improve accuracy more for tremor-affected users than steady-hand users?
- **RQ2:** AirPen vs. raycast VR keyboard — throughput/error rate, hands-busy vs. hands-free.
- **RQ3:** Does calibration-sample count (5 vs 10 vs 15) show diminishing returns, and does that curve differ for tremor vs. steady-hand users?
- **Honest fallback if real tremor-affected participants aren't recruitable this semester:** simulated-tremor pilot (weighted wrist attachment or deliberate wobble), explicitly labeled a scoping pilot, not a clinical claim.

---

## 11. Explicitly Out of Scope This Semester
- Continuous/cursive multi-letter recognition
- Predictive autocomplete (display constraint, see Section 7)
- Voice-gesture cross-validation / voice commands (Vosk offline keyword spotting)
- Continual/online learning
- Agentic intent interface

---

## 12. Development Tracks & Sequencing

Only one assembled ESP32+MPU6050 unit currently exists. This means data collection across multiple contributors is inherently **serialized, not parallel**, on that unit, and it also means any work that needs to talk to real hardware over BLE (companion-app testing, firmware changes) is gated behind whoever currently has the device — a bottleneck worth solving directly rather than working around indefinitely.

### 12.1 Device sequencing
1. A fast, broad first recording pass across all 36 characters (A-Z, 0-9) at a lower rep count (e.g. ~10-15 reps/char) is more efficient than going straight for the full 30 with one contributor — it produces a real, if partial, multi-class dataset sooner, and frees the device for the next contributor faster.
2. The device moves to the next contributor once that first pass is done, round-robin.
3. A second full-quota pass (topping everyone up from ~10-15 to 30 reps/char) happens later, once the first broad pass across all contributors is complete.
4. **Recommended: a second ESP32 DevKit + MPU6050 GY-521 set.** Both boards together cost a small fraction of the project budget, and fully unblocks firmware work and companion-app testing from waiting on the data-collection device at all — the single highest-leverage fix for the current bottleneck.

### 12.2 Independent tracks
The following tracks can proceed independently of each other, with the dependencies noted:

| Track | Depends on |
|---|---|
| Data collection | Physical device availability (sequenced per 12.1) |
| 6DMG pretraining, model training, personalization, evaluation | `load_6dmg.py` / `train_model.py` / `combine_datasets.py`; own data as it arrives |
| Autocorrect algorithm tuning | `autocorrect_prototype.py`; dictionary quality (Section 7) |
| Companion app (build) | BLE connection layer already in use for data collection (Section 6.1 schema); ideally a second device rather than waiting on the data-collection unit |
| Firmware hardening (DLPF register, BLE pairing reliability) | A device to flash and test against; ideally the second unit rather than the data-collection queue |
| Enclosure design | Fixed ESP32+MPU6050 footprint — doesn't depend on live device access |
| Paper/report | This document + the existing draft as source of truth |

---

## 13. Corrections Already Made (keep these settled, don't relitigate)
- **Form factor:** pen-grip is primary, NOT wristband — wrist rotation has fewer usable degrees of freedom, this is a genuine motor-task difficulty, not a tuning issue.
- **Filtering:** the pipeline uses EMA + deadzone + bias calibration — there is NO Madgwick filter or "$1 Recognizer" in the actual code, despite an earlier architecture diagram showing them. Code is ground truth, not the diagram.
- **v1 was already sophisticated:** Sakoe-Chiba banding, direction-reversal tolerance, shape-feature tiebreaker, spline smoothing, and idle-cursor smoothing all already existed in v1's `17.py` before v2 work started.

---

## 14. Open Checkpoints (need empirical answers, not yet known)
- Does confidence-based CNN+GRU/DTW routing actually separate correct from incorrect predictions? (needs validation once a trained model exists)
- Does the base CNN+GRU beat chance by a wide margin on real data, even the partial A–D set?
- What is the leave-one-contributor-out generalization gap?
- Does pen-grip measurably outperform wrist-strap in the planned small timing/effort comparison, or is that still just an assumption?
