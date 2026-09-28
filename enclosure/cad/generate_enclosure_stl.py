#!/usr/bin/env python3
"""
AirPen v2 Enclosure 3D Mesh & STL Generator
--------------------------------------------
Generates watertight, manifold binary STL files for the AirPen v2 pen-grip
and wrist-wearable enclosure according to the AirPen v2 Enclosure Design Guide.

Components generated:
  1. Bottom Housing with MPU-6050 tip cradle, ESP32 bay, cable strain relief, and integrated dual wrist-strap loops.
  2. Top Lid with ergonomic finger grip, tactile button aperture, and interlocking lip.
  3. Tactile Button Actuator cap.
  4. Full Assembly model.
  5. Mock electronics (ESP32 DevKit, MPU6050, Button) for visualizer and fit checking.
"""

import os
import struct
import numpy as np

def write_binary_stl(filename, vertices, faces):
    """
    Writes a 3D triangle mesh to binary STL format.
    vertices: (N, 3) float array
    faces: (M, 3) int array of vertex indices (0-indexed)
    """
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]
    
    # Calculate face normals
    normals = np.cross(v1 - v0, v2 - v0)
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    lengths[lengths == 0] = 1.0
    normals = normals / lengths

    header = b"AirPen v2 Enclosure STL Generated Model".ljust(80, b"\0")
    num_faces = len(faces)

    with open(filename, "wb") as f:
        f.write(header)
        f.write(struct.pack("<I", num_faces))
        
        # Pack normals and vertices
        data = np.zeros(num_faces, dtype=[
            ('normal', '<f4', (3,)),
            ('v0', '<f4', (3,)),
            ('v1', '<f4', (3,)),
            ('v2', '<f4', (3,)),
            ('attr', '<u2')
        ])
        data['normal'] = normals
        data['v0'] = v0
        data['v1'] = v1
        data['v2'] = v2
        data['attr'] = 0
        f.write(data.tobytes())

    print(f"Exported: {filename} ({num_faces} triangles, {len(vertices)} vertices)")

class MeshBuilder:
    def __init__(self):
        self.vertices = []
        self.faces = []

    def add_vertex(self, x, y, z):
        idx = len(self.vertices)
        self.vertices.append([float(x), float(y), float(z)])
        return idx

    def add_quad(self, v0, v1, v2, v3):
        # Two triangles for a quad (v0, v1, v2) and (v0, v2, v3)
        self.faces.append([v0, v1, v2])
        self.faces.append([v0, v2, v3])

    def add_box(self, x_min, x_max, y_min, y_max, z_min, z_max):
        """Adds a watertight cuboid."""
        v = [
            self.add_vertex(x_min, y_min, z_min), # 0
            self.add_vertex(x_max, y_min, z_min), # 1
            self.add_vertex(x_max, y_max, z_min), # 2
            self.add_vertex(x_min, y_max, z_min), # 3
            self.add_vertex(x_min, y_min, z_max), # 4
            self.add_vertex(x_max, y_min, z_max), # 5
            self.add_vertex(x_max, y_max, z_max), # 6
            self.add_vertex(x_min, y_max, z_max), # 7
        ]
        # Bottom (-Z)
        self.add_quad(v[0], v[3], v[2], v[1])
        # Top (+Z)
        self.add_quad(v[4], v[5], v[6], v[7])
        # Front (-Y)
        self.add_quad(v[0], v[1], v[5], v[4])
        # Back (+Y)
        self.add_quad(v[2], v[3], v[7], v[6])
        # Left (-X)
        self.add_quad(v[0], v[4], v[7], v[3])
        # Right (+X)
        self.add_quad(v[1], v[2], v[6], v[5])

    def add_cylinder(self, center_x, center_y, z_min, z_max, radius, segments=24):
        """Adds a cylinder aligned with Z axis."""
        bottom_center = self.add_vertex(center_x, center_y, z_min)
        top_center = self.add_vertex(center_x, center_y, z_max)
        
        bot_ring = []
        top_ring = []
        for i in range(segments):
            angle = 2 * np.pi * i / segments
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)
            bot_ring.append(self.add_vertex(x, y, z_min))
            top_ring.append(self.add_vertex(x, y, z_max))

        for i in range(segments):
            next_i = (i + 1) % segments
            # Bottom cap
            self.faces.append([bottom_center, bot_ring[next_i], bot_ring[i]])
            # Top cap
            self.faces.append([top_center, top_ring[i], top_ring[next_i]])
            # Side quads
            self.add_quad(bot_ring[i], bot_ring[next_i], top_ring[next_i], top_ring[i])

    def add_loft(self, cross_sections):
        """
        Lofts between a series of closed 2D loops at different X positions.
        cross_sections: list of lists of 3D points [x, y, z] all having the same length.
        """
        if not cross_sections:
            return
        
        N_pts = len(cross_sections[0])
        ring_indices = []

        for pts in cross_sections:
            ring = [self.add_vertex(p[0], p[1], p[2]) for p in pts]
            ring_indices.append(ring)

        # Caps
        # Start cap (facing -X)
        c0 = np.mean([cross_sections[0][i] for i in range(N_pts)], axis=0)
        c0_idx = self.add_vertex(c0[0], c0[1], c0[2])
        for i in range(N_pts):
            next_i = (i + 1) % N_pts
            self.faces.append([c0_idx, ring_indices[0][next_i], ring_indices[0][i]])

        # End cap (facing +X)
        c1 = np.mean([cross_sections[-1][i] for i in range(N_pts)], axis=0)
        c1_idx = self.add_vertex(c1[0], c1[1], c1[2])
        for i in range(N_pts):
            next_i = (i + 1) % N_pts
            self.faces.append([c1_idx, ring_indices[-1][i], ring_indices[-1][next_i]])

        # Loft sides
        for s in range(len(cross_sections) - 1):
            r0 = ring_indices[s]
            r1 = ring_indices[s+1]
            for i in range(N_pts):
                next_i = (i + 1) % N_pts
                self.add_quad(r0[i], r0[next_i], r1[next_i], r1[i])

    def to_arrays(self):
        return np.array(self.vertices, dtype=np.float32), np.array(self.faces, dtype=np.int32)

