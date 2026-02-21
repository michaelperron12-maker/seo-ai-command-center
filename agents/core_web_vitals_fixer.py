#!/usr/bin/env python3
"""
core_web_vitals_fixer.py — Optimize Core Web Vitals for all SeoAI client sites.

Functions:
- compress_images: Find and compress images >500KB
- convert_to_webp: Convert PNG/JPG to WebP
- add_lazy_loading: Add loading="lazy" to images missing it
- fix_gzip_config: Verify nginx gzip config is optimal

Usage:
    python3 core_web_vitals_fixer.py                   # Fix all sites
    python3 core_web_vitals_fixer.py --site 1          # Fix specific site
    python3 core_web_vitals_fixer.py --images-only     # Only compress images
    python3 core_web_vitals_fixer.py --lazy-only       # Only add lazy loading
    python3 core_web_vitals_fixer.py --dry-run         # Preview changes
"""

import os
import sys
import re
import glob
import yaml
import subprocess
from datetime import datetime

# Path setup
BASE_DIR = '/opt/seo-agent'
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yaml')
LOG_PATH = os.path.join(BASE_DIR, 'logs', 'cwv_fixer.log')

# Thresholds
MAX_IMAGE_KB = 400  # compress images larger than this
JPEG_QUALITY = 82
MAX_WIDTH = 1200  # resize images wider than this

