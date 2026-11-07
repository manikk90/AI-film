# Style menu

Every style the studio can pick from, in one place, for the social agent's style suggestions and the director's format brief.

- **Library styles (66)**, from [Lemo-Opuscar](https://github.com/lemomo-ai/lemo-opuscar) `styles/<slug>/`. Each has a demo film and engine code, so these are the reliable, faster picks.
- **Draft styles (74)**, from this repo's [`styles/`](../styles/README.md). Each has a written `STYLE.md` but no engine yet, so it needs more build time and an owner-approved preview.
- **Ready formats (47)**, imported skills from the owner's Ai-Animation repo (`studio/IMPORTED_SKILLS.json`). Each is a whole recipe, run as `/<name>` or picked as the format in a studio run, inside `studio/SKILL_HARNESS.md`. They have not been rendered in this repo yet.
- **Format prompts (12)**, from the "12 Claude Video Formats" guide (`studio/formats/`). Each is a one-line prompt (`Format: <name>.`) for `studio/templates/format-prompt.md`. They have a first-try result in the guide, not in this repo.

Rebuild this file with `python3 studio/build_style_menu.py --lemo <lemo-opuscar clone>` when either library changes.

## Library styles (66, each with a demo film)


### Cartoon & Anime

| Style | Slug | Look | Good for |
|---|---|---|---|
| 1930s Rubber Hose Cartoon | `rubber-hose` | Black-and-white hand-inked cartoons where every object is alive and swings to a hot jazz band. | Food & drink, Retro ads, Kids |
| 80s Cel Anime | `cel-anime-80s` | Hand-painted cel animation from the golden age of Japanese OVAs, re-created in code: flat two-tone cels over airbrushed backgrounds, backlit neon, limited-an… | Music videos, Game trailers, Nostalgia |
| Mid-century Cartoon | `midcentury-toon` | 1950s flat colour and limited animation for "follow along" films: colour printed a few pixels off its broken ink line, bodies that hold still while hands do … | Set-up guides, Help centres, How-to |
| Sci-Fi Sitcom Toon | `scifi-toon` | Adult-animation sci-fi sitcom: thick boiling outlines, flat colour, a duo whose reactions don't match, a glowing portal, and one palette per world. | Comedy, Tech brands, Social shorts |

### Cinema & Eras

| Style | Slug | Look | Good for |
|---|---|---|---|
| 1920s Silent Film | `silent-film` | An engraved-illustration silent film projected in a picture house: ink line and silver wash, a 4:3 print that flickers and weaves between velvet curtains, in… | Comedy, Retro brands, Silent storytelling |
| Liminal Found Footage | `backrooms` | Camcorder tapes recovered from empty, endless, fluorescent-lit spaces. Rules instead of monsters. | Horror, Mystery & ARG, Game teasers |

### East Asian Traditions

| Style | Slug | Look | Good for |
|---|---|---|---|
| Paper-cut Lightbox | `paper-lantern` | A layered paper-cut shadow box (纸雕灯) lit from behind: 6–9 sheets of cut card stacked in a shallow box, a warm light glowing through the paper, windows and mo… | Journeys and travel, Farewells and anniversaries, Places and their stories |
| Red Paper-cut | `papercut-red` | Chinese window-flower paper-cuts brought to life: jointed red cut-outs on paper grounds, where the cut *is* the drawing and the holes are where the light get… | Lunar New Year, Festive greetings, Folk tales |
| Shadow Puppetry | `shadow-puppet` | Chinese shadow theatre: translucent dyed-hide puppets, carved like lace, pressed against a cotton screen and lit from behind by oil lamps. | Myths & folklore, Heritage, Festivals |
| Ukiyo-e | `ukiyoe` | Edo-period woodblock prints brought to life: flat colour blocks, carved ink lines, bokashi skies, paper you can feel, and a camera that moves over the print … | Travel, Japanese culture, Poetry |

### Edit & Documentary

| Style | Slug | Look | Good for |
|---|---|---|---|
| 1920s Newsreel | `newsreel` | A sound newsreel of the late 1920s, cut from real archive material: a searchlight-and-globe ident with a brass fanfare, a newspaper that spins into the lens,… | History stories, Fads & eras, Anniversaries |
| Broadcast News Package | `news-package` | A television newsroom's on-air package, built entirely in code: a sting that becomes the channel bug, a rundown of today's stories that opens and closes the … | News round-ups, Bulletins, Market updates |
| Caption News | `caption-news` | Social-video news that reads with the sound off. Real footage, photos and the source document are the ground; huge captions are the lead actor, slammed in a … | Social news, Report explainers, Data shorts |
| Constructivist Montage | `kino-montage` | Real archive footage, photographs and documents, printed as one ink-and-paper poster with a single red, and cut on a machine beat. Diagonal bands carry the t… | Industry histories, Milestones, Collective effort |
| Live Countdown Split-screen | `countdown` | An edit style, not a look. Real footage of one event with a known zero (a launch, a verdict, a final whistle, polls closing), shown in real time: screen time… | Launches, Countdowns, Live events |
| Sports Telestrator | `telestrator` | The TV football analysis segment: play the clip at full speed, rewind, freeze it, and draw on the broadcast picture — rings under players' feet, marker arrow… | Sports analysis, Match recaps, Coaching |
| Time-lapse Symphony | `city-symphony` | A city film cut like a piece of minimalist music: time-lapse turns traffic, crowds and clouds into rivers of light, the cuts get denser with the score's subd… | City films, Music montages, Openers |
| Visual Investigation | `visual-investigation` | A cold investigation desk: footage, photographs, documents, sound and maps from one real event, laid out on one shared clock so they check each other. The cl… | Reconstructions, Fact-checks, Incident reports |

### Evidence Films

| Style | Slug | Look | Good for |
|---|---|---|---|
| Archive Light Table | `archive-lighttable` | Real archive objects (glass negatives, slides, letters, telegrams, clippings, drawings) lie on a cool, backlit light table. A loupe comes down on one of them… | Brand history, Archive stories, Museums |
| Data Physicalization | `data-physical` | Real statistics built as real objects: every unit is a countable piece of material (a plate, a block, a coin, a bar) stacked to exact scale on a crafted base… | Annual reports, Investor decks, Energy data |
| Engineering Briefing Board | `briefing-board` | One real whiteboard wall, filmed: window light on enamel, ghosts of erased marker, frame and tray. Cut-out photographs of real things land on it with weight;… | Engineering, Option comparisons, Briefings |
| Exploded Teardown | `teardown` | A real product, built from its own engineering files (CAD, PCB layout, bill of materials), lit like a studio packshot and taken apart in front of the camera:… | Hardware launches, Product pages, Spec explainers |
| LiDAR Survey | `lidar-survey` | Real airborne laser points of a real place, floating in the dark as a measured cloud; a scan line or a cutting plane passes through them and the points conde… | Heritage, Environment, Site surveys |
| Microscope Story | `microscope` | Real, licence-clean microscopy of a real specimen, seen as it is, and one continuous change of scale that carries the viewer from the glass slide in the hand… | Biomedicine, Materials science, Skincare science |
| Projection on White Model | `white-model` | A pure white massing model of a real place stands on a plinth in a dark room, and a projector paints data onto it as light: one layer at a time, falling on t… | Urban planning, Exhibitions, City data |
| Satellite Briefing | `satellite-briefing` | Real satellite imagery of a real place, graded down to an analyst's grey, with thin white measurement lines drawn on the ground: a lock-on reticle, outlines,… | Climate, News explainers, Geography |

### Games

| Style | Slug | Look | Good for |
|---|---|---|---|
| 16-bit Pixel RPG | `pixel-rpg` | A short film that looks, sounds and *behaves* like a mid-90s console role-playing game: 320×180 pixels, a limited indexed palette, text boxes that type, menu… | Game trailers, Recaps, Nostalgia |
| Game Show Flat | `game-show` | A rhythm-game variety show in flat vector: toy-like mascots with thick ink outlines on candy-coloured stripes and sunbursts, every hit landing on a fixed tem… | Tech timelines, Year in review, Variety shows |
| HD-2D | `hd-2d` | Hand-made pixel sprites standing like paper cut-outs inside a lit, fogged, fully 3D diorama, shot from a high three-quarter angle through a tilt-shift lens: … | Game trailers, Fantasy, Story films |
| Microgame Frenzy | `microgame` | A rapid-fire party-game film: one command word, a few seconds, one action. Every microgame is drawn in a completely different art style, and the film keeps g… | Game trailers, Onboarding, Social shorts |

### Graphic & Type

| Style | Slug | Look | Good for |
|---|---|---|---|
| 60s Spy Title Sequence | `spy-titles` | A cut-paper, four-ink opening title sequence for a film that never existed: silhouettes move through sets built out of the credits themselves, every brass st… | Title sequences, Event openers, Trailers |
| ASCII / CRT Terminal | `ascii-crt` | Everything on screen is a real character on a monospace grid, lit by the phosphor of an old monochrome CRT. | Developer tools, Sci-fi, Tech brands |
| Art Deco | `art-deco` | Black lacquer, engraved gold line and airbrushed geometry: a 1930s poster that moves. Every composition has a centre axis, transitions open or close along it… | Luxury & hospitality, Galas, Invitations |
| Blueprint | `blueprint` | Engineering drawings that come alive on a sheet of cyanotype paper: white technical line work on Prussian blue, drawn in drafting order, with annotations tha… | Engineering, Hardware launches, Tech explainers |
| Pictogram Motion | `pictogram-motion` | A beat-locked film built from three things only: a **square-grid "core graphic"** of circles, half-discs and tiny patterned cells whose rows slide past each … | Public services and city stories, Brand and event identity films, Explainers told through signs and objects |
| Stained Glass | `stained-glass` | A medieval stained-glass window seen from inside a dark stone hall, alive only where the sun touches it: light is the clock, the camera and the story. | Legends, Heritage, Holiday stories |
| Swiss Motion Graphics | `swiss-motion` | International Typographic Style in motion: a modular grid, one typeface, one signal colour, and movement as exact as a printing press. | Brand identity, Events, Design education |

### Hand-drawn & Painting

| Style | Slug | Look | Good for |
|---|---|---|---|
| Chalkboard | `chalkboard` | A real classroom blackboard on which chalk writes itself, stroke by stroke in true stroke order, with no hand, no chalk stick and no eraser in sight. One ide… | Word origins, Myth-busting, Lessons |
| Chinese Ink Wash | `ink-wash` | Xieyi ink painting on rice paper, animated: blank paper is space, one brushstroke is a mountain, a wave, a gesture or a cut. | Wuxia, Cultural brands, Poetry |
| Crayon Picture Book | `crayon-book` | A picture-book page drawn live in wax crayon on toothy paper, with a watercolour wash that reveals what the crayon was hiding. | Picture books, Bedtime stories, Kids' learning |
| Impasto Oil Painting | `impasto` | Thick oil paint laid with a palette knife: big, flat, sharp-edged planes of colour, raked by light so every ridge of paint shows. Clarity first: value struct… | Music videos, Art & culture, Emotional ads |
| One-line Drawing | `one-line` | A single ink line that never leaves the paper. Everything on screen is that one line being drawn; scenes don't cut, they morph. | Brand stories, Life milestones, Minimal ads |
| Urban Sketch · Pen & Wash | `urban-sketch` | A sketchbook page drawn on location: fine sepia fineliner lines that wobble, overshoot and never quite close, with loose transparent watercolour dropped on t… | City & travel, Architecture, Lifestyle brands |
| Watercolor Brush | `watercolor` | A hand-painted journal page that paints itself: translucent brush strokes with dry-brush flying white on warm cotton paper, hand-written notes beside what is… | Nature documentary, Travel, Science explainers |
| Whiteboard Explainer | `whiteboard` | An explainer drawn live on one glossy dry-erase board: single-line handwriting that is actually *written* stroke by stroke, floating markers with no hand, ma… | Explainers, Online courses, Science |

### Information & Keynote

| Style | Slug | Look | Good for |
|---|---|---|---|
| Circuit Board | `circuit-board` | The subject is drawn as a printed circuit board seen from straight above: the world is copper under green solder mask, routes are traces, places are pads, wo… | Energy, Supply chains, Devices |
| Dark Tech Keynote | `dark-keynote` | A software launch film where the interface itself is the star: near-black gradient, hairline grid, soft light, one brand accent, and UI that moves with snap-… | Product launches, SaaS, Keynotes |
| Data Storytelling | `dataviz` | A chart that tells a story: real data, drawn mark by mark on cream paper by a red–blue pencil, with handwritten notes pinned to the numbers. The chart itself… | Data journalism, Reports, Climate & science |
| Isometric Infographic | `iso-infographic` | A system diagram comes alive: an isometric diorama of flat three-tone blocks, thin ink labels and Isotype numbers, where things open up to show their insides… | Process explainers, Supply chains, Annual reports |
| Isometric Picture Book | `isometric-picture-book` | A calm explainer of an everyday rule, set in one real place drawn in true isometric with flat colour: small faceless people seen from behind do the thing in … | Everyday rules, Queues, Comparisons |
| Living Screencast | `living-screencast` | A product walkthrough that looks like a real screen recording, where a low-resolution mascot lives inside a high-resolution interface and acts out what the s… | Product tutorials, Feature launches, Onboarding |
| Sci-fi Hologram HUD | `hologram-hud` | An object is scanned into a glowing wireframe. Target boxes lock onto its parts; each opens in a local exploded view, a leader pulls out, and its number roll… | Spec walkthroughs, Launch videos, Trade shows |
| Transit Map | `transit-map` | A metro schematic printed on a physical sheet: lines held to eight directions, white stops, black-outlined interchange capsules, water as a flat blue band. T… | Transport, Growth over time, Networks |

### Materials & 3D

| Style | Slug | Look | Good for |
|---|---|---|---|
| Brick Toy | `brick-toy` | Stop-motion toy-brick films shot like macro photography on a real desk: a world built from interlocking plastic bricks with round studs, animated a pose at a… | Toys & kids, Product builds, Space |
| Desktop Flythrough | `desktop-flythrough` | App screens and tools lie on a sunlit desk as printed paper cards; small pixel characters, popped up into voxel toys, carry the work from card to card, while… | App explainers, Workflows, Products |
| Glass Product Render | `glass-product` | Launch-film product rendering in transparent and frosted glass: a dark-field studio, strip-light sweeps, dispersion, caustics, light travelling inside the ob… | Product launches, Consumer tech, Beauty |
| Low-poly Isometric Island | `lowpoly-island` | A tiny faceted world seen through an orthographic isometric lens: everything is a geometric block, and everything that appears arrives with a bounce and a note. | Game trailers, World building, Calm content |
| Memphis Diorama | `memphis-diorama` | A place built as a tabletop model: on warm white paper an organic, grainy frame grows open, and inside it a small world in flat Memphis colours, ink outlines… | Web heroes, Ambient loops, Seasons |
| Paper Pop-up Book | `paper-popup` | A pop-up book on a real desk becomes a stage: flat cut-paper actors with white borders perform in front of paper sets that spring up from the page, under rea… | Children's books, Game trailers, Story films |
| Tilt-Shift Miniature | `tilt-shift` | A real-looking place photographed from high above with a tilted lens and a time-lapse camera, so the whole world reads as a tabletop model. | City promos, Real estate, Transport |

### Print & Printmaking

| Style | Slug | Look | Good for |
|---|---|---|---|
| Copperplate Engraving | `engraving` | An intaglio plate that engraves itself: a burin cuts swelling lines into copper, a proof is pulled, and the figure builds up — outline, hatching, cross-hatch… | Museum labels, Science explainers, Brand heritage |
| Halftone Dossier | `halftone-dossier` | A retro print case file: cream archive paper, overprinted halftone dots in a few flat inks, huge heavy headlines with misregistered shadows, rubber stamps th… | Humour, Pet content, Social shorts |
| Printed Long Take | `printed-long-take` | A three-dimensional world rendered as a scratchboard print, ink and paper with one red, crossed by one unbroken camera move. Depth, weather and light are all… | Journeys, Wildlife, Landscapes |
| Risograph Print | `risograph` | Animation that looks printed, frame by frame, on a stencil duplicator: two or three translucent spot inks overprinted on warm paper, halftone dots, ink grain… | Indie brands, Zines, Lifestyle |
| Silkscreen Travel Poster | `silkscreen-poster` | Opaque, hard-edged flat inks pulled one colour at a time through a screen: 4–6 inks per poster, stepped colour bands instead of gradients, thin paper-white g… | Destination guides, Tourism, Event posters |
| Woodcut Print | `woodcut` | A relief print that carves itself: every frame is a black wood block, and light only exists where a knife has cut it away. One colour at most, and only for t… | Folk tales, Craft brands, Book trailers |

## Draft styles (74, no demo yet)


### Indian Traditions

| Style | हिंदी | Slug | Look | Good for |
|---|---|---|---|---|
| Bollywood Hand-painted Poster | हाथ से बना फ़िल्मी पोस्टर | `bollywood-poster` | The hand-painted cinema hoarding brought to life: giant brushed faces lit in two impossible colours, collaged action vignettes and a fat hand-lettered title,… | Launches & announcements, Comedy & melodrama, Local heroes |
| Gond | गोंड | `gond` | Gond painting in motion: big flat silhouettes of trees, animals and birds in bright colour on a plain ground, each body zoned and filled with rows of dots, d… | Nature & wildlife, Children's stories, Ecology explainers |
| Indian Truck Art | ट्रक आर्ट | `truck-art` | The painted goods truck of Indian highways as a moving canvas: enamel panels crowded with folk motifs, slogans and borders, reflective tape and chrome that f… | Road safety & public messages, Travel & logistics, Street culture |
| Kalamkari | कलमकारी | `kalamkari` | Pen-drawn, dye-painted cotton that tells a story in panels: a black line drawn with a bamboo kalam, colour that soaks into the weave in maroon, indigo and mu… | Process explainers, Heritage & crafts, Episodic narratives |
| Kalighat Pat | कालीघाट पट | `kalighat` | Bazaar watercolours from 19th-century Calcutta in motion: a large figure on blank paper, its outline laid in one sweeping, swelling brushstroke, its volume s… | Satire & social comment, Character portraits, City life |
| Kathputli Marionette | कठपुतली | `kathputli` | Rajasthani string-puppet theatre: carved wooden heads with huge painted eyes, bright cloth bodies trimmed with gold ribbon and mirrors, hanging and dancing o… | Fables & children's stories, Public awareness, Heritage |
| Kerala Mural | केरल भित्तिचित्र | `kerala-mural` | Wall painting from Kerala brought to life: long-eyed figures with swelling outlines in five earth pigments on lime plaster, rounded by deeper tones of the sa… | Heritage & history, Folk tales & fables, Craft & process |
| Kolam / Rangoli | कोलम / रंगोली | `kolam-rangoli` | Threshold drawings in powder brought to life: white rice-flour lines that loop around a grid of dots and close on themselves, and coloured powder poured by h… | Mathematics & patterns, Festivals & daily rituals, Community stories |
| Madhubani | मधुबनी | `madhubani` | Mithila painting that draws itself: every form is a double ink outline laid by a bamboo nib, then every gap is packed with hatching, dots and flat earth colo… | Folk tales & proverbs, Nature & ecology, Festivals & family occasions |
| Mehndi | मेहंदी | `mehndi` | Henna drawing brought to life: a cone squeezes a fine raised line of dark paste over a palm; lines grow into paisleys, vines, lattices and medallions, then d… | Weddings & celebrations, Personal & family stories, Craft & process |
| Mughal Miniature | मुग़ल लघुचित्र | `mughal-miniature` | An album page that comes alive: a jewel-bright scene in fine opaque colour, its ground tipped up so everything is seen at once, framed by rules and gold-illu… | History & courts, Gardens & natural history, Detailed explainers |
| Pattachitra | पट्टचित्र | `pattachitra` | Odisha cloth painting brought to life: opaque colour on a chalk-coated cloth, flat red grounds, figures in held dance-like poses, borders band inside band, s… | Heritage & festivals, Episodic narratives, Regional culture |
| Phad Scroll | फड़ | `phad-scroll` | A long painted cloth scroll performed at night: the whole story is laid out at once across metres of cloth in flat yellow, red and green, and a storyteller's… | Journeys & epics, Oral storytelling, Timelines |
| Pichwai | पिछवाई | `pichwai` | Painted temple hangings from Nathdwara in motion: a large cloth of deep indigo, black or green, filled edge to edge with rows of cows, lotus ponds, trees and… | Seasons & festivals, Nature & calm, Luxury & heritage |
| Tanjore | तंजौर | `tanjore` | Thanjavur painting as a lit object: flat bright colour on a gessoed board, raised relief built up under gold foil, inlaid stones that flash, a dark carved fr… | Heritage & crafts, Luxury & jewellery, Ceremonial openings |
| Warli | वारली | `warli` | Warli wall painting in motion: figures of a circle and two triangles, dabbed in white rice paste on a mud wall, hundreds of them working at once until they j… | Community & work, Agriculture & seasons, Explainers with crowds |

### World Folk

| Style | हिंदी | Slug | Look | Good for |
|---|---|---|---|---|
| Batik | बाटिक | `batik` | Wax-resist dyed cloth: lines of hot wax drawn or stamped onto cotton, the cloth dipped in successive dye baths from light to dark, each colour kept by wax be… | Process explainers, Heritage & craft, Fashion & textiles |
| Black-figure Vase | ग्रीक मृदभांड | `black-figure-vase` | A turning clay vessel whose painted frieze is the film: glossy black silhouettes on orange terracotta, detail scratched through the black to the clay, touche… | Fables & cycles, Museum & heritage, Sport and repeated labour |
| Blue Tiles (Delft / Azulejo) | नीली टाइलें | `delft-tiles` | Cobalt brushed onto white tin glaze across a wall of square tiles: each tile a small painted vignette or one fragment of a larger panel, the glaze milky and … | City & harbour stories, Trades & crafts, Domestic life |
| Codex Screenfold | कोडेक्स | `codex-screenfold` | A folded book of painted deerskin opens panel by panel: figures with heavy even outlines and flat mineral colours on a white gesso ground, read along red gui… | Genealogies & lineages, Journeys & migrations, Heritage education |
| Cross-stitch | क्रॉस-स्टिच | `cross-stitch` | Pictures counted onto even-weave cloth one X at a time: every cell of the grid is either bare fabric or a two-legged cross of cotton floss, outlines are stra… | Family & memory stories, Step-by-step explainers, Greetings & keepsakes |
| Ebru Marbling | एब्रू मार्बलिंग | `ebru-marbling` | Colours floated on a tray of thickened water: drops spread into rings, a stylus and combs drag them into veins, waves and flowers, and a sheet of paper laid … | Meditative openers, Science of fluids, Title sequences & transitions |
| Egyptian Registers | मिस्री चित्र | `egyptian-register` | Painted and carved wall scenes in the manner of ancient Egyptian tomb chapels: figures in composite profile standing on horizontal ground lines, stacked in r… | Processes & supply chains, Heritage & museums, Social structures |
| Mola Appliqué | मोला कपड़ा कला | `mola-applique` | Reverse appliqué brought to life: layers of bright cotton stacked and cut through, the cut edges turned under and hemmed with tiny stitches, so every shape i… | Nature & ecology, Science explainers, Craft & process |
| Persian Miniature | फ़ारसी लघुचित्र | `persian-miniature` | Persian manuscript painting brought to life: a jewel-coloured world seen from several heights at once (gardens and pools laid flat from above, pavilions in e… | Poetry & literature, History & heritage, Architecture & gardens |
| Stitched Tapestry | कढ़ाई टेपेस्ट्री | `stitched-tapestry` | Wool embroidery on a long strip of unbleached linen: flat figures outlined in stem stitch and filled with couched wool, one continuous story read left to rig… | Chronicles & histories, Community and company stories, Journeys & supply chains |
| Tenango Embroidery | टेनांगो कढ़ाई | `tenango-embroidery` | Dense satin-stitched animals, birds and flowers on plain white cotton: flat silhouettes filled with glossy parallel threads whose direction changes from part… | Nature & biodiversity, Community stories, Children's stories |
| Thangka | थांगका | `thangka` | Himalayan scroll painting brought to life for secular subjects: a gessoed cotton canvas built up from a charcoal proportion grid, dense mineral colours shade… | Nature & science, Geography, Heritage |
| Yarn Painting | धागा चित्र | `yarn-painting` | Pictures made of coiled thread: coloured yarn pressed strand by strand into a wax-covered board, each shape outlined and then filled with lines that echo its… | Nature & ecology, Children's education, Craft & process |

### Animation Techniques

| Style | हिंदी | Slug | Look | Good for |
|---|---|---|---|---|
| CGI Motion | CGI मोशन | `cgi-motion` | Glossy, tactile 3D motion design: soft-body balls, inflatable shapes, cloth and ramps in a seamless pastel studio, lit by big soft lights, moving in satisfyi… | Satisfying loops, Brand idents & product teasers, Music visuals |
| Cel-shaded 3D | सेल-शेडेड 3D | `cel-shaded-3d` | Three-dimensional models rendered to look hand-drawn: flat colour bands from a stepped light ramp, ink outlines of constant weight, hard shadow shapes, and c… | Game & app promos, Kids' adventure series, Brand mascots |
| Claymation | क्लेमेशन | `claymation` | Stop-motion with oil-based modelling clay: soft rounded characters and props sculpted by hand, fingerprints and tool marks left in, surfaces that "boil" a li… | Character comedy, Children's education, Mascots & product stories |
| Cut-paper Collage | कोलाज | `collage-cutout` | A tabletop of printed scraps (magazine-like cuttings, torn newsprint, kraft paper, tape, staples, handwriting) animated as cut-outs a frame at a time: mismat… | Social commentary, Culture and brand explainers, Music video |
| Felt Stop-motion | फ़ेल्ट स्टॉप-मोशन | `felt-stopmotion` | Needle-felted wool characters on a set of felt sheets and wool roving, shot with a macro lens a pose at a time: soft fuzzy silhouettes, bead eyes, matte satu… | Children's story, Gentle brand film, Nature fable |
| Flat Vector Explainer | फ़्लैट वेक्टर एक्सप्लेनर | `flat-vector-explainer` | Science explained in clean flat shapes: rounded geometric characters and objects, soft single-direction shading, bright saturated colours on dark or deep-col… | Science explainers, Health & body, Education |
| Flipbook | फ़्लिपबुक | `flipbook` | Pencil drawings on the corners of a notebook or pad, one drawing per page, brought to life by a thumb flipping the pages: graphite lines that boil because ev… | Short comic gag, Social short, Teaching how animation works |
| Glow Sketch | ग्लो स्केच | `glow-sketch` | Hand-drawn line art that emits light: a single pen draws white and coloured strokes on near-black paper, every stroke blooms like a neon tube or a light-pain… | Explainers & how-it-works, Science & tech stories, Motivational shorts |
| Kinetic Typography | काइनेटिक टाइपोग्राफी | `kinetic-type` | The words are the cast: the spoken text is set in type, and every word enters, acts and leaves on its own syllable, so reading and listening become one motion. | Poetry & lyric videos, Speeches & manifestos, Social explainers |
| Knitted World | बुना हुआ संसार | `knit-world` | A world made of knitted and crocheted fabric: every surface is a lattice of yarn stitches, colour is a knitting chart, objects are stuffed and seamed, and a … | Children's story, Systems and connections explainer, Seasonal film |
| Manga Screentone | मांगा स्क्रीनटोन | `manga-screentone` | Black-and-white comic printing set in motion: pressure-tapered pen ink, mechanical dot tones cut to shape, speed and focus lines, and a page whose panel bord… | Sports & action, Youth campaigns, Serialised stories |
| Miniature Diorama | मिनिएचर डायोरामा | `miniature-diorama` | A tiny hand-built world sitting on a real table: a model village or city on a wooden base, foam trees, painted houses and little figures, shot with a macro l… | Story shorts, Place & travel, Brand worlds |
| Origami | ओरिगामी | `origami` | Single sheets of paper folded into every shape on screen: flat facets with crisp creases, coloured on one side and white on the other, and transformations th… | Process explainer, Transformation story, Mathematics and design education |
| Paint-on-Glass | काँच पर पेंटिंग | `paint-on-glass` | Slow-drying oil paint pushed around on a lit glass sheet under the camera, repainted for every frame: light glows through thin paint, motion is paint dragged… | Literary adaptation, Music video, Dream and memory sequences |
| Pinscreen | पिनस्क्रीन | `pinscreen` | A white board pierced by a dense grid of pins, lit from one low side: pins pushed out cast long shadows (black), pins flush cast none (white), and everything… | Poetry film, Folk tale, Nocturne and memory |
| Rotoscope | रोटोस्कोप | `rotoscope` | Drawings traced over real motion: hand-wobbly contour lines and flat colour shapes that ride on the true weight and timing of a moving body, so the surface i… | Documentary interview, Music video, Sport and dance |
| Sand Animation | रेत एनिमेशन | `sand-animation` | Dark sand on a backlit glass table, filmed from above: light is wherever the sand has been pushed away, and a fingertip, the edge of a palm or a falling tric… | Poetic storytelling, Live-performance music video, Family history and memory |
| Wooden Toy | लकड़ी के खिलौने | `wooden-toy` | A world of lathe-turned and fretsaw-cut wooden toys under a warm lamp: peg people, pull-along animals and stacking rings in glossy lacquer over visible grain… | Kids & education, Craft & heritage brands, Festive greetings |
| Zoetrope | ज़ोइट्रोप | `zoetrope` | A Victorian motion toy: a strip of sequential drawings inside a spinning slotted drum, seen through the passing slits so the figures come alive in a short en… | Cinema history explainer, Loop-based music video, Museum installation |

### Art Movements

| Style | हिंदी | Slug | Look | Good for |
|---|---|---|---|---|
| Bauhaus | बाउहाउस | `bauhaus` | Built geometry in primary colours: circle, square and triangle in red, yellow and blue on off-white with heavy black bars, constructed with ruler and compass… | Design education, Product & furniture brands, Process explainers |
| Cubism | घनवाद | `cubism` | One subject seen from several sides at once and broken into overlapping planes: shards of muted ochre, grey and green, each holding a different view, with li… | Art education, Music & culture, Many-sided stories |
| De Stijl | दे स्टाइल | `de-stijl` | Neo-plastic composition in motion: thick black lines on a white ground divide the frame into rectangles, a few filled with red, yellow or blue, and the whole… | Architecture & interiors, Brand systems, Music & jazz |
| Expressionist Set | एक्सप्रेशनिस्ट सेट | `expressionist-set` | A 1920s nightmare built in a studio: crooked painted flats with light and shadow brushed onto the walls, streets that lean and narrow to a point, pale-faced … | Mystery & horror, Theatre promos, Psychological stories |
| Fauvism | फ़ॉविज़्म | `fauvism` | A moving painting in wild, unmixed colour: broad separate brushstrokes of pure hue laid on primed canvas, coloured contour lines, violet shadows and red tree… | Travel films, Art education, Festival and lifestyle brands |
| Futurism | फ़्यूचरिज़्म | `futurism` | Speed and noise made visible: a moving body leaves a fan of repeated contours behind it, wedges of colour shoot along its lines of force, and the street spli… | Sports & mobility, Engineering & industry, Urban culture |
| Pointillism | बिंदुवाद | `pointillism` | A picture built from separate dabs of pure, unmixed colour that blend only in the viewer's eye: up close a field of dots, at a distance a calm, luminous scen… | Art education, Nature & travel, Calm brand films |
| Surreal Dreamscape | अतियथार्थ स्वप्नलोक | `surreal-dream` | A painted dream rendered with total conviction: an empty plain under a deep graduated sky, a low sun throwing impossibly long shadows, and ordinary objects t… | Poetry and essay films, Music videos, Mental-health explainers |

### Internet & Digital

| Style | हिंदी | Slug | Look | Good for |
|---|---|---|---|---|
| Datamosh | डेटामोश | `datamosh` | Compressed video that has lost its key frames: the pixels of one picture are dragged by the motion of the next, macroblocks smear and swell, and a fresh key … | Music videos, Memory and identity essays, Fashion promos |
| Flow-field Generative | जनरेटिव फ़्लो फ़ील्ड | `flow-field` | Images drawn by code: thousands of lines follow an invisible vector field, and the picture is wherever they bunch, part or swirl. Change the field and the wh… | Data & science, Brand idents, Music visuals |
| Frutiger Aero | फ़्रूटिगर एरो | `frutiger-aero` | Glossy, sunlit tech optimism: sky-blue skies, lush green hills and clear aqua water, translucent gel shapes with a crisp white shine, bubbles and droplets th… | Clean-tech and wellness brands, Science for kids, App onboarding |
| Kaleidoscope | कैलिडोस्कोप | `kaleidoscope` | A view down a mirrored tube: loose pieces of coloured glass in a backlit cell are multiplied by mirrors into a perfectly symmetric pattern that re-forms ever… | Music videos, Memory & family, Festive brand films |
| Liquid Glass UI | लिक्विड ग्लास UI | `liquid-glass` | A fictional interface made of floating glass: panes and lenses refract the colourful content beneath them, bend it strongly at their rounded edges, catch a m… | App and product launches, UI/UX explainers, Brand idents |
| Minimal Ink Essay | मिनिमल इंक निबंध | `minimal-ink-essay` | A spoken essay drawn in very few lines: sparse white ink figures and symbols appear on black (or off-white) paper, one stroke per idea, with large calm serif… | Self-improvement essays, Philosophy & mindset, Founder & creator talks |
| Oscilloscope Art | ऑसिलोस्कोप आर्ट | `oscilloscope` | One green beam of light on the dark glass of an oscilloscope in XY mode, drawing every image as a single continuous path many times a second; brightness is w… | Music visualisers, Physics and audio explainers, Tech brand idents |
| PS2-era 3D | PS2 दौर का 3D | `ps2-era-3d` | A story told as an early-2000s console game: low-polygon characters with painted textures, vertex-lit rooms in fog, a soft bloom on every bright light, a sli… | Nostalgia & gaming culture, Comedy & memes, Story shorts |
| Synthwave | सिंथवेव | `synthwave` | A neon night drive into a retro-future: a glowing grid floor races toward a low horizon and a huge striped sun, wireframe mountains glow against a violet sky… | Music videos, Game and tech launches, Event trailers |
| Thermal Vision | थर्मल विज़न | `thermal-vision` | A long-wave infrared camera's view: the picture is a map of surface temperature shown through a false-colour palette, with a scale bar, a spot meter and the … | Science explainers, Nature & wildlife, Energy & buildings |
| Vaporwave | वेपरवेव | `vaporwave` | A slowed-down, pastel collage of consumer nostalgia: marble busts, columns and palms float in a pink-and-teal void over an endless checkerboard, framed by in… | Music videos, Nostalgia and internet-culture explainers, Fashion and lifestyle promos |
| Vector Arcade | वेक्टर आर्केड | `vector-arcade` | Glowing lines on pure black from an early-1980s vector arcade monitor: ships, rocks, tanks and tunnels drawn as bright wireframe outlines by a beam that jump… | Game-culture explainers, Tech and esports promos, Retro brand idents |
| Voxel World | वॉक्सल संसार | `voxel` | A world made only of equal cubes on one grid: terrain, houses, trees, water and people are stacks of blocks, and everything that happens is a block placed, a… | Kids & education, Games & tech, History & urban growth |
| What-if 3D Explainer | व्हाट-इफ़ 3D एक्सप्लेनर | `what-if-3d-explainer` | A short body or science fact shown in close, slightly gross, realistic-cartoon 3D: the camera dives into skin, blood or a machine, numbered steps walk throug… | Body & health facts, What-if science, Viral shorts |
| X-ray | एक्स-रे | `x-ray` | Projection radiography: rays from a point source pass through things and darken a film, so bone and metal glow white, air goes black, and every grey is how m… | How things work, Product & engineering, Museum & conservation |
| Y2K Chrome | Y2K क्रोम | `y2k-chrome` | Millennium futurism in liquid metal: mercury blobs that merge and split, inflated bubble lettering, iridescent and candy-translucent plastics, sparkle glints… | Fashion and beauty, Music and club promos, Tech product teasers |

### Cinema Eras

| Style | हिंदी | Slug | Look | Good for |
|---|---|---|---|---|
| 70s Grindhouse | 70s ग्राइंडहाउस | `grindhouse-70s` | A worn 1970s colour release print run through a tired projector at a double-feature house: faded, scratched and spliced, cut with crash zooms, split screens … | Comedy & parody, Retro ads, Event promos |
| Film Noir | फ़िल्म नोयर | `film-noir` | Black-and-white crime-film lighting built in code: one hard light per shot, shadows sharper and larger than the people who cast them, wet streets that mirror… | Mystery & drama, Brand storytelling, Music videos |

## Ready formats (47, imported skills)

Kind says where the words come from and which gate applies (see `studio/SKILL_HARNESS.md`).


### Animated videos (with engine)

| Format | Skill | Owner gives | Kind | Checks |
|---|---|---|---|---|
| Daksh AI (starter edition) — by Daksh AI | `/daksh-ai` | a voice recording (MP3), and the exact script if you have one | voice | facts |

### Animated videos

| Format | Skill | Owner gives | Kind | Checks |
|---|---|---|---|---|
| Anime reel | `/anime-reel` | a script and the voice MP3s for each line | script | original-characters |
| Blueprint explainer | `/blueprint-explainer` | a long voiceover MP3 (3–10 minutes) and the facts or numbers it covers | voice | facts |
| Comic book reel | `/comic-reel` | the scene's dialogue audio (MP3) | third-party-audio | - |
| Crayon lyric video | `/lyric-video` | a song MP3 and its lyrics, one sung line per row | song | - |
| Hindi lyric video | `/hindi-lyric-video` | a Hindi song MP3 and its lyrics in Devanagari, one line per row | song | - |
| Katha video | `/katha-video` | a 60–90 second pravachan MP3 | third-party-audio | - |
| Kinetic lyrics | `/kinetic-lyrics` | a song MP3 and its lyrics | song | - |
| Latent-style roast reel | `/latent-reel` | a show clip (MP3) with the guest and host talking | third-party-audio | brands |
| Madhubani kahani | `/madhubani-kahani` | a Hindi story voiceover MP3 | voice | - |
| Personal explainer | `/personal-explainer` | your voiceover MP3, the topic, and any source links | voice | facts, third-party-footage |
| Podcast explainer | `/podcast-explainer` | a 45–90 second podcast clip (MP3) | third-party-audio | facts |
| Pusho reel | `/pusho-reel` | a Puneet Superstar audio clip (MP3) | third-party-audio | - |
| Sketch music video | `/sketch-music-video` | a song MP3 and its lyrics, one sung line per row | song | - |
| Sketch to motion graphic | `/sketch-to-motion` | 8–10 photos of your sketches, plus your product photos and stock clips | assets | - |
| Talking-head edit | `/talking-head-edit` | a 9:16 talking-head clip | clip | - |
| Tech news report | `/news-report` | a news topic or 2–3 article links | written | facts, brands, third-party-footage |
| Titan anime episode | `/titan-anime` | a script and the voice MP3s for each line | script | original-characters |
| Watercolor map journey | `/watercolor-map` | two places, like “Bengaluru → California” | visual | - |

### Reel formats

| Format | Skill | Owner gives | Kind | Checks |
|---|---|---|---|---|
| Business short-form reel | `/business-short-form-reels` | a 9:16 talking-head clip | clip | - |
| Depth UI reel | `/depth-ui-reel` | a 9:16 talking-head clip | clip | - |
| Educational YouTube editor | `/educational-youtube-editor` | a long 16:9 lesson recording | clip | - |
| Personal B-roll library | `/personal-broll-library` | a folder of my B-roll clips | clip | - |
| Personal short-form reel | `/personal-short-form-reels` | a 9:16 talking-head clip | clip | - |
| Ranking / tier list | `/ranking-format` | a 9:16 talking-head clip | clip | - |
| YouTube clips | `/youtube-clips` | a long 16:9 video or a YouTube link | clip | own-footage-only |

### Edit styles

| Format | Skill | Owner gives | Kind | Checks |
|---|---|---|---|---|
| Dark red timeline | `/dark-red-timeline-motion-graphics` | a 9:16 talking-head clip | clip | - |
| Hindi pastel reel | `/hindi-pastel-reel-edit` | a 9:16 talking-head clip | clip | - |
| Instagram UI (Hinglish) | `/instagram-ui-hinglish` | a 9:16 talking-head clip | clip | brands |
| Kinetic talking head | `/kinetic-talking-head-edit` | a 9:16 talking-head clip | clip | - |
| Podcast reel edit | `/podcast-reel-edit` | a 9:16 talking-head clip | clip | - |
| Red kinetic collage | `/red-kinetic-collage-edit` | a 9:16 talking-head clip | clip | - |
| iPhone style | `/iphone-style-by-daksh-ai` | a 9:16 talking-head clip | clip | brands |

### Motion effects

| Format | Skill | Owner gives | Kind | Checks |
|---|---|---|---|---|
| Glass stat card | `/glass-stat-card` | a 9:16 talking-head clip | clip | facts |
| LED matrix text | `/led-matrix-text` | a 9:16 talking-head clip | clip | - |
| Match cut | `/match-cut` | a 9:16 talking-head clip | clip | - |
| Particle chart | `/particle-chart` | a 9:16 talking-head clip | clip | facts |
| Particle text | `/particle-text` | a 9:16 talking-head clip | clip | - |
| Price-tag zoom | `/price-tag-zoom` | a 9:16 talking-head clip | clip | facts |
| Shutter stack | `/shutter-stack` | a 9:16 talking-head clip | clip | - |

### Looks

| Format | Skill | Owner gives | Kind | Checks |
|---|---|---|---|---|
| Breaking news | `/breaking-news` | a 9:16 talking-head clip | clip | brands |
| Cinema scope | `/cinema-scope` | a 9:16 talking-head clip | clip | - |
| Comic halftone | `/comic-halftone` | a 9:16 talking-head clip | clip | - |
| Magazine cover | `/magazine-cover` | a 9:16 talking-head clip | clip | brands |
| Neon outline | `/neon-outline` | a 9:16 talking-head clip | clip | - |
| RGB glitch live | `/rgb-glitch-live` | a 9:16 talking-head clip | clip | brands |
| Triptych timecode | `/triptych-timecode` | three clips | clip | - |

## Format prompts (12, from the 12 Claude Video Formats guide)

Put `Format: <typed>.` as the last line of `studio/templates/format-prompt.md`. Prefer the nearest library style for a full film.

| Format | हिंदी | Slug | Typed | Look | Good for | Nearest |
|---|---|---|---|---|---|---|
| Kinetic typography | काइनेटिक टाइपोग्राफ़ी | `kinetic-typography` | Kinetic typography | The film is built from the words themselves: huge condensed letters fill the frame, stack behind objects and become parts of the set. | Quotes and one-line hooks, Announcements and lists, Punchy explainers | `kinetic-type`, `swiss-motion`, `/kinetic-lyrics` |
| Pixel art game | पिक्सेल आर्ट गेम | `pixel-art-game` | Pixel art game | The story becomes a game level: chunky pixels, a HUD with progress and a counter, and dialogue-box text. | Journeys and processes as levels, Nostalgia, Kids and gaming audiences | `pixel-rpg` |
| Claymation | क्लेमेशन स्टॉप मोशन | `claymation-stop-motion` | Claymation stop motion | Everything looks modelled in clay, with swirled fingerprint marks pressed into every surface and objects that come alive. | Warm family stories, Food and drink, Kids | `claymation`, `felt-stopmotion` |
| Anime opening | एनीमे ओपनिंग | `anime-opening` | Anime opening | An anime title sequence: dramatic skies, speed lines, diagonal split frames, a giant symbol filling the screen and a title card. | Hype intros and series openers, Mythic action, Youth audiences | `cel-anime-80s`, `/anime-reel` |
| Whiteboard sketch | व्हाइटबोर्ड स्केच | `whiteboard-sketch` | Whiteboard sketch | A drawn hand and marker build the page stroke by stroke on a whiteboard, with one coloured line tying the story together. | Explainers and how-it-works, Timelines, Education | `whiteboard`, `chalkboard` |
| 80s VHS commercial | 80 के दशक का VHS विज्ञापन | `80s-vhs-commercial` | 80s VHS commercial | An 80s tape ad: the tape machine is part of the story, with PLAY and FF overlays, a tape counter, static and a retro sunset. | Retro ads and satire, Comedy, Nostalgia (the VCR and Doordarshan era) | `vaporwave`, `ascii-crt`, `synthwave` |
| Rubber hose cartoon | रबर होज़ कार्टून | `rubber-hose-cartoon` | Rubber hose cartoon | A 1930s cartoon: everything gets eyes and white gloves, bodies bend like hoses, sunbursts behind, film grain on every frame. | Comedy, Food and drink, Retro ads | `rubber-hose` |
| Isometric 3D | आइसोमेट्रिक 3D | `isometric-3d` | Isometric 3D | One connected isometric world seen from a fixed angle, with the subject moving through it like a model railway. | Processes and supply chains, Village and city worlds, Infographics | `isometric-picture-book`, `iso-infographic` |
| Paper cut-out | पेपर कट-आउट | `paper-cut-out` | Paper cut-out | Layers of cut card with soft shadows under each piece: flames, waves and skies stacked as paper, words on paper strips. | Folk tales, Festivals, Gentle stories | `collage-cutout`, `papercut-red`, `paper-popup` |
| Comic book | कॉमिक बुक | `comic-book` | Comic book | Comic panels, halftone dots, starbursts, speech bubbles and onomatopoeia that the film invents itself. | Action, Comedy and case-file humour, Story beats in panels | `halftone-dossier`, `/comic-halftone`, `/comic-reel` |
| Neon synthwave (not in the guide's reel) | नियॉन सिंथवेव | `neon-synthwave` | Neon synthwave | A neon road into a striped sunset with a glowing grid on both sides; the road is the timeline. | Tech and AI, Music and nightlife, Retro-futurism | `synthwave`, `vaporwave` |
| Liquid motion (not in the guide's reel) | लिक्विड मोशन | `liquid-motion` | Liquid motion | Liquid is the transition: swirls of it fill the frame and carry the viewer into the next scene. | Chai, coffee and food, Product reveals, Smooth transitions | `liquid-glass`, `ebru-marbling` |