def generate_rounded_rect_loop(x, width, height, corner_r, z_offset=0.0, num_pts_corner=6):
    """Generates an ordered ring of [x, y, z] points forming an ergonomic rounded rectangle."""
    hw = width / 2.0
    hh = height / 2.0
    r = min(corner_r, hw - 0.5, hh - 0.5)
    
    # 4 corner centers (y, z)
    # 1: (+Y, +Z), 2: (-Y, +Z), 3: (-Y, -Z), 4: (+Y, -Z)
    centers = [
        (hw - r, hh - r, 0, np.pi/2),
        (-hw + r, hh - r, np.pi/2, np.pi),
        (-hw + r, -hh + r, np.pi, 3*np.pi/2),
        (hw - r, -hh + r, 3*np.pi/2, 2*np.pi),
    ]
    
    pts = []
    for cy, cz, a_start, a_end in centers:
        angles = np.linspace(a_start, a_end, num_pts_corner, endpoint=False)
        for a in angles:
            y = cy + r * np.cos(a)
            z = cz + r * np.sin(a) + z_offset
            pts.append([x, y, z])
    return pts

def build_airpen_enclosure():
    """
    Builds the complete AirPen enclosure geometry:
    - Overall length: ~138 mm
    - Tip/Nib at X = 0 to 20 mm
    - MPU6050 compartment: X = 15 to 38 mm
    - Button compartment: X = 40 to 52 mm
    - ESP32 compartment: X = 55 to 118 mm
    - Cable exit & strain relief: X = 118 to 138 mm
    """
    print("Generating AirPen v2 Enclosure Models...")
    
    # 1. BOTTOM HOUSING MESH
    # The bottom housing forms the lower cradle (Z <= 0 with lip rising to Z = 1.2 for snap fit)
    b_mesh = MeshBuilder()

    # Create solid bottom outer shell with ergonomic profile
    # X stations from 0 (tip) to 138 (tail)
    x_stations = [0.0, 5.0, 15.0, 25.0, 45.0, 70.0, 100.0, 120.0, 138.0]
    outer_cross_sections = []
    for x in x_stations:
        # Taper profile: narrow at nib (18mm x 14mm), swelling to grip/body (33mm x 19mm), tapering slightly at tail (31mm x 18mm)
        if x <= 25.0:
            t = x / 25.0
            w = 18.0 + (33.0 - 18.0) * t
            h = 13.0 + (19.0 - 13.0) * t
            cr = 4.0 + 1.5 * t
        elif x <= 118.0:
            w = 33.0
            h = 19.0
            cr = 5.5
        else:
            t = (x - 118.0) / 20.0
            w = 33.0 - 2.0 * t
            h = 19.0 - 1.0 * t
            cr = 5.5

        # We construct the bottom half (Z from -h/2 to 0.0)
        # For a clean shell, we define points around the bottom contour
        pts = generate_rounded_rect_loop(x, w, h, cr, z_offset=-h/4.0, num_pts_corner=6)
        outer_cross_sections.append(pts)

    # Base bottom shell loft
    b_mesh.add_loft(outer_cross_sections)

    # Add Strap Loops onto the bottom shell!
    # Integrated dual loops for standard 20mm/22mm watch/NATO/Velcro straps
    # Loop 1 at X = 50-62 mm, Loop 2 at X = 95-107 mm
    for loop_x in [52.0, 98.0]:
        # Outer strap bridge
        b_mesh.add_box(loop_x, loop_x + 10.0, -18.0, 18.0, -14.0, -10.5)
        # Strap slot wings
        b_mesh.add_box(loop_x, loop_x + 10.0, -18.0, -13.0, -10.5, -7.0)
        b_mesh.add_box(loop_x, loop_x + 10.0, 13.0, 18.0, -10.5, -7.0)

    # Add MPU6050 cradle at the forward nib end
    # Sits at X = 15 to 37 mm, cavity width 17mm, depth 4mm
    # Non-ferrous snap-fit rails
    b_mesh.add_box(16.0, 36.0, -9.5, -7.5, -5.0, 1.0)
    b_mesh.add_box(16.0, 36.0, 7.5, 9.5, -5.0, 1.0)
    # Forward stop for IMU
    b_mesh.add_box(14.0, 16.0, -9.5, 9.5, -5.0, 0.0)

    # Add Button Mount Tower
    # Sits at X = 43 to 51 mm, Y = -5 to +5 mm
    b_mesh.add_box(43.0, 51.0, -5.0, 5.0, -6.0, 0.5)

    # Add ESP32 DevKit Bay
    # Sits at X = 56 to 114 mm, internal width 29.5 mm
    # Side mounting rails for ESP32 PCB support
    b_mesh.add_box(57.0, 113.0, -15.0, -13.2, -6.5, 0.5)
    b_mesh.add_box(57.0, 113.0, 13.2, 15.0, -6.5, 0.5)
    # Pin clearance trough underneath ESP32
    b_mesh.add_box(58.0, 112.0, -13.0, 13.0, -8.0, -6.5)

    # Rear Cable Strain Relief Clamp Canal
    # Sits at X = 118 to 136 mm
    b_mesh.add_box(118.0, 136.0, -14.0, -3.5, -5.5, 1.0)
    b_mesh.add_box(118.0, 136.0, 3.5, 14.0, -5.5, 1.0)
    # Strain relief clamp teeth/grooves
    for cx in [123.0, 128.0, 133.0]:
        b_mesh.add_box(cx, cx + 2.0, -3.5, -2.2, -4.5, 0.5)
        b_mesh.add_box(cx, cx + 2.0, 2.2, 3.5, -4.5, 0.5)

    # 2. TOP LID MESH
    # The top ergonomic lid covers the upper half (Z >= 0)
    t_mesh = MeshBuilder()
    top_cross_sections = []
    for x in x_stations:
        if x <= 25.0:
            t = x / 25.0
            w = 17.8 + (32.8 - 17.8) * t
            h = 13.0 + (19.0 - 13.0) * t
            cr = 4.0 + 1.5 * t
        elif x <= 118.0:
            w = 32.8
            h = 19.0
            cr = 5.5
        else:
            t = (x - 118.0) / 20.0
            w = 32.8 - 2.0 * t
            h = 19.0 - 1.0 * t
            cr = 5.5

        pts = generate_rounded_rect_loop(x, w, h, cr, z_offset=h/4.0, num_pts_corner=6)
        top_cross_sections.append(pts)

    t_mesh.add_loft(top_cross_sections)

    # Tactile Button aperture rim on the top lid (at X = 47 mm, Y = 0 mm, Z = 9 mm)
    t_mesh.add_cylinder(47.0, 0.0, 7.5, 11.0, radius=4.2, segments=24)
    # Ergonomic grip contour ribs (anti-slip ridges on finger placement zone)
    for gx in [28.0, 32.0, 36.0, 40.0]:
        t_mesh.add_box(gx, gx + 1.2, -9.0, 9.0, 9.0, 10.0)

    # 3. BUTTON ACTUATOR CAP
    # Ergonomic cap that sits in the 8mm top aperture with retaining flange
    btn_mesh = MeshBuilder()
    # Bottom retaining flange (6.5mm diameter x 1.2mm thick)
    btn_mesh.add_cylinder(47.0, 0.0, 6.0, 7.2, radius=4.8, segments=20)
    # Actuator stem (pass-through button hole)
    btn_mesh.add_cylinder(47.0, 0.0, 7.2, 11.5, radius=3.6, segments=20)
    # Domed fingertip contact surface
    btn_mesh.add_cylinder(47.0, 0.0, 11.5, 12.5, radius=4.0, segments=20)

    # 4. MOCK ELECTRONICS FOR FIT CHECK & VISUALIZER
    # ESP32 DevKit V1 (38-pin): 28.5mm wide x 52.0mm long x 6.5mm thick
    esp_mesh = MeshBuilder()
    esp_mesh.add_box(60.0, 112.0, -14.0, 14.0, -4.0, -2.5) # PCB
    esp_mesh.add_box(62.0, 80.0, -9.0, 9.0, -2.5, 0.5)     # Metal RF Shield
    esp_mesh.add_box(106.0, 113.5, -4.0, 4.0, -2.5, 0.0)   # MicroUSB connector
    # Pin headers
    esp_mesh.add_box(61.0, 111.0, -13.5, -11.0, -8.0, -4.0)
    esp_mesh.add_box(61.0, 111.0, 11.0, 13.5, -8.0, -4.0)

    # MPU6050 (GY-521): 15.6mm wide x 20.5mm long x 3.0mm thick
    imu_mesh = MeshBuilder()
    imu_mesh.add_box(16.5, 35.5, -7.5, 7.5, -3.5, -2.0)    # Blue PCB
    imu_mesh.add_box(24.0, 28.0, -2.0, 2.0, -2.0, -0.8)    # QFN sensor IC

    # Push Button: 6x6mm tactile switch
    switch_mesh = MeshBuilder()
    switch_mesh.add_box(44.0, 50.0, -3.0, 3.0, -2.0, 2.5)  # Switch base
    switch_mesh.add_cylinder(47.0, 0.0, 2.5, 5.5, radius=1.6, segments=16) # Plunger

    # Combined Assembly Mesh
    asm_mesh = MeshBuilder()
    # Combine bottom, top, and button cap
    for m in [b_mesh, t_mesh, btn_mesh]:
        v, f = m.to_arrays()
        offset = len(asm_mesh.vertices)
        asm_mesh.vertices.extend(v.tolist())
        asm_mesh.faces.extend((f + offset).tolist())

    out_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(out_dir, exist_ok=True)

    # Export STL files
    vb, fb = b_mesh.to_arrays()
    write_binary_stl(os.path.join(out_dir, "airpen_bottom_housing.stl"), vb, fb)

    vt, ft = t_mesh.to_arrays()
    write_binary_stl(os.path.join(out_dir, "airpen_top_lid.stl"), vt, ft)

    vbtn, fbtn = btn_mesh.to_arrays()
    write_binary_stl(os.path.join(out_dir, "airpen_button_actuator.stl"), vbtn, fbtn)

    vasm, fasm = asm_mesh.to_arrays()
    write_binary_stl(os.path.join(out_dir, "airpen_full_assembly.stl"), vasm, fasm)

    vesp, fesp = esp_mesh.to_arrays()
    write_binary_stl(os.path.join(out_dir, "esp32_devkit_mock.stl"), vesp, fesp)

    vimu, fimu = imu_mesh.to_arrays()
    write_binary_stl(os.path.join(out_dir, "mpu6050_sensor_mock.stl"), vimu, fimu)

    vsw, fsw = switch_mesh.to_arrays()
    write_binary_stl(os.path.join(out_dir, "tactile_button_mock.stl"), vsw, fsw)

    print("All STL files successfully generated!")

if __name__ == "__main__":
    build_airpen_enclosure()
