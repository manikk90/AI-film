"""3D explainer shots in Blender: one scene, every shot in its own area, rendered headless with EEVEE.

    blender -b -P shots_template.py -- shots.json out_dir [--stills] [--fps 30]

shots.json: [{"id": "s1", "start": 0.0, "end": 3.2, "kind": "rocket|map|storm|earth|text", "label": "4 LAUNCH PADS"}]
(start/end are seconds on the voiceover clock, from forced alignment.)

- Each shot is built 40 m apart along X with its own camera, which pushes in slowly over the shot.
- Soft studio light (large area key + fill + world ambient), EEVEE, bloom on emissive parts (lights, flames, pins).
  Blender 4.2+ (EEVEE Next) has no scene.eevee.use_bloom; bloom then comes from a compositor Glare (Fog Glow) node.
- Renders 1080×1920 PNG frames per shot into out_dir/<id>/0001.png ...; --stills renders one middle frame per shot.
- 3D text is English only (Blender's text cannot shape Devanagari): Hindi captions go on in the canvas pass.
- `map` here is a placeholder plane with pins: for India, import the Natural Earth India point-of-view boundary
  (ne_10m_admin_0_countries_ind) and extrude it; never draw the outline by hand.
This is a skeleton: extend each build_* with the shot's real models.
"""
import json
import math
import sys
from pathlib import Path

import bpy

SPACING = 40.0


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) < 2:
        raise SystemExit("usage: blender -b -P shots_template.py -- shots.json out_dir [--stills] [--fps 30]")
    fps = int(argv[argv.index("--fps") + 1]) if "--fps" in argv else 30
    return Path(argv[0]), Path(argv[1]), "--stills" in argv, fps


