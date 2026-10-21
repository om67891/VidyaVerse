"""
Structured Curriculum Learning Maps & Learning Moments Engine.
Unified across:
- History (Std IV Shivachhatrapati, 18 lessons)
- Mathematics (Std X Part II, 7 chapters)
- Environmental Studies (Std V How We Came to Be, 10 chapters)

Provides:
- Stable learning moments (`moment_id`) with clear completion conditions
- "Moments you've explored" progress tracking
- Chapter objectives, core facts, and structured progression
"""
from __future__ import annotations

import re
from typing import Optional
from pydantic import BaseModel, Field

from backend.services.history_map import HISTORY_LEARNING_MAP


# ── Schemas ────────────────────────────────────────────────────────────────────


class LearningMoment(BaseModel):
    moment_id: str
    subject_id: str
    chapter_id: str
    chapter_number: int
    title: str
    summary: str
    key_concepts: list[str] = []
    format_type: str = "explanation"  # "story" | "explanation" | "figure" | "timeline" | "cause_effect" | "comparison" | "worked_solution" | "quiz" | "recap"
    book_page: int = 1
    completion_condition: str = "viewed_explanation"
    action_options: list[str] = []


class ChapterLearningMap(BaseModel):
    subject_id: str
    chapter_id: str
    chapter_number: int
    chapter_title: str
    learning_objectives: list[str] = []
    key_facts: list[str] = []
    moments: list[LearningMoment] = []


# ── Mathematics Standard X Learning Maps ──────────────────────────────────────

