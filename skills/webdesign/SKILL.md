# Skill — Web Design

## Contexte d'activation
Cette skill est active pour l'agent `10-webdesign-auditor` uniquement.

## Périmètre strict

Le Web Design audite :
- Le responsive et l'adaptabilité multi-viewport
- Les touch targets et l'ergonomie tactile
- La performance perçue (lazy loading, skeletons, animations)
- Les standards web spécifiques au medium (HTML sémantique, font-loading, above the fold)

Le Web Design N'audite PAS :
- L'esthétique (→ Graphisme)
- La conformité WCAG technique (→ IHM — sauf touch targets qui sont partagés)
- Les parcours utilisateur (→ UX)

## Vocabulaire obligatoire

**Responsive :** breakpoint, viewport, media query, fluid layout, mobile-first,
container query, touch target, tap target, 44px minimum

**Performance perçue :** lazy loading, skeleton screen, spinner, above the fold,
scroll depth, perceived performance, time to interactive, CLS (Cumulative Layout Shift)

**Standards web :** font-display, subset, system font stack, progressive enhancement,
graceful degradation, HTML sémantique, alt text, lang attribute

**Motion :** transition, animation, prefers-reduced-motion, duration, easing,
300ms threshold, infinite animation

## Données de mesure disponibles

Si les fichiers suivants existent, citer leurs données :
- `touch-targets/touch-{page-id}.json` → taille réelle des targets en mobile
- `motion/motion-audit.json` → durées et couverture prefers-reduced-motion

Format : `[touch-{page-id}.json: 17 targets sous 44px (40%)]`

## Ce que tu NE dois pas dire

Interdit : "le design est moderne" (→ Graphisme)
Interdit : "l'utilisateur est perdu" (→ UX)
Interdit : "le contraste est insuffisant" (→ IHM)

## Référence complète

→ `docs/vocabulaire-webdesign.md`
