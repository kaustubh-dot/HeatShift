# HeatShift Design Specification

## 1. Design Philosophy & Brief Inference

### Mode

**Product Mode with editorial presentation layer.** HeatShift is an operational decision-support tool — data-dense, precise, proof-driven. But it lives inside a hackathon demo where a judge must grasp the problem and transformation in under 30 seconds. The design straddles these two demands: every component is built for clarity and data integrity, but the chapter structure, typography scale, and motion choreography are tuned for cinematic impact during a 3–5 minute presentation.

### Domain

Municipal infrastructure operations under climate constraint. The visual language draws from:

- **Air traffic control / mission operations** — dark canvas, high-contrast data, status-driven color
- **Weather/climate dashboards** — thermal gradients, time-series heat bands, forecast severity
- **Cartographic/GIS** — schematic maps with thin lines, location markers, route overlays

### Memorable Detail

**The thermal field is a living data element.** The timeline strip renders the supplied heat series as discrete 15-minute bands; it never interpolates or invents intermediate values. A restrained ambient wash may echo the currently selected band as presentation styling. The +2°C heat shock updates the discrete strip first, then the ambient wash, making the changed constraint physically felt without blurring data and decoration.

### Design Direction (from DESIGN_BRIEF.md)

- Near-black charcoal canvas, warm ivory text, amber-to-vermilion heat, cool cyan recovery
- Bold grotesk display type, restrained interface sans, monospaced operational data
- Thin cartographic lines, subtle grain texture, thermal gradients, crisp schedule blocks
- Click-driven chapter presentation; no scroll hijacking
- Laptop presentation (1280px) is the primary viewport
- The UI must never fabricate, infer, or smooth over solver facts

### Judge-first implementation hierarchy

The visual ambition is deliberately high, but the experience has a strict priority order:

1. **Must ship:** three chapters, complete-day timeline, baseline-to-policy diff, explicit solver evidence, diagnosis, heat shock, fallback disclosure, keyboard access, and reduced motion.
2. **Should ship:** synchronized map selection, concise transformation motion, ambient thermal wash, and one polished transition between chapters.
3. **Cut first if time slips:** animated route drawing, grain texture, counter animations, elaborate tooltips, and the expanded all-work-orders inspector.

No visual effect may delay or obscure the result. A judge must understand the problem, the changed plan, and the reason for one deferral within 30 seconds.

---

## 2. Complete Design Token System

All color values use OKLCH for perceptual uniformity. All spacing uses a 4px base grid. All type uses a 1.200 (Minor Third) modular ratio for data-dense layouts.

### 2.1 Color Palette

```css
:root {
  /* ═══════════════════════════════════════════
     BACKGROUND SCALE — Warm-tinted charcoal
     ═══════════════════════════════════════════ */
  --bg-base:      oklch(0.13 0.01 70);   /* Primary canvas — near-black with warm undertone */
  --bg-surface:   oklch(0.17 0.01 70);   /* Card/panel backgrounds */
  --bg-elevated:  oklch(0.22 0.012 70);  /* Popovers, hover surfaces, active panels */
  --bg-recessed:  oklch(0.10 0.008 70);  /* Inset areas, timeline backdrop */

  /* ═══════════════════════════════════════════
     TEXT SCALE — Warm ivory
     ═══════════════════════════════════════════ */
  --text-primary:  oklch(0.93 0.02 85);  /* Primary text — warm ivory */
  --text-secondary:oklch(0.72 0.015 85); /* Muted labels, descriptions */
  --text-tertiary: oklch(0.52 0.01 85);  /* Disabled, placeholders */
  --text-inverse:  oklch(0.13 0.01 70);  /* Text on light backgrounds */

  /* ═══════════════════════════════════════════
     HEAT GRADIENT — Normal → Elevated → Severe → Extreme
     Hue rotates from warm amber (80) → orange (55) → vermilion (35) → deep crimson (20)
     ═══════════════════════════════════════════ */
  --heat-normal:   oklch(0.78 0.14 85);  /* Warm amber — comfortable */
  --heat-elevated: oklch(0.68 0.19 55);  /* Orange — caution */
  --heat-severe:   oklch(0.55 0.23 35);  /* Vermilion — danger */
  --heat-extreme:  oklch(0.42 0.26 22);  /* Deep crimson — stop-work */

  /* Muted variants for backgrounds/fills */
  --heat-normal-bg:   oklch(0.78 0.14 85 / 0.12);
  --heat-elevated-bg: oklch(0.68 0.19 55 / 0.15);
  --heat-severe-bg:   oklch(0.55 0.23 35 / 0.18);
  --heat-extreme-bg:  oklch(0.42 0.26 22 / 0.20);

  /* ═══════════════════════════════════════════
     RECOVERY / COOLING — Cool cyan
     ═══════════════════════════════════════════ */
  --recovery:      oklch(0.72 0.12 210); /* Primary cyan */
  --recovery-muted:oklch(0.50 0.08 210); /* Subdued variant */
  --recovery-bg:   oklch(0.72 0.12 210 / 0.12); /* Background fill */

  /* ═══════════════════════════════════════════
     PLAN DIFF CHANGE COLORS
     Each change type gets a unique hue
     ═══════════════════════════════════════════ */
  --diff-unchanged:     oklch(0.55 0.02 260);  /* Neutral gray — no action */
  --diff-moved-time:    oklch(0.68 0.15 270);  /* Periwinkle blue */
  --diff-moved-crew:    oklch(0.65 0.17 300);  /* Violet */
  --diff-recovery-added:oklch(0.72 0.12 210);  /* Cyan — same as recovery */
  --diff-served:        oklch(0.68 0.16 150);  /* Green — newly served */
  --diff-deferred:      oklch(0.55 0.23 35);   /* Vermilion — same as severe */

  /* ═══════════════════════════════════════════
     SOLVER STATUS COLORS
     ═══════════════════════════════════════════ */
  --solver-optimal:    oklch(0.72 0.16 150);  /* Confident green */
  --solver-feasible:   oklch(0.78 0.14 85);   /* Amber — solution found; optimality unproven */
  --solver-infeasible: oklch(0.55 0.23 25);   /* Red — proven impossible */
  --solver-unknown:    oklch(0.60 0.04 260);  /* Neutral gray — no conclusion */
  --solver-invalid:    oklch(0.50 0.20 25);   /* Dark red — model error */

  /* ═══════════════════════════════════════════
     TIMELINE SEGMENT STATE COLORS
     ═══════════════════════════════════════════ */
  --tl-work:        oklch(0.65 0.15 85);   /* Warm amber — active work */
  --tl-work-heavy:  oklch(0.58 0.20 50);   /* Deeper orange for heavy exertion */
  --tl-work-moderate:oklch(0.70 0.12 85);  /* Lighter amber for moderate */
  --tl-recovery:    oklch(0.72 0.12 210);  /* Cool cyan */
  --tl-travel:      oklch(0.50 0.06 260);  /* Blue-gray */
  --tl-idle:        oklch(0.30 0.02 70);   /* Near-invisible — warm dark */
  --tl-unavailable: oklch(0.18 0.005 0);   /* Barely visible dark gray */

  /* ═══════════════════════════════════════════
     CREW IDENTITY COLORS
     Three distinct hues, all accessible on dark backgrounds
     ═══════════════════════════════════════════ */
  --crew-asphalt:  oklch(0.72 0.13 55);   /* Warm orange — asphalt/road */
  --crew-drainage: oklch(0.70 0.14 210);  /* Teal/cyan — water/drainage */
  --crew-general:  oklch(0.68 0.12 310);  /* Soft violet — general ops */

  /* ═══════════════════════════════════════════
     PRIORITY COLORS
     ═══════════════════════════════════════════ */
  --priority-critical: oklch(0.60 0.22 25); /* Red-orange */
  --priority-high:     oklch(0.72 0.16 55); /* Orange */
  --priority-planned:  oklch(0.62 0.08 260);/* Muted blue-gray */

  /* ═══════════════════════════════════════════
     STRUCTURAL
     ═══════════════════════════════════════════ */
  --border-default:  oklch(0.30 0.015 70);  /* Subtle warm border */
  --border-strong:   oklch(0.42 0.02 70);   /* Emphasized divider */
  --border-focus:    oklch(0.72 0.12 210);  /* Focus ring — recovery cyan */
  --progress-scrim: oklch(0.08 0.01 70 / 0.62); /* Non-modal result-panel progress layer */
}
```

