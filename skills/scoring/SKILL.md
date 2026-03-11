# Skill — Scoring

## Contexte d'activation
Cette skill est active pour tous les agents qui produisent un score numérique.

## Principe fondamental

Un score n'est pas une note de satisfaction. C'est une mesure de distance
entre l'interface auditée et un étalon professionnel défini.

## Étalons par discipline

### Graphisme (score /100)
- **90-100** : Référence professionnelle (Stripe, Linear, Notion)
- **70-89** : Compétent — grille tenue, palette cohérente, typographie correcte
- **50-69** : Problèmes significatifs visibles à l'œil nu
- **30-49** : Problèmes majeurs — pas de grille, palette chaotique
- **0-29** : Non fonctionnel graphiquement

### UI (score /100)
- **90-100** : Design system cohérent, tous les états définis, densité maîtrisée
- **70-89** : Cohérence majoritaire, quelques accidents de composants
- **50-69** : Incohérences notables entre composants similaires
- **30-49** : Pas de système — chaque composant est un cas isolé
- **0-29** : Interface visuellement chaotique au niveau des composants

### UX (score /100)
- **90-100** : Toutes les tâches personas en ≤2 clics, charge cognitive maîtrisée
- **70-89** : Majorité des tâches accessibles, quelques frictions identifiées
- **50-69** : Plusieurs frictions sur les tâches fréquentes, architecture confuse
- **30-49** : Les tâches principales sont difficiles à accomplir
- **0-29** : L'interface ne permet pas d'accomplir les tâches des personas

### Web Design (score /100)
- **90-100** : Responsive parfait, touch targets conformes, motion maîtrisée
- **70-89** : Responsive fonctionnel, quelques touch targets sous le seuil
- **50-69** : Des breakpoints manquants, >20% des touch targets sous 44px
- **30-49** : Mobile non traité ou dégradé, performance perçue faible
- **0-29** : Pas de traitement responsive, interface inutilisable sur mobile

### IHM (scores /10 par heuristique Nielsen, score global /100)
- **9-10** : Heuristique parfaitement respectée, aucune violation
- **7-8** : Respectée avec quelques exceptions mineures documentées
- **5-6** : Violations notables sur 1-2 cas d'usage fréquents
- **3-4** : Violations systématiques sur cette heuristique
- **0-2** : Heuristique ignorée ou violée structurellement

### Wording (score /100)
- **90-100** : Terminologie cohérente, CTAs verbaux, tous les états ont un wording
- **70-89** : Quelques incohérences terminologiques, registre globalement cohérent
- **50-69** : Incohérences cross-vues, plusieurs CTAs génériques, empty states muets
- **30-49** : Terminologie chaotique, codes d'erreur techniques exposés
- **0-29** : Wording absent ou issu du développement (textes de placeholder non remplacés)

### Architecture d'information (score /100, agent 19)
Voir `agents/19-ia-auditor.md` pour les ancres détaillées par sous-score.

## Règle de calibration — universelle

**En cas de doute entre deux tranches : choisir la plus basse.**
Justifier pourquoi l'interface ne mérite pas la tranche supérieure.
Un score généreux non justifié est détecté par le quality-gate comme dérive complaisante.

## Règle de dérive

Si le quality-gate détecte que >80% des scores d'un run sont au-dessus de 75 :
→ Alerte dérive complaisante émise
→ L'agent doit re-justifier ses scores les plus élevés

## Ce qu'un score N'EST PAS

Un score n'est pas :
- Une moyenne automatique de critères
- Un reflet de l'effort de l'équipe de développement
- Une note sur l'intention — seulement sur le résultat observable
