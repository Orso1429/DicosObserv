#!/usr/bin/env python3
"""Dedoublonne un export JSON des dicos Observ' (Export_Dicos_JSON.json).

L'import JSON de l'application comparait les noms de signes/maladies avec une
casse exacte : un nom en minuscules ("anomalie...") etait ajoute comme un
nouvel item a cote de la version capitalisee ("Anomalie..."), ce qui doublait
le dico. Ce script fusionne les cles identiques insensible a la casse :

- la cle conservee est la forme avec majuscule si elle existe (premiere vue
  sinon) ;
- les sous-champs des doublons sont fusionnes dans la cle conservee (les
  champs deja presents dans la cle conservee sont prioritaires).

S'applique a chaque section du premier niveau dont la valeur est un
dictionnaire (DicoSignes, DicoMaladies, ...).

Usage :
    python3 dedupe_dicos.py Export_Dicos_JSON.json            # reecrit en place
    python3 dedupe_dicos.py Export_Dicos_JSON.json propre.json # ecrit propre.json
"""
import json
import sys


def fusionne(a, b):
    """Absorbe b dans a (recursif) ; les valeurs de a sont prioritaires."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k, v in b.items():
            a[k] = fusionne(a[k], v) if k in a else v
        return a
    return a


def dedoublonne(dico):
    """Retourne un dict sans cle doublon insensible a la casse."""
    out = {}
    par_minuscule = {}
    for cle, valeur in dico.items():
        cle_min = cle.lower()
        if cle_min in par_minuscule:
            conservee = par_minuscule[cle_min]
            if conservee.islower() and not cle.islower():
                # forme avec majuscule preferee comme cle conservee
                out[cle] = fusionne(out.pop(conservee), valeur)
                par_minuscule[cle_min] = cle
            else:
                out[conservee] = fusionne(out[conservee], valeur)
        else:
            par_minuscule[cle_min] = cle
            out[cle] = valeur
    return out


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    entree = argv[1]
    sortie = argv[2] if len(argv) > 2 else entree
    with open(entree, encoding="utf-8") as f:
        data = json.load(f)
    total = 0
    for section, contenu in list(data.items()):
        if isinstance(contenu, dict):
            nettoye = dedoublonne(contenu)
            fusions = len(contenu) - len(nettoye)
            if fusions:
                print(f"{section}: {fusions} doublon(s) fusionne(s) "
                      f"({len(contenu)} -> {len(nettoye)} items)")
            data[section] = nettoye
            total += fusions
    with open(sortie, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Total: {total} doublon(s) fusionne(s) -> {sortie}")


if __name__ == "__main__":
    main(sys.argv)
