# Vocabulaire — Discipline 3 : UX (User Experience)

## Définition de la discipline
L'**UX** traite de l'expérience vécue par l'utilisateur — les parcours, la charge cognitive, l'architecture de l'information, la pertinence fonctionnelle. Il évalue si l'interface permet à l'utilisateur d'atteindre ses objectifs efficacement et avec satisfaction. Il ne juge PAS le rendu visuel (graphisme/UI) ni les aspects techniques web (Web Design).

**Ce qui le distingue des autres disciplines :**
- Il parle de parcours et de tâches, pas de composants
- Il parle de charge cognitive, pas de poids visuel
- Il met l'utilisateur (le persona) au centre, pas le système

---

## Vocabulaire technique obligatoire

### Architecture de l'information
- **Architecture de l'information (IA)** : organisation, structuration et labellisation du contenu
- **Modèle mental** : représentation interne que l'utilisateur a du fonctionnement du système
- **Card sorting** : méthode de classification du contenu par les utilisateurs eux-mêmes
- **Taxonomie** : système de classification hiérarchique du contenu
- **Labellisation** : choix des termes pour nommer les catégories, boutons, menus
- **Wayfinding** : capacité de l'utilisateur à savoir où il est, d'où il vient, où il peut aller

### Charge cognitive
- **Charge cognitive** : effort mental requis pour utiliser l'interface
- **Mémoire de travail** : mémoire à court terme limitée (7±2 éléments — loi de Miller)
- **Progressive disclosure** : révélation progressive de la complexité selon le besoin
- **Chunking** : regroupement d'informations en blocs digestes
- **Cognitive load theory** : théorie de Sweller — charge intrinsèque, extrinsèque, pertinente
- **Paralysie décisionnelle** : blocage causé par un trop grand nombre de choix (paradoxe de Schwartz)

### Parcours utilisateur
- **Parcours utilisateur (user flow)** : séquence d'étapes pour accomplir une tâche
- **Tâche** : objectif concret que l'utilisateur veut atteindre
- **Sous-tâche** : étape intermédiaire dans l'accomplissement d'une tâche
- **Point de friction** : endroit du parcours qui ralentit ou bloque l'utilisateur
- **Dead end (impasse)** : état de l'interface sans issue évidente
- **Happy path** : parcours idéal sans erreur ni détour
- **Edge case** : cas d'usage rare mais prévisible
- **Error recovery** : capacité de se remettre d'une erreur
- **Onboarding** : accompagnement du nouvel utilisateur dans ses premiers pas

### Feedback et signalement
- **Feedback** : retour du système suite à une action de l'utilisateur
- **Affordance** : propriété qui suggère l'usage (ici au sens UX : compréhension de ce qu'on peut faire)
- **Signifiant (signifier)** : signal perceptible qui indique une affordance (Don Norman)
- **État du système** : visibilité de ce qui se passe (heuristique Nielsen #1)
- **Confirmation** : demande explicite avant une action irréversible
- **Message d'erreur actionnable** : erreur qui explique comment résoudre le problème

### Pertinence fonctionnelle
- **Adéquation tâche-interface** : correspondance entre les besoins du persona et ce que l'interface propose
- **Feature discoverability** : facilité de découvrir une fonctionnalité existante
- **Feature exposure** : degré de visibilité d'une fonctionnalité dans l'interface

---

## Frameworks de référence
- Heuristiques de Nielsen (pour la dimension évaluative)
- Jobs to be Done (Christensen) — pour comprendre les motivations
- Théorie de la charge cognitive (Sweller)
- Don Norman — The Design of Everyday Things

---

## Pièges à éviter
- Ne PAS parler de "belles couleurs" ou de composition — c'est le registre du graphisme
- Ne PAS évaluer la cohérence des composants — c'est le registre de l'UI
- Ne PAS recommander des changements visuels sans lien avec un problème d'expérience
- Ne PAS confondre "complexe" et "mauvais" — un outil pro peut être dense si le persona le tolère
- Ne PAS inventer des besoins utilisateur — se baser sur `personas.json` et `interview.json`
- Ne PAS recommander des fonctionnalités absentes de `capabilities.json`
