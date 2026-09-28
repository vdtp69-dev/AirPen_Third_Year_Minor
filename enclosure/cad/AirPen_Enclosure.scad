// =========================================================================
// AirPen v2 — Parametric 3D Printable Enclosure (OpenSCAD)
// Group 11 · Minor Project
// =========================================================================
// Features:
// 1. Chunky marker ergonomic grip (comfortable one-handed use).
// 2. MPU6050 placed at the forward tip (nib) for maximum rotational accuracy.
// 3. Non-magnetic snap/friction fit for MPU6050 (no ferrous screws near IMU).
// 4. Ergonomic thumb/index toggle button aperture at natural grip position.
// 5. ESP32 DevKit WROOM-32 mounting bay with header clearance troughs.
// 6. Strain-relieved rear power cable exit canal.
// 7. Dual integrated strap loops for secondary wrist-worn mode (one shell, two modes).
// =========================================================================

/* [Render Selection] */
// Which part to render
part = "exploded"; // [bottom: Bottom Housing Only, top: Top Lid Only, button: Button Actuator Only, assembled: Assembled View, exploded: Exploded Assembly View]

/* [Key Dimensions & Clearances] */
$fn = 40;

// Enclosure dimensions
enclosure_length = 138.0;
body_width       = 33.0;
body_height      = 19.0;
nib_width        = 18.0;
nib_height       = 13.0;
wall_thickness   = 1.8;
tolerance        = 0.3; // FDM 3D printing clearance

// ESP32 DevKit V1 (38-pin) dimensions
esp_length       = 52.0;
esp_width        = 28.5;
esp_height       = 9.5;

// MPU6050 (GY-521) dimensions
imu_length       = 21.0;
imu_width        = 16.0;
imu_height       = 3.5;

// Tactile Button (6x6mm)
button_pos_x     = 47.0;
button_hole_dia  = 8.2;

// Strap Slots (for wrist-worn secondary mode)
strap_width      = 22.0; // Standard 20mm/22mm NATO/velcro strap
strap_slot_thick = 3.2;

// -------------------------------------------------------------------------
// Helper Modules
// -------------------------------------------------------------------------

module rounded_hull(w, h, l, r=5.0) {
    hull() {
        translate([0, -(w/2 - r), -(h/2 - r)]) rotate([0, 90, 0]) cylinder(h=l, r=r);
        translate([0,  (w/2 - r), -(h/2 - r)]) rotate([0, 90, 0]) cylinder(h=l, r=r);
        translate([0, -(w/2 - r),  (h/2 - r)]) rotate([0, 90, 0]) cylinder(h=l, r=r);
        translate([0,  (w/2 - r),  (h/2 - r)]) rotate([0, 90, 0]) cylinder(h=l, r=r);
    }
}

// Ergonomic outer pen body shape
module pen_outer_hull() {
    hull() {
        // Nib / Tip section
        translate([0, 0, 0])
            rounded_hull(nib_width, nib_height, 22.0, r=3.5);
        // Forward grip transition
        translate([22, 0, 0])
            rounded_hull(body_width, body_height, 20.0, r=5.0);
        // Main body (holding button & ESP32)
        translate([42, 0, 0])
            rounded_hull(body_width, body_height, 75.0, r=5.5);
        // Tail cable exit taper
        translate([117, 0, 0])
            rounded_hull(body_width - 2.0, body_height - 1.5, 21.0, r=5.0);
    }
}

// -------------------------------------------------------------------------
// Bottom Housing
// -------------------------------------------------------------------------
module bottom_housing() {
    difference() {
        union() {
            // Lower half of the outer shell
            intersection() {
                pen_outer_hull();
                translate([-5, -30, -30]) cube([enclosure_length + 10, 60, 30]);
            }

            // Dual Strap Loops (for wrist-worn mode)
            for (lx = [52.0, 98.0]) {
                translate([lx, -strap_width/2 - 2, -body_height/2 - 3.5])
                    cube([10, strap_width + 4, 3.5]);
                // Left & Right Loop Stanchions
                translate([lx, -strap_width/2 - 2, -body_height/2])
                    cube([10, 3.5, 4]);
                translate([lx, strap_width/2 - 1.5, -body_height/2])
                    cube([10, 3.5, 4]);
            }
        }

        // Internal Cavity
        // 1. MPU6050 Bay at the nib tip (X = 14 to 36)
        translate([14.0, -(imu_width + tolerance)/2, -body_height/2 + wall_thickness])
            cube([imu_length + tolerance, imu_width + tolerance, 15]);

        // 2. Wire pass-through & button tower (X = 36 to 55)
        translate([36.0, -9.0, -body_height/2 + wall_thickness])
            cube([19.0, 18.0, 15]);

        // 3. ESP32 DevKit Bay (X = 55 to 114)
        translate([55.0, -(esp_width + tolerance)/2, -body_height/2 + wall_thickness])
            cube([esp_length + tolerance + 2.0, esp_width + tolerance, 15]);

        // Header pin clearance troughs underneath ESP32
        translate([56.0, -esp_width/2 + 0.5, -body_height/2 + 0.6])
            cube([esp_length, 3.5, 3.0]);
        translate([56.0, esp_width/2 - 4.0, -body_height/2 + 0.6])
            cube([esp_length, 3.5, 3.0]);

        // 4. Rear Power Cable Strain-Relief Canal (X = 114 to 138)
        translate([114.0, -2.5, -2.5])
            cube([26.0, 5.0, 10.0]);

        // Stepped interlocking lip recess for top lid
        difference() {
            translate([-1, -body_width/2, -1.2])
                cube([enclosure_length + 2, body_width, 1.3]);
            translate([-2, -body_width/2 + 1.2, -2])
                cube([enclosure_length + 4, body_width - 2.4, 3]);
        }
    }