MATH_LEARNING_MAPS: dict[str, ChapterLearningMap] = {
    "mathematics_chapter_01": ChapterLearningMap(
        subject_id="mathematics",
        chapter_id="mathematics_chapter_01",
        chapter_number=1,
        chapter_title="Similarity",
        learning_objectives=[
            "Understand ratio of areas of two triangles with equal bases or heights.",
            "Master the Basic Proportionality Theorem (Thales Theorem) and its converse.",
            "Apply the angle bisector property and property of three parallel lines.",
            "Identify similar triangles using AAA, SAS, and SSS similarity tests.",
            "Apply the theorem of areas of similar triangles: ratio = (s1/s2)^2.",
        ],
        key_facts=[
            "Ratio of areas of two triangles is equal to the ratio of products of their bases and corresponding heights: (A1/A2) = (b1*h1)/(b2*h2).",
            "Areas of triangles with equal heights are proportional to their corresponding bases: (A1/A2) = b1/b2.",
            "Basic Proportionality Theorem: If a line parallel to a side of a triangle intersects other two sides, it divides them in the same ratio: AP/PB = AQ/QC.",
            "Theorem of Areas of Similar Triangles: When two triangles are similar, the ratio of their areas is equal to the ratio of the squares of their corresponding sides.",
        ],
        moments=[
            LearningMoment(
                moment_id="MATH_CH01_M01",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_01",
                chapter_number=1,
                title="Ratio of Areas of Two Triangles",
                summary="The fundamental ratio (b1*h1)/(b2*h2) and conditions when bases or heights are equal.",
                key_concepts=["Area ratio", "Equal height", "Equal base"],
                format_type="worked_solution",
                book_page=1,
                action_options=["See equal height example", "Explore Basic Proportionality", "Try practice problem"],
            ),
            LearningMoment(
                moment_id="MATH_CH01_M02",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_01",
                chapter_number=1,
                title="Basic Proportionality Theorem (BPT)",
                summary="A line parallel to one side dividing the other two sides in the same ratio: AP/PB = AQ/QC.",
                key_concepts=["Parallel line", "Thales Theorem", "Proportion"],
                format_type="explanation",
                book_page=7,
                action_options=["See converse of BPT", "Examine proof steps", "Try BPT calculation"],
            ),
            LearningMoment(
                moment_id="MATH_CH01_M03",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_01",
                chapter_number=1,
                title="Property of Angle Bisector of a Triangle",
                summary="The bisector of an angle of a triangle divides the side opposite to the angle in the ratio of the remaining sides.",
                key_concepts=["Angle bisector", "Ratio of sides"],
                format_type="explanation",
                book_page=8,
                action_options=["Angle bisector example", "Property of 3 parallel lines", "Check understanding"],
            ),
            LearningMoment(
                moment_id="MATH_CH01_M04",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_01",
                chapter_number=1,
                title="Property of Three Parallel Lines and Transversals",
                summary="The ratio of intercepts made on one transversal by three parallel lines equals the ratio on any other transversal: AB/BC = PQ/QR.",
                key_concepts=["Parallel lines", "Transversal", "Intercept ratio"],
                format_type="worked_solution",
                book_page=10,
                action_options=["See transversal diagram", "Explore similarity tests", "Practice question"],
            ),
            LearningMoment(
                moment_id="MATH_CH01_M05",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_01",
                chapter_number=1,
                title="Tests of Similarity of Triangles (AAA, SAS, SSS)",
                summary="Sufficient criteria to establish that two triangles have equal angles and proportional sides.",
                key_concepts=["AAA test", "SAS test", "SSS test"],
                format_type="comparison",
                book_page=15,
                action_options=["Compare congruence vs similarity", "See SAS example", "Check criteria"],
            ),
            LearningMoment(
                moment_id="MATH_CH01_M06",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_01",
                chapter_number=1,
                title="Theorem of Areas of Similar Triangles",
                summary="If triangle ABC ~ triangle PQR, then Area(ABC) / Area(PQR) = AB^2 / PQ^2 = BC^2 / QR^2.",
                key_concepts=["Similar triangle area", "Square of sides ratio"],
                format_type="worked_solution",
                book_page=23,
                action_options=["Solve area ratio problem", "Chapter summary", "Take similarity quiz"],
            ),
        ],
    ),
    "mathematics_chapter_02": ChapterLearningMap(
        subject_id="mathematics",
        chapter_id="mathematics_chapter_02",
        chapter_number=2,
        chapter_title="Pythagoras Theorem",
        learning_objectives=[
            "Understand similarity in right-angled triangles.",
            "Master the Theorem of Geometric Mean.",
            "State and prove Pythagoras Theorem: c^2 = a^2 + b^2.",
            "Verify Pythagorean triplets and acute/obtuse triangle conditions.",
            "Apply 30°-60°-90° and 45°-45°-90° properties.",
            "Solve median lengths using Apollonius Theorem.",
        ],
        key_facts=[
            "In a right-angled triangle, the square of the hypotenuse is equal to the sum of the squares of the remaining two sides: c^2 = a^2 + b^2.",
            "Theorem of Geometric Mean: In a right-angled triangle, the perpendicular segment to the hypotenuse from opposite vertex is the geometric mean of the segments into which the hypotenuse is divided: BD^2 = AD * DC.",
            "30°-60°-90° Theorem: Side opposite 30° is 1/2 of hypotenuse, side opposite 60° is (sqrt(3)/2) of hypotenuse.",
            "45°-45°-90° Theorem: Each perpendicular side is (1/sqrt(2)) of hypotenuse.",
            "Apollonius Theorem: In triangle ABC if M is midpoint of BC, then AB^2 + AC^2 = 2 AM^2 + 2 BM^2.",
        ],
        moments=[
            LearningMoment(
                moment_id="MATH_CH02_M01",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_02",
                chapter_number=2,
                title="Similarity in Right-Angled Triangles",
                summary="When an altitude is drawn to the hypotenuse, the two smaller triangles are similar to each other and to the original triangle.",
                key_concepts=["Right triangle similarity", "Altitude to hypotenuse"],
                format_type="explanation",
                book_page=31,
                action_options=["Explore geometric mean", "See altitude diagram", "Check understanding"],
            ),
            LearningMoment(
                moment_id="MATH_CH02_M02",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_02",
                chapter_number=2,
                title="Theorem of Geometric Mean",
                summary="The altitude to the hypotenuse is the geometric mean: BD = sqrt(AD * DC).",
                key_concepts=["Geometric mean", "Altitude BD"],
                format_type="worked_solution",
                book_page=33,
                action_options=["Calculate altitude", "Explore Pythagoras proof", "Try example"],
            ),
            LearningMoment(
                moment_id="MATH_CH02_M03",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_02",
                chapter_number=2,
                title="Pythagoras Theorem (Statement & Proof)",
                summary="In a right-angled triangle, hypotenuse^2 = base^2 + height^2. Proved using similarity.",
                key_concepts=["c^2 = a^2 + b^2", "Proof by similarity"],
                format_type="worked_solution",
                book_page=34,
                action_options=["See step-by-step proof", "Verify a triplet", "Converse of Pythagoras"],
            ),
            LearningMoment(
                moment_id="MATH_CH02_M04",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_02",
                chapter_number=2,
                title="Converse of Pythagoras Theorem",
                summary="If the square of one side of a triangle equals the sum of squares of other two sides, the triangle is right-angled.",
                key_concepts=["Converse", "Right angle identification"],
                format_type="explanation",
                book_page=35,
                action_options=["Check triplet", "Explore 30-60-90 rules", "Acute/obtuse test"],
            ),
            LearningMoment(
                moment_id="MATH_CH02_M05",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_02",
                chapter_number=2,
                title="30°-60°-90° and 45°-45°-90° Triangle Theorems",
                summary="Special right triangles: side opp 30° is 1/2 hypotenuse; side opp 60° is (sqrt(3)/2) hypotenuse; side opp 45° is (1/sqrt(2)) hypotenuse.",
                key_concepts=["30-60-90", "45-45-90", "Special ratios"],
                format_type="worked_solution",
                book_page=36,
                action_options=["Calculate with 30-60-90", "Explore Apollonius Theorem", "Practice question"],
            ),
            LearningMoment(
                moment_id="MATH_CH02_M06",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_02",
                chapter_number=2,
                title="Apollonius Theorem (Median of Triangle)",
                summary="Relates triangle sides to median: AB^2 + AC^2 = 2(AM^2 + BM^2).",
                key_concepts=["Apollonius Theorem", "Median length AM"],
                format_type="worked_solution",
                book_page=40,
                action_options=["Solve median example", "Chapter recap", "Take Pythagoras quiz"],
            ),
        ],
    ),
    "mathematics_chapter_03": ChapterLearningMap(
        subject_id="mathematics",
        chapter_id="mathematics_chapter_03",
        chapter_number=3,
        chapter_title="Circle",
        learning_objectives=[
            "Understand tangent theorem and its converse.",
            "Prove tangent segment theorem: tangents from an external point are congruent.",
            "Classify touching circles (externally touching and internally touching).",
            "Relate central angle, arc measure, and inscribed angle theorem.",
            "Understand cyclic quadrilaterals and tangent secant theorem.",
        ],
        key_facts=[
            "Tangent at any point of a circle is perpendicular to the radius through the point of contact.",
            "Length of tangent segments drawn from an external point to a circle are equal.",
            "Inscribed Angle Theorem: The measure of an inscribed angle is half the measure of the arc intercepted by it.",
            "Opposite angles of a cyclic quadrilateral are supplementary (sum = 180°).",
        ],
        moments=[
            LearningMoment(
                moment_id="MATH_CH03_M01",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_03",
                chapter_number=3,
                title="Tangent Theorem & Radius Perpendicularity",
                summary="Radius to tangent point forms a 90° angle.",
                key_concepts=["Tangent theorem", "Perpendicular radius"],
                format_type="explanation",
                book_page=51,
                action_options=["Explore tangent segment theorem", "See diagram", "Check concept"],
            ),
            LearningMoment(
                moment_id="MATH_CH03_M02",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_03",
                chapter_number=3,
                title="Tangent Segment Theorem",
                summary="Tangent segments drawn from an external point to a circle are congruent.",
                key_concepts=["External point", "Congruent tangents"],
                format_type="worked_solution",
                book_page=53,
                action_options=["See proof", "Touching circles", "Practice problem"],
            ),
            LearningMoment(
                moment_id="MATH_CH03_M03",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_03",
                chapter_number=3,
                title="Touching Circles (Internal & External)",
                summary="Centers and point of contact are collinear. Distance between centers is r1+r2 (external) or r1-r2 (internal).",
                key_concepts=["Touching circles", "Collinear centers"],
                format_type="comparison",
                book_page=58,
                action_options=["Calculate center distance", "Inscribed angle theorem", "Check understanding"],
            ),
            LearningMoment(
                moment_id="MATH_CH03_M04",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_03",
                chapter_number=3,
                title="Inscribed Angle Theorem",
                summary="Angle subtended by an arc at the circumference is half the angle at the center.",
                key_concepts=["Inscribed angle", "Intercepted arc"],
                format_type="worked_solution",
                book_page=66,
                action_options=["Angle calculation", "Cyclic quadrilateral theorem", "Practice problem"],
            ),
            LearningMoment(
                moment_id="MATH_CH03_M05",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_03",
                chapter_number=3,
                title="Cyclic Quadrilateral Theorem",
                summary="Opposite angles of a cyclic quadrilateral are supplementary: A + C = 180° and B + D = 180°.",
                key_concepts=["Cyclic quadrilateral", "Supplementary opposite angles"],
                format_type="worked_solution",
                book_page=68,
                action_options=["Solve cyclic angle problem", "Chapter summary", "Take Circle quiz"],
            ),
        ],
    ),
    "mathematics_chapter_05": ChapterLearningMap(
        subject_id="mathematics",
        chapter_id="mathematics_chapter_05",
        chapter_number=5,
        chapter_title="Co-ordinate Geometry",
        learning_objectives=[
            "Calculate distance between two points: d = sqrt((x2-x1)^2 + (y2-y1)^2).",
            "Apply Section Formula for internal division.",
            "Use Midpoint and Centroid formulas.",
            "Calculate slope of a line: m = (y2-y1)/(x2-x1).",
            "Test collinearity using slope.",
        ],
        key_facts=[
            "Distance Formula: d = sqrt((x2 - x1)^2 + (y2 - y1)^2).",
            "Section Formula: P(x, y) dividing AB in ratio m:n has coordinates ((m*x2 + n*x1)/(m+n), (m*y2 + n*y1)/(m+n)).",
            "Midpoint Formula: M = ((x1+x2)/2, (y1+y2)/2).",
            "Slope of line passing through (x1, y1) and (x2, y2): m = (y2 - y1) / (x2 - x1).",
        ],
        moments=[
            LearningMoment(
                moment_id="MATH_CH05_M01",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_05",
                chapter_number=5,
                title="Distance Formula",
                summary="Distance between points (x1, y1) and (x2, y2): d = sqrt((x2-x1)^2 + (y2-y1)^2).",
                key_concepts=["Distance formula", "Coordinate distance"],
                format_type="worked_solution",
                book_page=101,
                action_options=["Calculate distance", "Explore section formula", "Practice example"],
            ),
            LearningMoment(
                moment_id="MATH_CH05_M02",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_05",
                chapter_number=5,
                title="Section Formula & Midpoint",
                summary="Coordinates of point dividing a segment in ratio m:n; midpoint when m=n=1.",
                key_concepts=["Section formula", "Midpoint formula"],
                format_type="worked_solution",
                book_page=109,
                action_options=["Find midpoint", "Explore slope of a line", "Try section calculation"],
            ),
            LearningMoment(
                moment_id="MATH_CH05_M03",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_05",
                chapter_number=5,
                title="Slope of a Line & Collinearity",
                summary="m = tan(theta) = (y2-y1)/(x2-x1). Three points A, B, C are collinear if slope(AB) = slope(BC).",
                key_concepts=["Slope m", "Collinearity", "Parallel lines"],
                format_type="worked_solution",
                book_page=118,
                action_options=["Test collinearity", "Chapter summary", "Take Co-ordinate Geometry quiz"],
            ),
        ],
    ),
    "mathematics_chapter_06": ChapterLearningMap(
        subject_id="mathematics",
        chapter_id="mathematics_chapter_06",
        chapter_number=6,
        chapter_title="Trigonometry",
        learning_objectives=[
            "Define sin, cos, tan, cosec, sec, and cot ratios.",
            "Verify fundamental trigonometric identities.",
            "Evaluate standard angles: 0°, 30°, 45°, 60°, 90°.",
            "Solve real-world heights and distances problems using angles of elevation and depression.",
        ],
        key_facts=[
            "Fundamental Identity: sin^2(theta) + cos^2(theta) = 1.",
            "Secant Identity: 1 + tan^2(theta) = sec^2(theta).",
            "Cosecant Identity: 1 + cot^2(theta) = cosec^2(theta).",
            "Angle of Elevation: Angle between line of sight and horizontal line when viewing an object above horizontal.",
        ],
        moments=[
            LearningMoment(
                moment_id="MATH_CH06_M01",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_06",
                chapter_number=6,
                title="Trigonometric Ratios & Relations",
                summary="Definitions of sin, cos, tan, sec, cosec, cot in terms of opposite, adjacent, and hypotenuse.",
                key_concepts=["sin", "cos", "tan", "sec", "cosec", "cot"],
                format_type="explanation",
                book_page=125,
                action_options=["See standard angle table", "Explore identities", "Practice ratios"],
            ),
            LearningMoment(
                moment_id="MATH_CH06_M02",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_06",
                chapter_number=6,
                title="Fundamental Trigonometric Identities",
                summary="Proving and applying sin^2 + cos^2 = 1, 1 + tan^2 = sec^2, and 1 + cot^2 = cosec^2.",
                key_concepts=["sin^2+cos^2=1", "Identities proof"],
                format_type="worked_solution",
                book_page=128,
                action_options=["Prove identity", "Explore elevation/depression", "Try practice problem"],
            ),
            LearningMoment(
                moment_id="MATH_CH06_M03",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_06",
                chapter_number=6,
                title="Heights and Distances (Angles of Elevation & Depression)",
                summary="Solving heights of buildings, trees, and towers using tan(theta) = opposite/adjacent.",
                key_concepts=["Angle of elevation", "Angle of depression", "Height calculation"],
                format_type="worked_solution",
                book_page=133,
                action_options=["Solve tower height problem", "Chapter recap", "Take Trigonometry quiz"],
            ),
        ],
    ),
    "mathematics_chapter_07": ChapterLearningMap(
        subject_id="mathematics",
        chapter_id="mathematics_chapter_07",
        chapter_number=7,
        chapter_title="Mensuration",
        learning_objectives=[
            "Compute volume, CSA, and TSA of cylinder and cone.",
            "Compute sphere and hemisphere surface areas and volumes.",
            "Understand frustum of a cone.",
            "Calculate area of sector and length of arc: A = (theta/360)*pi*r^2.",
        ],
        key_facts=[
            "Cylinder: Volume = pi * r^2 * h, CSA = 2 * pi * r * h, TSA = 2 * pi * r * (r + h).",
            "Cone: Slant height l = sqrt(r^2 + h^2), Volume = (1/3) * pi * r^2 * h, CSA = pi * r * l.",
            "Sphere: Volume = (4/3) * pi * r^3, Surface Area = 4 * pi * r^2.",
            "Sector Area = (theta / 360) * pi * r^2; Arc Length = (theta / 360) * 2 * pi * r.",
        ],
        moments=[
            LearningMoment(
                moment_id="MATH_CH07_M01",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_07",
                chapter_number=7,
                title="Cylinder & Cone (Volume & Surface Area)",
                summary="Formulas for cylinder (pi*r^2*h) and cone (1/3*pi*r^2*h, slant height l=sqrt(r^2+h^2)).",
                key_concepts=["Cylinder", "Cone", "Slant height"],
                format_type="worked_solution",
                book_page=141,
                action_options=["Calculate cone volume", "Explore sphere formulas", "Try cylinder problem"],
            ),
            LearningMoment(
                moment_id="MATH_CH07_M02",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_07",
                chapter_number=7,
                title="Sphere & Hemisphere",
                summary="Sphere Volume = 4/3*pi*r^3, Surface Area = 4*pi*r^2; Hemisphere TSA = 3*pi*r^2.",
                key_concepts=["Sphere", "Hemisphere", "Surface area"],
                format_type="worked_solution",
                book_page=145,
                action_options=["Calculate sphere volume", "Explore circle sectors", "Practice problem"],
            ),
            LearningMoment(
                moment_id="MATH_CH07_M03",
                subject_id="mathematics",
                chapter_id="mathematics_chapter_07",
                chapter_number=7,
                title="Area of Sector & Length of Arc",
                summary="Area = (theta/360)*pi*r^2; Length of arc = (theta/360)*2*pi*r.",
                key_concepts=["Sector area", "Arc length", "Central angle theta"],
                format_type="worked_solution",
                book_page=151,
                action_options=["Solve sector problem", "Chapter summary", "Take Mensuration quiz"],
            ),
        ],
    ),
}


