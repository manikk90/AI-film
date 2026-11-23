/*
 * Voxel kit (studio, 2026-11-23): 3D voxel scenes for canvas films, on the vendored three.js r159
 * (third_party/three/three.min.js, MIT). Load after canvas_kit.js:
 *
 *   <script src="__STUDIO__/canvas_kit.js"></script>
 *   <script src="__STUDIO__/../third_party/three/three.min.js"></script>
 *   <script src="__STUDIO__/voxel_kit.js"></script>
 *
 *   const V = STUDIO.voxel.create({ w: 1080, h: 1920, bg: '#9fd3ff', fov: 35 });
 *   const car = V.model([[x, y, z, '#e33'], ...]);   // one InstancedMesh group per model; 1 unit = 1 voxel
 *   FILM.render = (ctx, t) => { car.position.x = ...; V.camera.position.set(...); V.draw(ctx); };
 *
 * three.js draws into its own offscreen WebGL canvas; V.draw(ctx) renders the scene and copies it onto the film's 2D
 * canvas, which is what studio/render_canvas.cjs captures. Everything is a pure function of t, like every studio film.
 */
(function () {
  'use strict';
  const K = window.STUDIO;
  if (!K) throw new Error('voxel_kit.js needs canvas_kit.js first');
  if (!window.THREE) throw new Error('voxel_kit.js needs third_party/three/three.min.js first');
  const T = window.THREE;

  function create(opt) {
    const o = Object.assign({ w: 1080, h: 1920, bg: '#000000', fov: 35, light: [0.6, 1.0, 0.4] }, opt || {});
    const glCanvas = document.createElement('canvas');            // offscreen: never the first <canvas> on the page
    glCanvas.width = o.w; glCanvas.height = o.h;
    const renderer = new T.WebGLRenderer({ canvas: glCanvas, antialias: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(1);
    renderer.setSize(o.w, o.h, false);
    renderer.outputColorSpace = T.SRGBColorSpace;
    const scene = new T.Scene();
    scene.background = new T.Color(o.bg);
    const camera = new T.PerspectiveCamera(o.fov, o.w / o.h, 0.1, 2000);
    const sun = new T.DirectionalLight(0xffffff, 2.2);
    sun.position.set(...o.light);
    scene.add(sun, new T.HemisphereLight(0xdfefff, 0x5a4630, 1.1));
    const box = new T.BoxGeometry(1, 1, 1);

    // one model = one InstancedMesh per colour, so a scene of tens of thousands of cubes stays fast
    function model(voxels) {
      const group = new T.Group();
      const byColour = new Map();
      for (const [x, y, z, c] of voxels) {
        if (!byColour.has(c)) byColour.set(c, []);
        byColour.get(c).push([x, y, z]);
      }
      const m = new T.Matrix4();
      for (const [c, cells] of byColour) {
        const mesh = new T.InstancedMesh(box, new T.MeshLambertMaterial({ color: new T.Color(c) }), cells.length);
        cells.forEach(([x, y, z], i) => { m.makeTranslation(x, y, z); mesh.setMatrixAt(i, m); });
        mesh.instanceMatrix.needsUpdate = true;
        group.add(mesh);
      }
      scene.add(group);
      return group;
    }

    // voxels of a height field: f(x, z) -> height (and colour by height), over a w x d patch centred on 0
    function terrain(w, d, f, colour) {
      const out = [];
      for (let x = 0; x < w; x++) for (let z = 0; z < d; z++) {
        const hh = Math.round(f(x, z));                     // 0 or less: no column there (water, a gap)
        for (let y = 0; y < hh; y++) out.push([x - w / 2, y, z - d / 2, colour(x, y, z, hh)]);
      }
      return model(out);
    }

    function draw(ctx) {
      renderer.render(scene, camera);
      ctx.drawImage(glCanvas, 0, 0, ctx.canvas.width, ctx.canvas.height);
    }

    function setSize(w, h) {
      glCanvas.width = w; glCanvas.height = h;
      renderer.setSize(w, h, false);
      camera.aspect = w / h; camera.updateProjectionMatrix();
    }

    return { THREE: T, scene, camera, renderer, sun, model, terrain, draw, setSize, canvas: glCanvas };
  }

  K.voxel = { create };
})();
