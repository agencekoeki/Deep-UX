# Skill — JSON Output

## Contexte d'activation
Cette skill est active pour tout agent qui produit un fichier JSON.

## Conventions de nommage

### Identifiants
- Pages : `page-001`, `page-002` (zéro-padded sur 3 digits)
- Éléments DOM : `elem-001`, `elem-002`
- Recommandations : `rec-001`, `rec-002`
- Observations : `obs-001`, `obs-002`
- Contradictions : `contradiction-001`
- Gaps contextuels : `cgap-001`
- Capabilities : `cap-001`
- Personas : `persona-001`

### Timestamps
Format ISO 8601 avec Z : `"2025-03-11T14:32:00Z"`
Jamais de timestamp localisé sans timezone.

### Chemins de fichiers
Toujours relatifs à la racine du projet cible.
Exemple : `.audit/screenshots/page-001.png` — pas `/home/user/project/.audit/...`

## Conventions de contenu

### Champ `observation`
- Commence toujours par un fait observable (jamais par une évaluation)
- Contient une référence source entre crochets
- Est spécifique et non-paraphrasable
- Longueur : 1-3 phrases maximum

**Exemple correct :**
`"Le bouton 'Valider' du formulaire de contact mesure 28×18px en mobile [touch-page-003.json:target-012]. Le seuil minimum iOS/Google est 44×44px."`

**Exemple interdit :**
`"Le bouton est trop petit pour les utilisateurs mobiles."`

### Champ `recommendation`
- Commence toujours par un verbe à l'infinitif
- Décrit l'action à réaliser, pas l'état cible
- Contient une référence capability_id ou `"speculation": true`

**Exemple correct :**
`"Augmenter la zone de tap du bouton 'Valider' à minimum 44×44px en ajoutant du padding (min 8px vertical) — modifiable dans le composant Button.tsx"`

**Exemple interdit :**
`"Le bouton devrait être plus grand pour être accessible sur mobile."`

### Champ `severity` / `priority`
Valeurs strictes : `"critical"`, `"high"`, `"medium"`, `"low"`
Pas de valeurs libres ("urgent", "important", "minor").

### Champ `effort`
Valeurs strictes : `"xs"`, `"s"`, `"m"`, `"l"`, `"xl"`
Définitions :
- `xs` : ≤30 minutes — changement CSS/texte localisé
- `s` : ≤2 heures — modification d'un composant
- `m` : ≤1 jour — refonte d'une section
- `l` : ≤1 semaine — refonte d'un écran ou d'un système
- `xl` : >1 semaine — refonte architecturale

## Règles d'écriture atomique

Tout fichier JSON est écrit de façon atomique :
1. Écrire dans un fichier temporaire `{nom}.tmp`
2. Faire un `os.replace()` pour remplacer l'existant
3. Ne jamais écrire directement sur le fichier cible

Ceci est implémenté dans `lib/file_utils.py:write_json()`.
Les agents ne gèrent pas l'écriture directement — ils passent par `write_json()`.

## Validation schema

Avant de finaliser tout output JSON, vérifier la conformité au schema :
```python
import jsonschema
schema = read_json(f"schemas/{schema_name}.schema.json")
jsonschema.validate(instance=output, schema=schema)
```
Si la validation échoue : logger l'erreur, ne pas écrire le fichier, signaler dans `script-errors.json`.
