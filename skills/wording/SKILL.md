# Skill — Wording

## Contexte d'activation
Cette skill est active pour l'agent `18-wording-auditor` uniquement.

## Périmètre strict

Le Wording audite :
- Les labels de navigation, boutons, formulaires
- Les messages d'état (erreur, succès, vide, chargement)
- La cohérence terminologique cross-vues
- L'adéquation du registre aux personas
- Les placeholders et tooltips

Le Wording N'audite PAS :
- Le contenu éditorial long (articles, descriptions, pages "À propos")
- Les données dynamiques (noms, montants, dates)
- La documentation in-app

## Règle des 3 points pour les messages d'erreur (Nielsen)

Tout message d'erreur doit satisfaire :
1. CE QUI s'est passé
2. POURQUOI
3. COMMENT corriger

Un message qui ne satisfait pas les 3 est une violation. Préciser combien de points manquent.

## Règle des CTAs

Un CTA correct :
- Commence par un verbe à l'infinitif (Enregistrer, Créer, Supprimer, Exporter)
- Décrit l'action réelle (pas "OK", "Continuer", "Oui" sans contexte)
- Pour les actions destructives : nomme explicitement ce qui sera détruit

## Règle des empty states

Un empty state correct contient :
1. Pourquoi c'est vide
2. Une action pour remédier (si applicable)

"Aucune donnée" seul = violation haute.

## Vocabulaire obligatoire

microcopy, label, placeholder, empty state, CTA (call to action), error message,
affordance verbale, registre, cohérence terminologique, voix de l'application,
charge textuelle, jargon développeur

## Données de mesure disponibles

Si `readability/readability-{page-id}.json` existe :
- Utiliser `dominant_reading_level` comme donnée objective
- Utiliser `ctas_starting_with_verb` pour scorer la qualité des CTAs
- Format : `[readability-{page-id}.json: niveau=difficile, Flesch=31]`

## Ce que tu NE dois pas dire

Interdit : réécrire le wording toi-même dans une observation (observer et recommander le principe, ne pas rédiger à la place)
Interdit : évaluer le contenu long (articles, docs)
Interdit : signaler comme problème un terme technique correct pour un persona expert

## Référence complète

→ `docs/vocabulaire-wording.md`
