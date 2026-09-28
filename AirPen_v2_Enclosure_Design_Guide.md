# AirPen v2 — Enclosure Design Guide
*For: the team member owning enclosure design decisions · Group 11*

**Scope note:** this guide covers **design and specification only** — deciding the final pen shape, dimensions, component placement, and producing the CAD/print files. It does not cover physically soldering the electronics or wiring assembly — that's a separate task with its own owner (flag this to the team if it isn't assigned yet; see the note at the end of this doc).

---

## 1. What exists right now vs. what you're designing

**Current state:** ESP32 WROOM-32 DevKit + MPU6050 (GY-521 breakout) + push button, connected with breadboard jumper wires, no enclosure. Photos of this were already reviewed and confirmed the wiring is correct — you don't need to re-derive the wiring, just design a housing that fits it.

**What you're designing:** a pen-shaped enclosure that houses these three components properly, plus a strap-loop variant of the *same* enclosure for the secondary wrist-worn mode. Your deliverable is a finalized design (dimensions, component layout, CAD/print files) that whoever does the physical build can follow without needing to make layout decisions themselves.

---

## 2. What you need to know about the electronics (for layout purposes only)

```
MPU6050 connects to ESP32 via: SDA/SCL (I2C) + power + ground
Button connects to ESP32 via: one GPIO pin + ground
```
You don't need the exact pin numbers for design purposes — what matters for enclosure layout is: **3 components** (ESP32 board, MPU6050 breakout, small push button), **wired connections between them** (so they need to be close enough together that wire runs are short and manageable inside the shell), and **a cable exit point** for external power (see Section 4.3).

---

## 3. Physical dimensions — measure the real boards, don't guess from memory

Before finalizing any enclosure dimensions, **get the actual boards measured with calipers** (ask whoever has them, or do it yourself if you have access) rather than relying on generic spec-sheet numbers — board dimensions vary slightly between manufacturers even for "the same" ESP32 DevKit or GY-521 breakout, and a CAD model built on the wrong number won't fit the real part.

Rough starting expectations to plan around (verify against the actual boards before finalizing):
- ESP32 DevKit (38-pin): a rectangular board roughly in the 25-28mm × 48-55mm range, with the USB connector and pin headers adding a few mm on top of the bare board thickness.
- MPU6050 / GY-521 breakout: much smaller, roughly 15-20mm on its longer side.
- Push button: standard small tactile button footprint.

**Design constraint from the pen-grip form-factor decision:** the MPU6050 should sit as close to the "nib" end of the pen enclosure as practical — this matches how the device is meant to sense rotation/motion at the writing tip, consistent with the pen-grip precedent this project follows (Tironi et al.). The ESP32 (bulkier) should sit further back toward the body/tail of the pen.

---

## 4. Design decisions you own

### 4.1 Grip and shape
Aim for something closer to a chunky marker than a slim ballpoint — realistically the electronics won't fit in a true pen-thin diameter, and that's fine; comfortable one-hand grip matters more than looking exactly like a slim pen.

### 4.2 Button placement
The toggle button needs to be reachable by thumb or index finger without the user changing their grip. Recommend mocking this up physically first — even a cardboard/tape prototype held by a few different people — before committing to a final CAD position. Button placement mistakes are expensive to fix after a shell is printed.

### 4.3 Power/cable routing
Per the current design, power comes from an external source via a thin cable (not a battery built into the pen body). Design a clean, strain-relieved cable exit point that doesn't interfere with grip or the writing motion — this is a common failure point in wearable-adjacent enclosures if not planned deliberately.

### 4.4 One shell, two modes
The primary pen-grip housing needs a strap-loop attachment point so the *same physical enclosure* can also be worn on the wrist/forearm for the secondary mode. This was an explicit project decision (one design, two use modes) — don't design two separate enclosures.

### 4.5 Keep metal away from the MPU6050
Avoid metal fasteners or hardware directly adjacent to the IMU in your design if possible — magnetic/ferrous material close to the sensor can distort readings.

---

## 5. Design process

1. Get real component measurements (Section 3) before starting CAD — don't design around assumed dimensions.
2. Rough out the pen shape in cardboard/tape first — cheap, fast, and lets a few people physically test button reachability and grip comfort before any CAD work.
3. Model the enclosure in whatever CAD tool you're comfortable with (Fusion 360 / Tinkercad are both fine).
4. Produce a test-print file first (any FDM printer, PLA is sufficient) so whoever handles the physical build can do a fit-check against the real electronics before a "final" version is committed to.
5. Once the core shell fits, produce the strap-loop wrist variant using the same base design.

---

## 6. Your deliverable

- A finalized CAD file (or files) for the pen-grip enclosure and the wrist-strap variant.
- Documented dimensions and component placement, clear enough that whoever solders/assembles the electronics can follow it without needing to make additional layout decisions.
- A note of any constraints the assembler needs to know (e.g. "MPU6050 mounting point is X mm from the tip," "button housing needs a Y mm cutout").

## 7. Open item — flag to the team

Physical soldering/wiring assembly and the small firmware tasks (MPU6050 DLPF filter register, BLE pairing reliability check) aren't part of your scope and don't currently have an owner in the latest role split. Worth confirming with the team who's doing the actual soldering once your design is ready — ideally before a shell is finalized, since design details (like the cable exit point and component spacing) may need to reflect real constraints the person soldering runs into.