def mat(name, color, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 0.45
    if emit:
        key = "Emission Color" if "Emission Color" in bsdf.inputs else "Emission"
        bsdf.inputs[key].default_value = (*color, 1)
        bsdf.inputs["Emission Strength"].default_value = emit
    return m


def add(obj_op, mat_, **kw):
    obj_op(**kw)
    o = bpy.context.active_object
    o.data.materials.append(mat_)
    return o


def build_rocket(x, label):
    add(bpy.ops.mesh.primitive_cylinder_add, mat("pad", (0.25, 0.27, 0.3)), radius=3, depth=0.4, location=(x, 0, 0.2))
    add(bpy.ops.mesh.primitive_cylinder_add, mat("body", (0.92, 0.92, 0.95)), radius=0.6, depth=6, location=(x, 0, 3.4))
    add(bpy.ops.mesh.primitive_cone_add, mat("nose", (0.9, 0.35, 0.1)), radius1=0.6, depth=1.4, location=(x, 0, 7.1))
    add(bpy.ops.mesh.primitive_cone_add, mat("flame", (1.0, 0.55, 0.1), emit=12), radius1=0.5, depth=1.8,
        location=(x, 0, -0.5), rotation=(math.pi, 0, 0))
    return (x, 0, 3.5)


def build_map(x, label):
    add(bpy.ops.mesh.primitive_plane_add, mat("land", (0.85, 0.78, 0.6)), size=10, location=(x, 0, 0))
    for i, (px, py) in enumerate([(-1.5, 1.0), (0.5, -1.2), (2.0, 2.0)]):
        add(bpy.ops.mesh.primitive_uv_sphere_add, mat(f"pin{i}", (1.0, 0.3, 0.2), emit=8), radius=0.25,
            location=(x + px, py, 0.5))
    return (x, 0, 0)


def build_storm(x, label):
    add(bpy.ops.mesh.primitive_plane_add, mat("sea", (0.05, 0.2, 0.35)), size=30, location=(x, 0, 0))
    for i in range(14):  # a spiral of cloud puffs
        a, r = i * 0.7, 0.6 + i * 0.35
        add(bpy.ops.mesh.primitive_ico_sphere_add, mat(f"cloud{i}", (0.92, 0.94, 0.97)), radius=0.5 + i * 0.05,
            location=(x + r * math.cos(a), r * math.sin(a), 1.5))
    return (x, 0, 1.5)


def build_earth(x, label):
    add(bpy.ops.mesh.primitive_uv_sphere_add, mat("earth", (0.1, 0.35, 0.75)), radius=4, segments=64, ring_count=32,
        location=(x, 0, 4))
    add(bpy.ops.mesh.primitive_uv_sphere_add, mat("atmo", (0.4, 0.7, 1.0), emit=1.5), radius=4.15, location=(x, 0, 4))
    return (x, 0, 4)


def build_text(x, label):
    bpy.ops.object.text_add(location=(x, 0, 2), rotation=(math.pi / 2, 0, 0))
    t = bpy.context.active_object
    t.data.body = label or ""
    t.data.align_x = "CENTER"
    t.data.extrude = 0.08
    t.data.size = 1.2
    t.data.materials.append(mat("text", (1.0, 0.55, 0.1), emit=4))
    return (x, 0, 2)


BUILD = {"rocket": build_rocket, "map": build_map, "storm": build_storm, "earth": build_earth, "text": build_text}


def camera(name, target, start_f, end_f):
    tx, ty, tz = target
    bpy.ops.object.camera_add(location=(tx, -16, tz + 3))
    cam = bpy.context.active_object
    cam.name = name
    c = cam.constraints.new("TRACK_TO")
    bpy.ops.object.empty_add(location=target)
    c.target = bpy.context.active_object
    c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    cam.location.y = -16
    cam.keyframe_insert("location", frame=start_f)
    cam.location.y = -12.5  # slow push-in
    cam.keyframe_insert("location", frame=end_f)
    if cam.animation_data and cam.animation_data.action:
        for fc in cam.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "SINE"
    return cam


def setup(scene, fps):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
    scene.render.fps = fps
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in
        scene.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.025, 0.04, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
    if hasattr(scene.eevee, "use_bloom"):  # EEVEE legacy (< 4.2)
        scene.eevee.use_bloom = True
        scene.eevee.bloom_intensity = 0.08
    else:  # EEVEE Next: bloom through the compositor
        scene.use_nodes = True
        nt = scene.node_tree
        rl = nt.nodes.get("Render Layers") or nt.nodes.new("CompositorNodeRLayers")
        comp = nt.nodes.get("Composite") or nt.nodes.new("CompositorNodeComposite")
        glare = nt.nodes.new("CompositorNodeGlare")
        glare.glare_type = "FOG_GLOW"
        glare.threshold = 1.0
        nt.links.new(rl.outputs["Image"], glare.inputs["Image"])
        nt.links.new(glare.outputs["Image"], comp.inputs["Image"])


def lights(x):
    bpy.ops.object.light_add(type="AREA", location=(x - 6, -8, 10))
    key = bpy.context.active_object
    key.data.energy, key.data.size = 2500, 8
    key.rotation_euler = (math.radians(50), 0, math.radians(-30))
    bpy.ops.object.light_add(type="AREA", location=(x + 7, -6, 5))
    fill = bpy.context.active_object
    fill.data.energy, fill.data.size = 800, 10
    fill.rotation_euler = (math.radians(70), 0, math.radians(40))


def main():
    shots_path, out_dir, stills, fps = args()
    shots = json.loads(shots_path.read_text(encoding="utf-8"))
    scene = bpy.context.scene
    setup(scene, fps)
    plan = []
    for i, s in enumerate(shots):
        x = i * SPACING
        target = BUILD.get(s.get("kind", "text"), build_text)(x, s.get("label", ""))
        lights(x)
        f0 = int(round(s["start"] * fps)) + 1
        f1 = max(f0, int(round(s["end"] * fps)))
        plan.append((s["id"], camera(f"cam_{s['id']}", target, f0, f1), f0, f1))
    for sid, cam, f0, f1 in plan:
        scene.camera = cam
        dest = out_dir / sid
        dest.mkdir(parents=True, exist_ok=True)
        frames = [(f0 + f1) // 2] if stills else range(f0, f1 + 1)
        for f in frames:
            scene.frame_set(f)
            scene.render.filepath = str(dest / f"{f:04d}.png")
            bpy.ops.render.render(write_still=True)
        print(f"shot {sid}: frames {f0}-{f1} -> {dest}")


main()
