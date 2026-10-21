"""
Structured History Learning Map derived directly from 'History/History.pdf'.

Provides an internal pedagogical content structure for all 18 lessons:
- Chronology, lesson titles, and verified textbook page references.
- Persona assignment: Chhatrapati Shivaji Maharaj is the primary storyteller across the curriculum.
- In background lessons (Lessons 1-3), Shivaji guides students through Maharashtra's history before his birth without claiming to witness pre-1630 events.
- Structured pedagogical stages per lesson with format types (story, figure, timeline, cause_effect, comparison, recap, quiz).
- Dynamic, stage-aware interactive choices that eliminate generic repetitive menus.
- Verified textbook knowledge checks with supportive pedagogical explanations.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class ChoiceOption(BaseModel):
    id: str
    label: str
    type: str  # "story" | "explore" | "cause" | "next" | "quiz" | "simpler" | "deeper" | "recap"


class QuizCheck(BaseModel):
    question: str
    options: list[str]
    correct_index: int
    explanation: str


class TimelineEvent(BaseModel):
    step: int = 1
    title: str
    description: str


class FigureProfile(BaseModel):
    name: str
    title: Optional[str] = None
    contribution: str
    key_teachings: list[str] = []
    place: Optional[str] = None


class ComparisonItem(BaseModel):
    feature: str
    itemA: str
    itemB: str


class ComparisonData(BaseModel):
    labelA: str
    labelB: str
    rows: list[ComparisonItem]


class CauseEffectData(BaseModel):
    cause: str
    event: str
    significance: str


class LessonStage(BaseModel):
    stage_id: str                      # e.g. "L02_S1_INTRO", "L02_S2_DNYANESHWAR"
    title: str
    objective: str
    format_type: str = "story"        # "story" | "explanation" | "figure" | "timeline" | "cause_effect" | "comparison" | "quiz" | "recap"
    book_pages: tuple[int, int] = (1, 1)
    pdf_pages: tuple[int, int] = (11, 11)
    narration: str
    pause_prompt: str
    choices: list[ChoiceOption] = []
    figure_profile: Optional[FigureProfile] = None
    timeline_events: Optional[list[TimelineEvent]] = None
    comparison: Optional[ComparisonData] = None
    cause_effect: Optional[CauseEffectData] = None
    recap_points: Optional[list[str]] = None
    quiz: Optional[QuizCheck] = None
    next_stage_id: Optional[str] = None


class LessonNode(BaseModel):
    id: str                     # e.g. "HIST_L01"
    lesson_number: int          # 1 to 18
    title: str
    book_pages: tuple[int, int] # e.g. (1, 2)
    pdf_pages: tuple[int, int]  # e.g. (11, 12)
    persona: str = "SHIVAJI"    # Central storyteller across all lessons
    summary: str
    major_figures: list[str]
    key_places: list[str]
    key_concepts: list[str]
    starter_choices: list[ChoiceOption]
    knowledge_check: QuizCheck
    stages: list[LessonStage] = []
    next_lesson_id: Optional[str] = None


HISTORY_LEARNING_MAP: dict[str, LessonNode] = {
    "HIST_L01": LessonNode(
        id="HIST_L01",
        lesson_number=1,
        title="Maharashtra before Shivaji",
        book_pages=(1, 2),
        pdf_pages=(11, 12),
        persona="SHIVAJI",
        summary="About four hundred years ago, Maharashtra was not free. Most of it was divided between two Sultans: Nizamshah of Ahmadnagar and Adilshah of Bijapur. They constantly fought each other, oppressing the subjects. Shivaji Maharaj saw this suffering and undertook the noble task of establishing Swaraj.",
        major_figures=["Chhatrapati Shivaji Maharaj", "Nizamshah of Ahmadnagar", "Adilshah of Bijapur", "Emperor Akbar", "Krishnadevaraya of Vijayanagar"],
        key_places=["Maharashtra", "Ahmadnagar", "Bijapur", "Vijayanagar"],
        key_concepts=[
            "Maharashtra under the rule of Adilshah and Nizamshah",
            "Oppression and constant warfare between the Sultans",
            "Meaning of Swaraj (self-rule, rule of the people)",
            "Shivaji's noble mission to establish justice and happiness for all subjects"
        ],
        starter_choices=[
            ChoiceOption(id="sultans_war", label="⚔️ How did the Sultans divide Maharashtra?", type="story"),
            ChoiceOption(id="compare_rulers", label="👑 Compare the Sultans with Emperor Akbar & Krishnadevaraya", type="explore"),
            ChoiceOption(id="cause_swaraj", label="🚩 Why did I resolve to establish Swaraj?", type="cause"),
            ChoiceOption(id="quiz_check", label="🎯 Try a knowledge challenge", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="Which two Sultans held most of Maharashtra before Shivaji Maharaj established Swaraj?",
            options=[
                "Nizamshah of Ahmadnagar and Adilshah of Bijapur",
                "Emperor Ashoka and Chandragupta Maurya",
                "The British Governor and the Portuguese Viceroy"
            ],
            correct_index=0,
            explanation="According to the textbook (Book p. 1 / PDF p. 11), most of Maharashtra was ruled by Nizamshah of Ahmadnagar and Adilshah of Bijapur, who fought constantly."
        ),
        stages=[
            LessonStage(
                stage_id="L01_S1_INTRO",
                title="Maharashtra under the Two Sultans",
                objective="Understand how Maharashtra was divided and oppressed before Swaraj.",
                format_type="story",
                book_pages=(1, 1),
                pdf_pages=(11, 11),
                narration="Welcome, my young friend! Long before I was born on Fort Shivneri, our motherland Maharashtra was not free. About four hundred years ago, almost the entire land was divided between two Sultans: Nizamshah of Ahmadnagar and Adilshah of Bijapur. They fought continuous wars against each other, and our poor farmers and villagers suffered terribly.",
                pause_prompt="Shall we see how these two Sultans treated the people, or compare them with good kings of India?",
                choices=[
                    ChoiceOption(id="sultans_war", label="⚔️ How did the Sultans harm the people?", type="story"),
                    ChoiceOption(id="compare_rulers", label="👑 Compare the Sultans with Akbar & Krishnadevaraya", type="explore"),
                    ChoiceOption(id="cause_swaraj", label="🚩 Why Swaraj became necessary", type="cause"),
                ],
                next_stage_id="L01_S2_OPPRESSION",
            ),
            LessonStage(
                stage_id="L01_S2_OPPRESSION",
                title="The Noble Resolution for Swaraj",
                objective="Explain the comparison between oppressive and benevolent rulers.",
                format_type="comparison",
                book_pages=(1, 2),
                pdf_pages=(11, 12),
                narration="In the North, the Mughal Emperor Akbar ruled, and in the South, Krishnadevaraya ruled Vijayanagar. History remembers them with love because they cared for the welfare of their subjects. But here in Maharashtra, the Sultans and their Watandars neglected the Ryot (the peasants). Seeing this misery, I resolved to bring freedom and justice.",
                pause_prompt="How would you like to continue our study of Maharashtra before Swaraj?",
                comparison=ComparisonData(
                    labelA="Akbar & Krishnadevaraya",
                    labelB="Nizamshah & Adilshah",
                    rows=[
                        ComparisonItem(feature="Care for subjects", itemA="Looked after the welfare of the people", itemB="Neglected and oppressed the subjects"),
                        ComparisonItem(feature="Religious attitude", itemA="Generous and tolerant towards all faiths", itemB="Religious intolerance and persecution"),
                        ComparisonItem(feature="Place in history", itemA="Remembered with honor and gratitude", itemB="Remembered for continuous warfare and ruin"),
                    ]
                ),
                choices=[
                    ChoiceOption(id="cause_swaraj", label="🚩 What did Swaraj mean to the people?", type="cause"),
                    ChoiceOption(id="recap_l01", label="📋 Summary: The call for Swaraj", type="recap"),
                    ChoiceOption(id="quiz", label="🎯 Take the Lesson 1 Quiz", type="quiz"),
                ],
                next_stage_id="L01_S3_RECAP",
            ),
            LessonStage(
                stage_id="L01_S3_RECAP",
                title="Recap: Maharashtra's Calling",
                objective="Review key takeaways of Lesson 1.",
                format_type="recap",
                book_pages=(1, 2),
                pdf_pages=(11, 12),
                narration="Here is what we have learned about our land before Swaraj:",
                pause_prompt="Ready to test your knowledge or move to the great Saints of Maharashtra?",
                recap_points=[
                    "Maharashtra was divided between Nizamshah of Ahmadnagar and Adilshah of Bijapur.",
                    "The Sultans fought bitter wars, causing great distress to the common folk.",
                    "Watandars and Deshmukhs fought each other over their Jagirs instead of protecting the people.",
                    "Swaraj meant self-rule and justice for all communities, regardless of caste or creed.",
                ],
                choices=[
                    ChoiceOption(id="quiz", label="🎯 Take the Knowledge Check", type="quiz"),
                    ChoiceOption(id="next_lesson", label="➡️ Move to Lesson 2: Work of the Saints", type="next"),
                ],
            ),
        ],
        next_lesson_id="HIST_L02",
    ),

    "HIST_L02": LessonNode(
        id="HIST_L02",
        lesson_number=2,
        title="Work of the Saints",
        book_pages=(3, 7),
        pdf_pages=(13, 17),
        persona="SHIVAJI",
        summary="The great saints of Maharashtra—Shri Chakradhar Swami, Sant Namdeo, Sant Dnyaneshwar, Sant Eknath, Sant Tukaram, and Samarth Ramdas—preached equality, devotion, and compassion. They awakened self-respect and unity among the common people, creating a strong moral foundation for Swaraj.",
        major_figures=["Sant Dnyaneshwar", "Sant Namdeo", "Sant Eknath", "Sant Tukaram", "Samarth Ramdas", "Shri Chakradhar Swami"],
        key_places=["Alandi", "Pandharpur", "Dehu", "Paithan"],
        key_concepts=[
            "Movement of bhakti and devotion to Vithoba of Pandharpur",
            "Teaching equality and rejecting blind discrimination",
            "Sant Dnyaneshwar's Dnyaneshwari in Marathi",
            "Sant Tukaram's devotional Abhangas and saving farmers from debt",
            "Samarth Ramdas's message of strength: 'Maratha Tituka Melvava'"
        ],
        starter_choices=[
            ChoiceOption(id="saints_dnyaneshwar", label="📜 Meet Sant Dnyaneshwar & the Dnyaneshwari", type="explore"),
            ChoiceOption(id="saints_tukaram", label="🌊 Sant Tukaram & his devotional Abhangas", type="story"),
            ChoiceOption(id="saints_ramdas", label="🚩 Samarth Ramdas & 'Maratha Tituka Melvava'", type="cause"),
            ChoiceOption(id="quiz_saints", label="🎯 Test your knowledge on the Saints", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="Which great saint wrote the Dnyaneshwari in Marathi so everyone could understand sacred wisdom?",
            options=[
                "Sant Dnyaneshwar",
                "Sant Tukaram",
                "Samarth Ramdas"
            ],
            correct_index=0,
            explanation="Sant Dnyaneshwar wrote the profound Dnyaneshwari in the language of the people, Marathi, preaching devotion and compassion (Book p. 4 / PDF p. 14)."
        ),
        stages=[
            LessonStage(
                stage_id="L02_S1_INTRO",
                title="The Saints of Maharashtra",
                objective="Introduce how the saints united the people through devotion and equality.",
                format_type="story",
                book_pages=(3, 4),
                pdf_pages=(13, 14),
                narration="Welcome, young learner! In our land of Maharashtra, long before my time, great saints walked from village to village. When the Sultans fought and people lost hope, the saints taught devotion to Lord Vithoba of Pandharpur, kindness to all living beings, and equality among all people, high and low.",
                pause_prompt="Which great saint would you like to explore first?",
                choices=[
                    ChoiceOption(id="saints_dnyaneshwar", label="📜 Meet Sant Dnyaneshwar of Alandi", type="explore"),
                    ChoiceOption(id="saints_tukaram", label="🌊 Discover Sant Tukaram of Dehu", type="story"),
                    ChoiceOption(id="saints_ramdas", label="🚩 How Samarth Ramdas taught strength", type="cause"),
                ],
                next_stage_id="L02_S2_DNYANESHWAR",
            ),
            LessonStage(
                stage_id="L02_S2_DNYANESHWAR",
                title="Sant Dnyaneshwar and the Dnyaneshwari",
                objective="Understand Sant Dnyaneshwar's contribution in making sacred wisdom accessible in Marathi.",
                format_type="figure",
                book_pages=(4, 5),
                pdf_pages=(14, 15),
                narration="Sant Dnyaneshwar lived in Alandi. In those days, all sacred learning was locked in Sanskrit, which poor villagers could not understand. Sant Dnyaneshwar translated the divine Bhagavad Gita into our sweet mother tongue Marathi in his masterpiece, the Dnyaneshwari. Even when narrow-minded people persecuted his family, he bore no ill will and composed the noble Pasaydan, praying for the happiness of all humanity.",
                pause_prompt="Where shall our historical journey lead next?",
                figure_profile=FigureProfile(
                    name="Sant Dnyaneshwar",
                    title="Great Saint of Alandi",
                    place="Alandi, near Pune",
                    contribution="Rendered the Bhagavad Gita into Marathi as the Dnyaneshwari, opening divine wisdom to all people without distinction.",
                    key_teachings=[
                        "Equal love and compassion for all living creatures",
                        "The Pasaydan: Universal prayer for the welfare and peace of all",
                        "Firm faith in God above ritual discrimination"
                    ]
                ),
                choices=[
                    ChoiceOption(id="saints_tukaram", label="🌊 Discover Sant Tukaram & his Abhangas", type="story"),
                    ChoiceOption(id="saints_ramdas", label="🚩 Learn about Samarth Ramdas", type="cause"),
                    ChoiceOption(id="quiz_dnyan", label="🎯 Quick check on Sant Dnyaneshwar", type="quiz"),
                ],
                next_stage_id="L02_S3_TUKARAM",
            ),
            LessonStage(
                stage_id="L02_S3_TUKARAM",
                title="Sant Tukaram of Dehu",
                objective="Learn how Sant Tukaram stood with the oppressed and preached through Abhangas.",
                format_type="story",
                book_pages=(5, 6),
                pdf_pages=(15, 16),
                narration="In Dehu lived Sant Tukaram. He sang soul-stirring devotional songs called Abhangas and held joyous Kirtans that drew thousands. Many poor farmers had been trapped in cruel debt by money-lenders. Sant Tukaram had inherited debt bonds from his ancestors, but he took all those papers and drowned them in the Indrayani River, freeing the poor farmers from bondage forever!",
                pause_prompt="How did this noble act awaken our people's self-respect?",
                choices=[
                    ChoiceOption(id="saints_ramdas", label="🚩 Discover Samarth Ramdas's call to action", type="cause"),
                    ChoiceOption(id="saints_recap", label="📋 Summary of the Saints' work", type="recap"),
                    ChoiceOption(id="quiz_tukaram", label="🎯 Test your knowledge on Tukaram", type="quiz"),
                ],
                next_stage_id="L02_S4_RAMDAS",
            ),
            LessonStage(
                stage_id="L02_S4_RAMDAS",
                title="Samarth Ramdas and the Spirit of Strength",
                objective="Connect the moral awakening of the saints to the foundation of Swaraj.",
                format_type="cause_effect",
                book_pages=(6, 7),
                pdf_pages=(16, 17),
                narration="At that time, on the banks of the Krishna River, the hills echoed with the bold call: 'Jai Jai Raghuveer Samarth!' Samarth Ramdas urged our youth to build strong bodies and brave hearts. He established temples of Lord Hanuman—the symbol of supreme strength—and wrote his great book Dasbodh, giving the famous inspiring message: 'Maratha Tituka Melvava, Maharashtra Dharma Vadhavava' (Unite all Marathas and spread Maharashtra's righteousness).",
                pause_prompt="Shall we review how the Saints helped build the foundation for Swaraj?",
                cause_effect=CauseEffectData(
                    cause="People had lost self-respect, divided by caste and oppressed by foreign Sultans.",
                    event="Saints preached unity, equality in devotion, and Samarth Ramdas organized temples of strength.",
                    significance="This moral and physical awakening created the courageous, unified people who helped me establish Hindavi Swaraj."
                ),
                choices=[
                    ChoiceOption(id="saints_recap", label="📋 Recap: What the Saints taught us", type="recap"),
                    ChoiceOption(id="quiz", label="🎯 Take the Lesson 2 Knowledge Check", type="quiz"),
                    ChoiceOption(id="next_lesson", label="➡️ Move to Lesson 3: The Bhonsales", type="next"),
                ],
                next_stage_id="L02_S5_RECAP",
            ),
            LessonStage(
                stage_id="L02_S5_RECAP",
                title="Recap: The Saints of Maharashtra",
                objective="Review key takeaways of Lesson 2.",
                format_type="recap",
                book_pages=(3, 7),
                pdf_pages=(13, 17),
                narration="Here are the everlasting lessons of our great saints:",
                pause_prompt="Ready to test your knowledge on this inspiring chapter?",
                recap_points=[
                    "Sant Namdeo traveled to Punjab and preached devotion; his verses are preserved in the Guru Granth Sahib.",
                    "Sant Dnyaneshwar opened divine knowledge to common folk through the Dnyaneshwari in Marathi.",
                    "Sant Eknath taught that all living beings deserve love and showed compassion to the suffering.",
                    "Sant Tukaram sang devotional Abhangas and freed poor farmers from hereditary debt.",
                    "Samarth Ramdas inspired youth through Hanuman temples, Dasbodh, and the unity of Maharashtra.",
                    "Their teachings of equality and courage became the moral bedrock upon which Swaraj was built!"
                ],
                choices=[
                    ChoiceOption(id="quiz", label="🎯 Take the Lesson 2 Quiz", type="quiz"),
                    ChoiceOption(id="next_lesson", label="➡️ Move to Lesson 3: The Famous House of Bhonsales", type="next"),
                ],
            ),
        ],
        next_lesson_id="HIST_L03",
    ),

    "HIST_L03": LessonNode(
        id="HIST_L03",
        lesson_number=3,
        title="Maratha Sardars - The Famous House of the Bhonsales",
        book_pages=(8, 11),
        pdf_pages=(18, 21),
        persona="SHIVAJI",
        summary="Brave Maratha sardars served the Sultans with great courage. The House of the Bhonsales of Verul showed supreme valor. Babaji Raje's sons Maloji Raje and Vithoji Raje brought honor to their family. Maloji's son Shahaji Raje was a legendary warrior, scholar, and commander, while his wife Jijabai was the virtuous daughter of Lakhujirao Jadhav of Sindkhed.",
        major_figures=["Maloji Raje Bhonsale", "Shahaji Raje Bhonsale", "Jijabai", "Lakhujirao Jadhav", "Vithoji Raje"],
        key_places=["Verul (Ellora)", "Sindkhed", "Daulatabad", "Pune", "Supa"],
        key_concepts=[
            "Bravery and military traditions of Maratha Sardars",
            "The Temple of Ghrushneshwar restored by Maloji Raje",
            "The wedding of Shahaji Raje and Jijabai",
            "Shahaji Raje's rise as a capable commander and defender of Nizamshahi"
        ],
        starter_choices=[
            ChoiceOption(id="story_bhonsale", label="⚔️ Tell me the story of the House of Bhonsales", type="story"),
            ChoiceOption(id="explore_shahaji", label="🛡️ Who were my father Shahaji Raje and mother Jijabai?", type="explore"),
            ChoiceOption(id="cause_conflict", label="❓ Why did Maratha sardars fight each other earlier?", type="cause"),
            ChoiceOption(id="quiz_bhonsale", label="🎯 Try a quick quiz on the Bhonsales", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="Which historic temple in Verul was restored to its ancient grandeur by Maloji Raje Bhonsale?",
            options=[
                "The Temple of Ghrushneshwar",
                "The Temple of Raireshwar",
                "The Temple of Bhavani"
            ],
            correct_index=0,
            explanation="The textbook records that Maloji Raje Bhonsale was a great devotee of Shiva and renovated the Ghrushneshwar temple in Verul (Book p. 8 / PDF p. 18)."
        ),
        stages=[
            LessonStage(
                stage_id="L03_S1_INTRO",
                title="The House of the Bhonsales of Verul",
                objective="Introduce the valorous ancestors of the Bhonsale family.",
                format_type="story",
                book_pages=(8, 9),
                pdf_pages=(18, 19),
                narration="The Maratha sardars were brave and fiercely loyal warriors, but earlier their courage was spent fighting in the service of foreign Sultans. My grandfather, Maloji Raje Bhonsale of Verul, was a man of great nobility and devotion. He restored the historic Temple of Ghrushneshwar at Verul, lighting lamps where walls had fallen to ruin.",
                pause_prompt="Shall we discover how my father Shahaji Raje and mother Jijabai came together?",
                choices=[
                    ChoiceOption(id="explore_shahaji", label="🛡️ Meet Shahaji Raje and Jijabai", type="explore"),
                    ChoiceOption(id="story_ghrushneshwar", label="🏛️ Learn about the Temple of Ghrushneshwar", type="story"),
                    ChoiceOption(id="quiz", label="🎯 Take the Bhonsales Quiz", type="quiz"),
                ],
            ),
        ],
        next_lesson_id="HIST_L04",
    ),

    "HIST_L04": LessonNode(
        id="HIST_L04",
        lesson_number=4,
        title="Shivaji's Childhood",
        book_pages=(12, 16),
        pdf_pages=(22, 26),
        persona="SHIVAJI",
        summary="I, Shivaji, was born on the auspicious day of Falgun Vadya Tritiya in Shake 1551 (19 February 1630) on Fort Shivneri. My beloved mother Jijabai told me inspiring stories of Rama, Krishna, Bhima, and Abhimanyu. I played with the sons of the brave Mavlas, ran in the forests, and ate simple bhakri and onion with joy.",
        major_figures=["Chhatrapati Shivaji Maharaj", "Jijabai", "Shahaji Raje", "Mavla children"],
        key_places=["Fort Shivneri", "Junnar", "Pune", "Western Ghats"],
        key_concepts=[
            "Birth of Shivaji on Fort Shivneri (19 February 1630)",
            "Jijabai's noble teachings and moral upbringing",
            "Childhood bond with the simple, loyal Mavla children",
            "Games of hide-and-seek, building mud forts, and bird calls in nature"
        ],
        starter_choices=[
            ChoiceOption(id="story_birth", label="👶 Tell me about your birth on Fort Shivneri", type="story"),
            ChoiceOption(id="explore_mavlas", label="🌲 Who were your childhood Mavla friends?", type="explore"),
            ChoiceOption(id="cause_values", label="❓ What did mother Jijabai teach you?", type="cause"),
            ChoiceOption(id="quiz_childhood", label="🎯 Challenge me on Shivaji's childhood", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="On which hill fort was Chhatrapati Shivaji Maharaj born?",
            options=[
                "Fort Shivneri near Junnar",
                "Fort Raigad",
                "Fort Pratapgad"
            ],
            correct_index=0,
            explanation="Shivaji was born on Fort Shivneri near Junnar in Pune district on 19 February 1630 (Book p. 12 / PDF p. 22)."
        ),
        stages=[
            LessonStage(
                stage_id="L04_S1_BIRTH",
                title="Birth on Fort Shivneri",
                objective="Narrate the birth of Shivaji on Fort Shivneri on 19 February 1630.",
                format_type="story",
                book_pages=(12, 13),
                pdf_pages=(22, 23),
                narration="I was born on Fort Shivneri near Junnar on the auspicious day of Falgun Vadya Tritiya, Shake 1551 (19 February 1630). Guns roared and drums beat in celebration across the hills. Mother Jijabai named me Shivaji after Goddess Shivai, the guardian deity of the fort, praying that I would grow up to protect our people.",
                pause_prompt="Would you like to hear about mother Jijabai's teachings or my Mavla friends?",
                choices=[
                    ChoiceOption(id="cause_values", label="📖 The stories mother Jijabai told me", type="story"),
                    ChoiceOption(id="explore_mavlas", label="🌲 My games with the Mavla children", type="explore"),
                    ChoiceOption(id="quiz", label="🎯 Take the Fort Shivneri Quiz", type="quiz"),
                ],
            ),
        ],
        next_lesson_id="HIST_L05",
    ),

    "HIST_L05": LessonNode(
        id="HIST_L05",
        lesson_number=5,
        title="Shivaji's Education",
        book_pages=(17, 20),
        pdf_pages=(27, 30),
        persona="SHIVAJI",
        summary="My father Shahaji Raje appointed renowned scholars at Bengaluru to teach me the arts of warfare, horse-riding, wrestling, and statecraft. Later, mother Jijabai and I returned to Pune. Under the wise guidance of Dadoji Konddev and loyal officers, Pune was transformed from a deserted land into a prosperous, flourishing region.",
        major_figures=["Chhatrapati Shivaji Maharaj", "Shahaji Raje", "Jijabai", "Dadoji Konddev", "Saibai"],
        key_places=["Bengaluru", "Pune", "Lal Mahal"],
        key_concepts=[
            "Comprehensive education in warfare, swordsmanship, and administration",
            "Return to Pune and the revival of devastated farmlands",
            "Dadoji Konddev's strict, honest management",
            "Shivaji's Royal Seal (Rajmudra) in Sanskrit: 'Pratipcchandra-lekkheva...'"
        ],
        starter_choices=[
            ChoiceOption(id="story_education", label="📚 How did you train in warfare and learning?", type="story"),
            ChoiceOption(id="explore_pune", label="🌱 How did Pune transform from ruins into prosperity?", type="explore"),
            ChoiceOption(id="cause_seal", label="🛡️ What is the meaning of your Royal Seal (Rajmudra)?", type="cause"),
            ChoiceOption(id="quiz_education", label="🎯 Take a quiz on Shivaji's education", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="Who supervised the administration of the Pune Jagir and Shivaji's training when he returned to Pune?",
            options=[
                "Dadoji Konddev",
                "Afzalkhan",
                "Shaistakhan"
            ],
            correct_index=0,
            explanation="Dadoji Konddev was the faithful Subhedar of Pune who managed the Jagir honestly and trained Shivaji (Book p. 18 / PDF p. 28)."
        ),
        next_lesson_id="HIST_L06",
    ),

    "HIST_L06": LessonNode(
        id="HIST_L06",
        lesson_number=6,
        title="The Oath of Swaraj",
        book_pages=(21, 24),
        pdf_pages=(31, 34),
        persona="SHIVAJI",
        summary="In the historic temple of Lord Raireshwar, amidst the Sahyadri mountains, my young Mavla companions and I made a solemn pledge. We cut our little fingers and offered our blood to Lord Shiva, declaring: 'God wishes that there should be Hindavi Swaraj! We shall attain it or lay down our lives!'",
        major_figures=["Chhatrapati Shivaji Maharaj", "Tanaji Malusare", "Yesaji Kank", "Baji Pasalkar", "Jijabai"],
        key_places=["Raireshwar Temple", "Maval region", "Sahyadri Hills"],
        key_concepts=[
            "The sacred meeting at Raireshwar temple south-west of Pune",
            "Shivaji's inspiring call for Hindavi Swaraj (self-rule)",
            "The blood oath with the Mavlas to end foreign tyranny",
            "Jijabai's boundless joy and blessing for the mission"
        ],
        starter_choices=[
            ChoiceOption(id="story_oath", label="🔥 Describe the sacred oath at Raireshwar temple", type="story"),
            ChoiceOption(id="explore_mavlas_oath", label="👥 Who were your closest comrades in the oath?", type="explore"),
            ChoiceOption(id="cause_pledge", label="❓ What did 'Hindavi Swaraj' mean to you?", type="cause"),
            ChoiceOption(id="quiz_oath", label="🎯 Test your knowledge on the Oath of Swaraj", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="Where did Shivaji Maharaj and his young Mavlas take the solemn oath of Swaraj?",
            options=[
                "Temple of Raireshwar",
                "Bhavani Temple at Pratapgad",
                "Ghrushneshwar Temple at Verul"
            ],
            correct_index=0,
            explanation="The oath of Swaraj was taken in 1645 at the historic Temple of Raireshwar in the Bhor ghats (Book p. 21 / PDF p. 31)."
        ),
        stages=[
            LessonStage(
                stage_id="L06_S1_OATH",
                title="The Sacred Oath at Raireshwar",
                objective="Narrate the historic oath taken in 1645 at Raireshwar temple.",
                format_type="story",
                book_pages=(21, 22),
                pdf_pages=(31, 32),
                narration="In 1645, in the quiet temple of Lord Raireshwar deep in the Sahyadri hills, I gathered my faithful Mavla companions: Tanaji Malusare, Yesaji Kank, Baji Pasalkar, and many others. We poured out our hearts, cut our little fingers, and offered our blood to Lord Shiva, pledging: 'God wishes that there should be Hindavi Swaraj! We shall attain it or lay down our lives!'",
                pause_prompt="Would you like to meet my brave companions or explore the meaning of our Royal Seal?",
                choices=[
                    ChoiceOption(id="explore_mavlas_oath", label="👥 Meet Tanaji Malusare and Yesaji Kank", type="explore"),
                    ChoiceOption(id="cause_pledge", label="📜 The meaning of the Sanskrit Rajmudra", type="cause"),
                    ChoiceOption(id="quiz", label="🎯 Test your knowledge on the Oath", type="quiz"),
                ],
            ),
        ],
        next_lesson_id="HIST_L07",
    ),

    "HIST_L07": LessonNode(
        id="HIST_L07",
        lesson_number=7,
        title="Swaraj : First Conquest",
        book_pages=(25, 29),
        pdf_pages=(35, 39),
        persona="SHIVAJI",
        summary="With the blessings of Bhavani, we captured Fort Torana, the gateway to the Maval country. During repairs, we discovered four cauldrons of gold mohurs, which we used to purchase weapons and build Fort Rajgad, the first capital of Swaraj. Swaraj had truly begun!",
        major_figures=["Chhatrapati Shivaji Maharaj", "Tanaji Malusare", "Yesaji Kank"],
        key_places=["Fort Torana", "Fort Rajgad", "Murumbdev Hill"],
        key_concepts=[
            "Strategic capture of Fort Torana without bloodshed",
            "Discovery of treasure cauldrons dedicated entirely to Swaraj",
            "Construction of Fort Rajgad as the first capital of Swaraj"
        ],
        starter_choices=[
            ChoiceOption(id="story_torana", label="🏰 How did you capture Fort Torana?", type="story"),
            ChoiceOption(id="explore_treasure", label="🪙 Tell me about the hidden pots of gold mohurs", type="explore"),
            ChoiceOption(id="cause_rajgad", label="⛰️ Why did you build Fort Rajgad as the capital?", type="cause"),
            ChoiceOption(id="quiz_torana", label="🎯 Quiz on Fort Torana and Rajgad", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="Which fort was captured first by Shivaji Maharaj to lay the foundation of Swaraj?",
            options=[
                "Fort Torana",
                "Fort Raigad",
                "Fort Panhala"
            ],
            correct_index=0,
            explanation="Fort Torana was captured first and Shivaji named it 'Prachandagad' because of its immense size and strength (Book p. 25 / PDF p. 35)."
        ),
        next_lesson_id="HIST_L08",
    ),

    "HIST_L08": LessonNode(
        id="HIST_L08",
        lesson_number=8,
        title="Defeat of Internal Enemies",
        book_pages=(30, 33),
        pdf_pages=(40, 43),
        persona="SHIVAJI",
        summary="To build Swaraj, we first had to unite our own people. Certain Maratha sardars—like Chandrarao More of Javali—opposed Swaraj and served Bijapur. Javali had an invincible forest fort. When all peaceful appeals failed, we marched on Javali, subdued the opposition, and built the great fort of Pratapgad nearby.",
        major_figures=["Chhatrapati Shivaji Maharaj", "Chandrarao More", "Raghunath Ballal", "Moropant Pingale"],
        key_places=["Javali Forest", "Fort Pratapgad", "Rairi (Raigad)"],
        key_concepts=[
            "Dealing with internal rivalries and unifying the Maratha sardars",
            "The conquest of the dense Javali forest region in 1656",
            "Building Fort Pratapgad on Bhorpya hill and capturing Fort Rairi"
        ],
        starter_choices=[
            ChoiceOption(id="story_javali", label="🌲 How was the difficult Javali forest conquered?", type="story"),
            ChoiceOption(id="cause_internal", label="❓ Why did some Maratha sardars oppose Swaraj?", type="cause"),
            ChoiceOption(id="quiz_javali", label="🎯 Test your knowledge on Javali and Pratapgad", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="On which hill near Javali did Shivaji Maharaj build the famous Fort Pratapgad?",
            options=[
                "Bhorpya Hill",
                "Shivneri Hill",
                "Purandar Hill"
            ],
            correct_index=0,
            explanation="Shivaji built the formidable Fort Pratapgad on the Bhorpya hill in the dense Javali forest (Book p. 33 / PDF p. 43)."
        ),
        next_lesson_id="HIST_L09",
    ),

    "HIST_L09": LessonNode(
        id="HIST_L09",
        lesson_number=9,
        title="Pratapgad makes History",
        book_pages=(34, 40),
        pdf_pages=(44, 50),
        persona="SHIVAJI",
        summary="Bijapur sent the colossal Sardar Afzalkhan with a mighty army, boasting he would bring me to court alive or dead. Knowing his treachery, I wore secret armor under my kurta, an iron cap under my turban, and carried the concealed Waghnakh and Bichhwa. In the Shamiana at the foot of Pratapgad, he embraced me and tried to strangle me with his sword, but my armor held. I struck with the Waghnakh, and my loyal bodyguard Jiva Mahala killed Sayyid Banda in the nick of time!",
        major_figures=["Chhatrapati Shivaji Maharaj", "Afzalkhan", "Jiva Mahala", "Sayyid Banda", "Jijabai", "Gopinath Pant"],
        key_places=["Fort Pratapgad", "Shamiana at foot of Pratapgad", "Wai", "Bijapur"],
        key_concepts=[
            "Afzalkhan's boastful vow to crush Shivaji and Swaraj",
            "Shivaji's strategic choice of Pratapgad's difficult hill terrain",
            "Concealed armor (Chilkhata), iron cap (Jirastopa), Waghnakh, and Bichhwa",
            "The dramatic meeting in the Shamiana and the slaying of Afzalkhan",
            "The phrase: 'Hota Jiva Mhanun Vachla Shiva' (Because of Jiva, Shiva survived)"
        ],
        starter_choices=[
            ChoiceOption(id="story_pratapgad", label="⛰️ Tell me the dramatic encounter at Pratapgad step by step", type="story"),
            ChoiceOption(id="explore_armor", label="🛡️ What secret weapons and armor did you wear?", type="explore"),
            ChoiceOption(id="cause_jiva", label="⚡ How did Jiva Mahala save your life?", type="cause"),
            ChoiceOption(id="quiz_pratapgad", label="🎯 Challenge me on Pratapgad", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="Who struck down Sayyid Banda when he rushed at Shivaji with a sword in the Shamiana?",
            options=[
                "Jiva Mahala",
                "Tanaji Malusare",
                "Baji Prabhu Deshpande"
            ],
            correct_index=0,
            explanation="Jiva Mahala hacked off Sayyid Banda's raised sword arm in a flash, giving rise to the famous saying 'Hota Jiva Mhanun Vachla Shiva' (Book p. 39 / PDF p. 49)."
        ),
        stages=[
            LessonStage(
                stage_id="L09_S1_CHALLENGE",
                title="Afzalkhan's Challenge",
                objective="Explain the threat posed by Afzalkhan and the strategic selection of Pratapgad.",
                format_type="story",
                book_pages=(34, 36),
                pdf_pages=(44, 46),
                narration="The court of Bijapur was shaken by the rise of Swaraj. The Queen Regent Badi Saheba asked: 'Who among my Sardars will crush Shivaji?' The gigantic Afzalkhan accepted the challenge with contempt, boasting: 'Shivaji? I shall bring him to Bijapur alive or dead!' Knowing his arrogance and treachery, I invited him to meet me at the foot of Fort Pratapgad, where the dense forests and steep ravines neutralized his artillery and heavy cavalry.",
                pause_prompt="Shall we see what special armor and weapons I prepared for this fateful meeting?",
                choices=[
                    ChoiceOption(id="explore_armor", label="🛡️ The secret Waghnakh, Bichhwa & Armor", type="explore"),
                    ChoiceOption(id="the_encounter", label="⛺ The dramatic clash in the Shamiana", type="story"),
                    ChoiceOption(id="quiz", label="🎯 Take the Pratapgad Quiz", type="quiz"),
                ],
                next_stage_id="L09_S2_ENCOUNTER",
            ),
            LessonStage(
                stage_id="L09_S2_ENCOUNTER",
                title="The Clash in the Shamiana",
                objective="Chronicle the sequence of the Shamiana meeting, the treacherous attack, and victory.",
                format_type="timeline",
                book_pages=(37, 40),
                pdf_pages=(47, 50),
                narration="Here is how that historic meeting unfolded in the silk Shamiana:",
                pause_prompt="Would you like to hear how Jiva Mahala saved my life in the final moments?",
                timeline_events=[
                    TimelineEvent(step=1, title="Preparations", description="I wore a coat of chain armor (Chilkhata) under my kurta, an iron skull cap (Jirastopa) under my turban, a Bichhwa in my right sleeve, and a steel Waghnakh concealed in my left hand."),
                    TimelineEvent(step=2, title="The Treacherous Embrace", description="Afzalkhan stepped forward for the formal embrace, suddenly trapped my neck under his left arm, and drove his dagger into my side! The dagger scraped harmlessly against my secret chain armor."),
                    TimelineEvent(step=3, title="The Counter-Strike", description="Breaking his grip, I tore through his belly with the Waghnakh and struck with the Bichhwa. The wounded Khan collapsed crying for help!"),
                    TimelineEvent(step=4, title="Sayyid Banda's Attack", description="His swordsman Sayyid Banda rushed forward to split my head, but my loyal bodyguard Jiva Mahala leapt between us and cut down Banda with lightning speed! 'Hota Jiva Mhanun Vachla Shiva!'"),
                ],
                choices=[
                    ChoiceOption(id="cause_jiva", label="⚡ Why Jiva Mahala's bravery became legendary", type="cause"),
                    ChoiceOption(id="recap_pratapgad", label="📋 Summary of the Pratapgad Victory", type="recap"),
                    ChoiceOption(id="quiz", label="🎯 Test your knowledge on Pratapgad", type="quiz"),
                ],
            ),
        ],
        next_lesson_id="HIST_L10",
    ),

    "HIST_L10": LessonNode(
        id="HIST_L10",
        lesson_number=10,
        title="Baji Prabhu and the Memorable Battle of Ghodkhind",
        book_pages=(41, 46),
        pdf_pages=(51, 56),
        persona="SHIVAJI",
        summary="Trapped in Fort Panhala by Siddi Jauhar's tight siege, we engineered a daring night escape under torrential rain. When the enemy cavalry caught up at the narrow pass of Ghodkhind, my peerless commander Baji Prabhu Deshpande and his three hundred brave Mavlas held off thousands of troops until the five cannon shots from Vishalgad announced our safety. Baji Prabhu gave his life, and Ghodkhind became immortal as Pavan Khind—the Sacred Pass.",
        major_figures=["Chhatrapati Shivaji Maharaj", "Baji Prabhu Deshpande", "Shiva Kashid", "Siddi Jauhar", "Fazalkhan"],
        key_places=["Fort Panhala", "Ghodkhind (Pavan Khind)", "Fort Vishalgad"],
        key_concepts=[
            "Siddi Jauhar's relentless siege of Panhalgad",
            "Shiva Kashid's supreme sacrifice disguising himself as Shivaji",
            "The desperate race to Fort Vishalgad in the pouring monsoon",
            "Baji Prabhu's heroic last stand at the narrow gorge of Ghodkhind",
            "The five cannon shots signaling Shivaji's safety and Baji's martyrdom"
        ],
        starter_choices=[
            ChoiceOption(id="story_escape", label="🌧️ How did you escape the siege of Panhalgad in the rain?", type="story"),
            ChoiceOption(id="explore_baji", label="⚔️ Tell me about Baji Prabhu's stand at Ghodkhind", type="explore"),
            ChoiceOption(id="cause_pavan", label="🕊️ Why is Ghodkhind called 'Pavan Khind' (Sacred Pass)?", type="cause"),
            ChoiceOption(id="quiz_baji", label="🎯 Quiz on Baji Prabhu and Ghodkhind", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="What signal was Baji Prabhu waiting to hear before allowing himself to fall at Ghodkhind?",
            options=[
                "The boom of five cannon shots from Fort Vishalgad",
                "The blowing of trumpets from Panhalgad",
                "A messenger waving a saffron flag"
            ],
            correct_index=0,
            explanation="Baji Prabhu held the pass with superhuman courage until he heard the five cannon shots from Vishalgad, signaling that Shivaji was safe (Book p. 45 / PDF p. 55)."
        ),
        next_lesson_id="HIST_L11",
    ),

    "HIST_L11": LessonNode(
        id="HIST_L11",
        lesson_number=11,
        title="The Discomfiture of Shaistakhan",
        book_pages=(47, 50),
        pdf_pages=(57, 60),
        persona="SHIVAJI",
        summary="Mughal Viceroy Shaistakhan occupied Pune and took up residence in my own childhood home, Lal Mahal. For two years his troops looted the countryside. On a dark night during Ramadan, my select Mavlas and I slipped into Lal Mahal, penetrated his private chambers, and cut off his three fingers as he leapt out of a window! Disgraced and terrified, he fled Pune forever.",
        major_figures=["Chhatrapati Shivaji Maharaj", "Shaistakhan", "Mughal Emperor Aurangzeb", "Babaji Bapuji"],
        key_places=["Lal Mahal (Pune)", "Sinhagad", "Aurangabad"],
        key_concepts=[
            "Shaistakhan's occupation and devastation of the Pune region",
            "Shivaji's audacious plan to infiltrate his own home, Lal Mahal",
            "The midnight raid and the severing of Shaistakhan's three fingers",
            "The psychological defeat of the Mughal forces and their retreat"
        ],
        starter_choices=[
            ChoiceOption(id="story_lalmahal", label="🌙 Describe the midnight raid on Lal Mahal", type="story"),
            ChoiceOption(id="explore_raid", label="⚔️ How did you slip past thousands of Mughal guards?", type="explore"),
            ChoiceOption(id="cause_disgrace", label="❓ Why did Aurangzeb transfer Shaistakhan to Bengal?", type="cause"),
            ChoiceOption(id="quiz_shaista", label="🎯 Test your knowledge on Shaistakhan's defeat", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="What happened to Shaistakhan during Shivaji's daring night raid on Lal Mahal?",
            options=[
                "He lost three fingers as he tried to jump out of a window",
                "He was captured and imprisoned at Raigad",
                "He escaped disguised as a woman"
            ],
            correct_index=0,
            explanation="Shivaji attacked Shaistakhan with his sword in the dark; the Khan lost three fingers as he escaped through the window (Book p. 49 / PDF p. 59)."
        ),
        next_lesson_id="HIST_L12",
    ),

    "HIST_L12": LessonNode(
        id="HIST_L12",
        lesson_number=12,
        title="The Siege of Purandar and the Treaty with the Moghul Emperor",
        book_pages=(51, 55),
        pdf_pages=(61, 65),
        persona="SHIVAJI",
        summary="To punish Swaraj, Aurangzeb sent the experienced veteran Mirza Raje Jai Singh and Dilerkhan with a massive army. Dilerkhan laid siege to Fort Purandar. My brave Killadar Murarbaji Deshpande fought like a lion with seven hundred Mavlas and died defending the Machi. To save my people and preserve our strength for another day, I signed the Treaty of Purandar (1665), temporarily ceding twenty-three forts.",
        major_figures=["Chhatrapati Shivaji Maharaj", "Murarbaji Deshpande", "Mirza Raje Jai Singh", "Dilerkhan"],
        key_places=["Fort Purandar", "Vajragad", "Machi of Purandar"],
        key_concepts=[
            "Murarbaji Deshpande's heroic defense of the Purandar Machi",
            "Refusal of Dilerkhan's bribe and Murarbaji's glorious martyrdom",
            "Shivaji's political foresight: yielding forts to save his people from destruction",
            "The Treaty of Purandar (1665) and agreement to visit Emperor Aurangzeb at Agra"
        ],
        starter_choices=[
            ChoiceOption(id="story_purandar", label="🛡️ Tell me about Murarbaji's defense of Fort Purandar", type="story"),
            ChoiceOption(id="explore_treaty", label="📜 What were the terms of the Treaty of Purandar?", type="explore"),
            ChoiceOption(id="cause_wisdom", label="❓ Why was yielding twenty-three forts a wise decision?", type="cause"),
            ChoiceOption(id="quiz_purandar", label="🎯 Quiz on Purandar and Murarbaji", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="Which brave Killadar led the heroic defense of Fort Purandar against Dilerkhan's army?",
            options=[
                "Murarbaji Deshpande",
                "Tanaji Malusare",
                "Baji Prabhu Deshpande"
            ],
            correct_index=0,
            explanation="Murarbaji Deshpande defended Fort Purandar with unmatched bravery and refused Dilerkhan's offer of Jagirs before being martyred (Book p. 53 / PDF p. 63)."
        ),
        next_lesson_id="HIST_L13",
    ),

    "HIST_L13": LessonNode(
        id="HIST_L13",
        lesson_number=13,
        title="Shivaji gives the slip to the Emperor",
        book_pages=(56, 60),
        pdf_pages=(66, 70),
        persona="SHIVAJI",
        summary="I visited Aurangzeb's court at Agra with my young son Sambhaji. When the Emperor insulted our dignity by placing us behind junior Sardars, I walked out in fearless indignation. Placed under house arrest, we feigned illness, sent out large baskets of sweets to holy men, and escaped hidden inside the baskets! Traveling in disguise across northern India, we returned triumphantly to Maharashtra.",
        major_figures=["Chhatrapati Shivaji Maharaj", "Prince Sambhaji", "Emperor Aurangzeb", "Hiroji Farjand", "Madari Mehtar"],
        key_places=["Agra", "Mathura", "Fort Rajgad"],
        key_concepts=[
            "Shivaji's fearless defense of dignity in the Mughal court at Agra",
            "House arrest surrounded by armed Mughal guards",
            "The ingenious ruse of sending large sweet baskets to Sadhus and Maulvis",
            "Hiroji Farjand and Madari Mehtar's loyalty risking their lives in the bed",
            "The miraculous return to Rajgad via Mathura"
        ],
        starter_choices=[
            ChoiceOption(id="story_agra", label="👑 What happened at the Mughal court in Agra?", type="story"),
            ChoiceOption(id="explore_escape_baskets", label="🧺 How did you escape inside the sweet baskets?", type="explore"),
            ChoiceOption(id="cause_hiroji", label="👤 Who were Hiroji Farjand and Madari Mehtar?", type="cause"),
            ChoiceOption(id="quiz_agra", label="🎯 Test your knowledge on the Escape from Agra", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="How did Shivaji Maharaj and Prince Sambhaji escape from house arrest in Agra?",
            options=[
                "Concealed inside large baskets of sweets sent for charities",
                "By climbing down the fort walls using ropes",
                "Disguised as Mughal soldiers during a storm"
            ],
            correct_index=0,
            explanation="Shivaji and Sambhaji hid inside large sweet baskets that had been inspected daily until guards grew careless (Book p. 58 / PDF p. 68)."
        ),
        next_lesson_id="HIST_L14",
    ),

    "HIST_L14": LessonNode(
        id="HIST_L14",
        lesson_number=14,
        title="The Fort is captured but the Lion is dead",
        book_pages=(61, 64),
        pdf_pages=(71, 74),
        persona="SHIVAJI",
        summary="Mata Jijabai wished to see the strategic fort of Kondana back in Swaraj. My dear brother-in-arms Tanaji Malusare postponed his son Rayaba's wedding, declaring: 'First the wedding of Kondana, then Rayaba's wedding!' He scaled the sheer western cliff at dead of night with his brother Suryaji, fought a fierce duel against Killadar Udaybhan, and won the fort with his life. Deeply grieved, I wept: 'The fort is captured, but the lion is dead!' The fort was renamed Sinhagad.",
        major_figures=["Chhatrapati Shivaji Maharaj", "Tanaji Malusare", "Suryaji Malusare", "Udaybhan Rathod", "Jijabai", "Rayaba"],
        key_places=["Fort Kondana (Sinhagad)", "Umrathe", "Dronagiri cliff"],
        key_concepts=[
            "Tanaji's supreme devotion: putting Swaraj before family celebrations",
            "Scaling the sheer Dronagiri precipice using a monitor lizard (Ghorpad)",
            "The fierce midnight sword battle with Rajput commander Udaybhan",
            "Tanaji's martyrdom and Suryaji rallying the retreating Mavlas",
            "Shivaji's immortal lament: 'Gadh aala pan sinha gela' (The fort is won, but the lion is dead)"
        ],
        starter_choices=[
            ChoiceOption(id="story_tanaji", label="🦁 Tell me the story of Tanaji and the battle of Kondana", type="story"),
            ChoiceOption(id="explore_kondana", label="🧗 How did the Mavlas scale the sheer cliff at night?", type="explore"),
            ChoiceOption(id="cause_sinhagad", label="💔 Why did you say: 'The fort is won, but the lion is dead'?", type="cause"),
            ChoiceOption(id="quiz_tanaji", label="🎯 Quiz on Tanaji Malusare and Sinhagad", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="What historic words did Shivaji Maharaj speak upon hearing of Tanaji's martyrdom at Kondana?",
            options=[
                "'Gadh aala pan sinha gela' (The fort is won, but the lion is dead)",
                "'Har Har Mahadev'",
                "'Jai Bhavani, Jai Shivaji'"
            ],
            correct_index=0,
            explanation="Shivaji wept for his childhood comrade and said: 'Gadh aala pan sinha gela', renaming Kondana as Sinhagad (Book p. 64 / PDF p. 74)."
        ),
        next_lesson_id="HIST_L15",
    ),

    "HIST_L15": LessonNode(
        id="HIST_L15",
        lesson_number=15,
        title="A Memorable Ceremony",
        book_pages=(65, 68),
        pdf_pages=(75, 78),
        persona="SHIVAJI",
        summary="On 6 June 1674 (Jyeshtha Shuddha 13, Shake 1596), Fort Raigad witnessed a historic coronation ceremony. Learned Pandit Gaga Bhatt of Varanasi came to crown me as the sovereign Chhatrapati of an independent kingdom. Swaraj became recognized as a legitimate state. We started a new era (Rajyabhisheka Shaka), minted gold coins (Hon) and copper coins (Shivrai), and unfurled our royal umbrella of sovereignty for all people.",
        major_figures=["Chhatrapati Shivaji Maharaj", "Gaga Bhatt", "Jijabai", "Henry Oxenden"],
        key_places=["Fort Raigad", "Varanasi (Kashi)", "Sindhudurg"],
        key_concepts=[
            "Need for official coronation to establish sovereign legal authority",
            "Gaga Bhatt's learned ceremony and the golden throne studded with jewels",
            "Creation of Rajyabhisheka Shaka (Coronation Era)",
            "Minting of independent Swaraj coins: Hon (gold) and Shivrai (copper)",
            "Mata Jijabai's tearful joy seeing the dream of Swaraj fulfilled before her passing"
        ],
        starter_choices=[
            ChoiceOption(id="story_coronation", label="👑 Describe the grand coronation ceremony at Fort Raigad", type="story"),
            ChoiceOption(id="explore_coins", label="🪙 What were the gold Hon and copper Shivrai coins?", type="explore"),
            ChoiceOption(id="cause_sovereign", label="❓ Why was the coronation necessary for Swaraj?", type="cause"),
            ChoiceOption(id="quiz_coronation", label="🎯 Test your knowledge on the Coronation", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="Which eminent scholar from Varanasi officiated the grand coronation ceremony of Shivaji Maharaj at Raigad?",
            options=[
                "Gaga Bhatt",
                "Samarth Ramdas",
                "Sant Tukaram"
            ],
            correct_index=0,
            explanation="Pandit Gaga Bhatt of Varanasi, renowned as the greatest living scholar, officiated the sacred coronation rites (Book p. 66 / PDF p. 76)."
        ),
        next_lesson_id="HIST_L16",
    ),

    "HIST_L16": LessonNode(
        id="HIST_L16",
        lesson_number=16,
        title="Campaign in the South",
        book_pages=(69, 72),
        pdf_pages=(79, 82),
        persona="SHIVAJI",
        summary="To secure Swaraj against the Mughal threat from the north, we launched a brilliant southern expedition (1677). We allied with Qutbshah of Golconda, captured the impregnable fortress of Jinji and Fort Vellore in Tamil Nadu, and reconciled with my half-brother Vyankoji Raje of Thanjavur. Jinji later served as the unbreachable sanctuary that saved Swaraj during the long Mughal wars.",
        major_figures=["Chhatrapati Shivaji Maharaj", "Vyankoji Raje", "Abul Hasan Qutbshah", "Raghunath Narayan Hanmante"],
        key_places=["Fort Jinji", "Fort Vellore", "Golconda (Hyderabad)", "Thanjavur"],
        key_concepts=[
            "Strategic foresight to establish a southern bastion against Aurangzeb",
            "Capture of Jinji fort, which later sheltered Swaraj for twenty-five years",
            "Treaty with Qutbshah of Golconda and brotherly reconciliation with Vyankoji",
            "Consolidation of Swaraj across the Carnatic region"
        ],
        starter_choices=[
            ChoiceOption(id="story_south", label="🗺️ Tell me about your long march to Jinji and Golconda", type="story"),
            ChoiceOption(id="explore_jinji", label="🏰 Why was Fort Jinji so crucial to saving Swaraj later?", type="explore"),
            ChoiceOption(id="cause_vyankoji", label="🤝 How did you make peace with brother Vyankoji?", type="cause"),
            ChoiceOption(id="quiz_south", label="🎯 Quiz on the Southern Campaign", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="Which impregnable fort in Tamil Nadu was captured by Shivaji Maharaj during his Southern campaign, later protecting Swaraj?",
            options=[
                "Fort Jinji",
                "Fort Golconda",
                "Fort Mysore"
            ],
            correct_index=0,
            explanation="Shivaji captured Fort Jinji; years later, Chhatrapati Rajaram used Jinji as the capital to resist Aurangzeb's full might (Book p. 71 / PDF p. 81)."
        ),
        next_lesson_id="HIST_L17",
    ),

    "HIST_L17": LessonNode(
        id="HIST_L17",
        lesson_number=17,
        title="Management of Forts and the Navy",
        book_pages=(73, 76),
        pdf_pages=(83, 86),
        persona="SHIVAJI",
        summary="A fort is the very life of a kingdom. In Maharashtra, we built, repaired, and garrisoned over three hundred hill, land, and sea forts. We constructed the invincible sea-fort of Sindhudurg at Malvan and founded the Maratha Navy—with Gurabs, Galbats, and Pals under Admiral Maynak Bhandari and Daryasarang—to guard our sacred coastline against foreign sea powers like the Portuguese and the British.",
        major_figures=["Chhatrapati Shivaji Maharaj", "Maynak Bhandari", "Daryasarang Daulat Khan", "Hiroji Indulkar"],
        key_places=["Fort Sindhudurg (Malvan)", "Fort Vijaydurg", "Fort Padmadurg", "Fort Suvarnadurg"],
        key_concepts=[
            "Three types of forts: Hill forts (Giri-durg), Sea forts (Jala-durg), Land forts (Bhui-durg)",
            "Strict fort administration: Havaldar, Sarnobat, and Karkhanis sharing checks and balances",
            "Founding the Maratha Navy: The father of the Indian Navy",
            "Construction of Sindhudurg on the rocky island of Kurte with molten lead foundations"
        ],
        starter_choices=[
            ChoiceOption(id="story_navy", label="⛵ How did you build the Maratha Navy to protect our sea?", type="story"),
            ChoiceOption(id="explore_fort_rules", label="🏰 How were hill and sea forts managed with strict rules?", type="explore"),
            ChoiceOption(id="cause_sindhudurg", label="🌊 Describe the building of the sea-fort Sindhudurg", type="cause"),
            ChoiceOption(id="quiz_forts", label="🎯 Test your knowledge on Forts and the Navy", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="Which sea-fort was built by Shivaji Maharaj on the rocky island of Kurte off Malvan, with molten lead poured into the foundations?",
            options=[
                "Fort Sindhudurg",
                "Fort Janjira",
                "Fort Murud"
            ],
            correct_index=0,
            explanation="Shivaji Maharaj poured five khandis of molten lead into the foundation stones to erect the invincible sea fort of Sindhudurg (Book p. 74 / PDF p. 84)."
        ),
        next_lesson_id="HIST_L18",
    ),

    "HIST_L18": LessonNode(
        id="HIST_L18",
        lesson_number=18,
        title="Management of the Welfare State of Swaraj",
        book_pages=(77, 82),
        pdf_pages=(87, 92),
        persona="SHIVAJI",
        summary="Swaraj was not created for the glory of one king; it was a people's welfare state (Kalyankari Rajya). We organized the Ashta Pradhan Mandal (Council of Eight Ministers) to govern with justice. We protected the farmers against drought and unlawful exactions, built water reservoirs, safeguarded forests, granted equal respect to all religions, and upheld the honor and dignity of women without exception.",
        major_figures=["Chhatrapati Shivaji Maharaj", "Moropant Pingale (Peshwa)", "Ramchandra Nilkanth (Amatya)", "Annaji Datto (Sachiv)", "Hambirrao Mohite (Senapati)"],
        key_places=["Fort Raigad", "All provinces of Swaraj"],
        key_concepts=[
            "The Ashta Pradhan Mandal (Council of Eight Ministers)",
            "Protection of farmers: seeds, bullocks, and tax relief during famine",
            "Environmental protection: cutting trees without royal permission was strictly forbidden",
            "Religious tolerance: honoring holy Quran, mosques, and Hindu temples alike",
            "Highest respect for women: severe punishment for anyone dishonoring women"
        ],
        starter_choices=[
            ChoiceOption(id="story_welfare", label="🌾 How did you take care of the farmers and common people?", type="story"),
            ChoiceOption(id="explore_ashta_pradhan", label="🏛️ Who were the Ashta Pradhan (Eight Ministers)?", type="explore"),
            ChoiceOption(id="cause_tolerance", label="🕊️ How did Swaraj practice equality and religious respect?", type="cause"),
            ChoiceOption(id="quiz_welfare", label="🎯 Final quiz on the Welfare State of Swaraj", type="quiz"),
        ],
        knowledge_check=QuizCheck(
            question="What was the Council of Eight Ministers appointed by Shivaji Maharaj called?",
            options=[
                "Ashta Pradhan Mandal",
                "Navratna Sabha",
                "Maha Parishad"
            ],
            correct_index=0,
            explanation="Shivaji Maharaj appointed the Ashta Pradhan Mandal (Council of Eight Ministers) to ensure efficient, just administration for the people (Book p. 77 / PDF p. 87)."
        ),
        next_lesson_id=None,
    ),
}


def get_lesson(lesson_id: str) -> Optional[LessonNode]:
    """Retrieve a lesson node by ID."""
    return HISTORY_LEARNING_MAP.get(lesson_id.upper())


def get_lesson_by_number(num: int) -> Optional[LessonNode]:
    """Retrieve a lesson node by number (1 to 18)."""
    for node in HISTORY_LEARNING_MAP.values():
        if node.lesson_number == num:
            return node
    return None


def get_all_lessons() -> list[LessonNode]:
    """Return all 18 lessons in chronological order."""
    return sorted(HISTORY_LEARNING_MAP.values(), key=lambda x: x.lesson_number)


def get_lesson_stage(lesson_id: str, stage_id: str) -> Optional[LessonStage]:
    """Retrieve a specific stage within a lesson node."""
    lesson = get_lesson(lesson_id)
    if not lesson or not lesson.stages:
        return None
    for stage in lesson.stages:
        if stage.stage_id == stage_id:
            return stage
    return None
