#!/usr/bin/env python3
"""
LudoRef — Script de récupération des images BGG
À lancer depuis ta machine (pas bloquée par BGG).

Usage: python3 fetch_bgg_images.py

Le script:
1. Lit bgg_ids.json pour avoir les IDs BGG de chaque jeu
2. Appelle l'API BGG pour chaque jeu et récupère l'URL d'image
3. Stocke tout dans bgg_images.json
4. Met à jour games_data.json avec les URLs d'images
"""

import json, urllib.request, urllib.parse, time, xml.etree.ElementTree as ET, os, sys

BGG_IDS_FILE   = "bgg_ids.json"
GAMES_FILE     = "games_data.json"
OUTPUT_FILE    = "bgg_images.json"

def get_bgg_image(bgg_id, slug):
    """Appelle l'API BGG et retourne l'URL de l'image."""
    url = f"https://boardgamegeek.com/xmlapi2/thing?id={bgg_id}&type=boardgame"
    headers = {
        "User-Agent": "LudoRef/1.0 (ludoref.fr, board game reference site)",
        "Accept": "text/xml,application/xml,*/*",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=15)

        # BGG retourne 202 quand il est en train de préparer la réponse
        if resp.status == 202:
            print(f"  ⏳ BGG building response for {slug}, retry in 3s...")
            time.sleep(3)
            resp = urllib.request.urlopen(req, timeout=15)

        content = resp.read()
        root = ET.fromstring(content)

        # Essayer <image> d'abord, puis <thumbnail>
        img_el = root.find('.//image')
        if img_el is None or not img_el.text or not img_el.text.strip():
            img_el = root.find('.//thumbnail')

        if img_el is not None and img_el.text and img_el.text.strip():
            url = img_el.text.strip()
            if url.startswith('//'):
                url = 'https:' + url
            return url

    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"  ⚠️  Rate limit BGG, pause 30s...")
            time.sleep(30)
            return get_bgg_image(bgg_id, slug)  # retry
        print(f"  ✗ HTTP {e.code} pour {slug}")
    except Exception as e:
        print(f"  ✗ Erreur {slug}: {e}")

    return None


def main():
    # Charger les IDs BGG
    if not os.path.exists(BGG_IDS_FILE):
        print(f"❌ {BGG_IDS_FILE} introuvable. Lance ce script depuis le dossier du repo.")
        sys.exit(1)

    with open(BGG_IDS_FILE, encoding='utf-8') as f:
        bgg_ids = json.load(f)

    # Charger les images déjà récupérées (si le script a déjà tourné)
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding='utf-8') as f:
            bgg_images = json.load(f)
        print(f"✓ {len(bgg_images)} images déjà en cache dans {OUTPUT_FILE}")
    else:
        bgg_images = {}

    # Jeux à traiter (ignorer ceux déjà récupérés)
    to_fetch = {slug: bid for slug, bid in bgg_ids.items()
                if slug not in bgg_images or not bgg_images[slug]}

    print(f"\nTotal BGG IDs: {len(bgg_ids)}")
    print(f"Déjà récupérées: {len(bgg_ids) - len(to_fetch)}")
    print(f"À récupérer: {len(to_fetch)}")
    print("\nDémarrage dans 2 secondes...")
    time.sleep(2)

    ok = 0
    fail = 0

    for i, (slug, bgg_id) in enumerate(to_fetch.items(), 1):
        print(f"[{i}/{len(to_fetch)}] {slug} (BGG {bgg_id})...", end=' ', flush=True)

        img_url = get_bgg_image(bgg_id, slug)

        if img_url:
            bgg_images[slug] = img_url
            print(f"✓ {img_url[:60]}...")
            ok += 1
        else:
            bgg_images[slug] = None
            print("✗ pas d'image")
            fail += 1

        # Sauvegarder après chaque jeu (en cas d'interruption)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(bgg_images, f, ensure_ascii=False, indent=2)

        # Pause pour ne pas spammer BGG (1 req/seconde)
        time.sleep(1.2)

    print(f"\n✅ Terminé: {ok} images récupérées, {fail} échecs")
    print(f"Résultats dans: {OUTPUT_FILE}")

    # Mettre à jour games_data.json
    print(f"\nMise à jour de {GAMES_FILE}...")
    with open(GAMES_FILE, encoding='utf-8') as f:
        games = json.load(f)

    updated = 0
    for g in games:
        slug = g['slug']
        img = bgg_images.get(slug)
        if img and g.get('bgg_img') != img:
            g['bgg_img'] = img
            updated += 1
        elif not img and 'bgg_img' not in g:
            g['bgg_img'] = ""

    with open(GAMES_FILE, 'w', encoding='utf-8') as f:
        json.dump(games, f, ensure_ascii=False, indent=2)

    print(f"✅ {updated} jeux mis à jour dans {GAMES_FILE}")
    print(f"\nProchaine étape: commite et pousse games_data.json et bgg_images.json")

if __name__ == "__main__":
    main()
