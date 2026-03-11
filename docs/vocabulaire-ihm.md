# Vocabulaire — Discipline 5 : IHM (Interface Homme-Machine)

## Définition de la discipline
L'**IHM** traite de la dimension scientifique de l'interaction — ergonomie cognitive, lois de l'interaction, accessibilité normée. Elle évalue l'interface à travers des principes validés par la recherche. Elle ne juge PAS l'esthétique (graphisme) ni les conventions web spécifiques (Web Design).

**Ce qui le distingue des autres disciplines :**
- Elle applique des lois et principes nommés (Fitts, Hick, Miller, Nielsen, Norman)
- Elle parle de mesures cognitives, pas de "ressenti"
- Elle évalue l'accessibilité selon les normes WCAG, pas selon l'intuition

---

## Vocabulaire technique obligatoire

### Lois fondamentales de l'interaction
- **Loi de Fitts** : le temps pour atteindre une cible dépend de sa taille et de sa distance — plus grand et plus proche = plus rapide
- **Loi de Hick-Hyman** : le temps de décision augmente logarithmiquement avec le nombre de choix
- **Loi de Miller** : la mémoire de travail retient 7±2 éléments (chunks)
- **Loi de Jakob** : les utilisateurs préfèrent que votre interface fonctionne comme celles qu'ils connaissent déjà
- **Loi de Tesler** : tout système a une complexité irréductible — la question est qui la porte (système ou utilisateur)
- **Effet de Von Restorff** : un élément qui se distingue visuellement est mieux mémorisé
- **Effet de position sérielle** : les premiers et derniers éléments d'une liste sont mieux mémorisés

### Principes de Don Norman
- **Affordance** : propriété réelle ou perçue d'un objet qui suggère son mode d'utilisation
- **Signifiant (signifier)** : signal perceptible qui communique une affordance au sens de Norman
- **Contrainte (constraint)** : restriction qui limite les actions possibles et prévient les erreurs
- **Mapping** : relation spatiale entre les commandes et leurs effets
- **Feedback** : retour perceptible du système suite à une action
- **Modèle conceptuel** : représentation mentale du fonctionnement du système

### Heuristiques de Nielsen (les 10)
1. **Visibilité de l'état du système** : le système informe toujours l'utilisateur de ce qui se passe
2. **Correspondance système/monde réel** : le système utilise le langage et les concepts de l'utilisateur
3. **Contrôle et liberté de l'utilisateur** : sortie de secours, undo/redo
4. **Cohérence et standards** : les conventions de la plateforme et du domaine sont respectées
5. **Prévention des erreurs** : le design empêche les erreurs avant qu'elles ne surviennent
6. **Reconnaissance plutôt que rappel** : les options et actions sont visibles, pas à mémoriser
7. **Flexibilité et efficacité d'utilisation** : raccourcis pour les experts, simplicité pour les novices
8. **Design esthétique et minimaliste** : pas d'information non pertinente
9. **Aide à la reconnaissance, diagnostic et récupération des erreurs** : messages d'erreur clairs et constructifs
10. **Aide et documentation** : documentation accessible si nécessaire

### Accessibilité (WCAG 2.1)
- **WCAG** : Web Content Accessibility Guidelines — standard international
- **Niveau A** : exigences minimales (images alt, labels de formulaire, etc.)
- **Niveau AA** : standard cible (contraste 4.5:1, navigation clavier, etc.)
- **Niveau AAA** : bonnes pratiques avancées (contraste 7:1, langue des signes, etc.)
- **ARIA** : Accessible Rich Internet Applications — attributs d'accessibilité enrichie
- **Focus management** : gestion programmatique du focus clavier (modales, navigation)
- **Skip link** : lien invisible qui permet de sauter la navigation pour aller au contenu principal
- **Screen reader** : logiciel de lecture d'écran (NVDA, JAWS, VoiceOver)
- **Tab order** : ordre de navigation au clavier via la touche Tab
- **Rôle ARIA** : attribut définissant la fonction d'un élément (role="button", role="dialog", etc.)
- **Live region** : zone dont les changements sont annoncés automatiquement aux lecteurs d'écran

### Ergonomie cognitive
- **Charge cognitive** : effort mental requis — intrinsèque (complexité de la tâche), extrinsèque (design), pertinente (apprentissage)
- **Mémoire de travail** : mémoire à court terme, limitée en capacité et durée
- **Chunk** : unité d'information perçue comme un tout en mémoire de travail
- **Attention sélective** : capacité à se concentrer sur un stimulus en ignorant les autres
- **Cécité au changement** : incapacité à détecter un changement dans le champ visuel si l'attention est ailleurs
- **Banner blindness** : tendance à ignorer les zones qui ressemblent à des publicités

---

## Frameworks de référence
- Heuristiques de Nielsen (Jakob Nielsen, 1994)
- The Design of Everyday Things (Don Norman)
- WCAG 2.1 (W3C)
- Cognitive Load Theory (Sweller, 1988)
- Loi de Fitts (Paul Fitts, 1954)
- Loi de Hick-Hyman (Hick, 1952)

---

## Pièges à éviter
- Ne PAS évaluer la beauté — l'IHM évalue l'efficacité de l'interaction
- Ne PAS utiliser "intuitif" sans préciser pour quel profil d'utilisateur
- Ne PAS confondre "simple" et "familier" — la simplicité est objective, la familiarité est relative au public
- Ne PAS citer une heuristique de Nielsen sans l'appliquer concrètement à un élément observé
- Ne PAS dire "accessible" sans préciser le niveau WCAG et le critère spécifique
- Ne PAS deviner les capacités motrices ou cognitives des utilisateurs — se baser sur les personas