    // MPU6050 Non-magnetic friction retention tabs
    translate([15.0, -imu_width/2 - 0.2, -2.5])
        cube([3.0, 1.2, 2.5]);
    translate([15.0, imu_width/2 - 1.0, -2.5])
        cube([3.0, 1.2, 2.5]);
    translate([33.0, -imu_width/2 - 0.2, -2.5])
        cube([3.0, 1.2, 2.5]);
    translate([33.0, imu_width/2 - 1.0, -2.5])
        cube([3.0, 1.2, 2.5]);

    // Cable strain relief clamping ribs
    for (cx = [122.0, 127.0, 132.0]) {
        translate([cx, -2.2, -1.8]) cube([2.0, 1.0, 2.0]);
        translate([cx,  1.2, -1.8]) cube([2.0, 1.0, 2.0]);
    }
}

// -------------------------------------------------------------------------
// Top Lid
// -------------------------------------------------------------------------
module top_lid() {
    difference() {
        union() {
            // Upper half of the outer shell
            intersection() {
                pen_outer_hull();
                translate([-5, -30, 0]) cube([enclosure_length + 10, 60, 30]);
            }
            
            // Interlocking alignment lip (mates into bottom housing)
            translate([2, -body_width/2 + 1.2 + tolerance, -1.2])
                cube([enclosure_length - 4, body_width - 2.4 - 2*tolerance, 1.2]);

            // Ergonomic anti-slip grip ribs
            for (gx = [26.0, 30.0, 34.0, 38.0]) {
                translate([gx, -body_width/2 + 4, body_height/2 - 1.0])
                    cube([1.4, body_width - 8, 1.2]);
            }
        }

        // Internal Cavity Ceiling Hollow
        translate([12.0, -(body_width - 2*wall_thickness)/2, -2])
            cube([enclosure_length - 22, body_width - 2*wall_thickness, body_height/2]);

        // Push Button Aperture (thumb/finger toggle at natural rest)
        translate([button_pos_x, 0, 0])
            cylinder(d=button_hole_dia, h=25, center=true);

        // Rear Cable Exit Half-Port
        translate([114.0, -2.5, -0.5])
            cube([26.0, 5.0, 4.0]);
    }
}

// -------------------------------------------------------------------------
// Tactile Button Actuator Cap
// -------------------------------------------------------------------------
module button_actuator() {
    union() {
        // Bottom retaining flange (prevents falling out through top)
        cylinder(d=button_hole_dia + 2.5, h=1.5);
        // Actuator stem passing through top lid
        translate([0, 0, 1.5])
            cylinder(d=button_hole_dia - 0.6, h=4.5);
        // Tactile domed top surface
        translate([0, 0, 6.0])
            sphere(d=button_hole_dia - 0.6);
    }
}

// -------------------------------------------------------------------------
// Simulated Internal Electronics (for Assembly and Fit Inspection)
// -------------------------------------------------------------------------
module electronics_mock() {
    // MPU6050 (GY-521)
    color([0.1, 0.4, 0.8, 0.9])
        translate([15.0, -imu_width/2, -body_height/2 + wall_thickness + 0.5])
            cube([imu_length, imu_width, 1.6]);
    // IMU sensor IC
    color([0.1, 0.1, 0.1])
        translate([23.0, -2.0, -body_height/2 + wall_thickness + 2.1])
            cube([4.0, 4.0, 1.0]);

    // Push Button (6x6mm)
    color([0.2, 0.2, 0.2])
        translate([button_pos_x - 3, -3, -2.0])
            cube([6.0, 6.0, 4.5]);
    color([0.8, 0.2, 0.2])
        translate([button_pos_x, 0, 2.5])
            cylinder(d=3.2, h=3.0);

    // ESP32 DevKit WROOM-32
    color([0.15, 0.15, 0.15, 0.95])
        translate([58.0, -esp_width/2, -body_height/2 + wall_thickness + 2.0])
            cube([esp_length, esp_width, 1.6]); // PCB
    // ESP32 RF Shield
    color([0.7, 0.7, 0.7])
        translate([62.0, -9.0, -body_height/2 + wall_thickness + 3.6])
            cube([18.0, 18.0, 3.0]);
    // Micro USB Port
    color([0.6, 0.6, 0.6])
        translate([107.0, -3.8, -body_height/2 + wall_thickness + 3.6])
            cube([6.0, 7.6, 3.2]);
}

// -------------------------------------------------------------------------
// Main Render Scene Switch
// -------------------------------------------------------------------------
if (part == "bottom") {
    bottom_housing();
} else if (part == "top") {
    top_lid();
} else if (part == "button") {
    button_actuator();
} else if (part == "assembled") {
    color([0.25, 0.28, 0.32, 0.85]) bottom_housing();
    color([0.85, 0.85, 0.88, 0.85]) top_lid();
    color([0.9, 0.2, 0.2]) translate([button_pos_x, 0, body_height/2 - 2]) button_actuator();
    electronics_mock();
} else if (part == "exploded") {
    // Exploded View
    translate([0, 0, -12]) color([0.25, 0.28, 0.32, 0.9]) bottom_housing();
    electronics_mock();
    translate([0, 0, 20]) color([0.85, 0.85, 0.88, 0.8]) top_lid();
    translate([button_pos_x, 0, 32]) color([0.9, 0.2, 0.2]) button_actuator();
}
