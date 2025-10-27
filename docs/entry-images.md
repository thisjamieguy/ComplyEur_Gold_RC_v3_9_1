# Country Entry Requirement Images

To add a new country banner image for the Entry Requirements modal and cards:

- Place an image in `app/static/images/cityscapes/`.
- Name the file using lowercase with underscores: `{country}_{city}.webp` (e.g., `austria_vienna.webp`).
- Supported formats: `.webp`, `.jpg`, `.jpeg`, `.png`.

The app automatically picks the appropriate image by:
- Matching a two-letter country code file (e.g., `at.webp`) if provided.
- Otherwise, matching any file that starts with the country name (e.g., `austria_vienna.webp`).
- Falling back to `default.webp` when no match is found.

No external URLs or absolute paths are used; all assets are served locally from the `static` directory for Render compatibility.


