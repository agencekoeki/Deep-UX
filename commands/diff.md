# /deep-ux:diff — Compare deux runs d'audit

Tu compares les résultats de deux runs d'audit pour mesurer les progrès et détecter les régressions.

## Usage
```
/deep-ux:diff                    → compare le run actuel avec le run précédent
/deep-ux:diff --run=2024-01-15  → compare avec un run archivé à cette date
```

## Étapes

### 1. Trouver les runs à comparer
- **Run actuel :** les fichiers dans `.audit/screen-audits/`, `.audit/phase4/`, `.audit/reports/`
- **Run précédent :** chercher dans `.audit/archives/` le run le plus récent, ou celui correspondant à `--run=DATE`
- Si aucun run archivé n'existe → afficher un message clair et s'arrêter

### 2. Comparer les scores
Pour chaque écran présent dans les deux runs :
- Comparer le score global et les scores par discipline
- Calculer le delta (Δ) pour chaque
- Identifier les améliorations (Δ > 0) et les régressions (Δ < 0)

### 3. Identifier les changements
- **Nouveaux écrans :** présents dans le run actuel mais pas dans le précédent
- **Écrans supprimés :** présents dans le run précédent mais pas dans l'actuel
- **Recommandations implémentées :** recommandations du run précédent dont le score de la discipline correspondante s'est amélioré
- **Nouvelles recommandations :** recommandations qui n'existaient pas dans le run précédent

### 4. Produire le rapport diff
Output : `.audit/reports/diff-report.md`

```markdown
# Rapport de diff — [date run A] vs [date run B]

## Résumé
- Scores améliorés : N écrans
- Régressions : N écrans
- Nouveaux écrans : N
- Recommandations implémentées : N/total

## Évolution globale
| Discipline | Avant (moy) | Après (moy) | Δ |
|---|---|---|---|
| Graphisme | XX | XX | +X |
| UI | XX | XX | +X |
| UX | XX | XX | -X |
| Web Design | XX | XX | +X |
| IHM | XX | XX | +X |
| **Global** | **XX** | **XX** | **+X** |

## Par écran
### /dashboard
| Discipline | Avant | Après | Δ |
|---|---|---|---|
| Graphisme | 68 | 74 | +6 ✓ |
| UX | 55 | 48 | -7 ⚠ |

## Régressions à investiguer
[Liste des écrans/disciplines dont le score a baissé, avec hypothèses possibles]

## Recommandations encore non implémentées
[Liste des recommandations du run précédent qui semblent ne pas avoir été adressées]
```

## Archivage automatique
L'orchestrateur (via `commands/run.md`) archive automatiquement chaque run terminé dans `.audit/archives/{timestamp}/` avant de démarrer un nouveau run. L'archive contient une copie de :
- `screen-audits/`
- `phase4/`
- `reports/`
- `run-estimate.json`
- `quality-gates/`

## Anti-drift
- Ne pas inventer de données sur les runs passés — lire les fichiers archivés
- Si un écran n'existait pas dans le run précédent, ne pas le comparer — le lister comme "nouveau"
- Les régressions ne sont pas nécessairement des problèmes — un changement de contenu peut modifier les scores
