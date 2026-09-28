# AirPen v2 — Enclosure Specification & Assembly Manual
*Group 11 · Minor Project · Mechanical Design & Assembly Reference*

---

## 1. Executive Summary & Design Compliance

This manual and accompanying CAD package implement the complete enclosure system specified in [AirPen_v2_Enclosure_Design_Guide.md](file:///c:/Users/vihan/VS%20CODES/Airpen_MinorProject/AirPen_v2_Enclosure_Design_Guide.md).

### Key Accomplishments & Features
1. **Chunky Marker Form Factor:** Tapered ergonomic profile (138 mm length, 33 mm × 19 mm maximum grip cross-section, tapered to 18 mm × 13 mm at the writing nib). Gives a comfortable, fatigue-free one-handed grip matching handwriting precedents (Tironi et al.).
2. **Forward IMU Placement (Nib Tip):** The MPU-6050 (GY-521) is positioned **15.0 mm from the front tip**, maximizing sensitivity to fine finger and wrist rotational handwriting dynamics.
3. **Strict Non-Ferrous Sensor Zone:** The MPU-6050 is secured using built-in **3D-printed friction-retention tabs** without magnetic or ferrous screws, preventing magnetometer/accelerometer drift or distortion.
4. **Ergonomic Trigger Button:** Positioned on the upper contour at **47.0 mm from the tip**, directly resting beneath the natural index-finger or thumb grip position.
5. **One Shell, Two Modes (Pen + Wrist):** The underside incorporates **dual 22.0 mm × 3.5 mm strap loops** spaced 46 mm apart. It accepts standard 20 mm or 22 mm NATO, velcro, or elastic watchbands, allowing the exact same housing to be clipped or strapped to the forearm/wrist for secondary mode operation.
6. **Integrated Cable Strain Relief:** The tail features a 4.5 mm clamped serpentine channel that firmly grips the external power cable, preventing mechanical stress from reaching the ESP32 USB connector or internal solder points.
7. **Production & Inspection Deliverables:**
   - Watertight binary STL models ready for FDM 3D printing (`enclosure/models/`).
   - Fully parametric OpenSCAD source file (`enclosure/cad/AirPen_Enclosure.scad`).
   - Interactive 3D WebGL / Three.js assembly explorer with Exploded View and X-Ray inspection (`enclosure/viewer/index.html`).

---

## 2. Dimensional Blueprint & Component Layout

```
                        ◄───────────────────── 138.0 mm ─────────────────────►
 ┌───────────────┐
 │               │   MPU-6050           Tactile Button            ESP32 DevKit V1 (38-pin)       Strain Relief
 │  Writing Nib  │  (GY-521)              (GPIO4)                  (WROOM-32 MCU)                 & Cable Exit
 │  18mm x 13mm  │  X=15-36mm             X=47mm                   X=55-114mm                    X=118-138mm
 └───────┬───────┴──────┬───────────────────┬───────────────────────────┬──────────────────────────────┬─────────┘
         │              │                   │                           │                              │
         ▼              ▼                   ▼                           ▼                              ▼
     [Taper]       [IMU Bay]        [Finger Trigger]               [MCU Bay]                     [Clamp Canal]
    0 to 15mm     17 x 22 x 4mm      Ø8.2mm Aperture            29.5 x 56 x 10mm                   Ø4.5mm
```

### Critical Component Placement Specifications

| Component | Target Location (from Nib Tip) | Internal Cavity Dimensions | Retention / Fastening Method |
|---|---|---|---|
| **MPU-6050 (GY-521)** | **15.0 mm to 36.0 mm** | 17.0 mm (W) × 22.0 mm (L) × 4.0 mm (D) | Dual plastic snap-retention tabs (non-ferrous, zero screws) |
| **Tactile Push Button** | **47.0 mm** (centered) | 8.2 mm circular aperture (top lid) | Captive button pusher cap with 10.5 mm bottom flange |
| **ESP32 DevKit V1** | **55.0 mm to 114.0 mm** | 29.5 mm (W) × 56.0 mm (L) × 10.0 mm (D) | Dual lateral support shelves + 3.0 mm under-PCB pin relief troughs |
| **Dual Wrist Strap Loops** | Loop 1: **52.0 mm**, Loop 2: **98.0 mm** | 22.0 mm (Slot Width) × 3.5 mm (Height) | Integrated into bottom housing shell (monolithic print) |
| **Power Cable Exit** | **118.0 mm to 138.0 mm** | 4.5 mm diameter serpentine canal | 3-tooth compression clamp ribs on top and bottom shells |

---

## 3. Bill of Materials (BOM) & Pre-Fabrication Checklist

### Electronics
1. **ESP32 WROOM-32 DevKit V1 (38-pin)**: Main microcontroller.
2. **MPU-6050 (GY-521 Breakout Board)**: 6-axis IMU (3-axis gyroscope + 3-axis accelerometer).
3. **6 mm × 6 mm Tactile Push Button**: 4.3 mm to 7.0 mm height.
4. **Flexible Silicone Hookup Wires (28 AWG or 30 AWG)**: Highly recommended for flexibility inside the shell.
5. **External USB Power Cable (or 2-core 5V/GND wire)**: 3.5 mm to 4.5 mm outer jacket diameter.

### 3D Printed Parts
| File Name | Description | Material | Quantity |
|---|---|---|---|
| [`airpen_bottom_housing.stl`](file:///c:/Users/vihan/VS%20CODES/Airpen_MinorProject/enclosure/models/airpen_bottom_housing.stl) | Lower cradle with IMU bed, ESP32 rails, cable clamp & strap loops | PLA / PETG | 1 |
| [`airpen_top_lid.stl`](file:///c:/Users/vihan/VS%20CODES/Airpen_MinorProject/enclosure/models/airpen_top_lid.stl) | Upper ergonomic lid with button aperture, grip ribs & mating lip | PLA / PETG | 1 |
| [`airpen_button_actuator.stl`](file:///c:/Users/vihan/VS%20CODES/Airpen_MinorProject/enclosure/models/airpen_button_actuator.stl) | Tactile pusher button cap with retaining flange | PLA / PETG / Resin | 1 |
| [`airpen_full_assembly.stl`](file:///c:/Users/vihan/VS%20CODES/Airpen_MinorProject/enclosure/models/airpen_full_assembly.stl) | Reference complete assembly for slicer preview & verification | - | 1 |

---

## 4. 3D Printing Recipe & Slicer Recommendations

To ensure reliable tolerances and snap fits without post-processing:

* **Slicer Software:** Bambu Studio, PrusaSlicer, OrcaSlicer, or Cura.
* **Material:**
  * **PLA:** Recommended for rapid fit-check prototypes (stiff, minimal shrinkage).
  * **PETG:** Recommended for the final functional enclosure (superior layer adhesion, impact resistance, and flex for snap tabs).
* **Layer Height:** `0.20 mm` (or `0.16 mm` for smoother curved grip surfaces).
* **Wall Loops / Perimeters:** `3` or `4` (minimum `1.2 mm` shell thickness for rigidity).
* **Top / Bottom Solid Layers:** `5` layers.
* **Infill:** `20% to 25%` (Gyroid or Grid pattern).
* **Print Orientation:**
  * **Bottom Housing:** Place flat bottom / split line down on build plate. Use **Tree Supports** set to "Build Plate Only" to support the strap loop bridges.
  * **Top Lid:** Place split seam face flat on the build plate (zero supports needed for internal dome!).
  * **Button Actuator:** Place wide flange flat on build plate (zero supports needed).
* **Dimensional Compensation:**
  * XY Hole Compensation: `+0.1 mm` (if your printer runs tight).
  * Internal tolerance designed into CAD: `0.30 mm` standard clearance.

---

## 5. Wiring & Solder Lead Specifications

Before securing components into the enclosure, cut and strip the wires to the exact recommended lengths. This eliminates wire bunching and prevents pinching when the lid is closed.

```
       [MPU6050] ────(55mm Wires: 3.3V, GND, GPIO21, GPIO22)────┐
                                                                 ▼
       [BUTTON]  ────(25mm Wires: GPIO4, GND)─────────────► [ESP32 DevKit]
                                                                 ▲
       [EXTERNAL 5V/GND POWER] ───(Rear Exit Strain Relief)──────┘
```

### Wire Cut Lengths

| Connection | Origin Pin | Destination Pin | Cut Length | Notes |
|---|---|---|---|---|
| **IMU Power** | MPU6050 `VCC` | ESP32 `3.3V` | **55 mm** | ⚠ NEVER connect to VIN |
| **IMU Ground** | MPU6050 `GND` | ESP32 `GND` | **55 mm** | Common ground |
| **IMU I2C Data** | MPU6050 `SDA` | ESP32 `GPIO21` | **55 mm** | GY-521 has built-in pullups |
| **IMU I2C Clock** | MPU6050 `SCL` | ESP32 `GPIO22` | **55 mm** | Standard ESP32 I2C pins |
| **Trigger Signal** | Button Leg 1 | ESP32 `GPIO4` | **25 mm** | Internal pullup enabled in code |
| **Trigger Ground** | Button Leg 2 | ESP32 `GND` | **25 mm** | Connect to nearest ground |
| **External USB Cable** | USB 5V & GND | ESP32 Micro-USB (or 5V/GND) | **Clamp at 125 mm** | Outer jacket clamped in relief |

> [!CAUTION]
> **Soldering Advice for Low-Profile Assembly:**
> If using an ESP32 board with pre-soldered male pin headers, the enclosure features lower relief troughs to accommodate them. However, for the cleanest and lightest assembly, desoldering the bulky headers and soldering flexible silicone wires directly to the through-holes saves ~5 mm of internal height and reduces total pen weight by ~14 grams.

---

## 6. Step-by-Step Mechanical Assembly Procedure

1. **Fit-Check the Electronics (Dry Run):**
   - Place the bare MPU-6050 board into the front pocket. Confirm the board rests completely flat against the base and the front edge is ~15 mm from the tip.
   - Test-seat the ESP32 into the rear bay. Ensure the Micro-USB port faces toward the tail cable canal.
2. **Wire Assembly & Continuity Check:**
   - Solder the wires according to Section 5.
   - Run the firmware test sketch (`Blink`, `Wire.h` I2C scan, and button trigger) to verify electrical integrity before closing the shell.
3. **Mounting the MPU-6050:**
   - Slide the front edge of the MPU-6050 under the forward locating stop.
   - Gently press down until the side retention clips click over the board edge. No screws or adhesives required!
4. **Installing the Button & Actuator:**
   - Insert the `airpen_button_actuator.stl` into the top lid from the *inside* (flange stays inside the lid).
   - Place the tactile switch onto the button riser in the bottom shell (or secure with a small drop of hot glue / foam tape).
5. **Routing the Power Cable:**
   - Route the external USB cable through the rear strain relief teeth (X = 120 to 135 mm).
   - Press the cable jacket into the clamping ribs. Pull gently on the outside wire to verify that the clamp resists axial tension.
6. **Closing the Enclosure:**
   - Tuck wire slack into the transition bay between the button and ESP32.
   - Align the stepped interlocking lip of `airpen_top_lid.stl` with the groove on `airpen_bottom_housing.stl`.
   - Press firmly together until the seam is flush along the perimeter.
   - For temporary testing, secure with a narrow strip of Kapton tape or friction fit. For permanent use, a thin bead of B-7000 electronics adhesive or two non-magnetic M2 nylon screws can be applied.
7. **Wrist-Worn Mode Setup:**
   - Thread a 20 mm or 22 mm velcro/NATO watchstrap through the two integrated underside slots.
   - Strap to the dorsal side of the wrist or forearm. The IMU remains oriented forward in the direction of the hand.

---

## 7. Interactive 3D Viewer & CAD Verification

To inspect the 3D model, explode the assembly, or check clearances:
1. Open [`enclosure/viewer/index.html`](file:///c:/Users/vihan/VS%20CODES/Airpen_MinorProject/enclosure/viewer/index.html) in any standard web browser (Chrome, Edge, Firefox).
2. Features available:
   - **Exploded View Slider (0% to 100%):** View each individual part separating along the Z-axis.
   - **X-Ray Slider (0% to 100%):** See through the shell to verify MPU-6050, button, and ESP32 placement.
   - **Mode Switch (Pen Grip vs. Wrist Wearable):** Renders the simulated wrist straps through the integrated loops.
   - **Quick Camera Presets:** Isometric, Top, Side, Nib Tip, and Tail Port views.
   - **STL Downloads:** Direct download links for all generated parts.
