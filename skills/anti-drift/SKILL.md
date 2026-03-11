# Skill — Anti-Drift

## Contexte d'activation
Cette skill est active pour TOUS les agents de deep-ux sans exception.
Elle définit les contraintes de qualité non négociables.

## Les 7 règles — toutes obligatoires

**Règle 1 — Décrire avant d'évaluer**
Commencer toute analyse par une description factuelle de ce qui est observé.
Format : "Je vois : [description]"
Interdit : commencer par une évaluation sans description préalable.

**Règle 2 — Citer la source**
Toute observation cite le fichier, le sélecteur, ou la position exacte dont elle provient.
Acceptable : `[dom-page-001.json:elem-042 — bouton .btn-delete 28×18px]`
Interdit : "Le bouton de suppression est trop petit" sans référence.

**Règle 3 — Interdiction des généralités**
Ces formulations sont INTERDITES dans tout champ `observation` ou `recommendation` :
- "pourrait être amélioré"
- "manque de clarté"
- "n'est pas optimal"
- "devrait être plus [adjectif]"
- "gagnerait à être [verbe]"
- "il serait bien de"

Toute observation doit être spécifique, chiffrée quand possible, et non-paraphrasable.

**Règle 4 — Ancrage fonctionnel**
Toute recommandation fonctionnelle doit soit :
- Référencer un `capability_id` dans `capabilities.json`
- Être taguée `"speculation": true` avec explication

Interdit : recommander une fonctionnalité sans preuve qu'elle existe dans le code.

**Règle 5 — Schema strict**
Tout JSON produit est conforme au schema correspondant dans `schemas/`.
Tout champ obligatoire du schema est renseigné — jamais `null` sans raison documentée.

**Règle 6 — Reprendre, pas recréer**
Si un fichier output existe déjà, le lire et le compléter.
Ne jamais écraser un output existant sans vérification.

**Règle 7 — Vocabulaire disciplinaire**
Chaque agent utilise le vocabulaire de SA discipline.
Un agent graphisme n'utilise pas le vocabulaire IHM.
Un agent UX n'utilise pas le vocabulaire graphisme.
En cas de doute : charger la skill de la discipline concernée.

## Détection automatique de violation

Le `00b-quality-gate` scanne ces patterns interdits dans tous les JSON produits.
Une violation détectée bloque la progression vers la phase suivante.
→ Voir `docs/anti-drift-rules.md` pour la liste complète des patterns interdits.