# ── Environmental Studies Learning Maps ───────────────────────────────────────

EVS_LEARNING_MAPS: dict[str, ChapterLearningMap] = {
    "EVS_CH01": ChapterLearningMap(
        subject_id="evs",
        chapter_id="EVS_CH01",
        chapter_number=1,
        chapter_title="What is History?",
        learning_objectives=[
            "Understand that history is a scientific discipline that studies past events.",
            "Learn the scientific method in history: examining evidence and sources.",
            "Differentiate the three sources of history: material, written, and oral.",
            "Understand how past actions determine future developments.",
        ],
        key_facts=[
            "History is a coherent account of past events with the help of evidence.",
            "History uses scientific method to examine whether evidence is genuine and reliable.",
            "Sources of history are of three types: Material sources (coins, pottery, forts), Written sources (inscriptions, books), and Oral sources (folk songs, ballads).",
        ],
        moments=[
            LearningMoment(
                moment_id="EVS_CH01_M01",
                subject_id="evs",
                chapter_id="EVS_CH01",
                chapter_number=1,
                title="History as a Scientific Discipline",
                summary="Why history is not mere storytelling, but a systematic science based on evidence.",
                key_concepts=["Scientific method", "Evidence", "Past events"],
                format_type="explanation",
                book_page=1,
                action_options=["Explore sources of history", "See examples of evidence", "Check understanding"],
            ),
            LearningMoment(
                moment_id="EVS_CH01_M02",
                subject_id="evs",
                chapter_id="EVS_CH01",
                chapter_number=1,
                title="The Three Sources of History",
                summary="Material sources (artefacts, coins), Written sources (copper plates, records), and Oral sources (folk songs).",
                key_concepts=["Material sources", "Written sources", "Oral sources"],
                format_type="comparison",
                book_page=2,
                action_options=["Compare source types", "Explore past and future", "Take Chapter 1 quiz"],
            ),
        ],
    ),
    "EVS_CH04": ChapterLearningMap(
        subject_id="evs",
        chapter_id="EVS_CH04",
        chapter_number=4,
        chapter_title="Evolution",
        learning_objectives=[
            "Understand the concept of evolution as gradual and continuous change.",
            "Learn Charles Darwin's scientific contribution to evolutionary theory.",
            "Understand how species adapt to environmental changes and survive.",
            "Explore the evolution of animals from unicellular protozoa to vertebrates and mammals.",
        ],
        key_facts=[
            "Evolution is a process of gradual and continuous change in living beings.",
            "Charles Darwin was the first scientist to give a systematic explanation of evolution.",
            "Organisms capable of adapting to environmental changes survive; those unable to adapt become extinct (e.g. dinosaurs).",
            "Mammals are the most evolved animals: they give birth to young ones and nourish them on mother's milk.",
        ],
        moments=[
            LearningMoment(
                moment_id="EVS_CH04_M01",
                subject_id="evs",
                chapter_id="EVS_CH04",
                chapter_number=4,
                title="The Concept of Evolution",
                summary="How internal and physical structures of living organisms change gradually over generations to survive.",
                key_concepts=["Gradual change", "Survival", "Adaptation"],
                format_type="explanation",
                book_page=15,
                action_options=["Meet Charles Darwin", "Explore animal stages", "Check understanding"],
            ),
            LearningMoment(
                moment_id="EVS_CH04_M02",
                subject_id="evs",
                chapter_id="EVS_CH04",
                chapter_number=4,
                title="Charles Darwin's Theory of Natural Selection",
                summary="Species that adapt to changing environments survive; species that fail to adapt become extinct.",
                key_concepts=["Charles Darwin", "Natural selection", "Extinction of dinosaurs"],
                format_type="figure_profile",
                book_page=16,
                action_options=["Explore stages of animal evolution", "See dinosaur extinction", "Try Evolution quiz"],
            ),
            LearningMoment(
                moment_id="EVS_CH04_M03",
                subject_id="evs",
                chapter_id="EVS_CH04",
                chapter_number=4,
                title="Stages of Evolution of Animals",
                summary="From unicellular organisms (protozoa) to invertebrates, aquatic animals, amphibians, reptiles, and mammals.",
                key_concepts=["Protozoa", "Vertebrates", "Mammals"],
                format_type="timeline",
                book_page=17,
                action_options=["Chapter recap", "Take knowledge check", "Ask custom question"],
            ),
        ],
    ),
    "EVS_CH06": ChapterLearningMap(
        subject_id="evs",
        chapter_id="EVS_CH06",
        chapter_number=6,
        chapter_title="Stone Age: Stone Tools",
        learning_objectives=[
            "Understand tool making according to the task and available resources.",
            "Differentiate Old Stone Age (Palaeolithic), Middle Stone Age (Mesolithic), and New Stone Age (Neolithic).",
            "Explore tool evolution: Oldowan choppers, Acheulean handaxes, and microliths.",
        ],
        key_facts=[
            "Homo habilis made simple choppers by flaking pebbles (Oldowan tools).",
            "Homo erectus developed proportionate, symmetrical handaxes and cleavers (Acheulean tools).",
            "In Middle Stone Age (Mesolithic), humans made microliths (small, sharp stone blades fitted onto wooden or bone handles).",
            "In New Stone Age (Neolithic), stone tools were polished with smooth surfaces.",
        ],
        moments=[
            LearningMoment(
                moment_id="EVS_CH06_M01",
                subject_id="evs",
                chapter_id="EVS_CH06",
                chapter_number=6,
                title="Old Stone Age (Palaeolithic Tools)",
                summary="Choppers made by Homo habilis and symmetrical handaxes crafted by Homo erectus.",
                key_concepts=["Oldowan", "Acheulean handaxe", "Homo habilis", "Homo erectus"],
                format_type="explanation",
                book_page=25,
                action_options=["Explore Mesolithic microliths", "See toolmaking technique", "Check concept"],
            ),
            LearningMoment(
                moment_id="EVS_CH06_M02",
                subject_id="evs",
                chapter_id="EVS_CH06",
                chapter_number=6,
                title="Middle & New Stone Age Tools (Microliths & Polished Stone)",
                summary="Mesolithic microliths fitted into bone handles and Neolithic polished stone tools.",
                key_concepts=["Microliths", "Polished tools", "Neolithic"],
                format_type="comparison",
                book_page=28,
                action_options=["Compare stone age tools", "Take Stone Age quiz", "Chapter recap"],
            ),
        ],
    ),
}


