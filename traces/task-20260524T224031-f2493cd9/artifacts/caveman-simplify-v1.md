# Caveman Simplification — ink-pet

## What Matters

```
ink-pet = text canvas + ai pet + chinese radicals

core loop: user types → pet responds → text builds up → pet grows
magic: pet lives IN the text, pushes characters aside

remove nothing from core loop
add: particles, mouse, better art
```

## What to Add (3 things, not more)

### 1. Ink Particles
- When pet moves, ink droplets trail behind
- When text appears, ink bloom at insertion point
- Particles fade/drift like real ink on paper
- Very lightweight <canvas> layer, < 100 particles active

### 2. Pet Interaction
- Click near pet → pulse reaction
- Drag pet across canvas → text reflows in real-time
- Hover shows subtle glow

### 3. Dynamic ASCII Art
- Pet art responds to mood in real-time
- Character brightness field (like pretext variable typographic ascii)
- Same idea: brightness → character choice, but simpler
- Pet forms evolve shape, not just swap between static arrays

## What NOT to Add (keeper of simplicity)
- No complex animation framework
- No physics engine
- No webgl, no three.js
- No routing, no multi-page
- No database, no server
