import os

SUPPORTED_EXTS = [".webp", ".jpg", ".jpeg", ".png"]


def _static_fs_base() -> str:
    """Return absolute filesystem path to the app's static directory."""
    # utils/ is at project root; app/static is under app/
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(project_root, "app", "static")


def country_image_path(country_code: str, country_name: str) -> str:
    """
    Finds the correct cityscape image for a given country.
    Matches country code (e.g. 'AT') or country name ('Austria'),
    using local static files in /static/images/cityscapes/.

    Returns the path relative to the Flask static folder,
    e.g. "images/cityscapes/austria_vienna.webp".
    """
    base_rel = "images/cityscapes"

    code = (country_code or "").strip().lower()
    # normalize spaces and hyphens/underscores for filename prefix matching
    name = (country_name or "").strip().lower().replace(" ", "_").replace("-", "_")

    static_base = _static_fs_base()
    cityscapes_dir = os.path.join(static_base, base_rel)

    # Ensure directory exists; if not, fallback to default.webp
    if not os.path.isdir(cityscapes_dir):
        return f"{base_rel}/default.webp"

    # 1) Try by code (e.g. at.webp)
    if code:
        for ext in SUPPORTED_EXTS:
            candidate_abs = os.path.join(cityscapes_dir, f"{code}{ext}")
            if os.path.exists(candidate_abs):
                return f"{base_rel}/{code}{ext}"

    # 2) Try by name prefix (handles austria_vienna.webp)
    try:
        for file in os.listdir(cityscapes_dir):
            # be robust to uppercase extensions
            lower_file = file.lower()
            if any(lower_file.endswith(ext) for ext in SUPPORTED_EXTS):
                # compare prefix with underscores
                if name and lower_file.startswith(name):
                    return f"{base_rel}/{file}"
    except Exception:
        # Directory read error; continue to default
        pass

    # 3) Fallback default (try any supported ext)
    for ext in SUPPORTED_EXTS:
        default_abs = os.path.join(cityscapes_dir, f"default{ext}")
        if os.path.exists(default_abs):
            return f"{base_rel}/default{ext}"

    # 4) If no explicit default exists, pick the first available image in the folder
    try:
        files = sorted(os.listdir(cityscapes_dir))
        for file in files:
            lower_file = file.lower()
            if any(lower_file.endswith(ext) for ext in SUPPORTED_EXTS):
                return f"{base_rel}/{file}"
    except Exception:
        pass

    # Final hardcoded fallback (may 404 if no images exist at all)
    return f"{base_rel}/default.webp"


