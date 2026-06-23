#!/usr/bin/env python3
"""
LudoRef — Script d'injection des images BGG dans les fiches HTML
À lancer APRÈS fetch_bgg_images.py.

Usage: python3 inject_bgg_images.py

Le script remplace le container vide #bgg-image-container par une <img> statique.
"""

import json, os, re, sys

IMAGES_FILE = "bgg_images.json"
JEUX_DIR    = "jeux"

def main():
    if not os.path.exists(IMAGES_FILE):
        print(f"❌ {IMAGES_FILE} introuvable. Lance d'abord fetch_bgg_images.py")
        sys.exit(1)

    with open(IMAGES_FILE, encoding='utf-8') as f:
        bgg_images = json.load(f)

    available = {k: v for k, v in bgg_images.items() if v}
    print(f"Images disponibles: {len(available)}/{len(bgg_images)}")

    html_files = [f for f in os.listdir(JEUX_DIR) if f.endswith('.html')]
    print(f"Fiches HTML: {len(html_files)}")

    injected = 0
    skipped  = 0
    missing  = 0

    for fname in sorted(html_files):
        slug = fname.replace('.html', '')
        img_url = available.get(slug)

        fpath = os.path.join(JEUX_DIR, fname)
        with open(fpath, encoding='utf-8') as f:
            content = f.read()

        if img_url:
            # Remplacer le container vide par une img statique
            new_container = (
                f'<div class="sidebar-box" id="bgg-image-container" style="min-height:80px;">'
                f'<img src="{img_url}" alt="{slug}" '
                f'style="width:100%;display:block;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.3);" '
                f'loading="lazy" onerror="this.parentElement.style.display=\'none\'">'
                f'</div>'
            )
            # Remplacer l'ancien container (vide ou avec img existante)
            old_pattern = re.compile(
                r'<div class="sidebar-box" id="bgg-image-container"[^>]*>.*?</div>',
                re.DOTALL
            )
            new_content, n = old_pattern.subn(new_container, content, count=1)
            if n > 0 and new_content != content:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                injected += 1
            else:
                skipped += 1
        else:
            missing += 1

    print(f"\n✅ {injected} fiches mises à jour avec image statique")
    print(f"   {missing} sans image BGG (placeholder emoji conservé)")
    print(f"   {skipped} inchangées")

if __name__ == "__main__":
    main()
