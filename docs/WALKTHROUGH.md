# Use an external image/video tool

Start with the README's demo init and plan commands. The screenplay/plan is synthetic instructional material, not an existing user film.

## Add actual image references

Generate or supply real images in your selected tool, inspect them, then register them. Replace the example external paths below with your files:

```bash
python3 -m aifilm add-asset projects/demo MEERA_V1 character /path/to/meera.png \
  --description "Canonical Meera identity: preserve face and proportions"
python3 -m aifilm add-asset projects/demo KURTA_V1 costume /path/to/kurta.png \
  --description "Faded blue cotton kurta, right pocket"
python3 -m aifilm add-asset projects/demo ROOM_V1 location /path/to/room.png \
  --description "Doorway, wooden table and practical lamp; fixed geography"
python3 -m aifilm add-asset projects/demo LETTER_V1 prop /path/to/letter.png \
  --description "The same folded paper letter throughout the scene"
python3 -m aifilm add-asset projects/demo SH001_FRAME_V1 keyframe /path/to/frame.png \
  --description "Clean SH001 start frame, Meera at doorway, letter on table" \
  --derived-from MEERA_V1 KURTA_V1 ROOM_V1 LETTER_V1
```

Have the assistant update a copy of the plan. For SH001 set `asset_ids` to all five IDs, and `input_asset_ids` to `["SH001_FRAME_V1"]`. Use matching scene-specific references for the other shots. Do not register a contact sheet as a clean keyframe without inspecting/extracting the intended panel.

```bash
python3 -m aifilm set-plan projects/demo /path/to/revised-plan.json
python3 -m aifilm export-shot projects/demo SH001 exports/SH001-image-v1 \
  --profile profiles/portable-single-image.json
```

Read `RUN_IN_TOOL.md`. Check your tool's current settings and syntax before generation. A portable template is not evidence that the target model supports this shot. If you adapt the action/duration, update the plan and re-export first.

## Import the actual output

```bash
python3 -m aifilm import-take projects/demo SH001 /path/to/downloaded-shot.mp4 \
  --bundle exports/SH001-image-v1 --tool "Actual tool name" --model "Actual model version"
```

The output includes the take ID and hash. Repeating the same import against the same bundle returns the existing take rather than duplicating it.

## Review without inventing evidence

Open the actual clip in a media-capable environment. Compare the original source, shot plan, canonical images and adjacent shots. Create review JSON using [the contract](CONTRACT.md), replacing all uncertainty only with observed evidence. Include every beat/criterion for that shot and the imported take hash.

```bash
python3 -m aifilm review-take projects/demo T00001 /path/to/review.json
```

An independent breakdown pass must compare all original lines against all semantic beats and shots, including multiple actions per line. After that real review:

```bash
python3 -m aifilm review-breakdown projects/demo \
  --reviewer "Actual reviewer/run identifier" \
  --evidence "Describe the original-source comparison actually performed, including compound actions and dialogue."
python3 -m aifilm audit projects/demo
```

The example command does not constitute review evidence by itself. Use the actual findings. Completion stays false until every planned shot has a current accepted take and all coverage/decision gates pass.