**Semantic layering rule:** heat color belongs to the heat strip and heat-shock control; timeline fill communicates activity state; crew identity appears as a stroke, marker, or label; solver status always includes text. Priority and plan-diff meaning use an icon plus label. Do not place all color systems on the same element.

### 2.2 Typography

**Font Selection:**

| Role | Font | Source | Rationale |
|---|---|---|---|
| Display | **Space Grotesk** (700) | Bundled WOFF2 | Bold geometric grotesk. High-impact chapter headings. Strong industrial character matching municipal infrastructure. |
| Interface | **DM Sans** (400, 500, 600) | Bundled WOFF2 | Clean, modern, highly legible. Slightly warmer than Inter — better fit for the warm-ivory-on-dark palette. |
| Operational | **JetBrains Mono** (400, 500) | Bundled WOFF2 | Precise tabular figures. Excellent for solver values, time codes, slot numbers. |

```css
/* Bundle licensed WOFF2 files under /public/fonts; the demo must not depend on a CDN. */
@font-face {
  font-family: 'Space Grotesk';
  src: url('/fonts/space-grotesk-700.woff2') format('woff2');
  font-weight: 700;
  font-display: swap;
}

@font-face {
  font-family: 'DM Sans';
  src: url('/fonts/dm-sans-variable.woff2') format('woff2');
  font-weight: 400 600;
  font-display: swap;
}

@font-face {
  font-family: 'JetBrains Mono';
  src: url('/fonts/jetbrains-mono-variable.woff2') format('woff2');
  font-weight: 400 500;
  font-display: swap;
}

:root {
  --font-display: 'Space Grotesk', system-ui, sans-serif;
  --font-sans:    'DM Sans', system-ui, sans-serif;
  --font-mono:    'JetBrains Mono', ui-monospace, monospace;

  /* ═══════════════════════════════════════════
     MODULAR SCALE — 1.200 Ratio (Minor Third)
     Base: 16px (1rem)
     Compact ratio chosen for data-dense UI
     ═══════════════════════════════════════════ */
  --text-xs:   0.75rem;    /* 12px — hard minimum for captions */
  --text-sm:   0.833rem;   /* ~13px — labels, badges */
  --text-base: 1rem;       /* 16px — body text */
  --text-lg:   1.2rem;     /* ~19px — emphasized body */
  --text-xl:   1.44rem;    /* ~23px — section headers */
  --text-2xl:  1.728rem;   /* ~28px — subsection display */
  --text-3xl:  2.074rem;   /* ~33px — chapter subtitles */
  --text-4xl:  2.488rem;   /* ~40px — chapter titles */
  --text-5xl:  2.986rem;   /* ~48px — hero statistics */
  --text-6xl:  3.583rem;   /* ~57px — opening "41°C" hook */
  --text-7xl:  4.3rem;     /* ~69px — reserved for dramatic temperature display */

  /* ═══════════════════════════════════════════
     LINE HEIGHTS
     ═══════════════════════════════════════════ */
  --leading-display: 1.05;  /* Display/hero text — very tight */
  --leading-heading: 1.2;   /* Section headings */
  --leading-body:    1.65;  /* Body text — generous for readability */
  --leading-data:    1.4;   /* Captions, labels, table data */

  /* ═══════════════════════════════════════════
     LETTER SPACING
     ═══════════════════════════════════════════ */
  --tracking-tight:  -0.02em;  /* Display type */
  --tracking-normal:  0em;     /* Body text */
  --tracking-wide:    0.06em;  /* All-caps labels, badges */
  --tracking-mono:   -0.03em;  /* Monospace data — tightened */
}

/* ═══════════════════════════════════════════
   GLOBAL TYPOGRAPHY RULES
   ═══════════════════════════════════════════ */
body {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  line-height: var(--leading-body);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

h1, h2, h3 {
  font-family: var(--font-display);
  font-weight: 700;
  letter-spacing: var(--tracking-tight);
  text-wrap: balance;
}

/* All numeric/data contexts */
.data-value,
.metric-value,
.solver-value,
.slot-label,
.time-label {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  letter-spacing: var(--tracking-mono);
}

/* All-caps labels */
.label-caps {
  font-family: var(--font-sans);
  font-weight: 600;
  font-size: var(--text-xs);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  color: var(--text-secondary);
}
```

