# ScanChina

Scanne le code-barre d'un aliment et obtiens les kcal et les macros, même sans connexion.

**App :** https://osaring.github.io/scanchina/

- Les données viennent d'[Open Food Facts](https://world.openfoodfacts.org) (licence ODbL) : tous les produits vendus en Chine, Hong Kong, Taïwan et Macao, plus les 30 000 produits les plus scannés au monde.
- La base est stockée dans `data.json` et gardée sur le téléphone : la recherche est instantanée et marche hors ligne.
- Elle est mise à jour automatiquement chaque lundi par l'action GitHub « Mise à jour des produits » (relançable à la main dans l'onglet Actions).
- Si un produit n'est pas dans la base et qu'il y a du réseau, l'app interroge Open Food Facts en direct et garde le résultat sur le téléphone.
- Lecteur de code-barre : [zxing-wasm](https://github.com/Sec-ant/zxing-wasm) (Apache 2.0), embarqué dans `lib/`.
