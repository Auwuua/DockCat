# How To Use This File

This file records the ChatGPT prompts we used to generate DockCat art assets: default cat characters, app icons, and collectables. Feel free to use them for generating the cat identity, postures, animation frames, and collectables to customize your DockCat. If you would like the cat to look more realistic or more cartoon-like, you can adjust the art style part of the prompt in the way you like.

## Contents

- `Prompts > Cat`: shared cat art style, static posture prompts, and animation frame prompts.
- `Prompts > App Icon`: sleeping and non-sleeping Dock icon source prompts.
- `Prompts > Collectables`: prompts for collectables the cat can bring home.

## How To Use Prompts

For cat assets, start with `Cat > General Art Style`, then combine it with either the static posture prompt template or the animation frame prompt template. Replace the bracketed placeholders with the posture, motion plan, frame count, and output paths you need.

For one-off assets, you can use the example prompt as a tested starting point. The examples omit file-format requirements already covered by the templates, so add the template requirements when generating production images.

For custom cats, upload reference photos before prompting. The prompt assumes ChatGPT can see those references and should preserve the cat's identity: coat color, markings, fur length, body shape, facial features, and overall personality.

# Prompts

## Cat

### General Art Style

Use the uploaded real cat photos as reference images. Transform the cat into a cute retro web-game style 2D digital illustration while preserving the cat's original coat color, fur length, markings, body shape, facial features, and overall identity exactly as shown in the reference photo. Do not change the cat into a different breed, fur type, or coat pattern. The cat must be in the posture or animation frame specified by the production prompt.

Render the cat in a simplified, rounded, cartoon-like style inspired by early 2000s browser pet games or Flash game animal icons. The overall visual style should feel soft, charming, nostalgic, and slightly low-detail, like an old web UI pet illustration or sticker asset. Use clean, smooth outlines with slightly thick dark linework, simple flat or softly blended colors, and minimal gentle shading. Suggest the fur texture and markings using a few simplified curved lines, short strokes, or stylized pattern shapes rather than realistic individual hairs.

Keep the anatomy cute and stylized, with a compact rounded form, slightly enlarged head proportions, small paws, and a gentle, appealing expression. The final result should look like a small illustrated pet icon from an old casual browser game: clean silhouette, warm and slightly muted colors, soft hand-drawn digital painting feel, low visual complexity, and a nostalgic 2000s pet-game aesthetic.

The cat must be isolated with a fully transparent background. There should be no background elements at all: no floor, no shadows on the ground, no scenery, no room, no gradient backdrop, and no decorative objects. Output only the cat as a clean standalone transparent-background character asset / sticker-style illustration.

### Static Pose Prompts

#### Prompt Template

Create a single static transparent-background PNG of the referenced cat in this posture: `[Describe the exact cat posture, body orientation, expression, and any app-specific use case here.]`

Use the art style specified above. Preserve the cat's exact identity, coat markings, fur length, colors, face shape, and body proportions from the reference photos.

File requirements:

- File format: PNG with alpha transparency.
- Color space: sRGB.
- Default canvas: 512 x 512 px.
- Runtime display target: the app preserves each PNG's source aspect ratio and renders poses at 10% of the source PNG point size by default. Users can adjust this scale percentage.
- Padding: keep at least 8% transparent padding around the cat.
- Anchor consistency: keep the cat's body-bottom or paw-bottom anchor visually consistent across all poses in the same asset pack.
- Naming: use lowercase English letters, numbers, underscores, and hyphens only.
- Background: fully transparent. No shadow, floor, scenery, object, UI, text, or decorative element.
- Output file: `[Add the target path, for example poses/resting/side.png.]`

#### Rest Side

Create the referenced cat lying on its side in a relaxed resting pose. The cat should look calm and comfortable, with a soft rounded silhouette and visible tail placement.

Example output file: `poses/resting/side.png`

#### Rest Loaf

