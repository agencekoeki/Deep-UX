# Grille d'évaluation par discipline

## Principe général
Chaque discipline évalue un écran sur 100 points. Le score global d'un écran est la moyenne pondérée des 5 disciplines.

**Règle absolue : décrire avant d'évaluer.**
Avant toute notation, l'agent décrit factuellement ce qu'il observe. Pas de score sans observation concrète.

---

## Pondération par défaut
| Discipline | Poids | Justification |
|---|---|---|
| Graphisme | 15% | Qualité visuelle pure |
| UI | 20% | Cohérence du système de composants |
| UX | 30% | Expérience utilisateur et parcours |
| Web Design | 15% | Adaptation au medium web |
| IHM | 20% | Ergonomie cognitive et accessibilité |

---

## Barème de scoring

### 90-100 : Excellent
- Aucun problème majeur détecté
- Bonnes pratiques respectées de manière exemplaire
- Peut servir de référence

### 70-89 : Bon
- Quelques problèmes mineurs
- Fondamentaux respectés
- Améliorations possibles mais non critiques

### 50-69 : Moyen
- Problèmes significatifs identifiés
- Certaines bonnes pratiques ignorées
- Améliorations nécessaires

### 30-49 : Faible
- Problèmes majeurs impactant l'expérience
- Plusieurs bonnes pratiques violées
- Refonte partielle recommandée

### 0-29 : Critique
- Problèmes bloquants
- Expérience fortement dégradée
- Refonte majeure nécessaire

---

## Grille détaillée par discipline

### 1. Graphisme (100 points)
| Critère | Points | Poids |
|---|---|---|
| Composition et mise en page | 30 | Grille, rapport plein/vide, hiérarchie visuelle, alignements |
| Couleur | 25 | Nombre de teintes, température, contraste, cohérence, accidents |
| Typographie comme graphisme | 25 | Personnalité, contraste de graisse, hiérarchie typographique |
| Identité et cohérence | 20 | Identité identifiable, cohérence de style, iconographie |

### 2. UI (100 points)
| Critère | Points | Poids |
|---|---|---|
| Système de composants | 25 | Cohérence, hiérarchie boutons, formulaires, tables |
| États interactifs | 25 | Hover, focus, active, disabled, loading, error, success |
| Système d'espacement | 20 | Grille, paddings, marges proportionnelles |
| Design tokens | 15 | Couleurs vs tokens, échelle typographique, valeurs hardcodées |
| Densité d'information | 15 | Adaptée au contexte, zones surchargées |

### 3. UX (100 points)
| Critère | Points | Poids |
|---|---|---|
| Architecture de l'information | 25 | Modèle mental, labellisation, navigation, breadcrumb |
| Charge cognitive | 25 | Loi de Miller, nombre d'actions, longueur formulaires, vocabulaire |
| Parcours et flows | 25 | Tâche en ≤2 clics, dead ends, confirmations, retour arrière |
| Feedback et signalement | 15 | Progression, confirmations, messages d'erreur |
| Pertinence pour le persona | 10 | Tâches clés, fonctionnalités attendues |

### 4. Web Design (100 points)
| Critère | Points | Poids |
|---|---|---|
| Responsive et adaptabilité | 30 | Breakpoints, réorganisation mobile, touch targets, stratégie tableaux |
| Performance perçue | 25 | Lazy loading, skeletons, animations, above the fold |
| Typographie web | 20 | font-display, taille ≥16px, contraste, redimensionnement |
| Standards web | 25 | HTML sémantique, liens distinguables, alt images |

### 5. IHM (100 points)
| Critère | Points | Poids |
|---|---|---|
| Loi de Fitts | 10 | Taille cibles, proximité, éloignement destructif |
| Loi de Hick-Hyman | 10 | Nombre de choix, progressive disclosure, défauts |
| Loi de Miller | 10 | Chunks ≤7, pagination, filtres |
| Heuristiques de Nielsen (×10) | 50 | 5 points par heuristique |
| Principes de Norman | 10 | Affordances, signifiants, contraintes, feedback, modèle conceptuel |
| Accessibilité WCAG | 10 | Niveau A/AA/AAA |

---

## Priorisation des recommandations (MoSCoW)

| Priorité | Signification | Critère |
|---|---|---|
| **critical** | Bloquant | Empêche l'utilisateur d'accomplir sa tâche |
| **high** | Doit être corrigé | Dégrade significativement l'expérience |
| **medium** | Devrait être corrigé | Amélioration notable de l'expérience |
| **low** | Pourrait être corrigé | Amélioration marginale, polish |

## Estimation de l'effort

| Effort | Signification |
|---|---|
| **xs** | < 30 min — changement CSS, texte, couleur |
| **s** | 30 min - 2h — composant simple, réorganisation mineure |
| **m** | 2h - 1 jour — composant complexe, refonte section |
| **l** | 1 - 3 jours — refonte page, nouveau flow |
| **xl** | > 3 jours — refonte structurelle, nouveau système |
