# SKILL — deep-ux Audit

## Activation
Cette skill est auto-activée quand le contexte d'audit UX est détecté dans une session Claude Code utilisant le plugin deep-ux.

---

## Les 5 disciplines et leurs périmètres

### 1. Graphisme
**Périmètre :** Qualité plastique pure — composition, couleur comme matière, typographie comme forme, identité visuelle.
**Ne couvre PAS :** Utilisabilité, parcours, standards web.
**Vocabulaire clé :** kerning, leading, tracking, weight, valeur tonale, teinte, saturation, contraste simultané, gestalt, figure/fond, rythme visuel, tension, respiration, focal point.

### 2. UI (User Interface Design)
**Périmètre :** Système de composants, états interactifs, cohérence du design system, tokens.
**Ne couvre PAS :** Esthétique pure, parcours utilisateur, performance web.
**Vocabulaire clé :** affordance, état, design system, token, composant, variant, instance, atomic design, densité, padding, margin, gap, grille, baseline grid.

### 3. UX (User Experience)
**Périmètre :** Expérience vécue — parcours, charge cognitive, architecture de l'information, pertinence fonctionnelle.
**Ne couvre PAS :** Rendu visuel pur, aspects techniques web.
**Vocabulaire clé :** modèle mental, charge cognitive, architecture de l'information, affordance, signifiant, feedback, parcours utilisateur, tâche, point de friction, dead end, progressive disclosure, onboarding, error recovery.

### 4. Web Design
**Périmètre :** Spécificités du medium web — responsive, performance perçue, typographie web, standards HTML/CSS.
**Ne couvre PAS :** Esthétique pure, ergonomie cognitive.
**Vocabulaire clé :** breakpoint, viewport, touch target, lazy loading, skeleton screen, font-display, above the fold, scroll depth, progressive enhancement, graceful degradation.

### 5. IHM (Interface Homme-Machine)
**Périmètre :** Dimension scientifique — lois de l'interaction (Fitts, Hick, Miller), heuristiques de Nielsen, principes de Norman, accessibilité WCAG.
**Ne couvre PAS :** Esthétique, conventions web spécifiques.
**Vocabulaire clé :** affordance, signifiant, contrainte, feedback, modèle conceptuel, heuristique, charge cognitive, mémoire de travail, chunk, loi de Fitts, loi de Hick, WCAG, ARIA, focus management, skip link.

---

## Règle de grounding fonctionnel

**Principe fondamental :** deep-ux ne recommande JAMAIS ce qui n'existe pas dans le code.

Chaque recommandation fonctionnelle DOIT être ancrée sur `capabilities.json` :
- Si la recommandation concerne une capacité existante → citer le `capability_id`
- Si la recommandation suppose une capacité non implémentée → marquer `"speculation": true`
- Un agent ne suggère JAMAIS "il faudrait ajouter X" si X n'est pas dans `capabilities.json`
- Il PEUT suggérer de "mieux exposer" une capacité existante mal mise en avant

---

## Vocabulaire transversal

Ces termes sont utilisés par tous les agents, au-delà de leur discipline spécifique :

- **Observation** : constat factuel, mesurable, citable — ce qui EST
- **Recommandation** : action concrète et spécifique — ce qui DEVRAIT être fait
- **Score** : note de 0 à 100, toujours justifiée par des observations spécifiques
- **Quick win** : recommandation à impact élevé et effort faible (xs ou s)
- **Issue critique** : problème qui empêche l'utilisateur d'accomplir sa tâche
- **Persona** : profil utilisateur construit à partir de données réelles (interview + recherche)
- **Capability** : fonctionnalité réellement trouvée dans le code source
- **Design token** : valeur nommée dans le système de design (couleur, taille, espacement)

---

## Schéma de pensée obligatoire

Tout agent d'audit suit ce cycle en 3 étapes :

### 1. DÉCRIRE
```
Je vois : [description factuelle et précise de ce qui est observé]
```
- Que voit-on concrètement ?
- Quelles mesures (tailles, couleurs, espacements) ?
- Quel fichier source / screenshot ?

### 2. ÉVALUER
```
Évaluation : [jugement basé sur les critères de la discipline]
```
- Par rapport à quel critère/standard/loi ?
- Quel score et pourquoi ?
- Quel impact sur l'utilisateur (le persona) ?

### 3. RECOMMANDER
```
Recommandation : [action concrète et spécifique]
```
- Que faut-il changer précisément ?
- Quel effort (xs/s/m/l/xl) ?
- Quelle priorité (critical/high/medium/low) ?
- Quelle capability est concernée ?

**Règle absolue : jamais recommander sans avoir décrit et évalué d'abord.**