Create the referenced cat in a loaf pose with paws tucked under the body and eyes closed. The cat should look relaxed, compact, and gently alert.

Example output file: `poses/resting/loaf.png`

#### Held

Create the referenced cat being held by the armpits, shown as a cute dangling desktop-pet pose. The cat's body may hang slightly downward with small paws visible and the body naturally stretched longer due to gravity, but the expression should remain gentle and charming rather than distressed. Do not draw human hands or arms.

Example output file: `poses/held/held.png`

#### Dialogue Stand

Create the referenced cat standing or sitting upright facing the viewer directly, suitable as one concrete dialogue pose for reminder dialogs and returning-home messages. The expression should be attentive, friendly, and slightly expectant. Leave enough transparent space above the head in the canvas for the app to place a speech bubble. Do not include the speech bubble.

Example output file: `poses/dialogue/stand.png`

#### Transition Stretch

Create the referenced cat at the peak of a satisfying stretch, suitable as one concrete 2-second transition pose: front paws stretched far forward, body low in front, back arched, and rear raised upward. This is not an animation.

Example output file: `poses/transition/stretch.png`

### Animation Frame Prompts

#### Prompt Template

Create a transparent-background PNG animation cycle of the referenced cat performing this motion: `[Describe the animation action, movement direction, mood, body mechanics, and intended app use case here.]`

The cycle should contain `[frame count]` frames. Before generating images, plan the motion for every frame so the cycle connects smoothly:

- `[frame_01.png]`: `[Describe the pose for frame 1.]`
- `[frame_02.png]`: `[Describe the pose for frame 2.]`
- `[Add or remove frame rows as needed.]`

Use the art style specified above. Preserve the cat's exact identity, coat markings, fur length, colors, face shape, and body proportions from the reference photos across all frames.

File requirements:

- File format: PNG with alpha transparency.
- Color space: sRGB.
- Default canvas: 512 x 512 px for every frame.
- Runtime display target: the app preserves each PNG's source aspect ratio and renders animation frames at 10% of the source PNG point size by default. Users can adjust this scale percentage.
- Padding: keep at least 8% transparent padding around the cat.
- Frame consistency: use identical canvas size, identical cat scale, consistent baseline or paw-bottom position, consistent head/body size, consistent line weight, consistent color palette, and consistent transparent padding for every frame.
- Naming: use lowercase English letters, numbers, underscores, and hyphens only. Sortable filenames are required because the app plays every loadable image in filename order.
- Background: fully transparent. No shadow, floor, scenery, object, UI, text, or decorative element.
- Output folder: `[Add the target folder, for example animations/walk/.]`

If generating frames one at a time, always reference the planned full-frame cycle and the previously generated frames. Keep canvas size, scale, anchor position, line weight, color palette, and visual style identical across all frames.

#### Single-Sided Walk

Create a looping walk cycle of the referenced cat walking to one side. Before generating images, plan the motion for every frame so the cycle connects smoothly:

- `walk_01.png`: contact pose, front paw on the walking side reaching forward, opposite rear paw pushing back.
- `walk_02.png`: passing pose, body slightly centered, paws moving under the body.
- `walk_03.png`: opposite contact pose, the other front and rear paws taking weight.
- `walk_04.png`: return/passing pose that leads cleanly back into `walk_01.png`.

The walk should be slow, relaxed, and cute, suitable for a desktop pet strolling along the macOS Dock. Keep paw motion clear and readable, with a stable body anchor so the app can move the character horizontally.

If your AI image generation tool cannot generate multiple frames in one request, try generating the walk frames one at a time.

Example output folder: `animations/walk/`

## App Icon

### Sleep State App Icon

Create a macOS app icon source image showing the referenced cat sleeping peacefully on a cute square cushion. The cushion should be soft, simple, rounded-square, and charming, with a retro web-game pet-app feeling. Preserve the cat's exact identity, coat markings, fur length, colors, face shape, and body proportions from the reference photos. The cat should be curled up or compactly sleeping on top of the cushion. Use the shared cute retro 2D illustration style, but compose it as a polished macOS app icon. The background outside the icon artwork should be transparent or app-icon-safe, with no text, no extra objects, and no scenery.

