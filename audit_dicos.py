#!/usr/bin/env python3
"""Audit de cohérence de Export_Dicos_JSON.json (DicoSignes / DicoMaladies).

Lancez :  python3 audit_dicos.py [chemin_du_json]

Signale les classes d'erreurs habituelles (ex. « abcès rénal » saisi comme
signe et relié à tort comme descripteur d'« abcès anal ») :

  1. MALADIE_SAISIE_COMME_SIGNE : signe jamais utilisé comme descripteur,
     ressemblant à une maladie, sans maladie homonyme dans DicoMaladies.
     -> Correction : créer l'entrée DicoMaladies (modèle : « abcès hépatique »,
        descripteurs = clés existantes de DicoSignes uniquement), garder ou
        supprimer l'entrée DicoSignes selon la convention dual.
  2. LIEN_DESCRIPTEUR_SUSPECT : descripteur dont le nom ne diffère de la
     maladie que par le dernier mot (ex. « abcès anal » <- « abcès rénal »).
     -> À relire manuellement : supprimer le descripteur s'il est faux.
  3. DESCRIPTEUR_HORS_DicoSignes : descripteur sans entrée signe exacte,
     classé en : variante de casse/accents (renommer), nom de maladie
     (référence vers une maladie, pas un signe), ou inconnu.
  4. DOUBLONS : clés identiques à la normalisation près (casse/accents/espaces)
     dans un même dictionnaire.

Le JSON se réécrit sans perte de format avec :
  json.dumps(data, ensure_ascii=False, separators=(',', ':'))
"""

import json
import re
import sys
import unicodedata

RESERVED = {
    "ages", "cat", "caractéristiques spécifiques", "contexte", "définition",
    "document de référence", "h-f", "synonymes", "icone", "photo",
    "nb", "nb femme", "sexe",
}

DISEASE_PATTERN = re.compile(
    r"(syndrome|maladie|abcès|tumeur|cancer|infarctus|hémorragie|fracture|"
    r"luxation|infection|insuffisance|déficit|anévrisme|thrombose|embolie|"
    r"occlusion|sténose|nécrose|kyste|polype|adénome|carcinome|sarcome|"
    r"lymphome|leucémie|méningite|encéphalite|pneumonie|péritonite|arthrite|"
    r"endocardite|hépatite|néphrite|pyélo|cystite|urétrite|prostatite|"
    r"orchite|salpingite|sepsis|choc|fièvre)", re.I)


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def descripteurs(maladie_key, value):
    if not isinstance(value, dict):
        return []
    return [k for k, v in value.items()
            if k != maladie_key and norm(k) not in RESERVED and isinstance(v, dict)]


def main(path):
    data = json.load(open(path, encoding="utf-8"))
    signes = data["DicoSignes"]
    maladies = data["DicoMaladies"]
    signes_norm = {norm(s): s for s in signes}
    maladies_norm = {norm(m): m for m in maladies}

    ref = {}
    for mk, mv in maladies.items():
        for sk in descripteurs(mk, mv):
            ref.setdefault(sk, []).append(mk)

    print("== 1) Signes orphelins ressemblant à une maladie, SANS maladie homonyme")
    print("   (candidats « maladie saisie comme signe ») :")
    n = 0
    for s in sorted(signes):
        if s not in ref and DISEASE_PATTERN.search(s) and norm(s) not in maladies_norm:
            print(f"    {s!r}")
            n += 1
    print(f"   -> {n} candidat(s)")

    print()
    print("== 2) Descripteurs dont le nom ne diffère de la maladie que par le dernier mot")
    print("   (liens suspects, ex. abcès anal <- abcès rénal) :")
    n = 0
    for mk, mv in maladies.items():
        nm = norm(mk).split()
        for sk in descripteurs(mk, mv):
            ns = norm(sk).split()
            if ns != nm and len(ns) >= 2 and ns[:-1] == nm[:-1]:
                print(f"    maladie {mk!r} <- descripteur {sk!r}")
                n += 1
    print(f"   -> {n} lien(s) à relire")

    print()
    print("== 3) Descripteurs sans entrée DicoSignes exacte :")
    variantes, vers_maladie, inconnus = {}, {}, {}
    for sk, mks in sorted(ref.items()):
        if sk in signes:
            continue
        n = norm(sk)
        if n in signes_norm:
            variantes.setdefault(sk, set()).add(signes_norm[n])
        elif n in maladies_norm:
            vers_maladie.setdefault(sk, []).extend(mks)
        else:
            inconnus.setdefault(sk, []).extend(mks)
    print(f"   3a) variante de casse/accents d'un signe existant (à renommer) : {len(variantes)}")
    for k, v in list(variantes.items())[:20]:
        print(f"      {k!r} -> {sorted(v)}")
    print(f"   3b) noms de maladies utilisés comme descripteurs (pas de signe dédié) : {len(vers_maladie)}")
    print(f"   3c) totalement inconnus : {len(inconnus)}")
    for k, v in list(inconnus.items())[:20]:
        print(f"      {k!r} <- {v[:3]}")

    print()
    print("== 4) Doublons (normalisés casse/accents/espaces) dans chaque dictionnaire :")
    from collections import defaultdict
    for nom, dico in (("DicoSignes", signes), ("DicoMaladies", maladies)):
        groupes = defaultdict(list)
        for k in dico:
            groupes[norm(k)].append(k)
        dups = {n: v for n, v in groupes.items() if len(v) > 1}
        print(f"   {nom} : {len(dups)} doublon(s)")
        for n, v in list(dups.items())[:20]:
            print(f"      {v}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Export_Dicos_JSON.json")
