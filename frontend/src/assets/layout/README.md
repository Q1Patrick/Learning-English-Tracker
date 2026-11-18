# Layout SVG assets

Original vectors extracted from the user-provided Figma SVG export (`Pasted text.txt`) for FE-025. The user approved extraction on 16 November 2026.

- Figma file: [Untitled](https://www.figma.com/design/7Z0gBaqUE3W6tWMFcRgnUP/Untitled?node-id=32-157)
- Figma file key: `7Z0gBaqUE3W6tWMFcRgnUP`
- Source node: `32:157`
- Original frame: `1487 x 1058`, viewBox `0 0 1487 1058`
- Source SHA-256: `6BAB493F93DF16B85F8D1FC24A9F158A6CCFCA24A27BB02DD1E632C622BF9DD5`

Each file retains the original path elements and every source path attribute, including path data, strokes, fill behavior, line caps, and line joins. Only a standalone SVG wrapper is added. The viewBox uses the original frame coordinates; the paths have not been translated, redrawn, recolored, or rasterized.

| Asset | Source group element indices | Intrinsic size | Original-coordinate viewBox |
|---|---|---|---|
| `logo.svg` | 2, 3 | 48 x 48 | `32 28 48 48` |
| `home.svg` | 6, 7 | 25 x 25 | `35 117 25 25` |
| `dashboard.svg` | 10, 11, 12, 13 | 25 x 25 | `35 174 25 25` |
| `vocabulary.svg` | 16 | 25 x 25 | `35 231 25 25` |
| `daily-goals.svg` | 18, 19, 20 | 25 x 25 | `35 288 25 25` |
| `study-sessions.svg` | 22, 23 | 25 x 25 | `35 345 25 25` |
| `statistics.svg` | 26, 27, 28 | 25 x 25 | `35 402 25 25` |
| `quiz.svg` | 30, 31 | 25 x 25 | `35 459 25 25` |
| `ai-feedback.svg` | 33, 34 | 25 x 25 | `35 516 25 25` |
| `profile.svg` | 36, 37 | 25 x 25 | `35 602 25 25` |
| `settings.svg` | 39, 40 | 25 x 25 | `35 659 25 25` |
| `search.svg` | 44, 45 | 23 x 23 | `305 31 23 23` |
| `notification.svg` | 47, 48 | 25 x 25 | `1206 29 25 25` |
| `user.svg` | 51, 52 | 25 x 25 | `1289 29 25 25` |
| `chevron-down.svg` | 54 | 18 x 18 | `1442 32 18 18` |

Indices are zero-based direct element children of the source root group; whitespace nodes are excluded. The logo includes the two book paths without the wordmark. The notification includes the original flat lower path at index 48.

Navigation source colors remain unchanged, including the white Dashboard icon. The application may use these monochrome vectors as CSS masks with `currentColor` to express navigation states without editing the source assets. Render the two-color logo as an image, not a monochrome mask.

These files contain only the selected vector shapes. They do not embed the complete Dashboard SVG, user data, base64 content, PNG dependencies, or source-frame images. Accessible labels belong to the surrounding application controls; decorative icon images should have empty alternative text.
