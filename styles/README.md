# Style library (drafts)

Style prompts for films rendered entirely in code (Canvas 2D, WebGL, three.js, sampled and synthesised audio), in the same format as the [Lemo-Opuscar](https://github.com/lemomo-ai/lemo-opuscar) style library (MIT). Each folder holds:

| File | What it holds |
|---|---|
| `style.json` | metadata: slug, number, English / Hindi / Chinese names, category, status, a proposed demo idea, uses, nearest Lemo-Opuscar styles |
| `STYLE.md` | the style's invariants only, in 11 fixed sections: essence, materials & rendering, colour logic, type & subtitles, motion, camera grammar, sound palette, native moves, pitfalls, engine, variation space |

**Status: every style here is a `draft`.** None has a demo film, `DEMO.md`, stills or engine code yet. They are written prompts, not tested looks: before one is treated as a library style it needs a demo film made in code and the Lemo-Opuscar `MAINTAINING.md` gates (human approval of the style frame and the film; voice, loudness and reading-time checks). The "Proposed demo" line is an idea, not a made film.

None of these duplicates the 66 Lemo-Opuscar library styles or the 98 OPUSCAR 98 style prompts (checked 2026-11-01).

Making a film in one of the "Claude animation styles" (pixel art, PS2, glow sketch, ZackD-type 3D explainers and more): see [CLAUDE-ANIMATION-WORKFLOW.md](CLAUDE-ANIMATION-WORKFLOW.md) for where each style lives, the build steps and a starting prompt per style.

## Use one

- **With the Lemo-Opuscar library:** copy a folder to `~/lemo-my-styles/<slug>/` (its "my styles" location) and ask for a film in it by name. The agent reads `STYLE.md` the way it reads a library style; there is no demo engine yet, so §10 lists what to build first.
- **With AI-film:** use a `STYLE.md` as the creative-direction reference for a project's look (`skills/creative-direction`); its rules are tool-agnostic.

Living traditions (the Indian and world folk styles) are described as visual grammar, with credit to their communities. Do not present a code-made film as authentic handmade craft, and consult or credit artists of the tradition for commercial work.

## Maintain

Edit `style.json` / `STYLE.md`, then run `python3 styles/build_index.py` to rebuild the index below and `catalog.json`; `python3 -m unittest tests.test_styles -v` checks every folder (keys, the 11 headings, size, status line).

## Index

<!-- index:start -->
74 styles.

### Indian Traditions · भारतीय परंपरा (16)

| # | Style | हिंदी | Slug | Status | Proposed demo |
|---|---|---|---|---|---|
| 01 | [Madhubani](madhubani/STYLE.md) | मधुबनी | `madhubani` | draft | one monsoon day at a village pond, where every fish, lotus and bird is drawn in a double outline and then hatched and patterned until no bare ground is left. |
| 02 | [Warli](warli/STYLE.md) | वारली | `warli` | draft | a harvest day on a hillside village, told by hundreds of white triangle figures who plough, carry, cook and finally join one turning spiral of dancers. |
| 03 | [Gond](gond/STYLE.md) | गोंड | `gond` | draft | a single forest tree through one night, its trunk, birds and the deer beneath it filled with rows of dots and dashes that flow like sap as the animals wake. |
| 04 | [Kalamkari](kalamkari/STYLE.md) | कलमकारी | `kalamkari` | draft | how a river town's ferry works, told in pen-drawn cloth panels where each red area appears only after an invisible mordant is painted and the cloth is dipped in the dye bath. |
| 05 | [Pattachitra](pattachitra/STYLE.md) | पट्टचित्र | `pattachitra` | draft | a fisherman's week on the Odisha coast, laid out as a grid of bordered panels on a red ground, each panel painted border first and outlined in black last. |
| 06 | [Phad Scroll](phad-scroll/STYLE.md) | फड़ | `phad-scroll` | draft | a camel caravan's crossing of the desert, painted on one long cloth scroll in the dark, where only the part the storyteller's lamp touches lights up and moves. |
| 07 | [Kalighat Pat](kalighat/STYLE.md) | कालीघाट पट | `kalighat` | draft | a city office worker's morning commute as a run of satirical portraits, each figure drawn in one sweeping brush outline on blank paper and shaded soft along its edge. |
| 08 | [Pichwai](pichwai/STYLE.md) | पिछवाई | `pichwai` | draft | a lotus pond through the seasons, one cloth hanging lowered over another, rows of cows and lotuses changing with the light until the full-moon night turns everything to white and silver. |
| 09 | [Tanjore](tanjore/STYLE.md) | तंजौर | `tanjore` | draft | a temple-town goldsmith's workshop seen as a gilded panel, where a lamp moves across raised gesso and inlaid stones and each gleam marks one step of the craft. |
| 10 | [Mughal Miniature](mughal-miniature/STYLE.md) | मुग़ल लघुचित्र | `mughal-miniature` | draft | a garden through one day, seen as an album page with gold margins, where the camera leans in with a magnifier and each closer look reveals finer brushwork and a new small event. |
| 11 | [Kerala Mural](kerala-mural/STYLE.md) | केरल भित्तिचित्र | `kerala-mural` | draft | a fishing village's day told along one long plastered wall, each figure painted in from its ochre sketch to full five-pigment colour as an oil lamp travels across it. |
| 12 | [Bollywood Hand-painted Poster](bollywood-poster/STYLE.md) | हाथ से बना फ़िल्मी पोस्टर | `bollywood-poster` | draft | a small-town tailor's ordinary week sold like a blockbuster, as a painter on scaffolding brushes giant faces and a hand-lettered title onto a cinema hoarding. |
| 13 | [Indian Truck Art](truck-art/STYLE.md) | ट्रक आर्ट | `truck-art` | draft | one night's highway journey told on the panels of a single goods truck, its painted parrots and slogans waking up whenever headlights sweep the reflective tape. |
| 14 | [Kolam / Rangoli](kolam-rangoli/STYLE.md) | कोलम / रंगोली | `kolam-rangoli` | draft | a lane of doorsteps at dawn, each kolam drawn in rice flour around its dot grid by an unseen hand, until the loops join into one line running down the whole street. |
| 15 | [Mehndi](mehndi/STYLE.md) | मेहंदी | `mehndi` | draft | a family's history drawn as henna growing over one palm, paisley by vine, with an invented name hidden in the pattern, then drying, flaking and leaving its deepening stain. |
| 16 | [Kathputli Marionette](kathputli/STYLE.md) | कठपुतली | `kathputli` | draft | a village-fair marionette show about a stubborn camel who will not cross a bridge, with the puppeteer's strings rising out of a small arched booth. |

### World Folk · विश्व लोक कला (13)

| # | Style | हिंदी | Slug | Status | Proposed demo |
|---|---|---|---|---|---|
| 17 | [Yarn Painting](yarn-painting/STYLE.md) | धागा चित्र | `yarn-painting` | draft | how a mountain spring becomes a valley's river, coiled strand by strand into one wax board, each shape outlined in a contrasting yarn and filled with echo lines. |
| 18 | [Mola Appliqué](mola-applique/STYLE.md) | मोला कपड़ा कला | `mola-applique` | draft | a coral reef's food chain revealed by cutting through layers of cloth, each creature appearing as the top colour is opened to show the colours beneath. |
| 19 | [Persian Miniature](persian-miniature/STYLE.md) | फ़ारसी लघुचित्र | `persian-miniature` | draft | one day in a walled garden seen from above and from the side at once, its pool, terraces and pavilions coming alive while the gold sky turns to lapis night. |
| 20 | [Thangka](thangka/STYLE.md) | थांगका | `thangka` | draft | the water cycle of a Himalayan valley built in thangka grammar from charcoal grid to gold line, a glacier peak at the centre and cloud scrolls, rivers and villages in the registers around it. |
| 21 | [Stitched Tapestry](stitched-tapestry/STYLE.md) | कढ़ाई टेपेस्ट्री | `stitched-tapestry` | draft | a village builds a stone bridge along one long linen strip, each stage sewn in as the camera slides, while creatures in the borders argue about whether it will hold. |
| 22 | [Black-figure Vase](black-figure-vase/STYLE.md) | ग्रीक मृदभांड | `black-figure-vase` | draft | a relay of water carriers painted round a turning jar comes alive as zoetrope frames under a strobe, then the jar is fired and the black figures emerge from the orange clay. |
| 23 | [Egyptian Registers](egyptian-register/STYLE.md) | मिस्री चित्र | `egyptian-register` | draft | one loaf of bread traced from field to table, register by register, every worker labelled with the quantity they handled. |
| 24 | [Codex Screenfold](codex-screenfold/STYLE.md) | कोडेक्स | `codex-screenfold` | draft | a family's move across the mountains told as footprints crossing the folds of a painted screenfold book that opens panel by panel, the days counted in dots. |
| 25 | [Blue Tiles (Delft / Azulejo)](delft-tiles/STYLE.md) | नीली टाइलें | `delft-tiles` | draft | a kitchen wall where each tile shows one hour of a canal-side day, until at dusk the tiles join into a single panel of the whole street. |
| 26 | [Batik](batik/STYLE.md) | बाटिक | `batik` | draft | a sea turtle's year drawn in hot wax and revealed through four dye baths, the final boiling-out showing the whole cloth at once. |
| 27 | [Ebru Marbling](ebru-marbling/STYLE.md) | एब्रू मार्बलिंग | `ebru-marbling` | draft | one day's weather over a city told only with drops, combs and a stylus on a marbling tray, each pattern lifted onto paper as the day's record. |
| 28 | [Tenango Embroidery](tenango-embroidery/STYLE.md) | टेनांगो कढ़ाई | `tenango-embroidery` | draft | a forest waking at dawn, stitched creature by creature on white cotton, each animal arriving in its own thread colour until no gap is left. |
| 29 | [Cross-stitch](cross-stitch/STYLE.md) | क्रॉस-स्टिच | `cross-stitch` | draft | a family recipe stitched as a sampler, the dish forming cell by cell, while the back of the cloth shows the tangled work behind each step. |

### Animation Techniques · एनिमेशन तकनीक (19)

| # | Style | हिंदी | Slug | Status | Proposed demo |
|---|---|---|---|---|---|
| 30 | [Claymation](claymation/STYLE.md) | क्लेमेशन | `claymation` | draft | a lump of clay on a workbench keeps trying to become a useful household object, failing in funny ways, until it finally settles into a cup. |
| 31 | [Sand Animation](sand-animation/STYLE.md) | रेत एनिमेशन | `sand-animation` | draft | in one overhead take on a lightbox, a river delta is swept by a palm into a town, a market, a field of lamps and back into a river. |
| 32 | [Paint-on-Glass](paint-on-glass/STYLE.md) | काँच पर पेंटिंग | `paint-on-glass` | draft | a monsoon afternoon over a harbour town, each scene smeared out of the last, from a dry street to a storm to a sky wiped open into evening light. |
| 33 | [Pinscreen](pinscreen/STYLE.md) | पिनस्क्रीन | `pinscreen` | draft | a lighthouse in fog pushed out of the dark pin by pin, whose turning lamp is the moving light that re-shades the whole board. |
| 34 | [Rotoscope](rotoscope/STYLE.md) | रोटोस्कोप | `rotoscope` | draft | a cyclist's ride through a monsoon city, traced over the film's own rigged 3D render, the colour shapes drifting loose from the lines as the rain sets in. |
| 35 | [Cut-paper Collage](collage-cutout/STYLE.md) | कोलाज | `collage-cutout` | draft | a commuter's week assembled from generated newsprint, torn timetables, tape and ransom-note headlines, each day ripped away to reveal the next. |
| 36 | [Felt Stop-motion](felt-stopmotion/STYLE.md) | फ़ेल्ट स्टॉप-मोशन | `felt-stopmotion` | draft | a felted sheep loses its fleece to the wind and follows the tufts down a felt hillside to find they have become clouds, snow and a scarf. |
| 37 | [Knitted World](knit-world/STYLE.md) | बुना हुआ संसार | `knit-world` | draft | a knitted fishing village unravels into one long strand when a loose end snags on a boat, and the strand knits the village back up as a new shape. |
| 38 | [Origami](origami/STYLE.md) | ओरिगामी | `origami` | draft | one square of paper folds into a boat, a frog, a house and a star in turn, its crease scars accumulating into a map of the journey. |
| 39 | [Flipbook](flipbook/STYLE.md) | फ़्लिपबुक | `flipbook` | draft | a doodle in the corner of a school notebook tries to escape the margin, flip by flip, as the pad runs out of pages. |
| 40 | [Zoetrope](zoetrope/STYLE.md) | ज़ोइट्रोप | `zoetrope` | draft | a parlour drum spins up a cyclist, a juggler and a bird in flight, then slows until each loop freezes into a row of drawings and a new strip goes in. |
| 41 | [Manga Screentone](manga-screentone/STYLE.md) | मांगा स्क्रीनटोन | `manga-screentone` | draft | A night-shift baker races the sunrise to finish one perfect loaf, told in panels that cut, tone and burst into speed lines. |
| 42 | [Kinetic Typography](kinetic-type/STYLE.md) | काइनेटिक टाइपोग्राफी | `kinetic-type` | draft | The shy word “hello” tries to join a loud, crowded sentence and only finds its place when the beat drops out. |
| 43 | [Cel-shaded 3D](cel-shaded-3d/STYLE.md) | सेल-शेडेड 3D | `cel-shaded-3d` | draft | A small delivery robot crosses a rainy rooftop city on its first day, drawn in flat tone bands with ink outlines that hold as the camera circles it. |
| 44 | [Wooden Toy](wooden-toy/STYLE.md) | लकड़ी के खिलौने | `wooden-toy` | draft | A turned wooden ring is sliced like bread, and every slice is a different animal that rolls off to join a pull-along parade across the table. |
| 68 | [Glow Sketch](glow-sketch/STYLE.md) | ग्लो स्केच | `glow-sketch` | draft | a single glowing pen draws how a city's power grid wakes up at dusk, every line lighting the next until the whole skyline hums. |
| 70 | [Flat Vector Explainer](flat-vector-explainer/STYLE.md) | फ़्लैट वेक्टर एक्सप्लेनर | `flat-vector-explainer` | draft | why a mosquito bite itches, from the bite to the histamine to the scratch, in rounded flat shapes that morph from one scale to the next. |
| 72 | [CGI Motion](cgi-motion/STYLE.md) | CGI मोशन | `cgi-motion` | draft | a soft glossy ball rolls through a pastel studio of ramps and cloth, each satisfying interaction landing on a beat of the music. |
| 74 | [Miniature Diorama](miniature-diorama/STYLE.md) | मिनिएचर डायोरामा | `miniature-diorama` | draft | a tiny hand-made village on a kitchen table wakes up for a festival morning while a real cup of chai steams at the edge of frame. |

### Art Movements · कला आंदोलन (8)

| # | Style | हिंदी | Slug | Status | Proposed demo |
|---|---|---|---|---|---|
| 45 | [Pointillism](pointillism/STYLE.md) | बिंदुवाद | `pointillism` | draft | A riverbank on a summer afternoon resolves out of loose dots as the camera pulls back, then the evening light changes the colour of every dab. |
| 46 | [Cubism](cubism/STYLE.md) | घनवाद | `cubism` | draft | A kettle coming to the boil is seen from five sides at once; as the steam rises, the facets turn until the whole kitchen shares one canvas. |
| 47 | [Futurism](futurism/STYLE.md) | फ़्यूचरिज़्म | `futurism` | draft | A cyclist's morning commute where speed is drawn: wheels repeat, lines of force cut the street open and the city roars like a noise orchestra. |
| 48 | [Bauhaus](bauhaus/STYLE.md) | बाउहाउस | `bauhaus` | draft | A circle, a square and a triangle build a working table lamp in a workshop, each part constructed with ruler and compass and fitted on the beat. |
| 49 | [De Stijl](de-stijl/STYLE.md) | दे स्टाइल | `de-stijl` | draft | A quiet grid of black lines rebalances itself each time a red, yellow or blue block arrives, until one small square tips it into boogie-woogie traffic. |
| 50 | [Expressionist Set](expressionist-set/STYLE.md) | एक्सप्रेशनिस्ट सेट | `expressionist-set` | draft | A lamplighter walks a crooked painted street where every shadow is painted on the walls, until one shadow starts to move without him. |
| 51 | [Surreal Dreamscape](surreal-dream/STYLE.md) | अतियथार्थ स्वप्नलोक | `surreal-dream` | draft | on an endless evening plain, the objects of one ordinary morning (a kettle, a chair, a stack of letters) stand at impossible sizes, and their long shadows show what they will become. |
| 52 | [Fauvism](fauvism/STYLE.md) | फ़ॉविज़्म | `fauvism` | draft | one fishing harbour is painted three times in a single day, its colours re-chosen stroke by stroke as the painter's mood moves from calm to joy to heat. |

### Internet & Digital · इंटरनेट और डिजिटल (16)

| # | Style | हिंदी | Slug | Status | Proposed demo |
|---|---|---|---|---|---|
| 53 | [Vaporwave](vaporwave/STYLE.md) | वेपरवेव | `vaporwave` | draft | the last night of a closed shopping mall told by its lost-and-found desk, where each forgotten object opens in its own pastel window and turns slowly in the void. |
| 54 | [Synthwave](synthwave/STYLE.md) | सिंथवेव | `synthwave` | draft | a night delivery rider crosses an endless neon grid toward a setting striped sun, each kilometre marked by a city that builds itself in wireframe and switches its lights on. |
| 55 | [Frutiger Aero](frutiger-aero/STYLE.md) | फ़्रूटिगर एरो | `frutiger-aero` | draft | a single raindrop travels from a cloud to a glossy green hillside spring, passing through bubbles that each hold a small clean-energy machine at work. |
| 56 | [Y2K Chrome](y2k-chrome/STYLE.md) | Y2K क्रोम | `y2k-chrome` | draft | a drop of liquid chrome lands in an empty silver studio and keeps reshaping itself into the gadgets one teenager imagined for the year 2000. |
| 57 | [Liquid Glass UI](liquid-glass/STYLE.md) | लिक्विड ग्लास UI | `liquid-glass` | draft | one city's day scrolls beneath a few drops of glass that magnify, merge and split to show the moments a single commuter notices. |
| 58 | [Datamosh](datamosh/STYLE.md) | डेटामोश | `datamosh` | draft | an old portrait of a grandmother is carried, melted frame by frame, through the motion of her granddaughter's day until a fresh key frame reveals the present face. |
| 59 | [Oscilloscope Art](oscilloscope/STYLE.md) | ऑसिलोस्कोप आर्ट | `oscilloscope` | draft | one green beam draws a seed, a tree, a city and a planet in a single continuous line, and the soundtrack you hear is the very signal that draws them. |
| 60 | [Vector Arcade](vector-arcade/STYLE.md) | वेक्टर आर्केड | `vector-arcade` | draft | an attract-mode loop on a dark arcade screen in which a small wireframe ship clears a field of drifting ideas, explodes into its own line segments and reassembles for the next level. |
| 61 | [Thermal Vision](thermal-vision/STYLE.md) | थर्मल विज़न | `thermal-vision` | draft | on a frosty night a thermal camera follows the fading warm traces of one fox across a sleeping village: paw prints, a just-vacated doorstep, a car bonnet still warm. |
| 62 | [X-ray](x-ray/STYLE.md) | एक्स-रे | `x-ray` | draft | a wind-up tin toy is X-rayed on a lightbox and then watched live, revealing step by step the spring and gears that make it hop. |
| 63 | [Flow-field Generative](flow-field/STYLE.md) | जनरेटिव फ़्लो फ़ील्ड | `flow-field` | draft | thousands of lines tracing a day of wind over a coastal city slowly gather into the shape of the monsoon's first cloud, then release it as rain. |
| 64 | [Voxel World](voxel/STYLE.md) | वॉक्सल संसार | `voxel` | draft | one small island grows block by block from a single shoreline stone into a village, loses half of it to a flood, and is rebuilt on higher ground. |
| 65 | [Kaleidoscope](kaleidoscope/STYLE.md) | कैलिडोस्कोप | `kaleidoscope` | draft | a grandmother's buttons, bangle shards and spice seeds drop one by one into a kaleidoscope cell, each turn re-forming the pattern, until the camera pulls out to the toy in a child's hands. |
| 69 | [PS2-era 3D](ps2-era-3d/STYLE.md) | PS2 दौर का 3D | `ps2-era-3d` | draft | a delivery rider's last run of the night told as a 2002 console cutscene, with a menu screen, a loading bar and a save prompt at the end. |
| 71 | [Minimal Ink Essay](minimal-ink-essay/STYLE.md) | मिनिमल इंक निबंध | `minimal-ink-essay` | draft | a two-minute essay on why focus beats talent, drawn as sparse white ink figures on black paper that appear one stroke per idea. |
| 73 | [What-if 3D Explainer](what-if-3d-explainer/STYLE.md) | व्हाट-इफ़ 3D एक्सप्लेनर | `what-if-3d-explainer` | draft | what happens inside your skin in the ten minutes after a splinter goes in, step by step in close 3D with a step counter and bold captions. |

### Cinema Eras · सिनेमा के दौर (2)

| # | Style | हिंदी | Slug | Status | Proposed demo |
|---|---|---|---|---|---|
| 66 | [Film Noir](film-noir/STYLE.md) | फ़िल्म नोयर | `film-noir` | draft | a night watchman recalls in voice-over how the lights of one office building went out floor by floor, told through blinds, stairwell shadows and the wet street below. |
| 67 | [70s Grindhouse](grindhouse-70s/STYLE.md) | 70s ग्राइंडहाउस | `grindhouse-70s` | draft | a trailer for a film that never existed, in which two rival street-food carts race to feed a midnight crowd, with freeze-frame name titles, split screens, a missing reel and a burn-through finale. |
<!-- index:end -->
