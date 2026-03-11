# Contribuer à deep-ux

## Ce qui est bienvenu
- Nouvelles questions d'interview pour des secteurs spécifiques
- Amélioration des grilles d'évaluation disciplinaires
- Scripts de découverte pour des stacks non couverts
- Corrections de bugs dans les scripts Python
- Traductions des docs/ dans d'autres langues

## Ce qui n'est PAS bienvenu
- Recommandations qui affaiblissent les règles anti-drift
- Agents qui produisent des évaluations sans description préalable
- Scripts qui modifient les fichiers du projet cible

## Comment contribuer
1. Forkez le repo
2. Créez une branche : `git checkout -b feature/ma-contribution`
3. Testez sur un vrai projet avant de proposer
4. PR avec description de ce que vous avez testé et sur quel type de projet

## Structure à respecter
Chaque nouvel agent DOIT :
- Avoir un numéro dans son nom (`18-mon-agent.md`)
- Déclarer ses inputs et outputs en entête
- Utiliser le vocabulaire de sa discipline (voir `docs/`)
- Respecter la règle "décrire avant d'évaluer"
- Produire un JSON conforme à un schema dans `schemas/`

## Tester son agent
Avant toute PR, votre agent doit avoir tourné sur au moins un projet réel.
Joignez un exemple d'output anonymisé dans votre PR.
