#!/usr/bin/env python3
"""Construit data.json pour ScanChina à partir de l'export CSV d'Open Food Facts.

Usage : curl -sL <csv.gz> | python3 scripts/build_data.py > data.json
(lit l'export CSV gzippé sur l'entrée standard, écrit le JSON sur la sortie standard)

On garde :
  1. tous les produits vendus en Chine continentale, Hong Kong, Taïwan ou Macao,
     ou dont le code-barre est chinois (préfixes 690-699, 489, 471, 958) ;
  2. les produits les plus scannés dans le monde (produits importés courants).
Seulement ceux qui ont au moins les calories pour 100 g.
"""
import csv
import gzip
import heapq
import io
import json
import sys
from datetime import date

TOP_WORLD = 30000  # produits populaires mondiaux ajoutés en plus de la Chine

CN_COUNTRIES = ("en:china", "en:hong-kong", "en:taiwan", "en:macau", "en:macao")
CN_PREFIXES = tuple(str(p) for p in range(690, 700)) + ("489", "471", "958")

# Ordre des valeurs dans chaque entrée de data.json (voir FIELDS dans index.html)
FIELDS = ["name", "brand", "kcal", "prot", "carb", "sugar", "fat", "satfat",
          "fiber", "salt", "serving_g", "serving_txt", "pack_g", "quantity"]


def num(v):
    if v is None or v == "":
        return None
    try:
        x = float(v)
    except ValueError:
        return None
    if x != x or x < 0:  # NaN ou négatif
        return None
    return x


def r1(x):
    return None if x is None else round(x, 1)


def clean(s, n):
    s = (s or "").replace("\t", " ").strip()
    return s[:n]


def row_to_entry(row):
    kcal = num(row.get("energy-kcal_100g"))
    if kcal is None:
        kj = num(row.get("energy-kj_100g")) or num(row.get("energy_100g"))
        if kj is not None:
            kcal = kj / 4.184
    if kcal is None or kcal > 950:
        return None
    vals = {k: num(row.get(c)) for k, c in [
        ("prot", "proteins_100g"), ("carb", "carbohydrates_100g"),
        ("sugar", "sugars_100g"), ("fat", "fat_100g"),
        ("satfat", "saturated-fat_100g"), ("fiber", "fiber_100g"),
        ("salt", "salt_100g")]}
    if vals["salt"] is None:
        sod = num(row.get("sodium_100g"))
        if sod is not None:
            vals["salt"] = sod * 2.5
    # valeurs aberrantes (> 100 g pour 100 g) -> on les ignore
    for k, v in vals.items():
        if v is not None and v > 100:
            vals[k] = None
    serving_g = num(row.get("serving_quantity"))
    if serving_g is not None and (serving_g <= 0 or serving_g > 5000):
        serving_g = None
    pack_g = num(row.get("product_quantity"))
    if pack_g is not None and (pack_g <= 0 or pack_g > 20000):
        pack_g = None
    name = clean(row.get("product_name") or row.get("generic_name")
                 or row.get("abbreviated_product_name"), 80)
    brand = clean((row.get("brands") or "").split(",")[0], 40)
    return [name, brand, round(kcal), r1(vals["prot"]), r1(vals["carb"]),
            r1(vals["sugar"]), r1(vals["fat"]), r1(vals["satfat"]),
            r1(vals["fiber"]), r1(vals["salt"]), r1(serving_g),
            clean(row.get("serving_size"), 30), r1(pack_g),
            clean(row.get("quantity"), 30)]


def main():
    csv.field_size_limit(sys.maxsize)
    stream = io.TextIOWrapper(gzip.GzipFile(fileobj=sys.stdin.buffer),
                              encoding="utf-8", errors="replace", newline="")
    reader = csv.DictReader(stream, delimiter="\t", quoting=csv.QUOTE_NONE)
    china = {}
    world = []  # tas (scans, code, entry) des produits mondiaux les plus scannés
    seen = 0
    for row in reader:
        seen += 1
        code = (row.get("code") or "").strip()
        if not code.isdigit() or len(code) not in (8, 12, 13, 14):
            continue
        if len(code) == 12:
            code = "0" + code  # UPC-A -> EAN-13
        countries = row.get("countries_tags") or ""
        is_cn = code.startswith(CN_PREFIXES) or any(c in countries for c in CN_COUNTRIES)
        scans = num(row.get("unique_scans_n")) or 0
        if not is_cn and scans < 2:
            continue
        entry = row_to_entry(row)
        if entry is None:
            continue
        if is_cn:
            china[code] = entry
        else:
            item = (scans, seen, code, entry)
            if len(world) < TOP_WORLD:
                heapq.heappush(world, item)
            elif scans > world[0][0]:
                heapq.heapreplace(world, item)
    products = {code: e for _, _, code, e in world}
    products.update(china)
    print(f"lignes lues: {seen}, Chine: {len(china)}, monde: {len(world)}, "
          f"total: {len(products)}", file=sys.stderr)
    out = {"date": date.today().isoformat(), "fields": FIELDS,
           "count": len(products), "cn": len(china), "products": products}
    json.dump(out, sys.stdout, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
