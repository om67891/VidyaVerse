"""
Generate 24 distinct, high-fidelity SVG avatars for all VidyaVerse personas.
Each avatar features a unique subject-tailored palette, character portrait,
historical/scientific iconography, and a crisp badge.
"""
from pathlib import Path

AVATARS_BASE = Path(__file__).resolve().parent.parent / "frontend" / "public" / "avatars"

AVATARS = {
    # ── History Personas ─────────────────────────────────────────────────────────
    "history/shivaji_maharaj": {
        "title": "Chhatrapati Shivaji Maharaj",
        "bg_grad": ("#F59E0B", "#B45309"),
        "role": "Founder of Swaraj",
        "icon_svg": """
            <!-- Royal Maratha Turban (Pheta) with Jewel (Jijamata kalgi) -->
            <path d="M60,80 Q100,35 140,80 Q150,105 130,115 Q100,120 70,115 Z" fill="#DC2626" stroke="#991B1B" stroke-width="2"/>
            <path d="M95,35 L105,35 L102,15 L98,15 Z" fill="#FCD34D" stroke="#D97706" stroke-width="1.5"/>
            <circle cx="100" cy="40" r="5" fill="#EF4444" stroke="#F59E0B" stroke-width="1.5"/>
            <!-- Face Profile -->
            <ellipse cx="100" cy="110" rx="30" ry="34" fill="#FDE68A"/>
            <!-- Moustache & Royal Beard -->
            <path d="M78,118 Q100,128 122,118 Q115,135 100,138 Q85,135 78,118 Z" fill="#1F2937"/>
            <path d="M85,112 Q100,118 115,112 Q100,115 85,112 Z" fill="#111827"/>
            <!-- Eyes & Tilak (Chandra-kor) -->
            <path d="M96,86 A4,4 0 0,0 104,86" stroke="#B45309" stroke-width="2" fill="none"/>
            <circle cx="90" cy="100" r="2.5" fill="#1F2937"/>
            <circle cx="110" cy="100" r="2.5" fill="#1F2937"/>
            <!-- Royal Armor & Pearl Necklace -->
            <path d="M65,142 C75,132 125,132 135,142 L145,185 L55,185 Z" fill="#9A3412" stroke="#7C2D12" stroke-width="2"/>
            <path d="M80,146 Q100,160 120,146" stroke="#FEF3C7" stroke-width="3" stroke-dasharray="2,4" fill="none"/>
            <circle cx="100" cy="162" r="4" fill="#F59E0B"/>
        """,
    },
    "history/sant_dnyaneshwar": {
        "title": "Sant Dnyaneshwar",
        "bg_grad": ("#FBBF24", "#D97706"),
        "role": "Bhakti Guide & Philosopher",
        "icon_svg": """
            <!-- Divine Golden Aura -->
            <circle cx="100" cy="95" r="50" fill="#FEF3C7" opacity="0.6"/>
            <!-- Meditative Face -->
            <ellipse cx="100" cy="95" rx="26" ry="30" fill="#FDE68A"/>
            <!-- Gopi Chandan Tilak -->
            <path d="M98,75 L102,75 L100,90 Z" fill="#F59E0B"/>
            <circle cx="100" cy="92" r="1.5" fill="#DC2626"/>
            <!-- Peaceful Eyes -->
            <path d="M86,92 Q92,97 96,92" stroke="#451A03" stroke-width="2" fill="none"/>
            <path d="M104,92 Q108,97 114,92" stroke="#451A03" stroke-width="2" fill="none"/>
            <!-- Saffron Robe -->
            <path d="M68,125 C78,115 122,115 132,125 L145,185 L55,185 Z" fill="#EA580C"/>
            <!-- Dnyaneshwari Palm Leaf Scroll -->
            <rect x="75" y="145" width="50" height="20" rx="3" fill="#FFFBEB" stroke="#B45309" stroke-width="1.5"/>
            <line x1="82" y1="152" x2="118" y2="152" stroke="#B45309" stroke-width="1"/>
            <line x1="82" y1="158" x2="112" y2="158" stroke="#B45309" stroke-width="1"/>
        """,
    },
    "history/sant_namdeo": {
        "title": "Sant Namdeo",
        "bg_grad": ("#F97316", "#C2410C"),
        "role": "Devotional Kirtan Guide",
        "icon_svg": """
            <!-- Varkari Cap & Face -->
            <ellipse cx="100" cy="72" rx="24" ry="14" fill="#FAFAF9" stroke="#E7E5E4" stroke-width="1.5"/>
            <ellipse cx="100" cy="98" rx="25" ry="28" fill="#FDE68A"/>
            <!-- Tulsi Mala & Tilak -->
            <circle cx="100" cy="90" r="2" fill="#DC2626"/>
            <circle cx="91" cy="95" r="2" fill="#292524"/>
            <circle cx="109" cy="95" r="2" fill="#292524"/>
            <path d="M92,108 Q100,114 108,108" stroke="#292524" stroke-width="2" fill="none"/>
            <!-- Robe -->
            <path d="M68,126 C80,118 120,118 132,126 L142,185 L58,185 Z" fill="#F97316"/>
            <!-- Chipli / Kartal (Devotional Cymbals) -->
            <rect x="68" y="145" width="22" height="10" rx="2" fill="#D97706" stroke="#78350F" stroke-width="1.5"/>
            <rect x="110" y="145" width="22" height="10" rx="2" fill="#D97706" stroke="#78350F" stroke-width="1.5"/>
            <circle cx="79" cy="150" r="2" fill="#FEF3C7"/>
            <circle cx="121" cy="150" r="2" fill="#FEF3C7"/>
        """,
    },
    "history/sant_ekanath": {
        "title": "Sant Eknath",
        "bg_grad": ("#F59E0B", "#B45309"),
        "role": "Compassion & Service Guide",
        "icon_svg": """
            <!-- Head & Kind Expression -->
            <ellipse cx="100" cy="95" rx="26" ry="29" fill="#FDE68A"/>
            <path d="M82,78 Q100,70 118,78" fill="#E7E5E4" stroke="#A8A29E" stroke-width="1.5"/>
            <!-- Eyes & Warm Smile -->
            <circle cx="91" cy="93" r="2.5" fill="#451A03"/>
            <circle cx="109" cy="93" r="2.5" fill="#451A03"/>
            <path d="M92,106 Q100,113 108,106" stroke="#451A03" stroke-width="2" fill="none"/>
            <!-- White Khadi Kurta -->
            <path d="M68,125 C80,116 120,116 132,125 L145,185 L55,185 Z" fill="#F5F5F4" stroke="#D6D3D1" stroke-width="1.5"/>
            <!-- Kalash (Water Vessel of Godavari) symbol of feeding thirsty animal -->
            <ellipse cx="100" cy="155" rx="14" ry="10" fill="#D97706" stroke="#78350F" stroke-width="1.5"/>
            <path d="M93,145 L107,145 L105,148 L95,148 Z" fill="#F59E0B"/>
            <circle cx="100" cy="153" r="3" fill="#38BDF8"/>
        """,
    },
    "history/sant_tukaram": {
        "title": "Sant Tukaram",
        "bg_grad": ("#EA580C", "#9A3412"),
        "role": "Abhang & Equality Guide",
        "icon_svg": """
            <!-- Varkari Pheta & Gentle Face -->
            <ellipse cx="100" cy="74" rx="26" ry="14" fill="#FDE047" stroke="#CA8A04" stroke-width="1.5"/>
            <ellipse cx="100" cy="98" rx="25" ry="28" fill="#FDE68A"/>
            <!-- Traditional Tilak -->
            <rect x="98" y="82" width="4" height="12" fill="#B45309"/>
            <circle cx="91" cy="96" r="2.5" fill="#292524"/>
            <circle cx="109" cy="96" r="2.5" fill="#292524"/>
            <path d="M93,110 Q100,116 107,110" stroke="#292524" stroke-width="2" fill="none"/>
            <!-- Robe -->
            <path d="M68,126 C80,118 120,118 132,126 L142,185 L58,185 Z" fill="#F97316"/>
            <!-- Veena / Ektara Motif -->
            <line x1="72" y1="135" x2="128" y2="165" stroke="#78350F" stroke-width="3"/>
            <circle cx="72" cy="135" r="7" fill="#B45309" stroke="#78350F" stroke-width="1.5"/>
            <line x1="124" y1="160" x2="132" y2="170" stroke="#FDE68A" stroke-width="2"/>
        """,
    },
    "history/samarth_ramdas": {
        "title": "Samarth Ramdas",
        "bg_grad": ("#DC2626", "#991B1B"),
        "role": "Discipline & Strength Guide",
        "icon_svg": """
            <!-- Resolute Face with Long Beard -->
            <ellipse cx="100" cy="90" rx="25" ry="28" fill="#FDE68A"/>
            <path d="M80,105 Q100,140 120,105 Q115,135 100,140 Q85,135 80,105 Z" fill="#1C1917"/>
            <circle cx="91" cy="88" r="2.5" fill="#1C1917"/>
            <circle cx="109" cy="88" r="2.5" fill="#1C1917"/>
            <!-- Saffron Cap/Cloth -->
            <path d="M75,75 Q100,55 125,75 Z" fill="#EA580C"/>
            <!-- Saffron Robe -->
            <path d="M65,130 C75,120 125,120 135,130 L145,185 L55,185 Z" fill="#C2410C"/>
            <!-- Staff (Danda) & Dasbodh Symbol -->
            <line x1="65" y1="90" x2="65" y2="185" stroke="#78350F" stroke-width="4"/>
            <rect x="90" y="145" width="28" height="22" rx="2" fill="#FEF3C7" stroke="#991B1B" stroke-width="1.5"/>
            <line x1="95" y1="152" x2="113" y2="152" stroke="#991B1B" stroke-width="1.5"/>
            <line x1="95" y1="158" x2="110" y2="158" stroke="#991B1B" stroke-width="1.5"/>
        """,
    },
    "history/baji_prabhu_deshpande": {
        "title": "Baji Prabhu Deshpande",
        "bg_grad": ("#7F1D1D", "#450A0A"),
        "role": "Hero of Ghodkhind",
        "icon_svg": """
            <!-- Warrior Turban & Intrepid Face -->
            <path d="M70,72 Q100,48 130,72 Q135,85 120,92 Q100,94 80,92 Z" fill="#B91C1C" stroke="#7F1D1D" stroke-width="2"/>
            <ellipse cx="100" cy="98" rx="26" ry="29" fill="#FDE68A"/>
            <!-- Warrior Moustache -->
            <path d="M78,106 Q100,118 122,106 Q115,116 100,114 Q85,116 78,106 Z" fill="#111827"/>
            <circle cx="91" cy="95" r="2.5" fill="#111827"/>
            <circle cx="109" cy="95" r="2.5" fill="#111827"/>
            <!-- Armor (Chilkhath) -->
            <path d="M65,128 C75,120 125,120 135,128 L145,185 L55,185 Z" fill="#4B5563" stroke="#374151" stroke-width="2"/>
            <!-- Twin Crossed Dandpatta Swords -->
            <line x1="60" y1="140" x2="140" y2="175" stroke="#E5E7EB" stroke-width="3"/>
            <line x1="140" y1="140" x2="60" y2="175" stroke="#E5E7EB" stroke-width="3"/>
            <circle cx="100" cy="157" r="5" fill="#F59E0B" stroke="#B45309" stroke-width="1.5"/>
        """,
    },
    "history/moro_trimbak_pingle": {
        "title": "Moro Trimbak Pingle",
        "bg_grad": ("#854D0E", "#713F12"),
        "role": "First Peshwa & Administrator",
        "icon_svg": """
            <!-- Peshwa Pagadi (Turban) -->
            <path d="M68,75 Q100,45 132,75 Q140,90 125,98 Q100,102 75,98 Z" fill="#CA8A04" stroke="#854D0E" stroke-width="2"/>
            <ellipse cx="100" cy="104" rx="26" ry="28" fill="#FDE68A"/>
            <!-- Moustache & Thoughtful Eyes -->
            <path d="M82,112 Q100,120 118,112 Q100,116 82,112 Z" fill="#374151"/>
            <circle cx="92" cy="102" r="2" fill="#1F2937"/>
            <circle cx="108" cy="102" r="2" fill="#1F2937"/>
            <!-- Royal Ministerial Angarkha -->
            <path d="M68,132 C78,124 122,124 132,132 L145,185 L55,185 Z" fill="#FEF08A" stroke="#EAB308" stroke-width="1.5"/>
            <!-- Royal Mudra (Administrative Seal) -->
            <circle cx="100" cy="158" r="14" fill="#B91C1C" stroke="#FEF08A" stroke-width="2"/>
            <rect x="94" y="152" width="12" height="12" fill="none" stroke="#FEF08A" stroke-width="1.5"/>
        """,
    },

    # ── Mathematics Personas ───────────────────────────────────────────────────
    "mathematics/pythagoras": {
        "title": "Pythagoras",
        "bg_grad": ("#1E3A8A", "#172554"),
        "role": "Right-Angle Geometry Guide",
        "icon_svg": """
            <!-- Classical Greek Philosopher Profile & Beard -->
            <ellipse cx="100" cy="90" rx="26" ry="28" fill="#FDE68A"/>
            <path d="M78,98 Q100,135 122,98 Q115,125 100,130 Q85,125 78,98 Z" fill="#F5F5F4"/>
            <!-- Olive Wreath (Laurel) -->
            <path d="M75,76 Q100,60 125,76" stroke="#16A34A" stroke-width="3" fill="none" stroke-linecap="round"/>
            <circle cx="92" cy="88" r="2.5" fill="#1E293B"/>
            <circle cx="108" cy="88" r="2.5" fill="#1E293B"/>
            <!-- Toga -->
            <path d="M68,126 C80,118 120,118 132,126 L145,185 L55,185 Z" fill="#F8FAFC" stroke="#94A3B8" stroke-width="1.5"/>
            <!-- Iconic Right-Angle Triangle with squares (a² + b² = c²) -->
            <polygon points="85,170 120,170 120,145" fill="#3B82F6" stroke="#60A5FA" stroke-width="2"/>
            <rect x="114" y="164" width="6" height="6" fill="none" stroke="#F8FAFC" stroke-width="1"/>
        """,
    },
    "mathematics/apollonius": {
        "title": "Apollonius of Perga",
        "bg_grad": ("#0369A1", "#0C4A6E"),
        "role": "Conics & Proof Guide",
        "icon_svg": """
            <!-- Greek Scholar with Scroll & Geometric Compass -->
            <ellipse cx="100" cy="90" rx="25" ry="28" fill="#FDE68A"/>
            <path d="M78,96 Q100,126 122,96 Q100,120 78,96 Z" fill="#E2E8F0"/>
            <circle cx="92" cy="88" r="2" fill="#0F172A"/>
            <circle cx="108" cy="88" r="2" fill="#0F172A"/>
            <!-- Blue Toga -->
            <path d="M68,125 C80,116 120,116 132,125 L145,185 L55,185 Z" fill="#0284C7"/>
            <!-- Apollonian Circles Symbol -->
            <circle cx="92" cy="155" r="12" fill="none" stroke="#BAE6FD" stroke-width="2"/>
            <circle cx="108" cy="155" r="8" fill="none" stroke="#FDE047" stroke-width="1.5"/>
        """,
    },
    "mathematics/similarity_coach": {
        "title": "Similarity Coach",
        "bg_grad": ("#2563EB", "#1D4ED8"),
        "role": "Triangle & Ratio Mentor",
        "icon_svg": """
            <!-- Two Nested Similar Triangles with Ratio Symbols -->
            <polygon points="100,45 155,145 45,145" fill="#3B82F6" opacity="0.4" stroke="#93C5FD" stroke-width="2"/>
            <polygon points="100,75 135,135 65,135" fill="#60A5FA" stroke="#FFFFFF" stroke-width="2.5"/>
            <!-- Corresponding Angle Markers -->
            <path d="M96,85 A5,5 0 0,0 104,85" stroke="#FDE047" stroke-width="2" fill="none"/>
            <circle cx="100" cy="165" r="16" fill="#1E40AF" stroke="#BFDBFE" stroke-width="2"/>
            <text x="100" y="171" font-family="sans-serif" font-size="16" font-weight="bold" fill="#FFFFFF" text-anchor="middle">~</text>
        """,
    },
    "mathematics/geometry_proof_coach": {
        "title": "Geometry Proof Coach",
        "bg_grad": ("#4338CA", "#312E81"),
        "role": "Deductive Proofs & Logic",
        "icon_svg": """
            <!-- Blueprint Grid & Drafting Compass -->
            <circle cx="100" cy="85" r="40" fill="#3730A3" stroke="#818CF8" stroke-width="1.5" stroke-dasharray="3,3"/>
            <!-- Drafting Compass Instrument -->
            <line x1="100" y1="50" x2="80" y2="115" stroke="#E0E7FF" stroke-width="3"/>
            <line x1="100" y1="50" x2="120" y2="115" stroke="#E0E7FF" stroke-width="3"/>
            <circle cx="100" cy="50" r="5" fill="#FCD34D"/>
            <!-- Q.E.D. / Axiom Badge -->
            <rect x="75" y="145" width="50" height="22" rx="4" fill="#4F46E5" stroke="#A5B4FC" stroke-width="1.5"/>
            <text x="100" y="161" font-family="monospace" font-size="11" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Q.E.D.</text>
        """,
    },
    "mathematics/circle_geometry_coach": {
        "title": "Circle Geometry Coach",
        "bg_grad": ("#0D9488", "#115E59"),
        "role": "Tangents & Chords Specialist",
        "icon_svg": """
            <!-- Geometric Circle with Tangent and Radius -->
            <circle cx="100" cy="95" r="45" fill="#134E4A" stroke="#5EEAD4" stroke-width="2.5"/>
            <!-- Center Point & Radius Line -->
            <circle cx="100" cy="95" r="3.5" fill="#FDE047"/>
            <line x1="100" y1="95" x2="132" y2="127" stroke="#FDE047" stroke-width="2"/>
            <!-- Tangent Line at Contact Point -->
            <line x1="90" y1="165" x2="165" y2="90" stroke="#F43F5E" stroke-width="2.5"/>
            <!-- Chord Line -->
            <line x1="60" y1="115" x2="125" y2="60" stroke="#A7F3D0" stroke-width="2"/>
        """,
    },
    "mathematics/coordinate_geometry_coach": {
        "title": "Coordinate Geometry Coach",
        "bg_grad": ("#475569", "#1E293B"),
        "role": "Grid & Slope Specialist",
        "icon_svg": """
            <!-- Cartesian Grid Plane -->
            <rect x="55" y="55" width="90" height="90" fill="#0F172A" rx="4" stroke="#64748B" stroke-width="1.5"/>
            <line x1="55" y1="100" x2="145" y2="100" stroke="#94A3B8" stroke-width="2"/>
            <line x1="100" y1="55" x2="100" y2="145" stroke="#94A3B8" stroke-width="2"/>
            <!-- Plotted Points and Linear Vector -->
            <line x1="70" y1="130" x2="130" y2="70" stroke="#38BDF8" stroke-width="2.5"/>
            <circle cx="70" cy="130" r="4" fill="#F43F5E" stroke="#FFFFFF" stroke-width="1"/>
            <circle cx="130" cy="70" r="4" fill="#10B981" stroke="#FFFFFF" stroke-width="1"/>
            <text x="100" y="168" font-family="monospace" font-size="10" fill="#94A3B8" text-anchor="middle">(x₂, y₂)</text>
        """,
    },
    "mathematics/trigonometry_coach": {
        "title": "Trigonometry Coach",
        "bg_grad": ("#7C3AED", "#5B21B6"),
        "role": "Sin/Cos/Tan Studio Guide",
        "icon_svg": """
            <!-- Unit Circle with Sine Wave Curve -->
            <circle cx="85" cy="100" r="35" fill="none" stroke="#C4B5FD" stroke-width="2"/>
            <line x1="50" y1="100" x2="120" y2="100" stroke="#A78BFA" stroke-width="1.5"/>
            <line x1="85" y1="65" x2="85" y2="135" stroke="#A78BFA" stroke-width="1.5"/>
            <!-- Theta Angle Arc -->
            <line x1="85" y1="100" x2="115" y2="75" stroke="#FDE047" stroke-width="2.5"/>
            <path d="M125,75 Q135,100 145,125 T165,125" stroke="#34D399" stroke-width="2.5" fill="none"/>
            <!-- Greek Theta Symbol Badge -->
            <circle cx="100" cy="162" r="14" fill="#4C1D95" stroke="#DDD6FE" stroke-width="1.5"/>
            <text x="100" y="168" font-family="serif" font-size="16" fill="#FDE047" text-anchor="middle">θ</text>
        """,
    },
    "mathematics/mensuration_coach": {
        "title": "Mensuration Coach",
        "bg_grad": ("#059669", "#065F46"),
        "role": "Area & Volume Studio Guide",
        "icon_svg": """
            <!-- 3D Solid Shapes: Cylinder & Cone -->
            <!-- Cylinder -->
            <ellipse cx="85" cy="80" rx="18" ry="7" fill="#6EE7B7" stroke="#047857" stroke-width="1.5"/>
            <rect x="67" y="80" width="36" height="35" fill="#34D399" stroke="#047857" stroke-width="1.5"/>
            <ellipse cx="85" cy="115" rx="18" ry="7" fill="#10B981" stroke="#047857" stroke-width="1.5"/>
            <!-- Sphere -->
            <circle cx="125" cy="100" r="18" fill="#10B981" stroke="#047857" stroke-width="1.5"/>
            <ellipse cx="125" cy="100" rx="18" ry="6" fill="none" stroke="#A7F3D0" stroke-width="1" stroke-dasharray="2,2"/>
            <!-- Volume Formula Badge -->
            <rect x="70" y="148" width="60" height="20" rx="3" fill="#064E3B" stroke="#6EE7B7" stroke-width="1"/>
            <text x="100" y="162" font-family="sans-serif" font-size="11" font-weight="bold" fill="#FFFFFF" text-anchor="middle">πr²h</text>
        """,
    },

    # ── EVS Personas ───────────────────────────────────────────────────────────
    "evs/charles_darwin": {
        "title": "Charles Darwin",
        "bg_grad": ("#065F46", "#064E3B"),
        "role": "Naturalist & Evolution Guide",
        "icon_svg": """
            <!-- Naturalist with Iconic Beard & Observation Notebook -->
            <ellipse cx="100" cy="85" rx="25" ry="27" fill="#FDE68A"/>
            <!-- Bushy White Hair & Full Beard -->
            <path d="M74,75 Q100,60 126,75 Q135,115 125,145 Q100,155 75,145 Q65,115 74,75 Z" fill="#F5F5F4" stroke="#E7E5E4" stroke-width="1"/>
            <circle cx="92" cy="85" r="2.5" fill="#1F2937"/>
            <circle cx="108" cy="85" r="2.5" fill="#1F2937"/>
            <!-- Victorian Coat -->
            <path d="M68,132 C78,124 122,124 132,132 L145,185 L55,185 Z" fill="#1E293B"/>
            <!-- Darwin's Finches / Tree of Life sketch icon -->
            <circle cx="100" cy="162" r="13" fill="#047857" stroke="#A7F3D0" stroke-width="1.5"/>
            <path d="M100,172 L100,155 M100,162 L94,156 M100,162 L106,156" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/>
        """,
    },
    "evs/carl_linnaeus": {
        "title": "Carl Linnaeus",
        "bg_grad": ("#15803D", "#166534"),
        "role": "Botanist & Taxonomy Guide",
        "icon_svg": """
            <!-- 18th-century Peruke Wig & Botany Specimen -->
            <path d="M72,70 Q100,50 128,70 Q138,100 128,115 Q100,118 72,115 Z" fill="#E2E8F0" stroke="#CBD5E1" stroke-width="1.5"/>
            <ellipse cx="100" cy="95" rx="24" ry="26" fill="#FDE68A"/>
            <circle cx="92" cy="92" r="2" fill="#1E293B"/>
            <circle cx="108" cy="92" r="2" fill="#1E293B"/>
            <!-- 18th Century Frock Coat -->
            <path d="M68,128 C78,120 122,120 132,128 L145,185 L55,185 Z" fill="#14532D"/>
            <!-- Linnaea Borealis (Twinflower) Herbarium Flower -->
            <path d="M100,170 Q100,150 93,142 Q100,150 107,142" stroke="#FDE047" stroke-width="2" fill="none"/>
            <circle cx="93" cy="142" r="3" fill="#F472B6"/>
            <circle cx="107" cy="142" r="3" fill="#F472B6"/>
        """,
    },
    "evs/louis_leakey": {
        "title": "Louis Leakey",
        "bg_grad": ("#B45309", "#78350F"),
        "role": "Olduvai Paleontologist",
        "icon_svg": """
            <!-- Safari Expedition Hat & Fossil Explorer -->
            <ellipse cx="100" cy="70" rx="36" ry="12" fill="#D97706" stroke="#92400E" stroke-width="1.5"/>
            <rect x="78" y="52" width="44" height="20" rx="3" fill="#B45309"/>
            <ellipse cx="100" cy="95" rx="25" ry="27" fill="#FDE68A"/>
            <circle cx="91" cy="92" r="2.5" fill="#292524"/>
            <circle cx="109" cy="92" r="2.5" fill="#292524"/>
            <!-- Field Khaki Shirt -->
            <path d="M68,126 C78,118 122,118 132,126 L145,185 L55,185 Z" fill="#D97706"/>
            <!-- Homo Habilis Fossil Skull Specimen -->
            <path d="M90,152 C90,140 110,140 110,152 C110,162 105,166 100,166 C95,166 90,162 90,152 Z" fill="#FEF3C7" stroke="#78350F" stroke-width="1.5"/>
            <circle cx="96" cy="150" r="1.5" fill="#78350F"/>
            <circle cx="104" cy="150" r="1.5" fill="#78350F"/>
        """,
    },
    "evs/christian_thomsen": {
        "title": "Christian Thomsen",
        "bg_grad": ("#78350F", "#451A03"),
        "role": "Curator & Three-Age System",
        "icon_svg": """
            <!-- Classical Scholar with Stone, Bronze, Iron artifacts -->
            <ellipse cx="100" cy="85" rx="25" ry="27" fill="#FDE68A"/>
            <circle cx="92" cy="83" r="2" fill="#1C1917"/>
            <circle cx="108" cy="83" r="2" fill="#1C1917"/>
            <path d="M78,75 Q100,62 122,75" stroke="#78716C" stroke-width="2" fill="none"/>
            <!-- Museum Curator Coat -->
            <path d="M68,124 C78,116 122,116 132,124 L145,185 L55,185 Z" fill="#292524"/>
            <!-- Three-Age System Badges: Stone, Bronze, Iron -->
            <circle cx="75" cy="155" r="9" fill="#A8A29E" stroke="#57534E" stroke-width="1.5" title="Stone"/>
            <circle cx="100" cy="155" r="9" fill="#D97706" stroke="#92400E" stroke-width="1.5" title="Bronze"/>
            <circle cx="125" cy="155" r="9" fill="#475569" stroke="#1E293B" stroke-width="1.5" title="Iron"/>
        """,
    },
    "evs/archaeologist": {
        "title": "Archaeologist",
        "bg_grad": ("#92400E", "#713F12"),
        "role": "Field Excavation Specialist",
        "icon_svg": """
            <!-- Trowel, Stratigraphy & Ancient Pottery Sherd -->
            <circle cx="100" cy="90" r="35" fill="#B45309" opacity="0.3"/>
            <!-- Excavation Trowel -->
            <path d="M100,55 L115,85 L100,105 L85,85 Z" fill="#CBD5E1" stroke="#475569" stroke-width="2"/>
            <rect x="97" y="105" width="6" height="25" rx="2" fill="#78350F"/>
            <!-- Terracotta Ancient Pot Fragment -->
            <path d="M80,150 Q100,135 120,150 Q125,170 100,172 Q75,170 80,150 Z" fill="#EA580C" stroke="#9A3412" stroke-width="2"/>
            <line x1="88" y1="156" x2="112" y2="156" stroke="#FED7AA" stroke-width="1.5"/>
        """,
    },
    "evs/human_evolution_scientist": {
        "title": "Human-Evolution Scientist",
        "bg_grad": ("#047857", "#064E3B"),
        "role": "Anthropology & Fossil Specialist",
        "icon_svg": """
            <!-- DNA Double Helix & Fossil Cranium -->
            <!-- DNA Helix Ribbon -->
            <path d="M60,60 Q80,75 100,60 T140,60" fill="none" stroke="#6EE7B7" stroke-width="3"/>
            <path d="M60,75 Q80,60 100,75 T140,75" fill="none" stroke="#38BDF8" stroke-width="3"/>
            <line x1="80" y1="67" x2="80" y2="68" stroke="#FDE047" stroke-width="3"/>
            <line x1="120" y1="67" x2="120" y2="68" stroke="#FDE047" stroke-width="3"/>
            <!-- Calipers Measuring Tool -->
            <path d="M82,105 L100,135 L118,105" fill="none" stroke="#E2E8F0" stroke-width="2.5"/>
            <!-- Evolutionary Skull Silhouette -->
            <circle cx="100" cy="155" r="16" fill="#047857" stroke="#A7F3D0" stroke-width="1.5"/>
            <path d="M93,153 A3,3 0 0,0 99,153" stroke="#A7F3D0" stroke-width="1.5" fill="none"/>
        """,
    },
    "evs/prehistoric_life_guide": {
        "title": "Prehistoric-Life Guide",
        "bg_grad": ("#78350F", "#451A03"),
        "role": "Stone Tools & Settlement Guide",
        "icon_svg": """
            <!-- Flint Microlith Handaxe & Thatch Shelter -->
            <!-- Stone Handaxe (Flint tool) -->
            <polygon points="100,45 120,95 105,125 95,125 80,95" fill="#78716C" stroke="#44403C" stroke-width="2"/>
            <line x1="100" y1="45" x2="100" y2="120" stroke="#A8A29E" stroke-width="1.5"/>
            <!-- Primitive Thatch Shelter (Neolithic Hut) -->
            <polygon points="100,135 135,175 65,175" fill="#B45309" stroke="#78350F" stroke-width="2"/>
            <rect x="94" y="155" width="12" height="20" fill="#451A03"/>
        """,
    },
    "evs/ancient_civilization_guide": {
        "title": "Ancient-Civilization Guide",
        "bg_grad": ("#B45309", "#854D0E"),
        "role": "River Valleys & Cities Guide",
        "icon_svg": """
            <!-- Harappan Brick Ramparts, Potter's Wheel & River -->
            <!-- Wavy River Curve -->
            <path d="M45,75 C75,55 125,95 155,75" stroke="#38BDF8" stroke-width="4" fill="none"/>
            <!-- Ancient City Brick Wall -->
            <rect x="65" y="100" width="70" height="35" rx="2" fill="#C2410C" stroke="#9A3412" stroke-width="2"/>
            <line x1="65" y1="112" x2="135" y2="112" stroke="#FED7AA" stroke-width="1"/>
            <line x1="65" y1="124" x2="135" y2="124" stroke="#FED7AA" stroke-width="1"/>
            <!-- Potter's Wheel Disk -->
            <ellipse cx="100" cy="158" rx="22" ry="8" fill="#78350F" stroke="#FDE68A" stroke-width="2"/>
            <circle cx="100" cy="158" r="3" fill="#FDE68A"/>
        """,
    },
}


