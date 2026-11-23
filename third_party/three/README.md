# three.js r159 (vendored)

- Source: npm `three@0.159.0` (`build/three.min.js`), MIT licence (`LICENSE`), © 2010-2023 three.js authors.
- SHA-256 of `three.min.js`: `7b1c5d75b28d9de15042e2b374f83566d8c7146697af8fdeb4558b0fb528a585`.
- Why vendored: `studio/render_canvas.cjs` renders offline from `file://` pages, so a CDN or ES-module import cannot be
  used. r159 is the last release that ships the classic (UMD) build, which loads with a plain `<script>` tag.
- Used by the Voxel 3D style of `/style-montage` and `/living-painting` (`studio/voxel_kit.js`). Do not edit; replace the
  file with a newer UMD build only together with the tests in `tests/test_style_montage.py`.