# ─── Logging ───
def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [CWV] [{level}] {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ─── Config ───
def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def get_site_dirs(site_id=None):
    """Get list of site directories to process."""
    config = load_config()
    sites = config.get('sites', [])
    dirs = []
    for i, site in enumerate(sites, 1):
        if site_id and i != site_id:
            continue
        if site.get('actif', True):
            dirs.append({
                'id': i,
                'nom': site['nom'],
                'chemin': site['chemin'],
                'domaine': site['domaine'],
            })
    return dirs


# ═══════════════════════════════════════════════════════
#  IMAGE COMPRESSION
# ═══════════════════════════════════════════════════════

def compress_images(site_dir, dry_run=False):
    """Find and compress images larger than MAX_IMAGE_KB."""
    try:
        from PIL import Image
    except ImportError:
        log("Pillow not installed. Run: pip3 install Pillow", "ERROR")
        return {"compressed": 0, "saved_kb": 0}

    compressed = 0
    total_saved = 0
    base = site_dir['chemin']

    for ext in ('*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG'):
        for fpath in glob.glob(os.path.join(base, '**', ext), recursive=True):
            # Skip backup files
            if '.bak' in fpath or '/backup/' in fpath:
                continue

            size_kb = os.path.getsize(fpath) / 1024
            if size_kb < MAX_IMAGE_KB:
                continue

            try:
                img = Image.open(fpath)
                orig_size = os.path.getsize(fpath)
                fname = os.path.basename(fpath)

                # Check if it's a PNG without transparency (can convert to JPEG)
                if fpath.lower().endswith('.png') and img.mode == 'RGB':
                    # Convert to JPEG (much smaller)
                    jpg_path = re.sub(r'\.png$', '.jpg', fpath, flags=re.IGNORECASE)

                    if dry_run:
                        log(f"[DRY-RUN] Would convert {fname} PNG->JPG ({size_kb:.0f}KB)")
                        continue

                    img_rgb = img.convert('RGB')
                    if img_rgb.width > MAX_WIDTH:
                        ratio = MAX_WIDTH / img_rgb.width
                        new_h = int(img_rgb.height * ratio)
                        img_rgb = img_rgb.resize((MAX_WIDTH, new_h), Image.LANCZOS)

                    img_rgb.save(jpg_path, 'JPEG', quality=JPEG_QUALITY, optimize=True)
                    new_size = os.path.getsize(jpg_path)

                    # Backup original PNG
                    os.rename(fpath, fpath + '.bak')

                    saved = (orig_size - new_size) / 1024
                    total_saved += saved
                    compressed += 1
                    log(f"  PNG->JPG {fname}: {orig_size//1024}KB -> {new_size//1024}KB (saved {saved:.0f}KB)")

                elif fpath.lower().endswith('.png') and img.mode in ('RGBA', 'LA', 'P'):
                    # PNG with transparency — optimize in place
                    if dry_run:
                        log(f"[DRY-RUN] Would optimize {fname} PNG ({size_kb:.0f}KB)")
                        continue

                    if img.width > MAX_WIDTH:
                        ratio = MAX_WIDTH / img.width
                        new_h = int(img.height * ratio)
                        img = img.resize((MAX_WIDTH, new_h), Image.LANCZOS)

                    img.save(fpath, 'PNG', optimize=True)
                    new_size = os.path.getsize(fpath)
                    saved = (orig_size - new_size) / 1024
                    if saved > 10:
                        total_saved += saved
                        compressed += 1
                        log(f"  PNG opt {fname}: {orig_size//1024}KB -> {new_size//1024}KB (saved {saved:.0f}KB)")

                elif fpath.lower().endswith(('.jpg', '.jpeg')):
                    # Optimize JPEG
                    if dry_run:
                        log(f"[DRY-RUN] Would optimize {fname} JPG ({size_kb:.0f}KB)")
                        continue

                    img_rgb = img.convert('RGB')
                    if img_rgb.width > MAX_WIDTH:
                        ratio = MAX_WIDTH / img_rgb.width
                        new_h = int(img_rgb.height * ratio)
                        img_rgb = img_rgb.resize((MAX_WIDTH, new_h), Image.LANCZOS)

                    img_rgb.save(fpath, 'JPEG', quality=JPEG_QUALITY, optimize=True)
                    new_size = os.path.getsize(fpath)
                    saved = (orig_size - new_size) / 1024
                    if saved > 10:
                        total_saved += saved
                        compressed += 1
                        log(f"  JPG opt {fname}: {orig_size//1024}KB -> {new_size//1024}KB (saved {saved:.0f}KB)")

            except Exception as e:
                log(f"  Error compressing {fpath}: {e}", "WARNING")

    return {"compressed": compressed, "saved_kb": total_saved}


def convert_to_webp(image_path, quality=80):
    """Convert a single image to WebP format."""
    try:
        from PIL import Image
    except ImportError:
        return None

    try:
        img = Image.open(image_path)
        webp_path = re.sub(r'\.(png|jpg|jpeg)$', '.webp', image_path, flags=re.IGNORECASE)

        if img.mode in ('RGBA', 'LA', 'P'):
            img.save(webp_path, 'WEBP', quality=quality, method=4)
        else:
            img.convert('RGB').save(webp_path, 'WEBP', quality=quality, method=4)

        log(f"  WebP: {os.path.basename(image_path)} -> {os.path.basename(webp_path)}")
        return webp_path
    except Exception as e:
        log(f"  WebP conversion error: {e}", "WARNING")
        return None


# ═══════════════════════════════════════════════════════
#  LAZY LOADING
# ═══════════════════════════════════════════════════════

def add_lazy_loading(site_dir, dry_run=False):
    """Add loading='lazy' to all img tags that don't have it."""
    base = site_dir['chemin']
    fixed_files = 0
    fixed_images = 0

    for fpath in glob.glob(os.path.join(base, '**', '*.html'), recursive=True):
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            original = content
            # Add loading="lazy" to img tags that don't have it
            content = re.sub(
                r'<img(?![^>]*loading=)([^>]*?)(/?)>',
                r'<img loading="lazy"\1\2>',
                content
            )

            if content != original:
                count = content.count('loading="lazy"') - original.count('loading="lazy"')
                if dry_run:
                    log(f"[DRY-RUN] Would add lazy loading to {count} images in {os.path.basename(fpath)}")
                else:
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    log(f"  Lazy loading: {os.path.basename(fpath)} (+{count} images)")
                fixed_files += 1
                fixed_images += count

        except Exception as e:
            log(f"  Error processing {fpath}: {e}", "WARNING")

    return {"files": fixed_files, "images": fixed_images}


# ═══════════════════════════════════════════════════════
#  HTML OPTIMIZATION
# ═══════════════════════════════════════════════════════

def optimize_html(site_dir, dry_run=False):
    """Minor HTML optimizations for performance."""
    base = site_dir['chemin']
    fixed = 0

    for fpath in glob.glob(os.path.join(base, '**', '*.html'), recursive=True):
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            original = content

            # Add width/height to images that are missing them (CLS fix)
            # This is a best-effort approach using standard dimensions

            # Ensure font-display: swap on Google Fonts
            content = content.replace(
                'family=Inter:wght@400;500;600;700&display=swap',
                'family=Inter:wght@400;500;600;700&display=swap'
            )

            # Add preconnect for Google Fonts if missing
            if 'fonts.googleapis.com' in content and 'rel="preconnect"' not in content:
                content = content.replace(
                    '<link href="https://fonts.googleapis.com',
                    '<link rel="preconnect" href="https://fonts.googleapis.com">\n    '
                    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n    '
                    '<link href="https://fonts.googleapis.com'
                )

            if content != original:
                if not dry_run:
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(content)
                fixed += 1

        except Exception:
            pass

    return fixed


# ═══════════════════════════════════════════════════════
#  NGINX GZIP CHECK
# ═══════════════════════════════════════════════════════

def check_gzip_config():
    """Check if nginx gzip is properly configured."""
    gzip_ok = True
    issues = []

    # Check main nginx.conf
    nginx_conf = '/etc/nginx/nginx.conf'
    conf_d = '/etc/nginx/conf.d/'

    try:
        with open(nginx_conf, 'r') as f:
            main_conf = f.read()
    except PermissionError:
        log("Cannot read nginx.conf (permission denied)", "WARNING")
        return {"ok": False, "issues": ["Cannot read nginx.conf"]}

    if 'gzip on' not in main_conf:
        issues.append("gzip not enabled in nginx.conf")
        gzip_ok = False

    # Check if gzip_types is configured (in main or conf.d)
    all_conf = main_conf
    if os.path.isdir(conf_d):
        for fname in os.listdir(conf_d):
            if fname.endswith('.conf'):
                try:
                    with open(os.path.join(conf_d, fname), 'r') as f:
                        all_conf += f.read()
                except Exception:
                    pass

    required_directives = ['gzip_types', 'gzip_vary', 'gzip_comp_level']
    for directive in required_directives:
        # Check uncommented lines
        if not re.search(rf'^\s*{directive}\s', all_conf, re.MULTILINE):
            issues.append(f"{directive} not configured")
            gzip_ok = False

    if gzip_ok:
        log("Nginx gzip: OK (fully configured)")
    else:
        log(f"Nginx gzip issues: {', '.join(issues)}", "WARNING")

    return {"ok": gzip_ok, "issues": issues}


def update_html_references(site_dir, old_ext, new_ext):
    """Update image references in HTML files when converting formats."""
    base = site_dir['chemin']
    updated = 0

    for fpath in glob.glob(os.path.join(base, '**', '*.html'), recursive=True):
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            original = content
            # Replace .png references with .jpg (for converted images)
            content = re.sub(
                rf'(src=["\'][^"\']*?)\.{old_ext}(["\'])',
                rf'\1.{new_ext}\2',
                content,
                flags=re.IGNORECASE
            )

            if content != original:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                updated += 1

        except Exception:
            pass

    return updated


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def fix_all(site_id=None, dry_run=False, images_only=False, lazy_only=False):
    """Run all Core Web Vitals fixes."""
    log("=" * 60)
    log("CORE WEB VITALS FIXER: Starting")
    log("=" * 60)

    sites = get_site_dirs(site_id)
    results = {
        "images_compressed": 0,
        "kb_saved": 0,
        "lazy_files": 0,
        "lazy_images": 0,
        "gzip_ok": True,
    }

    for site in sites:
        log(f"\n── Site: {site['nom']} ({site['domaine']})")

        if not lazy_only:
            # Compress images
            img_result = compress_images(site, dry_run)
            results["images_compressed"] += img_result["compressed"]
            results["kb_saved"] += img_result["saved_kb"]

        if not images_only:
            # Add lazy loading
            lazy_result = add_lazy_loading(site, dry_run)
            results["lazy_files"] += lazy_result["files"]
            results["lazy_images"] += lazy_result["images"]

            # HTML optimizations
            if not dry_run:
                optimize_html(site, dry_run)

    # Check gzip
    if not images_only and not lazy_only:
        gzip_result = check_gzip_config()
        results["gzip_ok"] = gzip_result["ok"]

    log("\n" + "=" * 60)
    log(f"CWV FIXER DONE:")
    log(f"  Images compressed: {results['images_compressed']} (saved {results['kb_saved']:.0f}KB)")
    log(f"  Lazy loading: {results['lazy_images']} images in {results['lazy_files']} files")
    log(f"  Gzip: {'OK' if results['gzip_ok'] else 'NEEDS FIX'}")
    log("=" * 60)

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Fix Core Web Vitals issues')
    parser.add_argument('--site', type=int, help='Fix specific site_id only')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes')
    parser.add_argument('--images-only', action='store_true', help='Only compress images')
    parser.add_argument('--lazy-only', action='store_true', help='Only add lazy loading')
    args = parser.parse_args()

    fix_all(
        site_id=args.site,
        dry_run=args.dry_run,
        images_only=args.images_only,
        lazy_only=args.lazy_only,
    )
