================================================================================
EPISTEMIC ANCHOR DOCUMENT — GENERALIZED TEMPLATE (v1)
================================================================================

PURPOSE
  A reusable scaffold for producing a domain-specific "Epistemic Anchor"
  document from the output of an Expert Six research prompt plus a follow-on
  knowledge-extraction prompt. The completed document grounds an AI agent's
  reasoning in a target domain by capturing:
    1. WHO the foundational experts are
    2. WHAT non-obvious, decomposable knowledge they expose
    3. HOW the system should reason with that knowledge (terms, corrections,
       disambiguations, and quantitative anchors)

INPUTS EXPECTED (from upstream pipeline stages)
  - Stage 1 output: Six identified experts with platforms, focus, content style
                    (from an "Expert Six" research prompt)
  - Stage 2 output: Per-expert knowledge extraction blocks
                    (from a follow-on extraction prompt run against each
                     expert's long-form footprint)

OUTPUT
  A single, dense, ingestible Markdown document following the structure below.
  Designed to be loaded as a system-prompt anchor, an Obsidian note, or a
  retrieval document for an agent.

PLACEHOLDER CONVENTIONS
  - {{ UPPER_SNAKE_CASE }}  — single-value substitution
  - {{ #BLOCK }} … {{ /BLOCK }}  — repeating block (Mustache-style)
  - <!-- @readme -->...<!-- /@readme -->  — author guidance; safe to strip
  - All blockquotes (>) marked "**Section purpose:**" are author guidance
    and may also be stripped if a cleaner final artifact is desired.

PROCESSING NOTES
  - Each section's instructional prose is intentionally verbose so the LLM
    pass that populates the template needs no external context.
  - Repeating blocks are demonstrated once; the renderer should iterate.
  - Counts and length guidance are explicit per section.

================================================================================
-->

---
document_type: epistemic_anchor
domain: {{ DOMAIN_NAME }}
domain_short_description: {{ DOMAIN_SHORT_DESCRIPTION }}
target_task: {{ TARGET_TASK_DESCRIPTION }}
target_agent: {{ TARGET_AGENT_NAME }}
expert_six_research_prompt_ref: {{ EXPERT_SIX_PROMPT_REFERENCE }}
extraction_prompt_ref: {{ EXTRACTION_PROMPT_REFERENCE }}
version: {{ VERSION }}
date_created: {{ DATE_ISO }}
authors: {{ AUTHORS }}
render_mode: {{ RENDER_MODE }}  # "production" (default) or "qa_review"
include_review_table: {{ INCLUDE_REVIEW_TABLE }}  # false in production, true for QA
---

# {{ DOMAIN_NAME }} — Epistemic Anchor

<!-- @readme
The H1 title is the domain plus the artifact type. Keep it short. The
metadata block above is canonical: downstream agents and the vault index
read it. Do not embed prose before the metadata block.
/@readme -->

> **Document purpose.** This is the foundational reasoning anchor for an AI agent operating in the **{{ DOMAIN_NAME }}** domain on the task: *{{ TARGET_TASK_DESCRIPTION }}*. It captures the six expert sources that ground the agent, the non-obvious knowledge those experts expose, the vocabulary needed to reason at expert level, and the cognitive-correction layer that prevents common failure modes. Read top-to-bottom on first ingestion; reference by section thereafter.

---

## Combined Coverage Statement

> **Section purpose.** A 2–3 sentence justification of *why these six* — analytically valuable and not redundant with the detailed profiles. Read this paragraph and the H1 title alone and you should understand the analytical shape of the anchor. This section is **always present** in the rendered output.

<!-- @readme
COMBINED_COVERAGE_STATEMENT must make explicit:
  (a) the dimensions of the domain each expert covers
  (b) the gaps each closes for the others
  (c) the decomposability claim — together they expose codifiable
      decision logic, not just intuition

LENGTH: 2–4 sentences. Prose, no bullets.
/@readme -->

{{ COMBINED_COVERAGE_STATEMENT }}

{{ #INCLUDE_REVIEW_TABLE }}

## Expert Six at a Glance (QA Review Block — Optional)

<!-- @readme
This block is rendered ONLY when the pipeline flag INCLUDE_REVIEW_TABLE
is true. It is a human-review aid for QA passes on pipeline output —
it lets a reviewer eyeball "did we get six coherent experts with
distinct lenses?" in one glance.

Production agent-consumption renders should leave this block off:
frontier LLMs (GPT-5.x, Claude Opus 4.x, Gemini 2.x) hold the full
anchor in working context, so a TL;DR table is redundant and wastes
tokens on every load.

Keep each row to a single line. Order matches the detailed profiles
below.
/@readme -->

> **Section purpose (when included).** Single-screen reference card for the six anchor experts. Used for human QA review of pipeline output. Default off in production renders.

| # | Expert | Primary Role | Signature Lens | Anchor Platform |
|---|--------|--------------|----------------|-----------------|
| 1 | {{ EXPERT_1_NAME }} | {{ EXPERT_1_ROLE }} | {{ EXPERT_1_LENS }} | {{ EXPERT_1_PLATFORM_SHORT }} |
| 2 | {{ EXPERT_2_NAME }} | {{ EXPERT_2_ROLE }} | {{ EXPERT_2_LENS }} | {{ EXPERT_2_PLATFORM_SHORT }} |
| 3 | {{ EXPERT_3_NAME }} | {{ EXPERT_3_ROLE }} | {{ EXPERT_3_LENS }} | {{ EXPERT_3_PLATFORM_SHORT }} |
| 4 | {{ EXPERT_4_NAME }} | {{ EXPERT_4_ROLE }} | {{ EXPERT_4_LENS }} | {{ EXPERT_4_PLATFORM_SHORT }} |
| 5 | {{ EXPERT_5_NAME }} | {{ EXPERT_5_ROLE }} | {{ EXPERT_5_LENS }} | {{ EXPERT_5_PLATFORM_SHORT }} |
| 6 | {{ EXPERT_6_NAME }} | {{ EXPERT_6_ROLE }} | {{ EXPERT_6_LENS }} | {{ EXPERT_6_PLATFORM_SHORT }} |

{{ /INCLUDE_REVIEW_TABLE }}

---

# Section 1 — The {{ DOMAIN_NAME }} Expert Six (Detailed Profiles)

> **Section purpose.** Long-form profile of each expert. Establishes (a) who they are, (b) where their long-form expression lives, (c) what specific specialization they bring to the anchor, and (d) why their writing/teaching style is dense enough to support extraction. Each profile must justify the expert as a *foundational* source — not a popularizer, not a generalist who happens to mention the domain.

<!-- @readme
COUNT: Exactly 6 profiles. Numbered 1–6. Order should reflect the
analytical order chosen in the research prompt (e.g., classical anchors
first, modern complements second; or supply-side first, demand-side
second). Order is editorial — preserve it from the research output.

QUALITY BAR per expert profile:
  - Title line must include name AND a substantive title phrase that
    establishes credibility (not just "AI expert")
  - Primary Digital Platform must be a real, linkable destination with
    long-form content
  - Expertise Focus must be 2–4 bullets, each naming a specific
    sub-specialty (not vague adjectives)
  - Content Depth must reference observable features of the writing
    (structure, technical density, methodology, evaluation framework)
  - Optional "Signal of Recognition" bullet when there's a non-influencer
    credential (industry award, peer recognition, formal role)
/@readme -->

{{ #EACH_EXPERT }}

### {{ EXPERT_INDEX }}) {{ EXPERT_NAME }} — {{ EXPERT_TITLE_LINE }}

**Primary Digital Platform:**
{{ EXPERT_PRIMARY_PLATFORM_DESCRIPTION }}
{{ EXPERT_PLATFORM_LINKS }}

**Expertise Focus:**

- **{{ EXPERT_FOCUS_BULLET_1_LABEL }}** — {{ EXPERT_FOCUS_BULLET_1_BODY }}
- **{{ EXPERT_FOCUS_BULLET_2_LABEL }}** — {{ EXPERT_FOCUS_BULLET_2_BODY }}
- **{{ EXPERT_FOCUS_BULLET_3_LABEL }}** — {{ EXPERT_FOCUS_BULLET_3_BODY }}
{{ #OPTIONAL_FOCUS_BULLET_4 }}
- **{{ EXPERT_FOCUS_BULLET_4_LABEL }}** — {{ EXPERT_FOCUS_BULLET_4_BODY }}
{{ /OPTIONAL_FOCUS_BULLET_4 }}

**Content Depth (writing/teaching style):**
{{ EXPERT_CONTENT_DEPTH_PARAGRAPH }}

{{ #OPTIONAL_RECOGNITION_SIGNAL }}
**Signal of recognition (non-influencer):**
{{ EXPERT_RECOGNITION_SIGNAL }}
{{ /OPTIONAL_RECOGNITION_SIGNAL }}

{{ /EACH_EXPERT }}

---

# Section 2 — {{ DOMAIN_NAME }} Domain Knowledge Extraction

> **Section purpose.** This is the *value-creating* section of the anchor. The expert profiles above tell you *who* to listen to; this section captures *what they actually know that you didn't*. Every anchor entry below must be a non-obvious, decomposable piece of knowledge — something that exposes the expert's underlying decision logic in a form an agent can apply. Vague principles do not belong here. Specific protocols, factor models, dose/ratio anchors, named methods, and causal claims do.

<!-- @readme
This section has TWO sub-sections that must both be present:
  2.1 Unfamiliar Knowledge Extraction (Bulleted List) — per-expert anchor blocks
  2.2 Analysis of the Role of Information — single dense synthesis paragraph

DECOMPOSABILITY FILTER: Every anchor bullet must pass the test
"could this be turned into a system instruction, an elicitation
question, or a verification rule?" If no, cut it.
/@readme -->

## 2.1 Unfamiliar Knowledge Extraction (Bulleted List)

> **Sub-section purpose.** Per-expert knowledge anchors. The "unfamiliar" framing is deliberate — these are the things a domain-literate but non-expert reader would *not* already know. They are the deltas that make this anchor worth carrying. Each expert gets a headline bullet (their name + one-line thematic claim) followed by 4–10 nested anchor bullets.

<!-- @readme
PER-EXPERT BLOCK STRUCTURE:
  - Top-level bullet: **Expert Name — Theme line.** (bold)
  - Nested bullets (4–10): each one is a specific, decomposable anchor
    - Use **bold lead phrase** to name the concept/claim
    - Follow with the explanatory body in plain text
    - Embed quantitative anchors, named protocols, and specific
      terminology where the expert provides them
    - Cite source artifact at end of bullet if appropriate

COUNT: 4–10 anchor bullets per expert. Aim for 6–8 in typical cases.
       Fewer than 4 means the extraction pass was too shallow.
       More than 10 means the bullets are too granular — consolidate.

VOICE: Crisp, technical, claim-first. Avoid hedging adjectives.
/@readme -->

{{ #EACH_EXPERT_KNOWLEDGE_BLOCK }}

- **{{ EXPERT_NAME }} ({{ EXPERT_SHORT_HANDLE }}) — {{ EXPERT_KNOWLEDGE_THEME }}**

  - **{{ ANCHOR_1_LEAD }}** — {{ ANCHOR_1_BODY }}
  - **{{ ANCHOR_2_LEAD }}** — {{ ANCHOR_2_BODY }}
  - **{{ ANCHOR_3_LEAD }}** — {{ ANCHOR_3_BODY }}
  - **{{ ANCHOR_4_LEAD }}** — {{ ANCHOR_4_BODY }}
  - {{ ADDITIONAL_ANCHORS_AS_NEEDED }}

{{ /EACH_EXPERT_KNOWLEDGE_BLOCK }}

## 2.2 Analysis of the Role of Information

> **Sub-section purpose.** A single dense synthesis paragraph (or two) explaining *how the extracted anchors work together* to enable expert-level reasoning by the agent. This is the bridge between raw extraction and operational use. It should explicitly state: what failure mode the anchors prevent, what causal handles they give the agent, and which expert supplies which handle. Read this section by itself and you should understand the system's reasoning capability.

<!-- @readme
FORMAT: 1–2 paragraphs, prose, no bullets. Each expert should be
named at least once with the specific contribution they make.

LENGTH: 200–400 words.

TEST: A reader who reads only this paragraph and the Expert Six at a
Glance table should be able to explain the agent's reasoning approach.
/@readme -->

{{ ROLE_OF_INFORMATION_PARAGRAPH }}

---

# Section 3 — Foundational Concepts (Glossary)

> **Section purpose.** Alphabetized definitions of the technical vocabulary the agent must use precisely. Every term here should either (a) appear in the Knowledge Extraction section above, (b) appear in the Cognitive Alignment section below, or (c) be a term users frequently use imprecisely that the agent must disambiguate. The glossary is not a dictionary — it is the agent's enforced vocabulary.

<!-- @readme
COUNT: 15–40 terms. Density depends on domain. Highly technical
domains (chemistry, infrastructure) trend toward 30+. Methodological
domains (sales, marketing) trend toward 15–25.

ORDERING: Alphabetical. Do not group by theme — the glossary should be
linear-scannable.

FORMAT per entry:
  **Term** (bold, on its own line, with parenthetical disambiguation
  if the term is overloaded elsewhere)
  Definition paragraph (2–5 sentences). Must include not just *what*
  the term means but *why it matters for selection/decision* in the
  target task.

QUALITY BAR: A definition should never just paraphrase a public
encyclopedia entry. It should add the *operational implication* —
how this term influences the agent's reasoning when it appears.
/@readme -->

{{ #EACH_GLOSSARY_TERM }}

**{{ TERM }}**
{{ TERM_DEFINITION_WITH_OPERATIONAL_IMPLICATION }}

{{ /EACH_GLOSSARY_TERM }}

---

# Section 4 — Cognitive Alignment & Distractor Mitigation

> **Section purpose.** This section converts the extracted knowledge into the agent's *cognitive guardrails*. It catches the common errors a reasonable-sounding LLM would make if it were operating on training data alone, and gives the agent explicit machinery to detect, disambiguate, and correct those errors. Four sub-sections cover four distinct guardrail types.

<!-- @readme
This section has FOUR required sub-sections:
  4.1 Direct Contradiction Pairs       — surface myths and their corrections
  4.2 Explicit "Verify & Rectify" Rules — imperative rules triggered by user input
  4.3 Ambiguity Shields                — terms that must be disambiguated before answering
  4.4 Hard Verification Markers        — quantitative anchors to prevent vibe-based guessing

These are NOT redundant with each other:
  - Contradiction Pairs say "this belief is wrong, and here is the correction"
  - Verify & Rectify Rules say "when X happens, do Y"
  - Ambiguity Shields say "when this term appears, force a disambiguation question"
  - Hard Markers say "use this number/fact as a sanity check"
/@readme -->

## 4.1 Direct Contradiction Pairs

> **Sub-section purpose.** The most common misconceptions in this domain, paired with the expert-grounded correction. Each pair is a single conceptual error the agent might absorb from generic training data. The correction is attributed to one or more of the Expert Six so the agent's confidence is calibrated to a named source.

<!-- @readme
COUNT: 8–15 pairs. Fewer than 8 likely means the domain is being
under-corrected. More than 15 means some pairs are duplicates of
verify-and-rectify rules — collapse them.

FORMAT per pair:
  - **[Misconception]**: One-sentence statement of the common-but-wrong belief
  - **[Expert Correction (Attribution)]**: Specific correction, with
    quantitative/structural detail where the expert provided it

ATTRIBUTION: Always name the expert(s). When multiple experts agree,
list them combined: "(Expert A + Expert B)".
/@readme -->

{{ #EACH_CONTRADICTION_PAIR }}

- **[Misconception]**: {{ MISCONCEPTION_STATEMENT }}
  **[Expert Correction ({{ ATTRIBUTED_EXPERTS }})]**: {{ CORRECTION_STATEMENT }}

{{ /EACH_CONTRADICTION_PAIR }}

## 4.2 Explicit "Verify & Rectify" Rules

> **Sub-section purpose.** Imperative cognitive rules — these are the agent's hard-coded behaviors. Each rule has a *trigger* (something in user input or context), a *verification step* (what the agent must check), and a *rectification action* (what it must do or not do). These are the rules that survive into production system prompts.

<!-- @readme
COUNT: 8–15 rules. Each must be triggerable — i.e., a clearly
identifiable signal in user input or agent context should fire it.

FORMAT per rule:
  - **Rule Name** (bold, named like a constraint — e.g., "Performance
    ≠ Concentration Rule", "Pyramid Skepticism Rule")
  - Imperative body using MUST / MUST NOT in capitals
  - State trigger condition and required action

VOICE: Imperative, prescriptive. These are commands to the agent, not
suggestions.
/@readme -->

{{ #EACH_VERIFY_RECTIFY_RULE }}

- **{{ RULE_NAME }}**
  {{ RULE_BODY_WITH_TRIGGER_VERIFY_RECTIFY }}

{{ /EACH_VERIFY_RECTIFY_RULE }}

## 4.3 Ambiguity Shields

> **Sub-section purpose.** Terms that users routinely use imprecisely and that map to multiple distinct underlying realities. For each ambiguous term, list the meanings it can carry and the disambiguation question the agent must ask *before* proceeding. These prevent the most expensive failure mode: confidently answering the wrong question.

<!-- @readme
COUNT: 5–12 shields. Each must name a term the agent is likely to
encounter in real user input.

FORMAT per shield:
  - **"Term"** (in quotes, because we're referring to user usage)
  - Bulleted list of the distinct meanings the term can carry,
    each with a 1-line definition
  - **Shield**: The disambiguation question or behavior the agent
    must execute before responding
/@readme -->

{{ #EACH_AMBIGUITY_SHIELD }}

- **"{{ AMBIGUOUS_TERM }}"**

  - **{{ MEANING_1_LABEL }}**: {{ MEANING_1_DEFINITION }}
  - **{{ MEANING_2_LABEL }}**: {{ MEANING_2_DEFINITION }}
  {{ #OPTIONAL_MEANING_3 }}
  - **{{ MEANING_3_LABEL }}**: {{ MEANING_3_DEFINITION }}
  {{ /OPTIONAL_MEANING_3 }}

  **Shield**: {{ DISAMBIGUATION_QUESTION_OR_BEHAVIOR }}

{{ /EACH_AMBIGUITY_SHIELD }}

## 4.4 Hard Verification Markers (Quantitative Anchors)

> **Sub-section purpose.** Specific, citable, quantitative facts that pin the agent's reasoning to reality. Each marker is a number, ratio, named protocol, or hard datum extracted from one of the Expert Six. Used as sanity checks: when the agent is about to make a quantitative claim, it should compare to these anchors. If it has no anchor and is about to assert a number, it should refuse or hedge.

<!-- @readme
COUNT: 4–10 markers. These are *hard* facts only — if you have no
specific number, named protocol, or precise structural claim, do not
fabricate one. Better four real markers than ten vague ones.

FORMAT per marker:
  - **Hard Marker: {Concrete claim with the number/ratio/name}
    ({Expert attribution})**
  **Use**: How the agent should apply this marker as a sanity check.

QUALITY BAR: Each marker must be falsifiable. "Aldehydes are common
in classic florals" is not a marker. "~1% aldehydes in Chanel No. 5
(Vosnaki)" is a marker.
/@readme -->

{{ #EACH_HARD_MARKER }}

- **Hard Marker: {{ MARKER_QUANTITATIVE_CLAIM }} ({{ MARKER_ATTRIBUTION }})**
  **Use**: {{ MARKER_OPERATIONAL_USE }}

{{ /EACH_HARD_MARKER }}

---

# Appendix A — Anchor Document Authoring Notes

<!-- @readme
This appendix is optional. Include it when the anchor was produced
by a multi-stage pipeline and downstream consumers benefit from
seeing the provenance. Strip it for production agent consumption.
/@readme -->

> **Section purpose.** Provenance and review metadata for the anchor itself. Useful for auditing, versioning, and re-running the extraction pipeline.

- **Domain definition:** {{ DOMAIN_NAME }} — {{ DOMAIN_SHORT_DESCRIPTION }}
- **Target task this anchor supports:** {{ TARGET_TASK_DESCRIPTION }}
- **Expert Six identification prompt:** {{ EXPERT_SIX_PROMPT_REFERENCE }}
- **Knowledge extraction prompt:** {{ EXTRACTION_PROMPT_REFERENCE }}
- **Research execution surface:** {{ RESEARCH_PLATFORM_NAME }}
- **Authoring surface:** {{ AUTHORING_PLATFORM_NAME }}
- **Known gaps / unresolved items:** {{ KNOWN_GAPS_LIST }}
- **Refresh cadence:** {{ REFRESH_CADENCE }}
- **Last reviewed by:** {{ LAST_REVIEWER }} on {{ LAST_REVIEW_DATE }}

---

<!--
================================================================================
END OF TEMPLATE
================================================================================

QUALITY CHECKLIST (run before marking the populated anchor as complete):

[ ] Metadata block populated with all fields (including render_mode)
[ ] Combined coverage statement is present and justifies *why these six*
    in 2–4 prose sentences
[ ] Expert Six at a Glance table is OMITTED in production renders;
    PRESENT only when render_mode = "qa_review"
[ ] All 6 expert profiles have: name + title line, platform with link,
    3–4 focus bullets, content depth paragraph
[ ] Per-expert knowledge blocks have 4–10 anchor bullets each
[ ] Role of Information paragraph names all 6 experts
[ ] Glossary has 15+ terms, alphabetized, each with operational implication
[ ] Direct Contradiction Pairs: 8–15, all attributed
[ ] Verify & Rectify Rules: 8–15, all imperative with MUST/MUST NOT
[ ] Ambiguity Shields: 5–12, each with disambiguation behavior
[ ] Hard Markers: 4–10, all quantitative and attributed
[ ] No placeholder strings remain in the rendered document

================================================================================
