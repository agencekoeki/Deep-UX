# Règles anti-drift pour tous les agents

## Les 7 règles fondamentales

### Règle 1 — Décrire avant d'évaluer
Tout agent DOIT commencer par une description factuelle avant toute évaluation.
```
✓ "Je vois : un header de 64px avec un logo à gauche, une navigation de 5 items centrée, et un bouton CTA bleu à droite"
✗ "Le header est bien conçu"
```

### Règle 2 — Citer la source
Toute observation DOIT citer le fichier source ou le screenshot d'où elle provient.
```
✓ "Le bouton 'Valider' (Dashboard.tsx:142) utilise un padding de 6px, inférieur au minimum recommandé de 8px"
✗ "Les boutons ont un padding insuffisant"
```

### Règle 3 — Schema strict
Tout JSON produit DOIT être conforme à son `.schema.json` correspondant. Un agent ne produit JAMAIS un fichier JSON avec des champs non prévus ou des champs manquants.

### Règle 4 — Pas de dérive fonctionnelle
Aucune recommandation fonctionnelle ne peut être émise sans référence à un `capability_id` de `capabilities.json`.
- Si la recommandation concerne une capacité existante → citer le `capability_id`
- Si la recommandation suppose une capacité non existante → marquer `"speculation": true`
- Un agent ne dit JAMAIS "il faudrait ajouter une fonction de recherche" si la recherche n'est pas dans `capabilities.json`

### Règle 5 — Pas de généralités
Toute observation et recommandation DOIT être spécifique et mesurable.
```
✓ "Le corps de texte en 13px avec un line-height de 1.1 est sous le seuil de lisibilité web (recommandé : ≥16px, line-height ≥1.5)"
✗ "La typographie pourrait être améliorée"
```

### Règle 6 — Reprendre pas recréer
Si un fichier output existe déjà, l'agent le lit et le complète — il ne le recrée jamais.
- Avant d'écrire : vérifier si le fichier existe
- Si oui : le lire, comprendre son état, compléter
- Si non : le créer selon le schema

### Règle 7 — Vocabulaire disciplinaire
Chaque agent utilise EXCLUSIVEMENT le vocabulaire de sa discipline.
- L'agent graphisme ne parle pas de "parcours utilisateur"
- L'agent UX ne parle pas de "valeur tonale"
- L'agent IHM ne parle pas de "personnalité typographique"

---

## Règles de grounding des recommandations

### Structure obligatoire
Chaque recommandation produite par un agent d'audit DOIT suivre cette structure :
```json
{
  "id": "rec-NNN",
  "discipline": "nom_de_la_discipline",
  "priority": "critical|high|medium|low",
  "type": "visual|functional|content|structural",
  "observation": "Description factuelle de ce qui a été observé",
  "recommendation": "Action concrète et spécifique à entreprendre",
  "capability_id": "cap-NNN ou null",
  "speculation": false,
  "effort": "xs|s|m|l|xl",
  "wcag_criterion": "X.Y.Z ou null"
}
```

### Règles de typage
- `visual` : concerne l'apparence (couleurs, tailles, espacements, alignements)
- `functional` : concerne le comportement (états, interactions, navigation) — NÉCESSITE un `capability_id`
- `content` : concerne le texte, les labels, la terminologie
- `structural` : concerne l'architecture (ordre, groupement, hiérarchie)

### Règle de non-spéculation
- Si `speculation` est `true`, la recommandation est explicitement marquée comme hypothétique
- Les recommandations spéculatives ne sont JAMAIS en priorité `critical`
- Un rapport peut contenir au maximum 20% de recommandations spéculatives

---

## Règles de sauvegarde

### Sauvegarde incrémentale
- Chaque agent sauvegarde son output dès qu'il a terminé un écran ou une section
- Un agent ne garde JAMAIS tout en mémoire pour sauvegarder à la fin
- Si l'agent est interrompu, les résultats déjà sauvegardés sont préservés

### Reprise
- Un agent relancé vérifie les fichiers existants et reprend là où il s'est arrêté
- Il ne refait JAMAIS un travail déjà sauvegardé sauf demande explicite

### Fichiers intermédiaires
- Tous les fichiers intermédiaires sont dans `.audit/`
- Aucun fichier du projet cible n'est JAMAIS modifié par un agent (lecture seule absolue)

---

## Règles de communication inter-agents

### Pas de mémoire implicite
Un agent ne "se souvient" de rien entre deux invocations. Toute information DOIT être lue depuis les fichiers JSON de la phase précédente.

### Chaîne de dépendances
```
Interview → Capabilities, Design Tokens → Personas, Brand, Benchmarks → Screen Audits → Consistency, Gaps → Report
```
Un agent de phase N ne peut PAS s'exécuter si les outputs de phase N-1 sont absents ou incomplets.

### Pas de shortcut
Un agent ne peut PAS "deviner" ce qu'un autre agent aurait produit. Il lit le fichier ou il signale l'absence.
