#!/usr/bin/env python3
import os
import base64
import json

def pack_stls_to_js():
    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    js_path = os.path.join(os.path.dirname(__file__), "mesh_data.js")
    
    files = {
        'bottom': 'airpen_bottom_housing.stl',
        'top': 'airpen_top_lid.stl',
        'button': 'airpen_button_actuator.stl',
        'esp32': 'esp32_devkit_mock.stl',
        'mpu': 'mpu6050_sensor_mock.stl',
        'switch': 'tactile_button_mock.stl'
    }
    
    bundle = {}
    for key, fname in files.items():
        fpath = os.path.join(models_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "rb") as f:
                data = f.read()
                bundle[key] = {
                    'filename': fname,
                    'size': len(data),
                    'base64': base64.b64encode(data).decode('ascii')
                }
    
    with open(js_path, "w", encoding="utf-8") as out:
        out.write("// Auto-generated mesh data bundle for AirPen v2 3D Viewer\n")
        out.write("window.AIRPEN_MESHES = ")
        json.dump(bundle, out)
        out.write(";\n")
        
    print(f"Packed {len(bundle)} models into {js_path} (size: {os.path.getsize(js_path)} bytes)")

if __name__ == "__main__":
    pack_stls_to_js()
