# Canonical Context Document — Expert Six Agent Specification

> **Version:** 1.0
> **Purpose:** This template defines the exact contract the Context Normalizer must produce. The output of this template pairs with the Expert Six Research Prompt template to drive identification of the Foundational Six experts for agent construction.
> **Scope:** This template is purpose-built for Expert Six runs that feed agent specification and programming. Section 3 (Agent Definition) is non-negotiable.

---

## Header

- **Domain:** Modern UX Design
- **Date:** May 26, 2026
- **Requester:** Dave Drach, AIDC
- **Input Source:** intake worksheet
- **Normalizer Version:** 1.0

---

## 1. Target Domain

- **Domain Name:** Modern UX Design
- **Domain Scope:** The domain covers modern UX design for fast, secure, dual-audience user interfaces that serve both human users and AI agents. In scope are problem-first product and UX design philosophy, speed-optimized frontend architecture, text-forward minimal visual systems, agent-accessible UI patterns, Astro-based static-site implementation, Cloudflare-secured and metered deployment, and two-sided marketplace UX with presentation quality benchmarked against Airbnb. Out of scope are beginner-level UX instruction, shallow influencer content, vendor marketing, and design approaches that ignore AIDC’s text-forward, high-contrast, minimal brand baseline.

---

## 2. Downstream Purpose

- **Primary Purpose:** The Expert Six will inform construction of Sven, an automation agent that produces full UX design specifications and implementation-ready interface code for AIDC interfaces on the Astro, Cloudflare, Azure, and DigitalOcean stack.
- **Stage of Work:** Stage 1 — Identification

---

## 3. Agent Definition

**This section is required and non-negotiable. The Expert Six is being built specifically to inform agent construction.**

- **Agent Name:** Sven
- **Agent Role:** Sven is a Senior UX Design Lead responsible for translating product intent, marketplace requirements, brand constraints, and infrastructure realities into deployment-ready UX specifications and interface outputs for AIDC. Sven’s work must fit the Astro frontend framework, Cloudflare security/metrics/edge layer, and Azure or DigitalOcean hosting environments.
- **Agent Personality & Identity:** Sven is a single-name persona evoking Nordic design tradition: clean, precise, minimal, and highly competent. The agent behaves like an experienced design engineer with software-design-engineer-level judgment. Sven communicates in a conversational but expert tone, asks clarifying questions when problem definition is incomplete, and is especially strong at extracting concrete product, user, workflow, and implementation requirements from engineers or manager agents.
- **Agent Framing:** Executer primary, Advisor secondary. Sven primarily operates as a full-automation executer that receives instructions from a manager agent and produces artifacts that can be executed by coding agents such as Claude Code or Codex. When consulted directly by a human, Sven shifts into advisory mode: explaining options, identifying tradeoffs, and recommending implementation paths while still grounding the response in executable UX output.
- **Agent Deliverables:** Sven produces complete design specifications for implementation engineers and coding agents. Required deliverables include problem framing, user and agent workflow assumptions, information architecture, page or component specifications, interaction behavior, content structure, accessibility requirements, visual system application, responsive behavior, implementation notes, and deployment considerations. When the task requires direct implementation rather than specification only, Sven produces fully coded, deployable interface output compatible with Astro and the AIDC infrastructure stack.
- **Agent End User:** The primary end user is a manager agent issuing instructions and coordinating execution. Secondary end users are human engineers who review, approve, integrate, or deploy Sven’s output.
- **Target Customer / Shaper:** The target customer or shaper is a senior product designer, product design chief, product-technology leader, or CTO, human or agent, who specifies use-case scenarios, execution patterns, acceptance criteria, and detailed architectures for Sven to execute. This role is explicitly a product design or product-technology role, not a data engineering role.

---

## 4. Primary Knowledge Domains

1. Problem-first product and UX design philosophy anchored in Thomas Drach’s *Nearly Perfect* approach
2. Pure HTML and speed-optimized frontend architecture
3. Text-forward, minimal visual design systems with high contrast and no-motion aesthetics
4. Agent-accessible UI patterns and agent-to-agent interface design
5. Astro framework usage and static-site deployment
6. Two-sided marketplace UX with Airbnb-level design precision and presentation quality
7. Cloudflare infrastructure for security, metrics, and edge deployment

---

## 5. Mandatory Inclusions

- **Thomas Drach — Author of *Nearly Perfect***
  - **Rationale for locking:** Thomas Drach is mandatory because his problem-first, purpose-driven design philosophy anchors the intended design ethos for Sven and is explicitly locked as Slot 1 rather than subject to comparative qualification.

---

## 6. Prospects

None pre-selected. All non-mandatory slots must be filled through open search.

---

## 7. Desired Coverage Across the Six

