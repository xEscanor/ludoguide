#!/usr/bin/env python3
"""
LudoRef — Script de récupération des images BGG
Utilise l'authentification Basic BGG (requis depuis 2025).

Usage: python fetch_bgg_images.py
"""

import json, urllib.request, urllib.parse, time, xml.etree.ElementTree as ET, os, sys, base64

BGG_IDS_FILE = "bgg_ids.json"
GAMES_FILE   = "games_data.json"
OUTPUT_FILE  = "bgg_images.json"

# ============================================================
# REMPLIS ICI TON LOGIN BGG
BGG_USERNAME = ""   # ex: "MonPseudoBGG"
BGG_PASSWORD = ""   # ex: "monmotdepasse"
# ============================================================

def get_auth_header():
    if not BGG_USERNAME or not BGG_PASSWORD:
        return {}
    creds = base64.b64encode(f"{BGG_USERNAME}:{BGG_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {creds}"}

def get_bgg_image(bgg_id, slug):
    url = f"https://boardgamegeek.com/xmlapi2/thing?id={bgg_id}&type=boardgame"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/xml,application/xml,*/*",
        **get_auth_header()
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=15)
        if resp.status == 202:
            time.sleep(5)
            resp = urllib.request.urlopen(req, timeout=15)
        root = ET.fromstring(resp.read())
        img_el = root.find('.//image') or root.find('.//thumbnail')
        if img_el is not None and img_el.text and img_el.text.strip():
            u = img_el.text.strip()
            return ('https:' + u) if u.startswith('//') else u
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"\n  ⚠️  Rate limit, pause 60s...")
            time.sleep(60)
            return get_bgg_image(bgg_id, slug)
        print(f"  ✗ HTTP {e.code} pour {slug}")
    except Exception as e:
        print(f"  ✗ Erreur {slug}: {e}")
    return None

def main():
    if not BGG_USERNAME:
        print("❌ Remplis BGG_USERNAME et BGG_PASSWORD dans le script !")
        print("   Ouvre fetch_bgg_images.py avec un éditeur de texte")
        print("   et remplis les lignes BGG_USERNAME et BGG_PASSWORD")
        sys.exit(1)

    with open(BGG_IDS_FILE, encoding='utf-8') as f:
        bgg_ids = json.load(f)

    bgg_images = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding='utf-8') as f:
            bgg_images = json.load(f)
        print(f"✓ {sum(1 for v in bgg_images.values() if v)} images déjà en cache")

    to_fetch = {s: b for s, b in bgg_ids.items() if s not in bgg_images or not bgg_images[s]}
    print(f"À récupérer: {len(to_fetch)}\n")
    time.sleep(1)

    ok = 0
    for i, (slug, bgg_id) in enumerate(to_fetch.items(), 1):
        print(f"[{i}/{len(to_fetch)}] {slug} (BGG {bgg_id})...", end=' ', flush=True)
        img_url = get_bgg_image(bgg_id, slug)
        if img_url:
            bgg_images[slug] = img_url
            print(f"✓")
            ok += 1
        else:
            bgg_images[slug] = None
            print("✗ pas d'image")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(bgg_images, f, ensure_ascii=False, indent=2)
        time.sleep(1.5)

    print(f"\n✅ Terminé: {ok}/{len(to_fetch)} images récupérées")

    # Mettre à jour games_data.json
    with open(GAMES_FILE, encoding='utf-8') as f:
        games = json.load(f)
    for g in games:
        img = bgg_images.get(g['slug'])
        if img:
            g['bgg_img'] = img
    with open(GAMES_FILE, 'w', encoding='utf-8') as f:
        json.dump(games, f, ensure_ascii=False, indent=2)
    print(f"✅ games_data.json mis à jour")

if __name__ == "__main__":
    main()
