# Vocabulaire — Wording & Microcopy

## Définition de la discipline
Le wording (ou microcopy) désigne l'ensemble des textes fonctionnels d'une interface :
labels, boutons, titres, placeholders, messages d'erreur, états vides, tooltips, confirmations.
Ce n'est pas le contenu éditorial — c'est le tissu conjonctif textuel qui guide l'action.

Le wording auditor évalue trois dimensions indépendantes :
1. La cohérence interne (l'application parle-t-elle d'une seule voix ?)
2. L'adéquation au persona (le niveau de langue correspond-il aux utilisateurs réels ?)
3. La complétude (tous les états de l'interface ont-ils un wording, ou certains sont-ils muets ?)

## Ce que le wording n'est PAS
- Le contenu marketing ou éditorial (hors scope)
- Les données dynamiques (noms d'utilisateurs, montants, dates)
- Les textes d'aide longue forme (documentation)

## Vocabulaire technique obligatoire

**Microcopy** : texte court à haute valeur fonctionnelle (label de bouton, message d'erreur).
Contrairement au contenu long, chaque mot coûte cher en attention.

**Label** : texte attaché à un élément interactif qui décrit ce que cet élément est ou fait.
Un label ambigu crée de la friction. Un label absent crée de l'incompréhension.

**Placeholder** : texte indicatif dans un champ de formulaire, visible quand le champ est vide.
Règle : le placeholder ne remplace jamais le label — il le complète.

**Empty state** : message affiché quand une liste ou une vue ne contient pas de données.
Un empty state nul ("Aucune donnée") est une occasion manquée de guider l'utilisateur.
Un bon empty state explique pourquoi c'est vide ET propose une action.

**Error message** : texte affiché quand une action échoue ou qu'une validation est fausse.
Règle de Nielsen : l'erreur doit dire QUE s'est-il passé, POURQUOI, et COMMENT corriger.
"Erreur 422" viole les trois. "Ce champ doit contenir une adresse email valide" respecte les trois.

**CTA (Call to Action)** : label de bouton ou lien qui déclenche une action principale.
Règle : un CTA doit commencer par un verbe à l'infinitif (Enregistrer, Valider, Créer) ou impératif.
"OK" et "Continuer" sans contexte sont des anti-patterns.

**Cohérence terminologique** : utilisation d'un terme unique pour désigner un même concept
dans toute l'application. La terminologie incohérente impose au cerveau un travail de traduction.

**Registre** : niveau de langue et ton (formel/informel, technique/accessible, froid/chaleureux).
Le registre doit être homogène ET adapté au persona. Un registre technique pour un persona
non-technique est un mur invisible.

**Affordance verbale** : la capacité d'un label à indiquer ce qui se passera si l'utilisateur
clique ou interagit. "Supprimer" est une affordance verbale. "Action" n'en est pas une.

**Charge textuelle** : quantité de texte à lire avant de pouvoir agir. Plus la charge est élevée,
plus la friction est grande. Pour les interfaces de travail, la charge doit être minimale.

**Jargon développeur** : termes issus du vocabulaire technique interne non compris par les
utilisateurs finaux. Exemples : "null", "undefined", "404", "timeout", "UUID", "payload".

**Voix de l'application** : la personnalité textuelle perçue à travers le wording.
Cohérente si tous les écrans semblent écrits par la même personne.
Incohérente si certains écrans sont formels et d'autres familiers sans raison.

## Pièges à éviter

L'agent NE doit PAS :
- Réécrire le wording lui-même dans ses observations (il observe et recommande, il ne rédige pas à la place)
- Évaluer le contenu éditorial long (articles, descriptions, pages "À propos")
- Signaler comme problème un terme technique correct pour un persona expert
- Confondre internationalisation (i18n) et wording — les clés de traduction ne sont pas du wording évaluable