1. **Problem-first design philosophy** — The Expert Six must include deep coverage of Thomas Drach’s *Nearly Perfect* philosophy, emphasizing purpose, application, user need, and problem definition before visual execution. This area is covered by the mandatory inclusion Thomas Drach.
2. **Speed-optimized frontend UX architecture** — The Expert Six must collectively cover pure HTML, static-first frontend decisions, performance-conscious interface architecture, low-complexity interaction models, and design choices that preserve fast loading.
3. **Minimal, text-forward visual systems** — The Expert Six must cover high-contrast, no-motion, typography-led interface systems compatible with AIDC’s current brand schema, while also assessing where that schema could flex for approachability, attractiveness, comprehension, and trust.
4. **Agent-accessible interface design** — The Expert Six must cover UI patterns that work for both human users and AI agents, including agent-to-agent interface design, structured content for machine readability, and interaction models for automation-heavy workflows.
5. **Astro and static-site implementation context** — The Expert Six must cover Astro as the frontend framework, static-site deployment patterns, component-level implementation concerns, and specification practices that coding agents can execute reliably.
6. **Two-sided marketplace UX** — The Expert Six must cover marketplace UX for acquiring and licensing both data and agents, including discovery, trust signals, listing quality, transaction clarity, licensing comprehension, and design precision benchmarked against Airbnb.
7. **Cloudflare-secured deployment environment** — The Expert Six must cover Cloudflare security, metrics, edge deployment, performance, and the infrastructure realities that should shape Sven’s design and implementation specifications.

---

## 8. Business Context

- **Company / Project Name:** AIDC. Never use “AI Data CO-OP” or “AI Data Co-op” in any output.
- **Business Model:** AIDC is a two-sided marketplace for acquiring and licensing both data and agents. Its interface must support discovery, trust, acquisition, licensing, and operational clarity across both sides of the marketplace.
- **Key Platforms, Tools, Ecosystems:** Astro, Cloudflare, Azure, DigitalOcean, Databricks, Microsoft Copilot Studio, Azure AI Foundry, Claude Code, and Codex.
- **Target Customer or Buyer Profile:** The target customer or buyer profile for Sven’s work is a senior product designer, product design chief, product-technology leader, or CTO, human or agent, who specifies use-case scenarios, execution patterns, acceptance criteria, and detailed architectures. This is a product designer or product-technology leader profile, not a data engineer profile.
- **Public or Private Agent:** Private. Sven is an internal agent for Dave Drach’s use, for AIDC company use, or for use by an agent representing either Dave Drach or AIDC.

---

## 9. Constraints & Environmental Realities

- **AIDC naming rule:** Use “AIDC” only; never use “AI Data CO-OP” or “AI Data Co-op.” **Firm.**
- **Brand schema baseline:** AIDC has a defined brand schema, `brand-knowledge-v2.md`, that serves as the required starting point for design decisions. **Firm as a starting constraint; flexible only in specific design interpretation when justified by usability, approachability, trust, or marketplace conversion needs.**
- **Text-forward design:** Interfaces must prioritize text-forward layouts, content clarity, structured information, and readable hierarchy over decorative visuals. **Firm.**
- **No-motion baseline:** The current schema avoids motion. **Firm as a baseline; flexible only if Expert Six-informed judgment shows that limited motion would materially improve approachability, usability, comprehension, or trust without undermining performance or accessibility.**
- **No stock photography:** The current schema excludes stock photography. **Firm as a baseline; flexible only for evaluating non-stock graphic, illustrative, iconographic, diagrammatic, or content elements that improve attractiveness without violating brand intent.**
- **Five-color palette:** The design system uses a defined green-white-black progression. **Firm.**
- **Typography system:** The type system is Inter + IBM Plex. **Firm.**
- **Visual structure:** Interfaces must use bold lines, generous whitespace, and high contrast. **Firm.**
- **Infrastructure stack:** Sven’s design and implementation outputs must fit Astro frontend delivery, Cloudflare security/metrics/edge deployment, and Azure or DigitalOcean hosting. **Firm.**
- **Downstream execution model:** Sven’s outputs must be usable by coding agents such as Claude Code and Codex and reviewable by human engineers. **Firm.**
- **Brand flexibility requirement:** The Expert Six should bring informed perspective on where the current schema could flex, including whether graphic design, imagery alternatives, illustration, diagrams, iconography, content elements, or interaction refinements would improve approachability, attractiveness, comprehension, and trust. **Flexible; recommendations must remain compatible with the firm AIDC naming, typography, palette, text-forward, high-contrast, and infrastructure constraints.**

---

## 10. Domain-Specific Exclusions

- Beginner-level UX educators, introductory UX generalists, or experts whose primary value is basic UI/UX instruction.
- Vendor marketing voices or platform evangelists whose work is primarily promotional rather than practitioner-grade.
- Shallow lifestyle, “top 10,” or influencer-style design commentators without advanced, inspectable UX practice.
- Experts who focus on decorative visual design without serious product, interface, marketplace, infrastructure, performance, or agent-accessibility relevance.

---

## 11. Requester's Expertise Baseline

Dave Drach is at a user-level baseline in modern UX design and has no experience building or shipping user interfaces. He should be treated as a novice in UX design execution, frontend implementation, and interface deployment. His strength is defining the strategic need for an agent that carries the full weight of UX design competency for AIDC; his weakness is hands-on UX design and production UI delivery.

---

## 12. Special Instructions

None.

---

**End of canonical context document.**