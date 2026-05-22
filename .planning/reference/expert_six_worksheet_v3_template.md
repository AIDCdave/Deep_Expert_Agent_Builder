# Expert Six Intake Worksheet

**Purpose:** Complete this worksheet once. Paste the filled-out version into the prompt generator with the instruction: *"Generate a complete Expert Six research prompt AND a companion Context Document from this worksheet."* One shot, two deliverables.

**What this produces (three separate documents):**
1. **Completed Intake Worksheet** — this worksheet with the user's answers filled in, preserved as a standalone record
2. **Expert Six Research Prompt** — ready for execution against GPT 5.5+ with Exa.ai and Firecrawl search infrastructure
3. **Agent Context Document** — a standalone reference describing the agent's purpose, audience, architecture, and knowledge requirements, used to refine the Expert Six output and to drive downstream CustomGPT specification and build processes

---

## SECTION 1: DOMAIN & OBJECTIVE

**1.1 — Domain Name**
What is the domain or discipline this Expert Six covers?

*Examples: "Enterprise Security Advisory," "Databricks Notebook Development," "Cold Email Prospecting for Enterprise SaaS," "Perfume Selection and Valuation"*

> [Your answer]

**1.2 — Purpose Statement**
In a few sentences, what will the extracted knowledge be used for? What problem does this agent solve, and for whom?

> [Your answer]

**1.3 — Stage of Work**
Which Expert Six stage is this worksheet scoping?

- **Stage 1 — Identification Only** — find the six experts; do NOT extract knowledge yet
- **Stage 2 — Knowledge Elicitation** — experts are already identified; extract and structure their knowledge
- **Both stages in sequence** — identify first, then extract — delivered as two distinct outputs

> [Your answer]

---

## SECTION 2: THE REQUESTER'S BASELINE

**2.1 — Your Current Expertise Level in This Domain**
Be honest — this calibrates exclusion filters and depth expectations in the research prompt.

How would you describe your working knowledge in this domain? What have you built, shipped, or practiced? Where are your gaps?

> [Your answer]

**2.2 — Pre-Selected Experts (if any)**
If you've already identified some or all of the six, list them here with a one-line rationale for each. Mark open slots explicitly.

*Example:*
- *Slot 1: Chris Voss — negotiation frameworks that decompose into agent-executable objection handling. LOCKED.*
- *Slot 2: Open — need someone covering Gmail deliverability and sending infrastructure.*

> Slot 1:
> Slot 2:
> Slot 3:
> Slot 4:
> Slot 5:
> Slot 6:

---

## SECTION 3: AGENT DEFINITION

**3.1 — Agent Role**
What role does this agent play? Give it a title the way you'd title a job posting.

*Examples: "Senior Sales Executive," "CISO-Level Security Advisor," "CTO / Chief Architect," "Perfume Selection Consultant"*

> [Your answer]

**3.2 — Agent Personality & Identity**
How should this agent present itself?

- Does the agent have a **personality or persona**? If so, describe the tone, temperament, and any character traits. (e.g., "Direct and clinical, like a senior partner at McKinsey" or "Warm but rigorous, like a trusted mentor who doesn't let you cut corners.")
- Should the agent have a **fictitious human name**? If so, what name and why? (e.g., "Sarah Lin — sounds credible as a PR director.")
- Or is this a **system agent** with a functional name and no human persona? (e.g., "AIDC Security Monitor" — purely application-focused, no personality layer.)

> [Your answer]

**3.3 — Agent Framing: How Does It Work With the User?**
This distinction changes how knowledge is extracted and structured. Describe which of these best fits, or blend them:

- **Executer** — The agent performs tasks and produces deliverables in the user's voice or on the user's behalf. (Writes emails, builds plans, generates reports, fills templates.)
- **Collaborator** — The agent works alongside the user as a thinking partner. (Discusses options, challenges assumptions, helps refine ideas, provides analysis on demand.)
- **Advisor** — The agent interprets, recommends, and explains. (Translates complex signals into executive-level guidance, provides frameworks for decision-making.)
- **Orchestrator** — The agent manages workflows, coordinates with other agents or tools, and helps the user manage work and interactions across systems and people.

You can combine these. Describe the blend and which mode is primary.

> [Your answer]

**3.4 — What Should the Agent Produce?**
Describe the concrete outputs you expect from this agent. Think about what you'd hand off to a great human in this role and expect back.

