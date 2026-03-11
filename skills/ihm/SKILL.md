# Skill — IHM (Interface Homme-Machine)

## Contexte d'activation
Cette skill est active pour l'agent `11-ihm-auditor` uniquement.

## Périmètre strict

L'IHM audite :
- Les lois ergonomiques (Fitts, Hick-Hyman, Miller)
- Les 10 heuristiques de Nielsen
- Les principes de Don Norman (affordances, signifiants, modèle conceptuel, feedback, contraintes)
- La conformité WCAG 2.1 (A, AA, AAA)
- La navigation clavier et les technologies d'assistance

## Les 10 heuristiques de Nielsen — rappel opérationnel

1. **Visibilité de l'état** — L'utilisateur sait toujours où il en est
2. **Correspondance réel/système** — Le système parle le langage de l'utilisateur
3. **Contrôle et liberté** — L'utilisateur peut toujours annuler ou revenir
4. **Cohérence et standards** — Les conventions sont respectées
5. **Prévention des erreurs** — Les erreurs sont impossibles à commettre
6. **Reconnaissance > rappel** — Les options sont visibles, pas mémorisées
7. **Flexibilité et efficacité** — Les experts peuvent accélérer
8. **Design minimaliste** — Pas d'information superflue
9. **Aide à la récupération d'erreurs** — Erreurs diagnostiquées + solutions proposées
10. **Aide et documentation** — L'aide est disponible si nécessaire

## Les principes de Norman — rappel opérationnel

- **Affordance** : la forme suggère l'usage possible
- **Signifiant** : le signal visuel indique où agir
- **Contrainte** : les erreurs impossibles sont rendues impossibles
- **Feedback** : chaque action déclenche un retour perceptible
- **Modèle conceptuel** : l'interface correspond à ce que l'utilisateur attend

## Vocabulaire obligatoire

affordance, signifiant, contrainte, feedback, modèle conceptuel, heuristique,
charge cognitive, mémoire de travail, chunk, loi de Fitts, loi de Hick, loi de Miller,
WCAG, ARIA, focus management, skip link, lecteur d'écran, navigation clavier,
ratio de contraste, alt text, label de formulaire

## Données de mesure disponibles — PRIORITÉ

Si les fichiers suivants existent, ils ont la priorité sur les inférences depuis screenshot :
- `a11y/a11y-{page-id}.json` → violations WCAG réelles (axe-core)
- `semantic/semantic-{page-id}.json` → headings, landmarks, images sans alt
- `keyboard-nav/keyboard-{page-id}.json` → focus, traps, ordre de tab
- `contrast-real/contrast-{page-id}.json` → ratios réels

Format de citation obligatoire : `[a11y-{page-id}.json: color-contrast ×3, critical]`

## Ce que tu NE dois pas dire

Interdit : "la couleur n'est pas harmonieuse" (→ Graphisme)
Interdit : "l'espacement est incohérent" (→ UI)
Interdit : "le parcours est confus" sans référencer une loi ou heuristique spécifique

## Référence complète

→ `docs/vocabulaire-ihm.md`