### 2.3 Spacing

```css
:root {
  /* ═══════════════════════════════════════════
     4px BASE GRID
     ═══════════════════════════════════════════ */
  --space-0:  0;
  --space-1:  0.25rem;   /*  4px */
  --space-2:  0.5rem;    /*  8px */
  --space-3:  0.75rem;   /* 12px */
  --space-4:  1rem;      /* 16px */
  --space-5:  1.25rem;   /* 20px */
  --space-6:  1.5rem;    /* 24px */
  --space-8:  2rem;      /* 32px */
  --space-10: 2.5rem;    /* 40px */
  --space-12: 3rem;      /* 48px */
  --space-16: 4rem;      /* 64px */
  --space-20: 5rem;      /* 80px */
  --space-24: 6rem;      /* 96px */

  /* ═══════════════════════════════════════════
     SEMANTIC SPACING ALIASES
     ═══════════════════════════════════════════ */
  --pad-card:     var(--space-4);    /* Internal card padding */
  --pad-panel:    var(--space-6);    /* Panel/section padding */
  --pad-page:     var(--space-8);    /* Page edge padding */
  --gap-items:    var(--space-3);    /* Between sibling items */
  --gap-sections: var(--space-12);   /* Between major sections */
  --gap-chapters: 0;                 /* Chapters fill viewport — no gap */
}
```

### 2.4 Motion

```css
:root {
  /* ═══════════════════════════════════════════
     EASING CURVES
     ═══════════════════════════════════════════ */
  --ease-enter:  cubic-bezier(0.16, 1, 0.3, 1);     /* Deceleration — elements arrive and settle */
  --ease-exit:   cubic-bezier(0.55, 0, 1, 0.45);     /* Acceleration — elements depart */
  --ease-move:   cubic-bezier(0.45, 0, 0.55, 1);     /* Repositioning — ease-in-out */
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);  /* Subtle overshoot for emphasis */

  /* ═══════════════════════════════════════════
     DURATION TOKENS
     ═══════════════════════════════════════════ */
  --dur-instant:   100ms;   /* Hover feedback, focus rings */
  --dur-fast:      150ms;   /* Button press, toggle */
  --dur-normal:    250ms;   /* State changes, panel reveals */
  --dur-slow:      400ms;   /* Chapter content fade-in */
  --dur-cinematic: 800ms;   /* Plan-diff transformation, heat-shock effect */
  --dur-dramatic:  1200ms;  /* Opening hero reveal */
}

/* ═══════════════════════════════════════════
   SPECIFIC CHOREOGRAPHY TIMINGS
   ═══════════════════════════════════════════ */
:root {
  /* Plan-diff animation (Chapter 2) */
  --diff-highlight-dur:  600ms;   /* Step 1: glow on changing segments */
  --diff-transform-dur:  800ms;   /* Step 2: segments move/fade */
  --diff-settle-dur:     400ms;   /* Step 3: metrics counter-animate */
  --diff-stagger-offset: 60ms;    /* Delay between successive segment animations */

  /* Chapter transition */
  --chapter-exit-dur:    200ms;
  --chapter-enter-dur:   400ms;
  --chapter-stagger:     50ms;

  /* Heat-shock effect */
  --shock-flash-dur:     300ms;   /* Red flash across viewport */
  --shock-heat-dur:      600ms;   /* Heat band strip updates */
}

/* ═══════════════════════════════════════════
   REDUCED MOTION
   Preserve information, remove animation
   ═══════════════════════════════════════════ */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### 2.5 Layout

```css
:root {
  /* ═══════════════════════════════════════════
     BREAKPOINTS
     ═══════════════════════════════════════════ */
  --bp-tablet:  1024px;
  --bp-laptop:  1280px;  /* PRIMARY — presentation viewport */
  --bp-desktop: 1440px;

  /* ═══════════════════════════════════════════
     TIMELINE GRID DIMENSIONS
     ═══════════════════════════════════════════ */
  --slot-count:        40;       /* 07:00–17:00 = 10hrs = 40 slots */
  --slot-width-detail: 2.5rem;   /* Optional inspection zoom only */
  --timeline-width:    100%;     /* Overview always fits the available panel */
  --crew-row-height: 3.5rem; /* 56px per crew row */
  --crew-row-gap:    var(--space-2);
  --heat-strip-height: 0.375rem; /* 6px — thin heat band below slot headers */

  /* ═══════════════════════════════════════════
     MAP DIMENSIONS
     ═══════════════════════════════════════════ */
  --map-aspect-ratio: 4 / 3;
  --map-viewbox: 0 0 800 600;  /* SVG coordinate space */
  --map-node-radius: 8;        /* Job location dot */
  --map-depot-size:  12;       /* Depot square half-size */
  --map-route-width: 2;        /* Route polyline stroke width */
  --map-label-offset: 14;      /* Label offset from node center */
}
```

### 2.6 Effects

```css
:root {
  /* ═══════════════════════════════════════════
     SHADOWS — Subtle, used sparingly on dark canvas
     ═══════════════════════════════════════════ */
  --shadow-sm:   0 1px 2px oklch(0 0 0 / 0.3);
  --shadow-md:   0 4px 8px oklch(0 0 0 / 0.4);
  --shadow-lg:   0 8px 24px oklch(0 0 0 / 0.5);
  --shadow-glow-heat:     0 0 16px oklch(0.55 0.23 35 / 0.4);   /* Vermilion glow */
  --shadow-glow-recovery: 0 0 12px oklch(0.72 0.12 210 / 0.3);  /* Cyan glow */
  --shadow-glow-focus:    0 0 0 3px oklch(0.72 0.12 210 / 0.4); /* Focus ring glow */

  /* ═══════════════════════════════════════════
     BORDER RADII — Crisp, operational, not playful
     ═══════════════════════════════════════════ */
  --radius-xs:  2px;   /* Timeline segments — very crisp */
  --radius-sm:  4px;   /* Cards, badges */
  --radius-md:  6px;   /* Panels, inputs */
  --radius-lg:  8px;   /* Modals, popovers */
  --radius-full: 9999px; /* Status dots only */

  /* ═══════════════════════════════════════════
     THERMAL GRAIN TEXTURE
     Subtle noise overlay for cinematic depth
     ═══════════════════════════════════════════ */
  --grain-opacity: 0.03;
}

