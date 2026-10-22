"""Original hand-drawn style doodles for the infographic skill.

Drawn for this project as simple inline SVG (viewBox 0 0 160 160). They carry no
fill or stroke colors of their own: the page CSS colors them through the
classes below, so they follow the theme and the dark mode.

  l        outline (ink color, round caps)
  f-none   no fill          f-cream  card color      f-sage  sage
  f-leaf   leaf green       f-terra  terracotta       f-orange  warm orange
"""

DOODLES = {
    # Potted plant: for growth, setup, "start small" ideas
    "plant": (
        '<path class="l f-none" d="M80 98V60"/>'
        '<path class="l f-leaf" d="M80 74C58 74 42 62 40 42c22-2 38 8 40 32z"/>'
        '<path class="l f-leaf" d="M80 60C80 38 95 24 116 22c2 22-11 38-36 38z"/>'
        '<path class="l f-sage" d="M80 88c15 0 27-8 30-23-15 0-28 8-30 23z"/>'
        '<rect class="l f-terra" x="46" y="98" width="68" height="14" rx="5"/>'
        '<path class="l f-terra" d="M54 112h52l-5 28a6 6 0 0 1-6 5H65a6 6 0 0 1-6-5z"/>'
    ),
    # Mug with steam: for breaks, habits, daily routines
    "mug": (
        '<path class="l f-none" d="M62 48c-7-8 7-13 0-24M82 48c-7-8 7-13 0-24M102 48c-7-8 7-13 0-24"/>'
        '<path class="l f-none" d="M114 76h8a14 14 0 0 1 0 28h-10"/>'
        '<path class="l f-cream" d="M50 62h64v40a28 28 0 0 1-28 28H78a28 28 0 0 1-28-28z"/>'
        '<path class="l f-terra" d="M50 80h64v14H50z"/>'
        '<ellipse class="l f-sage" cx="82" cy="138" rx="46" ry="8"/>'
    ),
    # Light bulb: for ideas, tips, key insights
    "lightbulb": (
        '<path class="l f-none" d="M80 12v10M34 30l7 7M126 30l-7 7M20 78h10M140 78h-10"/>'
        '<path class="l f-orange" d="M80 34a36 36 0 0 0-20 66c4 3 6 7 6 12v4h28v-4c0-5 2-9 6-12a36 36 0 0 0-20-66z"/>'
        '<path class="l f-none" d="M70 94l10-14 10 14"/>'
        '<rect class="l f-cream" x="64" y="120" width="32" height="10" rx="4"/>'
        '<rect class="l f-cream" x="69" y="132" width="22" height="9" rx="4"/>'
    ),
    # Rocket: for launches, delivery, speed
    "rocket": (
        '<path class="l f-orange" d="M68 112c-2 14 4 24 12 34 8-10 14-20 12-34z"/>'
        '<path class="l f-terra" d="M58 80c-14 6-20 18-20 32l22-8z"/>'
        '<path class="l f-terra" d="M102 80c14 6 20 18 20 32l-22-8z"/>'
        '<path class="l f-cream" d="M80 16c22 14 30 42 24 80H56c-6-38 2-66 24-80z"/>'
        '<path class="l f-terra" d="M56 96h48l-2 12H58z"/>'
        '<circle class="l f-sage" cx="80" cy="56" r="11"/>'
    ),
    # Notebook with checks and pencil: for checklists, plans, to-dos
    "notebook": (
        '<rect class="l f-cream" x="36" y="22" width="80" height="112" rx="10"/>'
        '<path class="l f-none" d="M76 52h28M76 80h28M76 108h28"/>'
        '<path class="l f-none" d="M48 52l5 5 9-10M48 80l5 5 9-10"/>'
        '<rect class="l f-none" x="48" y="100" width="14" height="14" rx="3"/>'
        '<g transform="rotate(32 124 96)">'
        '<rect class="l f-orange" x="116" y="56" width="16" height="62" rx="3"/>'
        '<path class="l f-cream" d="M116 118l8 16 8-16z"/>'
        '</g>'
    ),
    # Bar chart with a spark: for data, numbers, results
    "chart": (
        '<path class="l f-none" d="M24 134h112"/>'
        '<rect class="l f-sage" x="34" y="94" width="22" height="40" rx="4"/>'
        '<rect class="l f-leaf" x="68" y="66" width="22" height="68" rx="4"/>'
        '<rect class="l f-terra" x="102" y="40" width="22" height="94" rx="4"/>'
        '<path class="l f-orange" d="M132 14l3 9 9 3-9 3-3 9-3-9-9-3 9-3z"/>'
    ),
    # Magnifying glass: for research, review, "look closer"
    "magnifier": (
        '<circle class="l f-cream" cx="68" cy="66" r="40"/>'
        '<path class="l f-none" d="M46 62a24 24 0 0 1 17-19"/>'
        '<rect class="l f-terra" x="98" y="98" width="16" height="54" rx="8" transform="rotate(-45 106 125)"/>'
        '<path class="l f-orange" d="M126 22l3 8 8 3-8 3-3 8-3-8-8-3 8-3z"/>'
    ),
    # Sofa: for home, comfort, overviews of "a place"
    "sofa": (
        '<rect class="l f-sage" x="32" y="46" width="96" height="52" rx="16"/>'
        '<rect class="l f-leaf" x="24" y="84" width="112" height="34" rx="12"/>'
        '<rect class="l f-leaf" x="16" y="68" width="28" height="52" rx="13"/>'
        '<rect class="l f-leaf" x="116" y="68" width="28" height="52" rx="13"/>'
        '<rect class="l f-terra" x="52" y="58" width="28" height="26" rx="8" transform="rotate(-8 66 71)"/>'
        '<path class="l f-none" d="M38 120v16M122 120v16"/>'
    ),
}