Some guiding sub-questions:
- What specific artifacts should it deliver? (e.g., emails, reports, playbooks, code, analysis, recommendations, sequences, templates)
- Should it generate work product directly, or should it guide you through producing it yourself?
- Are there specific formats or templates it should follow?
- Should it be able to write code or produce technical deliverables?

> [Your answer]

**3.5 — Who Is the Agent's End User?**
Describe the person who will interact with this agent.

- What is their role or title?
- What is their knowledge level in this domain? Where are they fluent, and where do they need the agent to fill gaps?
- What does this person need the agent to do that they can't efficiently do themselves?

> [Your answer]

---

## SECTION 4: KNOWLEDGE SCOPE & FOCUS

**4.1 — Primary Knowledge Domains**
List 3–7 specific knowledge areas the Expert Six must collectively cover. Be as precise as possible — these become the expertise focus categories in the research prompt.

*Example for a sales agent: cold email copywriting, deliverability/sending infrastructure, CRM sequencing, objection handling frameworks, founder-voice capture, LinkedIn DM motion.*

> 1.
> 2.
> 3.
> 4.
> 5.
> 6. (optional)
> 7. (optional)

**4.2 — What Should Be Excluded?**
Describe any content types, expertise levels, or sources that should be explicitly filtered out of the research.

*Note: Vendor marketing, promotional content, and shallow lifestyle/"top 10" influencer content are always excluded by default. You don't need to repeat those here. Focus on exclusions specific to your domain.*

*Examples: "No beginner tutorials — I need advanced practitioners only." Or conversely: "Include foundational/introductory experts — the end user is new to this domain." Or: "Exclude anyone primarily associated with [specific company or product]."*

> [Your answer]

---

## SECTION 5: BUSINESS CONTEXT

Providing business context anchors the research prompt to real operational needs rather than generic domain research. Complete what's relevant.

**5.1 — Company or Project Name**

> [Your answer]

**5.2 — Business Model**
In 2–4 sentences, what does the business do, who does it serve, and how does it make money?

> [Your answer]

**5.3 — Key Platforms, Tools, or Ecosystems**
What platforms, tools, or technology ecosystems are central to this business? These may constrain or focus the Expert Six search.

> [Your answer]

**5.4 — Target Customer or Buyer Profile**
Who is the business selling to? Describe the buyer in terms of role, company size, and what they care about.

> [Your answer]

**5.5 — Public or Private Agent?**
Will this agent be distributed externally or used internally only?

- **Public** — The agent will be available to external users, either freely or under a paid/licensed model (e.g., published to the GPT Store, embedded in a customer-facing product, distributed to clients).
- **Private** — The agent is for internal use only (personal productivity, team tooling, internal operations).

This affects how knowledge is packaged, what attribution or sourcing standards apply, and how proprietary the agent's knowledge base needs to be.

> [Your answer]

**5.6 — Specific Constraints or Realities**
Anything the prompt generator should know about operational realities, regulatory environment, partnership dynamics, or other constraints that should be baked into the research prompt.

> [Your answer]

---

## SECTION 6: SPECIAL INSTRUCTIONS

Freeform. Include anything else the prompt generator should know — style preferences, naming conventions, framing corrections, references to prior work, hard rules, or domain-specific terminology that matters.

> [Your answer]

---

# HOW TO USE THIS WORKSHEET

1. **Fill out all relevant sections.** Write your answers directly into the `> [Your answer]` blocks. Skip sub-questions that don't apply, but try to complete every section header.

2. **Paste the completed worksheet** into a new conversation with this instruction:

   > *"You are an expert in cognitive research, knowledge architecture, and high-performance research prompt design. Using the completed Expert Six Intake Worksheet below, produce three separate documents:*
   >
   > *1. Completed Intake Worksheet — return the worksheet with the user's answers filled in, formatted as a clean standalone Markdown document for the record.*
   >
   > *2. Expert Six Research Prompt — a complete research prompt ready for execution against GPT 5.5+ with Exa.ai and Firecrawl search infrastructure. Follow the Expert Six output template conventions (Name/Title, Primary Digital Platform, Expertise Focus, Content Depth, plus a synthesis section showing how the six fit together).*
   >
   > *3. Agent Context Document — a standalone Markdown reference describing the agent's purpose, target audience, role framing, knowledge architecture, and domain emphasis. This document will be used alongside the Expert Six output to drive downstream CustomGPT specification and build.*
   >
   > *Output each deliverable as a separate, clearly labeled Markdown document."*

---

*Expert Six Intake Worksheet v3 — May 2026*