/* Grain overlay — apply to body or chapter container */
.grain-overlay::after {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 9999;
  opacity: var(--grain-opacity);
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 256px 256px;
  mix-blend-mode: overlay;
}
```

---

## 3. Layout Macrostructure

**Hybrid: Full-Screen Stage (#17) + Dashboard Canvas (#8)**

At the primary presentation viewport, the app renders as a series of full-viewport chapters navigated by click without page-level scrolling. At smaller sizes or browser zoom, normal vertical scrolling is allowed so content is never clipped. Within each chapter, content is laid out using data-dense dashboard grids.

### Global Shell

```
┌─────────────────────────────────────────────────┐
│ ChapterNav (fixed top)                          │
│ ┌─ ① Tomorrow's Brief ─┬─ ② Plan ─┬─ ③ Why ─┐ │
├─────────────────────────────────────────────────┤
│                                                 │
│              Active Chapter Content             │
│              (fills remaining viewport)         │
│                                                 │
├─────────────────────────────────────────────────┤
│ TrustBar: disclaimer left · solver proof right  │
└─────────────────────────────────────────────────┘
```

### Chapter 1: Tomorrow's Brief

```
┌─────────────────────────────────────────────────┐
│                                                 │
│       41°C                                      │
│       Three crews. Twelve work orders.          │
│       How much public service survives          │
│       the heat?                                 │
│                                    [Space Grotesk│
│                                     text-7xl]   │
├─────────────────────────────────────────────────┤
│ Crew 1 · Crew 2 · Crew 3   [compact identity row]│
├────────┴────────┴───────────────────────────────┤
│ ███████ HeatBandStrip (full width) █████████████│
├──────────────────┬──────────────────────────────┤
│ 3 spotlight jobs │ Service-first   [Generate →] │
│ [Inspect all 12]  │ counterfactual               │
└──────────────────┴──────────────────────────────┘
```

### Chapter 2: Plan Transformation

```
┌─────────────────────────────────────────────────┐
│ MetricsBar (full width)                         │
│ ┌──────┬──────┬──────┬──────┬──────┬──────────┐ │
│ │Crit  │PlnSvc│Conflct│Travel│OT   │Work/Recv │ │
│ │ 4/4  │  71  │  0   │ 126m │ 0m  │ 525/105  │ │
│ │ ▼    │ ▼    │ ▼    │ ▼    │     │          │ │
│ └──────┴──────┴──────┴──────┴──────┴──────────┘ │
├───────────────────┬─────────────────────────────┤
│ SchematicMap      │ TimelineSlotHeader + Heat   │
│ (SVG)             │ ████ HeatBandStrip ████████ │
│                   ├─────────────────────────────┤
│  ○ depot          │ Crew 1  █W█W█R█W█ ░T░ █W█  │
│  ● job            │ Crew 2  ░T░ █W█W█W█R█ ░T░  │
│  ── route         │ Crew 3  █W█R█W█ ░T░ █W█W█  │
│                   ├─────────────────────────────┤
│ ← map syncs →    │ PlanDiffList (scrollable)    │
│ with timeline     │ ┌ job-d107 ──── DEFERRED ┐  │
│                   │ │ job-d103 ──── MOVED     │  │
│                   │ │ job-d109 ──── +RECOVERY │  │
│                   │ └─────────────────────────┘  │
└───────────────────┴─────────────────────────────┘
```

- **CSS Grid:** `grid-template-columns: 1fr 2fr` for map|timeline split
- **Interaction:** Clicking a PlanDiffCard highlights the job on both the map (node pulse) and timeline (segment glow). All other elements dim to 30% opacity.

### Chapter 3: Why / What-if

```
┌─────────────────────────────────────────────────┐
│ ┌───────────┬───────────────────────────────────┐│
│ │ Deferred  │ DiagnosisPanel                   ││
│ │ Jobs      │ ┌───────────────────────────────┐ ││
│ │           │ │ Classification: feasible_with ││
│ │ [job-d107]│ │ _cost (OPTIMAL)               ││
│ │ ■ active  │ │                               ││
│ │           │ │ Displaced: job-d104           ││
│ │  job-d104 │ │ Service: −4  Travel: +18min   ││
│ │  job-d111 │ │                               ││
│ │           │ ├───────────────────────────────┤ ││
│ │           │ │ Tested Interventions          ││
│ │           │ │ ┌ deadline +30min ── OPTIMAL ┐││
│ │           │ │ │ overtime +15min ── FEASIBLE│││
│ │           │ │ │ alt crew ──────── INFEASIBL│││
│ │           │ │ └────────────────────────────┘││
│ ├───────────┴─┤──────────────────────────────┤ ││
│ │             │ HeatShockControl             │ ││
│ │             │ [  Apply +2°C Heat Shock  ]  │ ││
│ │             │ ███████ intensity bar ███████│ ││
│ └─────────────┴──────────────────────────────┘ ││
└─────────────────────────────────────────────────┘
```

- **CSS Grid:** `grid-template-columns: minmax(240px, 1fr) 3fr`
- Two sub-sections in the right panel: diagnosis result + heat-shock control
- Heat shock triggers a full re-solve with non-modal solver progress, then replaces plan data only after a valid response

---

## 4. Component Inventory

### 4.1 ChapterNav

- **Visual:** Horizontal nav pinned to top. Three step indicators connected by thin lines. Active step shows warm ivory text + bottom accent bar in `--border-focus`. Inactive steps show `--text-tertiary`.
- **States:** default (clickable), active (current chapter), disabled (data not yet loaded)
- **Props:** `chapters: {id, label}[]`, `activeId: string`, `onNavigate: (id) => void`, `disabledIds: string[]`
- **A11y:** `<nav aria-label="Chapter navigation">`, `<button>` elements with `aria-current="step"` for active

### 4.2 TemperatureBadge

- **Visual:** Large mono number + "°C" suffix. Background pill colored by heat band. Font: `--font-mono` at `--text-3xl`.
- **States:** normal (`--heat-normal`), elevated (`--heat-elevated`), severe (`--heat-severe`), extreme (`--heat-extreme`)
- **Props:** `temperatureC: number`, `band: 'normal'|'elevated'|'severe'|'extreme'`
- **A11y:** `aria-label="Temperature: 41 degrees Celsius, severe heat band"`

### 4.3 HeatBandStrip

- **Visual:** Full-width horizontal bar, `--heat-strip-height` tall. Each supplied slot is a discrete colored segment using its explicit heat-band value. No gradients or tweening occur between adjacent data slots.
- **Props:** `heatSeries: HeatSlot[]`, `slotMinutes: number`
- **A11y:** `role="img"`, `aria-label="Heat progression: normal from 7:00, elevated from 10:00, severe from 12:00"`

### 4.4 CrewCard

- **Visual:** Card with left border in crew identity color. Crew name in `--font-display` `--text-xl`. Capabilities and equipment as inline tags. Shift times in `--font-mono`.
- **States:** default, hover (border brightens), selected (full left border glow)
- **Props:** `crew: Crew`
- **A11y:** Semantic `<article>` with `aria-label`

### 4.5 JobCard

- **Visual:** Compact card. Priority badge (critical = red dot, high = orange, planned = gray). Exertion indicator (heavy = filled thermometer icon, moderate = half). Time window in mono. Service value number.
- **States:** default, hover (subtle lift via `translateY(-1px)`), selected (cyan border), deferred (reduced opacity + strikethrough name)
- **Props:** `job: Job`, `isDeferred: boolean`, `isSelected: boolean`, `onClick: () => void`
- **A11y:** Semantic `<article>` containing a native `<button type="button">` with the full job description in its accessible name

### 4.6 MetricTile

- **Visual:** Vertical stack: label (`--label-caps` style) → value (`--font-mono` `--text-3xl`) → optional delta (below, colored by direction: green ↓conflicts, red ↑travel).
- **States:** default, animating (number transition during plan diff)
- **Props:** `label: string`, `value: number`, `unit?: string`, `delta?: number`, `deltaDirection?: 'good'|'bad'|'neutral'`
- **A11y:** `aria-label="Critical jobs scheduled: 4 of 4"`

### 4.7 MetricsBar

- **Visual:** Horizontal flex row of 6–7 MetricTiles spanning full width. Separated by thin vertical dividers (`--border-default`). Background: `--bg-surface`.
- **Props:** `metrics: Metrics`, `baselineMetrics?: Metrics` (for delta computation)
- **A11y:** `role="region"`, `aria-label="Plan metrics comparison"`

### 4.8 SolverStageIndicator

- **Visual:** Inline row: status dot (colored circle) + stage name (label-caps) + value (mono) + "/" + bound (mono, muted). Compact, single-line.
- **States:** OPTIMAL (green dot + checkmark), FEASIBLE (amber dot), INFEASIBLE (red dot + ✕), UNKNOWN (gray dot + "?")
- **Props:** `stage: Stage`
- **A11y:** `aria-label="Critical service: optimal, value 4, bound 4"`

### 4.9 SolverStatusPanel

- **Visual:** Compact row anchored to bottom-right of viewport. Shows all stages inline with thin separators. Background: `--bg-elevated` with subtle `--shadow-sm`.
- **Props:** `stages: Stage[]`, `maximumClaimAllowed: boolean`
- **A11y:** `role="status"`, `aria-live="polite"` — updates announced when solve completes

### 4.10 TimelineGrid

- **Visual:** The core visualization. CSS Grid with slot columns and crew rows. Slot header row at top with time labels and heat band strip underneath. Each crew row contains absolutely-positioned TimelineSegments.
- **Layout:** Crew labels occupy a fixed first column; the schedule uses `grid-template-columns: repeat(var(--slot-count), minmax(0, 1fr))` so all 40 slots remain visible in overview mode. An explicit optional detail mode may switch to `--slot-width-detail` and horizontal scrolling.
- **Props:** `crews: Crew[]`, `segments: TimelineSegment[]`, `heatSeries: HeatSlot[]`, `selectedJobId?: string`, `onJobClick: (jobId) => void`
- **A11y:** `role="grid"`, `aria-label="Crew schedule timeline"`. Rows have `role="row"`. Segments have `role="gridcell"` with descriptive labels. Arrow key navigation within grid.

### 4.11 TimelineSegment

- **Visual:** Colored block spanning `end_slot - start_slot` grid columns. Fill communicates state; heavy exertion adds a pattern or edge treatment rather than another competing palette. Show a short job ID only when it fits; the complete name and facts remain available on focus and in the synchronized detail panel.
- **States:** default, hover (brighten 10%), selected (glow border in `--border-focus`), dimmed (30% opacity when another job is selected), diff-highlight (pulsing glow during plan-diff animation)
- **Props:** `segment: TimelineSegment`, `isSelected: boolean`, `isDimmed: boolean`, `diffState?: 'entering'|'exiting'|'moving'`
- **A11y:** `role="gridcell"`, `aria-label="Asphalt Crew: work on School-zone pothole, 9:15 to 10:00, heavy exertion, policy rule hs01-heavy-elevated"`

### 4.12 TimelineSlotHeader

- **Visual:** Row of time labels (`07:00`, `07:15`, etc.) in `--font-mono` `--text-xs`. Major hour boundaries get full labels; quarter-hour slots get tick marks only. Below: a 6px HeatBandStrip showing slot-by-slot heat colors.
- **Props:** `slotCount: number`, `dayStart: string`, `slotMinutes: number`, `heatSeries: HeatSlot[]`

### 4.13 SchematicMap

- **Visual:** SVG element with dark background (`--bg-recessed`). Thin border. Location dots, route polylines, crew-colored paths. Depot markers are squares; job locations are circles. Explicit "Schematic service map" label in corner.
- **Props:** `locations: Location[]`, `routeSegments: RouteSegment[]`, `selectedJobId?: string`, `crewColors: Record<string, string>`, `onLocationClick: (jobId) => void`
- **A11y:** The SVG has `role="img"` and an informative label. Interactive locations use real HTML buttons positioned over the SVG, or focusable SVG groups with `tabindex="0"` plus Enter/Space handlers; a bare `<circle role="button">` is not sufficient.

### 4.14 MapNode

- **Visual:** SVG `<circle>` (job) or `<rect>` (depot). Fill matches crew color when assigned, or `--text-tertiary` when unassigned. Label positioned `--map-label-offset` pixels below.
- **States:** default, hover (scale 1.3), selected (pulse animation + glow ring), dimmed

### 4.15 MapRoute

- **Visual:** SVG `<polyline>` connecting two locations. Stroke color = crew identity color. `stroke-dasharray` animation shows travel direction.
- **States:** default (solid), active (animated dash), dimmed (20% opacity)

### 4.16 PlanDiffBadge

- **Visual:** Small inline pill. Text in `--text-xs` uppercase. Background color from `--diff-*` tokens. Icons: ✕ (deferred), ↔ (moved_time), ⇄ (moved_crew), + (recovery_added), ✓ (served), — (unchanged).
- **Props:** `change: PlanChangeType`

### 4.17 PlanDiffCard

- **Visual:** Horizontal card showing: job name + PlanDiffBadge + before/after state (crew, time range in mono). Binding rule IDs as small tags. Explanation code as tooltip.
- **States:** default, hover (border highlight), selected (expanded with full detail)
- **Props:** `diff: PlanDiff`, `isSelected: boolean`, `onClick: () => void`
- **A11y:** `<button>` with full description. `aria-expanded` if detail view is shown.

### 4.18 DiagnosisPanel

- **Visual:** Large right-side panel. Header: job name + ClassificationBadge. Body: retained commitments list, displaced jobs with links, ObjectiveDeltaTable. Footer: tested interventions.
- **States:** empty (no job selected — shows prompt), loading (skeleton), loaded, error
- **Props:** `diagnosis: DiagnosisResponse | null`, `isLoading: boolean`
- **A11y:** `role="region"`, `aria-label="Counterfactual diagnosis for [job name]"`, `aria-live="polite"`

### 4.19 ClassificationBadge

- **Visual:** Pill badge with classification text and color:
  - `equivalent_alternative` → green (`--solver-optimal`) → "Equal Alternative"
  - `feasible_with_cost` → amber (`--solver-feasible`) → "Feasible with Cost"
  - `proven_infeasible` → red (`--solver-infeasible`) → "Proven Infeasible"
  - `not_proven` → gray (`--solver-unknown`) → "Not Proven"
- **Props:** `classification: DiagnosisClassification`

### 4.20 ObjectiveDeltaTable

- **Visual:** Compact table. Rows: metric name | original value | forced value | delta (colored). Font: `--font-mono` for values. Columns right-aligned.
- **Props:** `delta: ObjectiveDelta`, `originalMetrics: Metrics`
- **A11y:** Proper `<table>` with `<thead>`, `<th scope="col">`

### 4.21 InterventionCard

- **Visual:** Row card. Intervention type + value as label. Solver status badge. Objective delta summary inline. Ordered by intervention rank.
- **States:** default, success (green left border if intervention resolved the issue), failure (red left border)
- **Props:** `intervention: TestedIntervention`

### 4.22 HeatShockControl

- **Visual:** Prominent button with thermal glow (`--shadow-glow-heat`). Label: "Apply +2°C Heat Shock". Background gradient from `--heat-severe` to `--heat-extreme`. On activation: button pulses, then solver progress appears over the result panel.
- **States:** idle (ready), active/pressed (scale 0.97), loading (disabled + spinner), complete (result displayed)
- **Props:** `onActivate: () => void`, `isLoading: boolean`, `isApplied: boolean`
- **A11y:** `<button aria-label="Apply plus 2 degrees Celsius heat shock to re-optimize the plan">`

### 4.23 PolicyDisclaimer

- **Visual:** Left side of the shared bottom TrustBar. Muted text (`--text-tertiary`, minimum 12px): "Synthetic demonstration policy. Not medical, legal, or workplace-safety guidance. Organizations must supply and approve their own policy." The right side holds compact solver proof. The bar reserves layout space and never overlays content.
- **A11y:** `role="contentinfo"`, always visible and readable

### 4.24 SolverProgress

- **Visual:** A non-modal solver progress layer over the result panel, not the whole application. It preserves the current plan, disables only the action that launched the solve, and shows "SOLVING…" plus the current stage. On first load, use an in-flow skeleton instead.
- **Props:** `stageName?: string`
- **A11y:** The affected result region uses `aria-busy="true"`; progress uses `role="status"` and `aria-live="polite"`. Focus remains on the triggering control and is not trapped.

### 4.25 ErrorState

- **Visual:** Centered panel with `--solver-infeasible` left border. Monospaced error message. Structured display of error code, message, and details array. Retry button below.
- **Props:** `error: ApiError`, `onRetry: () => void`
- **A11y:** `role="alert"`, `aria-live="assertive"`

### 4.26 FallbackBanner

- **Visual:** Thin, non-dismissible banner below ChapterNav. Amber background (`--heat-elevated` at 15% opacity). Text: "Saved solver run — live API unavailable — locked demo scenario". Keep the source disclosure visible for as long as fallback data is active.
- **A11y:** `role="alert"`, `aria-live="polite"`

### 4.27 TooltipInfo

- **Visual:** Dark tooltip (`--bg-base`, `--border-strong` border). Arrow pointing to trigger. Appears after 300ms hover delay. Max-width 280px. Text in `--text-sm`.
- **A11y:** `role="tooltip"`, trigger has `aria-describedby` pointing to tooltip ID

---

## 5. State & Interaction Choreography

### Chapter Transitions

1. Current chapter content fades out (`opacity 1→0`, `--dur-fast`, `--ease-exit`)
2. New chapter content fades in with staggered children (`opacity 0→1`, `translateY(8px)→0`, `--dur-slow`, `--ease-enter`, stagger `--chapter-stagger` per child)
3. ChapterNav active indicator slides to new position (`--dur-normal`, `--ease-move`)

### Plan-Diff Transformation (Chapter 2 — the signature moment)

| Step | Duration | What happens | Easing |
|---|---|---|---|
| 1. Baseline display | — | Service-first plan rendered in timeline + map | — |
| 2. Highlight changes | 300ms | Segments that will change get a brief glow ring (`--shadow-glow-heat`) | `--ease-spring` |
| 3a. Deferred exit | 500ms | Deferred segments fade to 0 opacity and scale down slightly | `--ease-exit` |
| 3b. Moved segments | 500ms | Segments with `moved_time` / `moved_crew` translate to the new grid position | `--ease-move` |
| 3c. Recovery grows | 500ms | Recovery segments scale from width 0 to full width in the gaps created | `--ease-enter` |
| 3d. Served enters | 500ms | Newly served segments fade in from 0 opacity | `--ease-enter` |
| 4. Metrics count | 250ms | MetricTile values update from old → new numbers | `--ease-move` |
| 5. Map routes | 500ms | Route polylines crossfade; route drawing is optional polish | `--ease-enter` |

Steps 3a–3d run simultaneously with at most 35ms stagger between individual segments. Total animation must stay at or below 1.6 seconds. Data and controls are available immediately, and a visible "Replay change" control lets the presenter repeat the signature moment.

**Reduced-motion:** Steps 2–5 are replaced by an instant swap. Changed segments display static PlanDiffBadges instead.

### Job Selection → Synchronized Highlight

1. User clicks a job (in timeline, map, or diff list)
2. All three views update simultaneously:
   - Timeline: selected segment gets `--border-focus` ring; all other segments dim to 30% opacity
   - Map: selected node pulses; corresponding route highlights; all other nodes/routes dim
   - Diff list: selected card gets `--bg-elevated` background; scroll into view if needed
3. Click on empty space or same job again deselects (everything returns to full opacity)

### Heat-Shock Effect

1. Button press: flash overlay (`--heat-extreme` at 10% opacity, 300ms fade in/out)
2. HeatBandStrip updates to the solver-returned +2°C discrete bands
3. SolverProgress appears ("RE-OPTIMIZING…") over the result panel
4. On result: full plan data swaps, plan-diff animation replays with new diff

### Solver Loading

- Non-modal progress layer with "SOLVING…" + current stage name
- No decorative spinner — just monospaced text and a thin indeterminate bar
- The current result remains visible; only the affected result panel is subdued

---

## 6. Accessibility Specification

### Focus Management

- On chapter transition: focus moves programmatically to the `<h1>` of the new chapter
- On diagnosis load: focus moves to DiagnosisPanel heading
- During a solve, focus stays on the trigger; only duplicate solve actions are disabled
- Skip-to-main-content link as the first focusable element

### Keyboard Navigation

| Key | Context | Action |
|---|---|---|
| `←` / `→` | ChapterNav | Navigate chapters |
| `↑` / `↓` | TimelineGrid | Move between crew rows |
| `←` / `→` | TimelineGrid | Move between segments in a row |
| `Enter` / `Space` | Any interactive | Activate/select |
| `Escape` | Any selection | Deselect current job |
| `Tab` | Global | Standard tab order |

### Screen Reader Landmarks

```html
<nav aria-label="Chapter navigation">
<main aria-label="Active chapter content">
  <section aria-label="Tomorrow's Brief">
  <section aria-label="Plan Transformation">
  <section aria-label="Counterfactual Diagnosis">
