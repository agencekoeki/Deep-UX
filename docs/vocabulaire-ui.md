# Vocabulaire — Discipline 2 : UI (User Interface Design)

## Définition de la discipline
L'**UI Design** traite du système de composants, de leur cohérence, de leurs états interactifs, et du design system sous-jacent. Il évalue si les éléments d'interface forment un tout cohérent et prévisible. Il ne juge PAS la qualité esthétique pure (graphisme) ni l'expérience globale (UX).

**Ce qui le distingue des autres disciplines :**
- Il parle de composants, pas de composition
- Il parle d'états interactifs (hover, focus, disabled), pas de parcours
- Il parle de tokens et de système, pas d'art

---

## Vocabulaire technique obligatoire

### Système de composants
- **Design system** : ensemble organisé de composants, tokens et règles qui garantissent la cohérence
- **Composant (component)** : élément d'interface réutilisable (bouton, champ, carte, etc.)
- **Variant** : déclinaison d'un composant (bouton primaire, secondaire, tertiaire)
- **Instance** : occurrence concrète d'un composant dans une page
- **Atomic design** : méthodologie de Brad Frost — atomes, molécules, organismes, templates, pages
- **Pattern** : solution récurrente à un problème d'interface (pagination, breadcrumb, modal, etc.)
- **Slot** : zone prévue dans un composant pour recevoir du contenu variable

### États interactifs
- **Affordance** : propriété perçue d'un objet qui suggère comment l'utiliser
- **État (state)** : apparence d'un composant selon l'interaction — default, hover, focus, active, disabled, loading, error, success
- **Hover** : survol souris — retour visuel au passage du curseur
- **Focus** : élément actif au clavier — doit être visuellement distinct
- **Active/Pressed** : état pendant le clic/tap
- **Disabled** : état inactif — visuellement atténué, non interactif
- **Loading** : état de chargement — spinner, skeleton, barre de progression
- **Feedback visuel** : retour immédiat à l'action de l'utilisateur

### Espacement et grille
- **Padding** : espace intérieur d'un composant (entre le contenu et la bordure)
- **Margin** : espace extérieur entre composants
- **Gap** : espace entre éléments dans un layout flex/grid
- **Grille (grid)** : structure en colonnes et rangées qui organise le layout
- **Baseline grid** : grille horizontale basée sur le line-height du texte
- **Densité** : quantité d'information par unité de surface

### Design tokens
- **Token** : valeur nommée dans un design system (couleur, taille, espacement, ombre, etc.)
- **Token sémantique** : token nommé par sa fonction, pas sa valeur (--color-error vs --red-500)
- **Valeur hardcodée** : valeur numérique directe au lieu d'un token — signe d'incohérence
- **Échelle (scale)** : suite ordonnée de valeurs (typographique, d'espacement, de couleurs)
- **Breakpoint** : seuil de largeur de viewport qui déclenche un changement de layout

### Hiérarchie des actions
- **Action primaire** : l'action principale de la page — visuellement dominante
- **Action secondaire** : actions complémentaires — visuellement moins affirmées
- **Action tertiaire** : actions peu fréquentes — boutons texte, liens discrets
- **Action destructive** : suppression, annulation — couleur d'alerte (rouge typiquement)
- **CTA (Call to Action)** : élément conçu pour provoquer un clic

---

## Frameworks de référence
- Atomic Design (Brad Frost)
- Material Design (Google) — comme référence de design system, pas comme obligation
- Human Interface Guidelines (Apple) — idem
- Design Tokens W3C Community Group

---

## Pièges à éviter
- Ne PAS juger la beauté d'un composant — juger sa cohérence et sa prévisibilité
- Ne PAS parler de "parcours utilisateur" — rester sur le composant et ses états
- Ne PAS confondre "composant" et "section de page" — un composant est réutilisable
- Ne PAS dire "il manque un design system" si le code utilise des variables CSS cohérentes — c'est un design system implicite
- Ne PAS évaluer la performance technique — rester sur le rendu visuel et interactif