# ── Unified Learning Map Service ──────────────────────────────────────────────


class LearningMapService:
    def get_chapter_map(self, subject_id: str, chapter_id: str) -> Optional[ChapterLearningMap]:
        norm_sub = (subject_id or "").strip().lower()
        clean_cid = (chapter_id or "").strip()

        # 1. History
        if norm_sub in ("history", "hist"):
            # Check HISTORY_LEARNING_MAP from history_map.py
            # Map chapter_id like 'HIST_L02' or '2' or 'history_chapter_02'
            m = re.search(r"(\d+)", clean_cid)
            if m:
                lesson_num = int(m.group(1))
                hist_key = f"HIST_L{lesson_num:02d}"
                node = HISTORY_LEARNING_MAP.get(hist_key)
                if node:
                    # Convert LessonNode to ChapterLearningMap
                    moments = []
                    for st in node.stages:
                        moments.append(
                            LearningMoment(
                                moment_id=st.stage_id,
                                subject_id="history",
                                chapter_id=hist_key,
                                chapter_number=node.lesson_number,
                                title=st.title,
                                summary=st.narration[:150] + "...",
                                key_concepts=node.key_concepts,
                                format_type=st.format_type,
                                book_page=st.book_pages[0],
                                action_options=[c.label for c in st.choices],
                            )
                        )
                    return ChapterLearningMap(
                        subject_id="history",
                        chapter_id=hist_key,
                        chapter_number=node.lesson_number,
                        chapter_title=node.title,
                        learning_objectives=[f"Master the events and significance of {node.title}."],
                        key_facts=[f"Lesson {node.lesson_number}: {node.title} (Book pages {node.book_pages[0]}-{node.book_pages[1]})."],
                        moments=moments,
                    )

        # 2. Mathematics
        elif norm_sub in ("mathematics", "math", "maths"):
            m = re.search(r"(\d+)", clean_cid)
            if m:
                canonical_cid = f"mathematics_chapter_{int(m.group(1)):02d}"
                return MATH_LEARNING_MAPS.get(canonical_cid)
            return MATH_LEARNING_MAPS.get(clean_cid)

        # 3. EVS
        elif norm_sub in ("evs", "environmental studies", "environmental_studies"):
            m = re.search(r"(\d+)", clean_cid)
            if m:
                canonical_cid = f"EVS_CH{int(m.group(1)):02d}"
                return EVS_LEARNING_MAPS.get(canonical_cid)
            return EVS_LEARNING_MAPS.get(clean_cid)

        return None

    def compute_progress(
        self,
        subject_id: str,
        chapter_id: str,
        explored_moment_ids: list[str],
    ) -> dict:
        """
        Calculates honest progress:
        - "You've explored X of Y learning moments."
        - Identifies the next unexplored moment.
        """
        ch_map = self.get_chapter_map(subject_id, chapter_id)
        if not ch_map or not ch_map.moments:
            return {
                "total_moments": 0,
                "explored_count": 0,
                "percentage": 0.0,
                "display_text": "Learning map ready.",
                "next_moment": None,
            }

        total = len(ch_map.moments)
        explored_set = set(explored_moment_ids)
        explored_count = sum(1 for m in ch_map.moments if m.moment_id in explored_set)
        pct = round((explored_count / total) * 100.0, 1) if total > 0 else 0.0

        next_moment = None
        for m in ch_map.moments:
            if m.moment_id not in explored_set:
                next_moment = m
                break

        return {
            "total_moments": total,
            "explored_count": explored_count,
            "percentage": pct,
            "display_text": f"You've explored {explored_count} of {total} learning moments.",
            "next_moment": next_moment.model_dump() if next_moment else None,
        }


# ── Global Singleton Provider ─────────────────────────────────────────────────

_learning_map_service: Optional[LearningMapService] = None


def get_learning_map_service() -> LearningMapService:
    global _learning_map_service
    if _learning_map_service is None:
        _learning_map_service = LearningMapService()
    return _learning_map_service
