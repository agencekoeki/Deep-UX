# Vocabulaire — Discipline 4 : Web Design

## Définition de la discipline
Le **Web Design** traite des spécificités du medium web — responsive design, performance perçue, typographie web, standards et compatibilité. Il évalue si l'interface exploite correctement les capacités et respecte les contraintes du web. Il ne juge PAS l'esthétique pure (graphisme) ni l'ergonomie cognitive (IHM).

**Ce qui le distingue des autres disciplines :**
- Il parle de viewport et breakpoints, pas de composition
- Il parle de performance perçue et chargement, pas de parcours utilisateur
- Il parle de standards web (HTML sémantique, WCAG de base), pas d'heuristiques de Nielsen

---

## Vocabulaire technique obligatoire

### Responsive et adaptabilité
- **Breakpoint** : seuil de largeur du viewport déclenchant un changement de mise en page
- **Viewport** : zone visible du navigateur
- **Media query** : règle CSS conditionnelle selon les propriétés du viewport
- **Mobile-first** : approche de conception partant du mobile et enrichissant pour le desktop
- **Desktop-first** : approche inverse — partant du desktop et adaptant pour le mobile
- **Touch target** : zone cliquable/tappable — minimum 44×44px (recommandation iOS/Google)
- **Responsive** : interface qui s'adapte fluidement à toutes les tailles d'écran
- **Adaptive** : interface avec des layouts fixes pour certains breakpoints
- **Fluid typography** : tailles de texte qui varient proportionnellement au viewport (clamp())
- **Container query** : adaptation basée sur la taille du conteneur parent (pas du viewport)

### Performance perçue
- **Above the fold** : contenu visible sans scroll au chargement
- **Lazy loading** : chargement différé des ressources hors viewport
- **Skeleton screen** : wireframe animé affiché pendant le chargement du contenu
- **Spinner** : indicateur de chargement rotatif
- **Progressive rendering** : affichage incrémental du contenu au fur et à mesure du chargement
- **Scroll depth** : profondeur de défilement atteinte par l'utilisateur
- **Perceived performance** : vitesse ressentie par l'utilisateur (distincte de la vitesse réelle)
- **First Contentful Paint (FCP)** : premier affichage de contenu visible
- **Largest Contentful Paint (LCP)** : chargement de l'élément le plus volumineux visible

### Typographie web
- **font-display** : propriété CSS contrôlant l'affichage pendant le chargement de police (swap, fallback, optional)
- **Web font** : police chargée depuis un serveur (Google Fonts, Adobe Fonts, self-hosted)
- **System font stack** : pile de polices système garantissant un affichage sans chargement
- **Font subsetting** : réduction d'une police aux seuls caractères nécessaires
- **Variable font** : police unique avec axes de variation (weight, width, slant)
- **FOUT (Flash of Unstyled Text)** : affichage bref de texte en police de fallback
- **FOIT (Flash of Invisible Text)** : texte invisible pendant le chargement de la police

### Standards web
- **HTML sémantique** : utilisation des balises HTML selon leur signification (nav, main, article, section, aside, header, footer)
- **Progressive enhancement** : base fonctionnelle pour tous, enrichie pour les navigateurs modernes
- **Graceful degradation** : conception pour navigateurs modernes avec repli acceptable pour les anciens
- **Attribut alt** : texte alternatif pour les images (accessibilité et SEO)
- **ARIA** : attributs d'accessibilité enrichie (Accessible Rich Internet Applications)
- **Focus visible** : indicateur visuel de focus pour la navigation clavier

---

## Frameworks de référence
- Web Content Accessibility Guidelines (WCAG) 2.1 — niveaux A, AA, AAA
- Core Web Vitals (Google) — LCP, FID/INP, CLS
- Progressive Enhancement (Gustafson)
- Responsive Web Design (Ethan Marcotte)

---

## Pièges à éviter
- Ne PAS juger la qualité esthétique d'une couleur — juger son contraste WCAG
- Ne PAS parler de charge cognitive — c'est le registre de l'UX/IHM
- Ne PAS recommander des changements de parcours — rester sur le medium web
- Ne PAS confondre "pas responsive" et "pas adapté" — certains outils pro desktop-only sont pertinents
- Ne PAS évaluer la performance réelle (temps de chargement mesuré) — évaluer la performance perçue visible dans le code et les screenshots
