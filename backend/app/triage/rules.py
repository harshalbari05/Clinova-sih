"""Deterministic red-flag rules for Clinova Step 6.

Defines high-priority emergency and urgent clinical patterns.
Rules are transparent, reproducible, and authoritative.

SAFETY PRINCIPLE:
    - These rules identify POTENTIAL URGENT/EMERGENCY FEATURES based
      on explicit patient statements.
    - They NEVER claim a definitive diagnosis.
    - Conservative thresholds prevent normal/vague complaints from over-triggering.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from app.triage.schemas import TriageCategory, TriageUrgency


@dataclass(frozen=True)
class RedFlagRule:
    """A deterministic clinical red-flag pattern specification."""

    code: str
    category: TriageCategory
    urgency: TriageUrgency
    severity: str  # "critical", "high", "medium"
    description: str
    explanation: str
    # Primary trigger patterns (regex compiled or string match)
    patterns: list[str]
    # Negative / context qualifiers that suppress this rule if present nearby
    negation_patterns: list[str]
    # Required co-occurring patterns (if any)
    required_conjunction_patterns: list[str] | None = None


# Common clinical negation phrases in English / transliterated medical text
DEFAULT_NEGATIONS = [
    r"\bno\b",
    r"\bnot\b",
    r"\bwithout\b",
    r"\bdenies\b",
    r"\bdenied\b",
    r"\bnever\b",
    r"\bresolved\b",
    r"\brule out\b",
    r"\bunlikely\b",
    r"\bmild\b",
    r"\bslight\b",
    r"\bslightly\b",
    r"\blittle bit\b",
]

# ---------------------------------------------------------------------------
# Rule Definitions
# ---------------------------------------------------------------------------

RED_FLAG_RULES: list[RedFlagRule] = [
    # -----------------------------------------------------------------------
    # 1. CARDIOVASCULAR / CHEST
    # -----------------------------------------------------------------------
    RedFlagRule(
        code="CHEST_PAIN_CRUSHING",
        category=TriageCategory.CARDIOVASCULAR_CHEST,
        urgency=TriageUrgency.EMERGENCY_REVIEW,
        severity="critical",
        description="Severe, crushing, or radiating chest pain",
        explanation="Patient explicitly reported severe, crushing, or squeezing chest pain.",
        patterns=[
            r"\b(crushing|severe|excruciating|unbearable|intense|heavy|squeezing)\s+(chest\s+pain|pain\s+in\s+(my\s+)?chest|pressure\s+in\s+(my\s+)?chest)\b",
            r"\b(chest\s+pain|pain\s+in\s+(my\s+)?chest)\s+(is\s+)?(crushing|severe|excruciating|unbearable|intense)\b",
            r"\bchest\s+pain\s+(radiating|spreading)\s+to\s+(my\s+)?(left\s+arm|jaw|neck|back)\b",
        ],
        negation_patterns=[
            r"\b(no|not|denies|denied|without|mild|slight|minor)\s+(severe\s+)?(crushing\s+)?(chest\s+pain|pain\s+in\s+chest)\b",
            r"\b(mild|slight|occasional|minor)\s+chest\s+(pain|discomfort)\b",
            r"\bchest\s+(feels\s+)?(slightly|a\s+little)\s+(uncomfortable|tight)\b",
        ],
    ),
    RedFlagRule(
        code="CHEST_PAIN_WITH_DYSPNEA",
        category=TriageCategory.CARDIOVASCULAR_CHEST,
        urgency=TriageUrgency.EMERGENCY_REVIEW,
        severity="critical",
        description="Chest pain co-occurring with shortness of breath or dyspnea",
        explanation="Patient reported chest pain combined with breathing difficulty.",
        patterns=[
            r"\b(chest\s+pain|pain\s+in\s+(my\s+)?chest|chest\s+tightness)\b",
        ],
        required_conjunction_patterns=[
            r"\b(shortness\s+of\s+breath|breathless(ness)?|difficulty\s+breathing|can'?t\s+breathe|struggling\s+to\s+breathe|gasping)\b",
        ],
        negation_patterns=[
            r"\b(no|without)\s+(chest\s+pain|shortness\s+of\s+breath|difficulty\s+breathing)\b",
            r"\bmild\s+chest\s+pain\b",
        ],
    ),
    RedFlagRule(
        code="CHEST_PAIN_WITH_SYNCOPE_OR_DIAPHORESIS",
        category=TriageCategory.CARDIOVASCULAR_CHEST,
        urgency=TriageUrgency.EMERGENCY_REVIEW,
        severity="critical",
        description="Chest pain co-occurring with fainting, cold sweating, or nausea",
        explanation="Patient reported chest pain alongside syncope, cold sweats, or collapse.",
        patterns=[
            r"\b(chest\s+pain|pressure\s+in\s+(my\s+)?chest|heaviness\s+in\s+(my\s+)?chest)\b",
        ],
        required_conjunction_patterns=[
            r"\b(fainted|fainting|passed\s+out|loss\s+of\s+consciousness|cold\s+sweat(s|ing)?|sudden\s+sweating)\b",
        ],
        negation_patterns=[
            r"\b(no|without)\s+(chest\s+pain|fainting|sweating)\b",
        ],
    ),

    # -----------------------------------------------------------------------
    # 2. BREATHING / RESPIRATORY
    # -----------------------------------------------------------------------
    RedFlagRule(
        code="BREATHING_SEVERE_DISTRESS",
        category=TriageCategory.RESPIRATORY,
        urgency=TriageUrgency.EMERGENCY_REVIEW,
        severity="critical",
        description="Severe difficulty breathing, gasping, or inability to speak",
        explanation="Patient reported severe acute breathing distress or inability to catch breath.",
        patterns=[
            r"\b(cannot|can'?t)\s+catch\s+(my\s+)?breath\b",
            r"\b(struggling|gasping)\s+(for\s+air|to\s+breathe)\b",
            r"\bsevere\s+(difficulty\s+breathing|shortness\s+of\s+breath|breathlessness|respiratory\s+distress)\b",
            r"\b(unable|cannot|can'?t)\s+to\s+speak\s+(because\s+of|due\s+to)\s+(breathlessness|shortness\s+of\s+breath)\b",
            r"\bchoking\s+and\s+(cannot|can'?t)\s+breathe\b",
        ],
        negation_patterns=[
            r"\b(no|not|denies|denied|without)\s+(severe\s+)?(difficulty\s+breathing|breathlessness)\b",
            r"\b(a\s+little|slightly|mildly)\s+short\s+of\s+breath\b",
            r"\bshort\s+of\s+breath\s+when\s+(climbing|running|walking\s+up)\s+stairs\b",
            r"\bmild\s+difficulty\s+breathing\b",
        ],
    ),

    # -----------------------------------------------------------------------
    # 3. NEUROLOGICAL
    # -----------------------------------------------------------------------
    RedFlagRule(
        code="STROKE_ONE_SIDED_WEAKNESS",
        category=TriageCategory.NEUROLOGICAL,
        urgency=TriageUrgency.EMERGENCY_REVIEW,
        severity="critical",
        description="Sudden weakness, numbness, or paralysis on one side of the body",
        explanation="Patient reported sudden unilateral weakness or numbness of face, arm, or leg.",
        patterns=[
            r"\b(sudden|suddenly)(\s+\w+)?\s+(weakness|numbness|paralysis|loss\s+of\s+movement)\s+(in|on|of)\s+(one|my\s+left|my\s+right)\s+(side|arm|leg|face|hand)\b",
            r"\b(left|right)\s+side\s+(of\s+(my\s+)?body|arm\s+and\s+leg)\s+(is|went|became)\s+(suddenly\s+)?(numb|weak|paralyzed|limp)\b",
            r"\b(face|mouth)\s+(is\s+)?drooping\s+(on\s+one\s+side|suddenly)\b",
            r"\bone\s+side\s+of\s+(my\s+)?(face|body)\s+(feels\s+)?(numb|weak|drooping)\b",
            r"\b(weakness|numbness)\s+(on|in)\s+(one|my\s+left|my\s+right)\s+side\b",
        ],
        negation_patterns=[
            r"\b(no|not|denies|denied|without)\s+(weakness|numbness)\b",
            r"\bgeneralized\s+weakness\b",
        ],
    ),
    RedFlagRule(
        code="STROKE_SPEECH_DIFFICULTY",
        category=TriageCategory.NEUROLOGICAL,
        urgency=TriageUrgency.EMERGENCY_REVIEW,
        severity="critical",
        description="Sudden difficulty speaking, slurred speech, or word-finding difficulty",
        explanation="Patient reported sudden onset of slurred speech or inability to speak words.",
        patterns=[
            r"\bslurred\s+speech\b",
            r"\b(sudden|suddenly)(\s+\w+)?\s+(slurred\s+speech|difficulty\s+speaking|unable\s+to\s+speak|lost\s+my\s+speech)\b",
            r"\bspeech\s+(became|is|was|got)\s+(suddenly\s+)?slurred\b",
            r"\b(can'?t|cannot)\s+get\s+words\s+out\b",
        ],
        negation_patterns=[
            r"\b(no|not|denies|without)\s+slurred\s+speech\b",
            r"\bhoarse\s+voice\b",
        ],
    ),
    RedFlagRule(
        code="SEIZURE_OR_CONVULSION",
        category=TriageCategory.NEUROLOGICAL,
        urgency=TriageUrgency.EMERGENCY_REVIEW,
        severity="critical",
        description="New seizure, convulsion, or fit",
        explanation="Patient or caregiver reported a new seizure, fitting episode, or convulsion.",
        patterns=[
            r"\b(had\s+a|new|sudden)\s+(seizure|convulsion|epileptic\s+fit|fits)\b",
            r"\bshaking\s+uncontrollably\s+with\s+loss\s+of\s+consciousness\b",
        ],
        negation_patterns=[
            r"\b(no|not|denies|without)\s+(seizures?|convulsions?)\b",
            r"\bshivering\b",
        ],
    ),

    # -----------------------------------------------------------------------
    # 4. BLEEDING
    # -----------------------------------------------------------------------
    RedFlagRule(
        code="BLEEDING_HEAVY_UNCONTROLLED",
        category=TriageCategory.BLEEDING,
        urgency=TriageUrgency.EMERGENCY_REVIEW,
        severity="critical",
        description="Heavy or uncontrolled bleeding",
        explanation="Patient reported heavy, spurting, or uncontrollable bleeding.",
        patterns=[
            r"\b(heavy|severe|uncontrolled|profuse|massive)\s+bleeding\b",
            r"\bbleeding\s+(heavily|profusely|won'?t\s+stop|uncontrollably)\b",
            r"\bsoaking\s+through\s+(bandages|towels|clothes)\s+with\s+blood\b",
        ],
        negation_patterns=[
            r"\b(no|not|denies|without|mild|minor|slight)\s+bleeding\b",
            r"\bbleeding\s+has\s+stopped\b",
            r"\bminor\s+cut\b",
            r"\bslight\s+bleeding\b",
        ],
    ),
    RedFlagRule(
        code="BLEEDING_HEMATEMESIS_OR_HEMOPTYSIS",
        category=TriageCategory.BLEEDING,
        urgency=TriageUrgency.EMERGENCY_REVIEW,
        severity="critical",
        description="Vomiting blood (hematemesis) or coughing significant blood (hemoptysis)",
        explanation="Patient reported vomiting blood, coffee-ground emesis, or coughing up blood.",
        patterns=[
            r"\b(vomiting|threw\s+up|throwing\s+up)\s+blood\b",
            r"\bhematemesis\b",
            r"\bcoffee\s+ground\s+(vomit|emesis)\b",
            r"\b(coughing|coughed)\s+up\s+(blood|large\s+amounts\s+of\s+blood)\b",
            r"\bhemoptysis\b",
            r"\b(black|tarry)\s+(stool|stools|poop)\b",
        ],
        negation_patterns=[
            r"\b(no|not|denies|without)\s+(vomiting\s+blood|coughing\s+blood|blood\s+in\s+stool)\b",
            r"\btiny\s+streak\s+of\s+blood\s+in\s+mucus\b",
        ],
    ),

    # -----------------------------------------------------------------------
    # 5. SEVERE ABDOMINAL PAIN
    # -----------------------------------------------------------------------
    RedFlagRule(
        code="ACUTE_SEVERE_ABDOMINAL_PAIN",
        category=TriageCategory.SEVERE_PAIN,
        urgency=TriageUrgency.EMERGENCY_REVIEW,
        severity="high",
        description="Sudden severe abdominal pain, especially with collapse or rigid abdomen",
        explanation="Patient reported sudden severe abdominal pain with associated concerning features.",
        patterns=[
            r"\b(sudden|suddenly)\s+(severe|excruciating|unbearable)\s+(abdominal|stomach|belly)\s+pain\b",
            r"\b(severe|excruciating|intense)\s+(abdominal|stomach|belly)\s+pain\s+(with|and)\s+(fainting|passed\s+out|vomiting\s+repeatedly)\b",
            r"\bworst\s+(abdominal|stomach|belly)\s+pain\s+of\s+my\s+life\b",
        ],
        negation_patterns=[
            r"\b(no|not|without|mild|minor|slight)\s+(severe\s+)?(abdominal|stomach)\s+pain\b",
            r"\bmild\s+(stomach|abdominal)\s+pain\b",
            r"\bstomach\s+upset\b",
            r"\bmild\s+cramps\b",
        ],
    ),

    # -----------------------------------------------------------------------
    # 6. ANAPHYLAXIS / ALLERGIC EMERGENCY
    # -----------------------------------------------------------------------
    RedFlagRule(
        code="ANAPHYLAXIS_AIRWAY_SWELLING",
        category=TriageCategory.ANAPHYLAXIS,
        urgency=TriageUrgency.EMERGENCY_REVIEW,
        severity="critical",
        description="Swelling of lips, tongue, or throat with breathing difficulty",
        explanation="Patient reported facial/airway swelling accompanied by difficulty breathing.",
        patterns=[
            r"\b(swelling|swollen)\s+(of\s+)?(lips|tongue|throat|mouth)\b",
            r"\bthroat\s+(is\s+)?closing\s+up\b",
            r"\b(allergic\s+reaction|anaphylaxis)\b",
        ],
        required_conjunction_patterns=[
            r"\b(can'?t\s+breathe|difficulty\s+breathing|shortness\s+of\s+breath|wheezing|stridor|gasping)\b",
        ],
        negation_patterns=[
            r"\b(no|without)\s+(swelling|difficulty\s+breathing)\b",
            r"\bmild\s+itch(ing)?\b",
            r"\bmild\s+rash\b",
        ],
    ),

    # -----------------------------------------------------------------------
    # 7. ALTERED CONSCIOUSNESS / COLLAPSE
    # -----------------------------------------------------------------------
    RedFlagRule(
        code="ALTERED_CONSCIOUSNESS_UNRESPONSIVE",
        category=TriageCategory.ALTERED_CONSCIOUSNESS,
        urgency=TriageUrgency.EMERGENCY_REVIEW,
        severity="critical",
        description="Unresponsive, loss of consciousness, or severe acute confusion",
        explanation="Patient reported loss of consciousness, collapse, or inability to stay awake.",
        patterns=[
            r"\b(passed\s+out|lost\s+consciousness|blacked\s+out)\s+(and\s+can'?t|multiple\s+times|with\s+(headache|pain))\b",
            r"\b(unresponsive|cannot\s+wake|won'?t\s+wake\s+up|difficult\s+to\s+wake)\b",
            r"\b(sudden|severe)\s+(confusion|delirium|disorientation)\b",
            r"\bfainted\s+and\s+(fell|hit\s+(my\s+)?head|still\s+confused)\b",
            r"\bcollapse(d)?\b",
        ],
        negation_patterns=[
            r"\b(no|not|denies|without)\s+(loss\s+of\s+consciousness|fainting|blackouts?)\b",
            r"\bfelt\s+a\s+little\s+dizzy\b",
            r"\bmild\s+dizziness\b",
        ],
    ),

    # -----------------------------------------------------------------------
    # 8. SELF-HARM / IMMEDIATE SAFETY
    # -----------------------------------------------------------------------
    RedFlagRule(
        code="SELF_HARM_INTENT",
        category=TriageCategory.SELF_HARM,
        urgency=TriageUrgency.EMERGENCY_REVIEW,
        severity="critical",
        description="Explicit statement of immediate intent to self-harm or suicide",
        explanation="Patient expressed explicit statement of immediate intent to end life or cause self-harm.",
        patterns=[
            r"\b(want\s+to|going\s+to|planning\s+to)\s+(kill\s+myself|end\s+my\s+life|commit\s+suicide)\b",
            r"\b(thinking\s+of|about)\s+suicide\s+right\s+now\b",
            r"\b(took|swallowed)\s+(all\s+my\s+pills|a\s+bottle\s+of\s+pills|poison)\s+to\s+(die|end\s+it)\b",
            r"\bi\s+am\s+going\s+to\s+harm\s+myself\b",
        ],
        negation_patterns=[
            r"\b(no|not|never|denies)\s+(suicidal|self\s*harm|thoughts\s+of\s+killing\s+myself)\b",
        ],
    ),

    # -----------------------------------------------------------------------
    # 9. PREGNANCY-RELATED URGENCY
    # -----------------------------------------------------------------------
    RedFlagRule(
        code="PREGNANCY_BLEEDING_OR_SEVERE_PAIN",
        category=TriageCategory.PREGNANCY_URGENT,
        urgency=TriageUrgency.EMERGENCY_REVIEW,
        severity="critical",
        description="Severe bleeding or severe pain during pregnancy",
        explanation="Patient is pregnant and reported heavy vaginal bleeding or severe abdominal pain.",
        patterns=[
            r"\b(pregnant|pregnancy)\b",
        ],
        required_conjunction_patterns=[
            r"\b(heavy\s+bleeding|bleeding\s+heavily|severe\s+(abdominal|belly|pelvic)\s+pain|lost\s+consciousness|fainted|cannot\s+breathe)\b",
        ],
        negation_patterns=[
            r"\b(not|never)\s+pregnant\b",
            r"\bmild\s+spotting\b",
        ],
    ),
]