def build_svg(info: dict) -> str:
    grad_from, grad_to = info["bg_grad"]
    title = info["title"]
    role = info["role"]
    icon_content = info["icon_svg"]

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <defs>
    <linearGradient id="bg_grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{grad_from}" />
      <stop offset="100%" stop-color="{grad_to}" />
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.35"/>
    </filter>
  </defs>

  <!-- Outer Ring and Background Circle -->
  <circle cx="100" cy="100" r="96" fill="url(#bg_grad)" stroke="#FFFFFF" stroke-width="4" filter="url(#shadow)"/>
  <circle cx="100" cy="100" r="91" fill="none" stroke="rgba(255,255,255,0.25)" stroke-width="1.5"/>

  <!-- Character / Educational Graphic Layer -->
  <g id="illustration">
    {icon_content}
  </g>

  <!-- Bottom Identity Pill Badge -->
  <g transform="translate(100, 182)">
    <rect x="-70" y="-12" width="140" height="18" rx="9" fill="rgba(15, 23, 42, 0.88)" stroke="rgba(255,255,255,0.4)" stroke-width="1"/>
    <text x="0" y="0.5" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="8.5" font-weight="700" fill="#FFFFFF" text-anchor="middle" dominant-baseline="central" letter-spacing="0.3">{role}</text>
  </g>
</svg>
"""


def main():
    for rel_path, info in AVATARS.items():
        out_file = AVATARS_BASE / f"{rel_path}.svg"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        svg_content = build_svg(info)
        out_file.write_text(svg_content.strip(), encoding="utf-8")
        print(f"Generated: {out_file}")

    print(f"\nSuccessfully generated all {len(AVATARS)} SVG avatars!")


if __name__ == "__main__":
    main()
