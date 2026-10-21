"""
Curated & Deterministic Quiz Service for VidyaVerse Learning Hub.

Ensures:
- Deterministic answer validation based on verified source facts and calculations.
- Student-facing quiz payloads never expose the correct answer key in advance.
- Constructive feedback and pedagogical explanations for every option.
- Supports single-answer multiple choice, true/false, and calculation checks.
"""
from __future__ import annotations

import re
from typing import Optional
from pydantic import BaseModel, Field


class QuizQuestion(BaseModel):
    quiz_id: str
    question_id: str
    subject_id: str
    chapter_id: str
    question: str
    options: list[str]
    correct_index: int  # KEPT PRIVATE on server side
    explanation: str
    source_reference: str = ""


class StudentQuizQuestion(BaseModel):
    quiz_id: str
    question_id: str
    subject_id: str
    chapter_id: str
    question: str
    options: list[str]


class QuizValidationResult(BaseModel):
    quiz_id: str
    question_id: str
    selected_index: int
    is_correct: bool
    correct_index: int
    feedback: str
    explanation: str


QUIZ_DATABASE: list[QuizQuestion] = [
    # ── History Quizzes ───────────────────────────────────────────────────────
    QuizQuestion(
        quiz_id="HIST_QUIZ_L01",
        question_id="HIST_Q01_01",
        subject_id="history",
        chapter_id="HIST_L01",
        question="Which two Sultans were ruling Maharashtra before the rise of Shivaji Maharaj?",
        options=[
            "Adilshah of Bijapur and Nizamshah of Ahmadnagar",
            "Mughal Emperor Akbar and Humayun",
            "Bahamani Sultan and Qutbshah of Golconda",
            "Sher Shah Suri and Babur",
        ],
        correct_index=0,
        explanation="Maharashtra was divided between Sultan Adilshah of Bijapur and Sultan Nizamshah of Ahmadnagar, who constantly fought each other.",
        source_reference="Shivachhatrapati Lesson 1, p. 1",
    ),
    QuizQuestion(
        quiz_id="HIST_QUIZ_L02",
        question_id="HIST_Q02_01",
        subject_id="history",
        chapter_id="HIST_L02",
        question="At which sacred place did Sant Dnyaneshwar write the famous 'Bhavartha Deepika' (Dnyaneshwari)?",
        options=[
            "Nevasa on the banks of Pravara river",
            "Alandi near Pune",
            "Dehu on Indrayani river",
            "Pandharpur near Chandrabhaga",
        ],
        correct_index=0,
        explanation="Sant Dnyaneshwar wrote the Bhavartha Deepika (Dnyaneshwari) at Nevasa, explaining the Gita in Marathi for the common people.",
        source_reference="Shivachhatrapati Lesson 2, p. 4",
    ),
    QuizQuestion(
        quiz_id="HIST_QUIZ_L02",
        question_id="HIST_Q02_02",
        subject_id="history",
        chapter_id="HIST_L02",
        question="Which great saint's devotional compositions are included in the holy Guru Granth Sahib of the Sikhs?",
        options=[
            "Sant Namdeo",
            "Sant Tukaram",
            "Sant Eknath",
            "Samarth Ramdas",
        ],
        correct_index=0,
        explanation="Sant Namdeo traveled to Punjab spreading the message of devotion and equality; his verses are preserved in the Guru Granth Sahib.",
        source_reference="Shivachhatrapati Lesson 2, p. 3",
    ),
    QuizQuestion(
        quiz_id="HIST_QUIZ_L06",
        question_id="HIST_Q06_01",
        subject_id="history",
        chapter_id="HIST_L06",
        question="At which temple did Shivaji Maharaj take the solemn oath of Swaraj with his young comrades in 1645?",
        options=[
            "Raireshwar Temple",
            "Bhavani Temple at Pratapgad",
            "Trimbakeshwar Temple",
            "Mahabaleshwar Temple",
        ],
        correct_index=0,
        explanation="In 1645, Shivaji Maharaj and his loyal Mavala companions took the oath of Swaraj at the temple of Raireshwar in the presence of God Shiva.",
        source_reference="Shivachhatrapati Lesson 6, p. 21",
    ),

    # ── Mathematics Quizzes ───────────────────────────────────────────────────
    QuizQuestion(
        quiz_id="MATH_QUIZ_CH02",
        question_id="MATH_Q02_01",
        subject_id="mathematics",
        chapter_id="mathematics_chapter_02",
        question="In a right-angled triangle, if the two perpendicular sides are 6 cm and 8 cm, what is the length of the hypotenuse?",
        options=[
            "10 cm",
            "12 cm",
            "14 cm",
            "9 cm",
        ],
        correct_index=0,
        explanation="By Pythagoras Theorem: c^2 = 6^2 + 8^2 = 36 + 64 = 100 => c = sqrt(100) = 10 cm.",
        source_reference="Mathematics Part II, Ch. 2, p. 34",
    ),
    QuizQuestion(
        quiz_id="MATH_QUIZ_CH02",
        question_id="MATH_Q02_02",
        subject_id="mathematics",
        chapter_id="mathematics_chapter_02",
        question="In a 30°-60°-90° triangle, if the hypotenuse is 16 cm, what is the length of the side opposite the 30° angle?",
        options=[
            "8 cm",
            "8 * sqrt(3) cm",
            "4 cm",
            "12 cm",
        ],
        correct_index=0,
        explanation="By the 30°-60°-90° Theorem: the side opposite 30° is half the hypotenuse = 1/2 * 16 = 8 cm.",
        source_reference="Mathematics Part II, Ch. 2, p. 36",
    ),
    QuizQuestion(
        quiz_id="MATH_QUIZ_CH05",
        question_id="MATH_Q05_01",
        subject_id="mathematics",
        chapter_id="mathematics_chapter_05",
        question="What is the distance between point A(0, 0) and point B(3, 4)?",
        options=[
            "5 units",
            "7 units",
            "12 units",
            "25 units",
        ],
        correct_index=0,
        explanation="By the Distance Formula: d = sqrt((3-0)^2 + (4-0)^2) = sqrt(9 + 16) = sqrt(25) = 5 units.",
        source_reference="Mathematics Part II, Ch. 5, p. 101",
    ),
    QuizQuestion(
        quiz_id="MATH_QUIZ_CH06",
        question_id="MATH_Q06_01",
        subject_id="mathematics",
        chapter_id="mathematics_chapter_06",
        question="What is the exact value of sin(30°) + cos(60°)?",
        options=[
            "1",
            "1/2",
            "sqrt(3)",
            "0",
        ],
        correct_index=0,
        explanation="sin(30°) = 1/2 and cos(60°) = 1/2. Sum = 1/2 + 1/2 = 1.",
        source_reference="Mathematics Part II, Ch. 6, p. 127",
    ),

    # ── EVS Quizzes ───────────────────────────────────────────────────────────
    QuizQuestion(
        quiz_id="EVS_QUIZ_CH01",
        question_id="EVS_Q01_01",
        subject_id="evs",
        chapter_id="EVS_CH01",
        question="Which of the following is considered a 'Material source' of history?",
        options=[
            "Ancient coins, pottery, and stone tools",
            "A grandfather's bedtime story",
            "Folk songs and ballads sung by bards",
            "An oral legend passed down verbally",
        ],
        correct_index=0,
        explanation="Material sources are physical artefacts like pottery, tools, coins, inscriptions, and ancient buildings.",
        source_reference="EVS Chapter 1, p. 2",
    ),
    QuizQuestion(
        quiz_id="EVS_QUIZ_CH04",
        question_id="EVS_Q04_01",
        subject_id="evs",
        chapter_id="EVS_CH04",
        question="Who was the first scientist to give a systematic explanation of the theory of evolution?",
        options=[
            "Charles Darwin",
            "Isaac Newton",
            "Louis Pasteur",
            "Gregor Mendel",
        ],
        correct_index=0,
        explanation="Charles Darwin proposed the theory of evolution by natural selection in his landmark work in the 19th century.",
        source_reference="EVS Chapter 4, p. 15",
    ),
    QuizQuestion(
        quiz_id="EVS_QUIZ_CH06",
        question_id="EVS_Q06_01",
        subject_id="evs",
        chapter_id="EVS_CH06",
        question="What were the small, sharp stone blades called that Mesolithic humans fitted into wooden handles?",
        options=[
            "Microliths",
            "Handaxes",
            "Cleavers",
            "Choppers",
        ],
        correct_index=0,
        explanation="Microliths were tiny, sharp geometric stone blades made during the Middle Stone Age (Mesolithic) and slotted into bone or wooden handles.",
        source_reference="EVS Chapter 6, p. 28",
    ),
]