<footer aria-label="Policy disclaimer">
<aside aria-label="Solver status">
```

### Live Regions

- `SolverStatusPanel`: `aria-live="polite"` — announces solve completion
- `DiagnosisPanel`: `aria-live="polite"` — announces diagnosis result
- `ErrorState`: `aria-live="assertive"` — announces errors immediately
- `FallbackBanner`: `aria-live="polite"` — announces fallback mode

### Color-Blind Safety

- All semantic meanings use both color AND text/icon (never color alone)
- Heat bands: color + band name label + slot-by-slot temperature number available on hover
- Solver status: color + explicit status text (OPTIMAL/FEASIBLE/etc.)
- Plan diff: color + icon + change type text
- Timeline segments: color + state label in tooltip + pattern (dashed for travel, dotted for idle)

---

## 7. Responsive Strategy

| Viewport | Strategy |
|---|---|
| **≥ 1280px** (laptop — primary) | Full layout as specified in §3. Two-column split with the entire 10-hour timeline visible in overview mode. |
| **1024–1279px** | Chapter 2: map stacks above the full-width timeline. Chapter 3: deferred list becomes a horizontal strip above the diagnosis panel. |
| **768–1023px** | Same as 1024px but with reduced padding. MetricsBar wraps to 2 rows × 3 tiles. |
| **< 768px** | Functional but degraded. An in-flow advisory says: "HeatShift is optimized for laptop presentation. Rotate or use a wider screen for the best experience." It never blocks the content. |

Overview mode preserves every 15-minute slot by using fractional grid columns rather than fixed pixels. Optional detail mode may scroll horizontally. Data fidelity comes from explicit slot boundaries and accessible details, not from forcing a 1,600px canvas.

---

## 8. Anti-Pattern Verification

| # | Anti-Pattern | Status |
|---|---|---|
| 1 | Centered hero + 3 feature cards | ✅ Avoided — Chapter 1 uses asymmetric marquee layout |
| 2 | Generic purple-to-cyan gradient | ✅ Avoided — palette is amber→vermilion heat + cyan recovery |
| 3 | Pure black on pure white | ✅ Avoided — all neutrals are warm-tinted OKLCH |
| 4 | Defaulting to Inter/Roboto/Arial | ✅ Avoided — Space Grotesk + DM Sans + JetBrains Mono |
| 5 | Cards nested in cards | ✅ Avoided — flat hierarchy, single-level panels |
| 6 | No typographic hierarchy | ✅ Avoided — strong scale from a 12px caption floor to a 69px hero |
| 7 | Decorative animation | ✅ Avoided — all motion serves data transitions |
| 8 | Glow effects everywhere | ✅ Avoided — glow only on heat-shock control and selected elements |
| 9 | Glassmorphism over busy backgrounds | ✅ Avoided — no blur effects, all surfaces are opaque |
| 10 | Placeholder copy | ✅ Avoided — all text is domain-specific operational language |
| 11 | Missing hover/focus/active states | ✅ Addressed — every interactive element has all states defined |
| 12 | `transition: all` | ✅ Avoided — all transitions list specific properties |
| 13 | Generic pill buttons | ✅ Avoided — crisp radii (`--radius-sm`, `--radius-md`) |
| 14 | Multiple competing CTAs | ✅ Avoided — one primary action per chapter |
| 15 | `<div>` soup | ✅ Avoided — semantic landmarks throughout |
| 16 | Scroll hijacking | ✅ Avoided — click-driven chapter navigation |
| 17 | Color alone for meaning | ✅ Avoided — all semantic uses include text + icon |
| 18 | Body text > 75 characters | ✅ Avoided — `max-width: 65ch` on all prose |
| 19 | `outline: none` without replacement | ✅ Avoided — custom focus ring on all interactive elements |
| 20 | Fabricated solver data | ✅ Avoided — UI displays only backend-provided values |