File requirements:

- Output file: `icon_sleep.png`.
- Custom pack path: `app_icons/icon_sleep.png`.
- 1024 x 1024 px PNG source.
- Square app-icon composition.
- Keep enough padding for macOS icon masking and scaling.
- This source should be exportable to `.icns`.
- For bundled runtime `Resources/AppIcon`, downsample the transparent PNG to about 512 px on the long edge after generating the high-resolution source, then inset the visible artwork to about 86% of the transparent source image.
- DockCat caches successfully loaded custom icons under `~/Library/Application Support/DockCat/AppIcon/`; regenerate the pack source and restart DockCat when changing the icon.

### Active State App Icon

Create a macOS app icon source image showing only the same cute square cushion from the sleeping app icon, with no cat on it. The cushion should match the sleeping icon exactly in style, shape, color palette, angle, scale, and lighting, so the Dock icon can switch between the cat-sleeping version and the empty-cushion version without feeling like a different icon. Use a soft, charming retro web-game pet-app illustration style. The background outside the icon artwork should be transparent or app-icon-safe, with no text, no extra objects, and no scenery.

File requirements:

- Output file: `icon_empty.png`.
- Custom pack path: `app_icons/icon_empty.png`.
- 1024 x 1024 px PNG source.
- Square app-icon composition.
- Keep enough padding for macOS icon masking and scaling.
- This source should be exportable to `.icns`.
- For bundled runtime `Resources/AppIcon`, downsample the transparent PNG to about 512 px on the long edge after generating the high-resolution source, then inset the visible artwork to about 86% of the transparent source image.
- DockCat caches successfully loaded custom icons under `~/Library/Application Support/DockCat/AppIcon/`; regenerate the pack source and restart DockCat when changing the icon.

## Collectables

### Prompt Template

Create a single small transparent-background PNG collectable item for DockCat: `[Describe the specific object, silhouette, angle, color, condition, and any story detail here.]`

Use a visual style compatible with the DockCat cat assets: simplified, rounded, charming, nostalgic early-2000s browser pet-game style, with clean smooth outlines, slightly thick dark linework, warm muted colors, flat or softly blended fills, minimal gentle shading, and low visual complexity. The collectable should feel like a tiny object the cat could bring home from a walk. It should be readable at small size and visually compatible with the cat.

If you add a display name for a new collectable, keep the English name at 16 characters or fewer, including spaces.

File requirements:

- File format: PNG with alpha transparency.
- Color space: sRGB.
- Default canvas: 128 x 128 px.
- Padding: keep at least 10% transparent padding around the object.
- Naming: use lowercase English letters, numbers, underscores, and hyphens only.
- Background: fully transparent. No shadow, floor, scenery, UI, text, or decorative element.
- Output file: `[Add the target path and filename.]`

### Leaf

Create a small fallen leaf collectable, slightly curled and simple, with a warm muted yellow-green or soft orange color. The silhouette should be readable and cute rather than realistic, with one or two simplified vein lines and a gently rounded shape. It should look like a tiny object the cat proudly brought home.

Example output file: `collectables/leaf.png`

### Pebble

Create a small smooth pebble collectable with a rounded irregular oval shape, soft gray-blue coloring, and one or two subtle lighter markings. The pebble should look tactile, simple, and charming, like a tiny keepsake from outside, while staying low-detail and readable at small size.

Example output file: `collectables/pebble.png`

### Feather

Create a feather collectable, light and gently curved, with a soft cream, pale gray, or muted tan color. The silhouette should be rounded and friendly rather than sharp, with a simple central shaft and only a few broad feather barbs so it remains readable at small size. It should feel like an ordinary outdoor bit the cat proudly carried home.

Example output file: `collectables/feather.png`