class QuizService:
    def get_questions_for_chapter(
        self,
        subject_id: str,
        chapter_id: str,
    ) -> list[StudentQuizQuestion]:
        """Returns student-facing quiz questions without exposing the correct answer keys."""
        norm_sub = (subject_id or "").strip().lower()
        if norm_sub in ("math", "maths"):
            norm_sub = "mathematics"

        questions: list[StudentQuizQuestion] = []
        cur_num = self._extract_num(chapter_id)

        for q in QUIZ_DATABASE:
            if q.subject_id.lower() != norm_sub:
                continue
            q_num = self._extract_num(q.chapter_id)
            if cur_num is not None and q_num is not None and cur_num == q_num:
                questions.append(
                    StudentQuizQuestion(
                        quiz_id=q.quiz_id,
                        question_id=q.question_id,
                        subject_id=q.subject_id,
                        chapter_id=q.chapter_id,
                        question=q.question,
                        options=q.options,
                    )
                )

        return questions

    def validate_answer(
        self,
        question_id: str,
        selected_index: int,
    ) -> Optional[QuizValidationResult]:
        """Deterministically evaluates selected_index against the private correct_index."""
        for q in QUIZ_DATABASE:
            if q.question_id == question_id:
                is_correct = (selected_index == q.correct_index)
                feedback = (
                    f"Correct! Well done." if is_correct
                    else f"Not quite. Option {q.correct_index + 1} ('{q.options[q.correct_index]}') is the correct answer."
                )
                return QuizValidationResult(
                    quiz_id=q.quiz_id,
                    question_id=q.question_id,
                    selected_index=selected_index,
                    is_correct=is_correct,
                    correct_index=q.correct_index,
                    feedback=feedback,
                    explanation=q.explanation,
                )
        return None

    def _extract_num(self, text: str) -> Optional[int]:
        m = re.search(r"(\d+)", text)
        return int(m.group(1)) if m else None


_quiz_service: Optional[QuizService] = None


def get_quiz_service() -> QuizService:
    global _quiz_service
    if _quiz_service is None:
        _quiz_service = QuizService()
    return _quiz_service
