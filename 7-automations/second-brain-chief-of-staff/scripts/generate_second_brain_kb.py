from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "knowledge-base"
BASE.mkdir(parents=True, exist_ok=True)

def doc(title, typ, domain, date, keywords, summary, context, key_ideas, decisions, constraints, open_questions, next_actions):
    return f"""---
Title: {title}
Type: {typ}
Domain: {domain}
Date: {date}
Keywords: {keywords}
Summary: {summary}
---

## Context
{context}

## Key Ideas
{key_ideas}

## Decisions
{decisions}

## Constraints
{constraints}

## Open Questions
{open_questions}

## Next Actions
{next_actions}
"""

files = {
    "SB__OperatingSystem__IdentityAndMission.md": doc(
        "Identity and Mission",
        "Operating System",
        "Personal Strategy",
        "2026-04-21",
        "identity, mission, stewardship, discipline, service",
        "Defines identity anchors and mission filters for decision quality across academics, engineering, faith, and athletics.",
        "- Profile: Bioengineering major; minors in Computer Science and Chemistry.\n- Roles: Student-researcher, software builder, strength athlete, Orthodox Christian.\n- Current season: Build a rigorous second-brain workflow that improves execution quality and reduces cognitive overload.",
        "- Primary mission: Build a life of disciplined competence and service through science, engineering, and faith.\n- Identity standard: Be reliable, technically sharp, physically prepared, spiritually grounded.\n- Strategic posture: Choose fewer high-value commitments and execute deeply.\n- Decision filter: Prefer options that compound skill, trust, and long-term leverage.\n- Anti-drift rule: If an activity does not support mission or recovery, it must be reduced or removed.",
        "- Prioritize depth over breadth in semester commitments.\n- Preserve a weekly Sabbath window and liturgical obligations.\n- Keep 3 non-negotiables daily: coursework progress, training/recovery, spiritual rule.\n- Require documented rationale for adding any new project.",
        "- Weekly schedule capacity is finite (~55 focused hours including classes, labs, and study).\n- High CNS demand from powerlifting and BJJ limits late-night deep work frequency.\n- Lab and course deadlines are externally fixed.\n- Personal energy dips after 8:30 PM; planning should front-load hard cognition.",
        "- Which commitments create the most mission-aligned return this semester?\n- Where is perfectionism creating hidden procrastination?\n- What should be paused for 8 weeks to unlock deep progress?",
        "- Write a one-page mission scorecard and review every Sunday.\n- Rank current commitments by strategic value and eliminate bottom 20%.\n- Define explicit minimums for faith, academics, athletics, and project execution."
    ),
    "SB__OperatingSystem__RulesOfEngagement.md": doc(
        "Rules of Engagement",
        "Operating System",
        "Execution",
        "2026-04-21",
        "rules, execution, focus, planning, anti-procrastination",
        "Behavioral operating rules that force clear priorities, realistic planning, and evidence-based progress tracking.",
        "- Problem: Too many parallel tracks create context switching and shallow progress.\n- Need: A strict rule set for how to accept, schedule, and finish work.",
        "- Rule 1: No plan is valid without constraints (time, energy, dependencies).\n- Rule 2: Every week has one defining academic outcome and one defining project outcome.\n- Rule 3: Work in sequence, not mood. Execute highest leverage block first.\n- Rule 4: Tasks must be verb-first and completion-verifiable.\n- Rule 5: If workload exceeds capacity, cut scope explicitly instead of silently slipping.\n- Rule 6: No new commitments without identifying trade-offs.\n- Rule 7: End each day with a written reset for tomorrow’s first block.",
        "- Use 90-minute deep-work blocks for cognitively heavy tasks.\n- Cap active projects to 3 (excluding coursework).\n- Maintain a rolling blocker list and clear one blocker daily.\n- Escalate unresolved blockers >72 hours to advisor/teammate/professor.",
        "- Class timetable and lab access windows are fixed.\n- BJJ and lifting sessions consume physical/mental recovery bandwidth.\n- Communication overhead (email/Slack) can consume mornings if unbounded.",
        "- What is the best trigger for switching from planning to execution each morning?\n- Which recurring meeting could be shortened or replaced async?\n- What % of weekly time is currently untracked?",
        "- Implement a weekly capacity budget (hours by category).\n- Create a red-flag metric: planned vs completed deep-work blocks.\n- Add a Friday shutdown checklist to prevent weekend drift."
    ),
    "SB__OperatingSystem__LongTermGoals.md": doc(
        "Long-Term Goals",
        "Operating System",
        "Strategy",
        "2026-04-21",
        "goals, roadmap, career, graduate-school, entrepreneurship",
        "Three-horizon strategy spanning degree completion, research depth, and product/venture readiness.",
        "- Horizon 1 (0-12 months): Academic excellence, systemization, and portfolio credibility.\n- Horizon 2 (1-3 years): Research publication trajectory + strong software/AI engineering competence.\n- Horizon 3 (3-7 years): Leadership in biomedical innovation with technical and ethical depth.",
        "- H1 outcomes: GPA target >=3.7, reproducible study/research system, 2 high-quality project artifacts.\n- H2 outcomes: Competitive profile for PhD/MS or R&D roles; one significant research contribution.\n- H3 outcomes: Build/lead products that improve patient outcomes and care workflows.\n- Capital strategy: Invest in rare skill intersections (wet-lab literacy + computation + systems thinking).",
        "- Prioritize roles/projects that sharpen quantitative modeling, experimental design, and software shipping.\n- Preserve time for foundational math/CS upskilling each semester.\n- Treat communication skill (writing/presentation) as a core technical multiplier.",
        "- Financial constraints may limit unpaid research opportunities.\n- Time competition between coursework, research, athletics, and product development.\n- Geographic and mentorship availability can shape next-stage options.",
        "- Which graduate pathways best match bioengineering + AI translational interests?\n- What evidence is still missing for a top-tier research application package?\n- Which current projects are portfolio-grade vs learning-only?",
        "- Build a 12-month milestone map with quarterly checkpoints.\n- Create a target-lab and mentor list with fit criteria.\n- Define one flagship project narrative bridging bioengineering and software."
    ),
    "SB__Academics__CurrentSemesterOverview.md": doc(
        "Current Semester Overview",
        "Academic Planning",
        "Academics",
        "2026-04-21",
        "semester, courses, workload, study-system",
        "High-level map of active semester obligations, risk areas, and study execution strategy.",
        "- Assumed course mix: Biotransport, Biomaterials, Organic Chemistry II, Data Structures/Algorithms, Linear Algebra.\n- Lab components: Biomaterials lab + O-Chem lab reports.\n- Weekly fixed obligations: lectures, office hours, recitations, lab blocks, training sessions.",
        "- Heavy cognitive load courses: Biotransport and Data Structures.\n- Memorization-heavy stream: Organic Chemistry reaction mechanisms and spectroscopy.\n- Mathematical backbone: Linear Algebra supports modeling and ML readiness.\n- Strategy: Pre-read before lecture; convert notes to retrieval prompts same day; spaced recall on 48-hour cycle.",
        "- Use Sunday planning to allocate deep-work blocks by course difficulty.\n- Pair problem-solving courses with morning slots; reading-heavy tasks in afternoon.\n- Maintain a weekly exam-prep runway (minimum 7 days before major assessments).",
        "- Lab write-ups create deadline compression if postponed >24 hours post-lab.\n- Peak fatigue after consecutive class + training days.\n- Group project coordination risk in Biomaterials.",
        "- Which course currently has the highest grade volatility?\n- Where are office hours underutilized despite confusion signals?\n- What should be delegated or simplified in non-academic commitments this month?",
        "- Build course-specific scoreboards: topic mastery, assignment status, exam runway.\n- Schedule two recurring office-hour touchpoints each week.\n- Audit current note quality against exam-style questions."
    ),
    "SB__Academics__DeadlinesAndDeliverables.md": doc(
        "Deadlines and Deliverables",
        "Academic Operations",
        "Academics",
        "2026-04-21",
        "deadlines, exams, labs, deliverables, risk",
        "Operational timeline of upcoming deliverables with risk level and preparation lead time.",
        "- Purpose: Single source of truth for due dates across courses and research obligations.\n- Update cadence: daily quick check + Sunday full refresh.",
        "- Recommended columns: Item, Course/Project, Due Date, Effort, Dependency, Risk, Next Step.\n- Lead-time rules: exams (10 days), lab reports (3 days), coding assignments (5 days), reading memos (2 days).\n- Risk flags: RED if no started draft by 50% of runway; YELLOW if dependencies unresolved.",
        "- Use rolling 14-day horizon for active scheduling and 45-day horizon for awareness.\n- Break every deliverable into draft-review-final stages.\n- Lock a hard buffer: submit 12 hours before official deadline when possible.",
        "- Some due dates shift with professor announcements; verification required weekly.\n- Shared-team deliverables depend on others’ response latency.\n- Competing exam clusters may force triage.",
        "- Which upcoming deadlines are under-scoped relative to true effort?\n- Are there hidden dependencies (TA feedback, data collection, teammate code)?\n- What can be pre-committed this week to reduce next week’s load?",
        "- Populate the table with exact dates from LMS/syllabi tonight.\n- Add risk color tags and runway percentages.\n- Set automated reminders at T-7, T-3, T-1 days."
    ),
    "SB__Projects__MasterProjectIndex.md": doc(
        "Master Project Index",
        "Project Portfolio",
        "Engineering Projects",
        "2026-04-21",
        "projects, portfolio, software, prioritization",
        "Portfolio-level view of active and paused projects with objective, status, and strategic value.",
        "- Active software themes: study tooling, biomedical data workflows, automation agents.\n- Candidate projects: GlucoLoop prototype, MindMap knowledge navigator, Jonny Study App enhancements, workflow automation utilities.",
        "- Portfolio rule: each project must map to one of three outcomes—learning, portfolio signal, or real user value.\n- Maintain project cards: objective, user, scope, success metric, next milestone.\n- Avoid parallel complexity by limiting build-stage projects to max 2 at once.",
        "- Current focus candidates:\n  1) Jonny Study App: strengthen weekly planning + retrieval practice modules.\n  2) GlucoLoop: define MVP data pipeline and simulation assumptions.\n  3) MindMap: evaluate utility vs overlap with core Second Brain workflows.\n- Pause low-leverage experiments lacking clear users.",
        "- Limited weekly build hours during exam windows.\n- Data/privacy considerations for health-adjacent tools.\n- Need documented architecture before adding features.",
        "- Which project provides strongest internship/research signal by end of term?\n- What technical debt is silently compounding?\n- Which project should be intentionally archived?",
        "- Build a weighted scoring matrix (impact, effort, learning, credibility).\n- Mark one flagship and one maintenance project for the next 6 weeks.\n- Publish concise README updates for each active repo."
    ),
    "SB__Projects__CurrentFocusAndBlockers.md": doc(
        "Current Focus and Blockers",
        "Project Execution",
        "Engineering Projects",
        "2026-04-21",
        "focus, blockers, execution, dependencies",
        "Execution board for immediate priorities, blockers, and unblock plans.",
        "- Objective: convert project intent into weekly shipping behavior.\n- Current sprint window: 2 weeks.",
        "- Focus A: Jonny Study App weekly planner + task sequencing UX.\n- Focus B: GlucoLoop data schema draft + synthetic dataset tests.\n- Focus C: Automation cleanup for note ingestion and tagging pipeline.\n- Blockers must be concrete: missing spec, missing data, unclear ownership, unresolved bug.",
        "- Blocker log examples:\n  - Study App: unclear state model for recurring tasks.\n  - GlucoLoop: uncertain clinical assumptions for glucose dynamics simplification.\n  - Automation: parser fails on mixed markdown/pdf extraction outputs.\n- Escalation path: if blocked >3 days, reduce scope or request expert input.",
        "- Time fragmentation across too many repositories.\n- Domain uncertainty in biomedical assumptions.\n- Incomplete test harness slows confident iteration.",
        "- Which blocker, if solved first, unlocks the most downstream progress?\n- What scope cuts keep momentum without harming project integrity?\n- What can be converted to a one-hour spike instead of a multi-day rabbit hole?",
        "- Define one weekly ship target per active project.\n- Add blocker-owner-deadline fields to sprint board.\n- Reserve one weekly architecture review slot to prevent chaotic builds."
    ),
    "SB__Research__CurrentResearchQuestions.md": doc(
        "Current Research Questions",
        "Research Planning",
        "Research",
        "2026-04-21",
        "research-questions, bioengineering, computation, literature",
        "Working set of bioengineering and computational research questions with hypotheses and evidence gaps.",
        "- Aim: develop publishable-quality question framing while balancing coursework load.\n- Interest intersection: biomedical signals, mechanistic modeling, AI-assisted analysis.",
        "- RQ1: How can lightweight mechanistic + ML hybrid models improve glucose trend prediction interpretability?\n- RQ2: What feature representations best connect physiological priors with wearable time-series modeling?\n- RQ3: Which validation protocols reduce optimistic bias in small biomedical datasets?\n- RQ4: How can note-linked literature mapping reduce review blind spots in interdisciplinary domains?",
        "- Prioritize papers with transparent methods and reproducible code/data.\n- Track each question with: hypothesis, candidate methods, required data, failure modes, ethical constraints.\n- Compare papers by assumptions, dataset curation, metrics, and external validity.",
        "- Limited access to clinical-grade datasets.\n- IRB/privacy concerns for any patient-linked data.\n- Need stronger statistics foundation for robust evaluation claims.",
        "- Which question is tractable within one semester?\n- What minimum dataset and baseline models are necessary for credible pilot results?\n- Which faculty/lab mentorship aligns with these questions?",
        "- Create annotated bibliography with 15 cornerstone papers.\n- Draft one-page mini-proposal for top-priority question.\n- Define reproducibility checklist for experiments."
    ),
    "SB__WeeklyReview__Template.md": doc(
        "Weekly Review Template",
        "Review System",
        "Operations",
        "2026-04-21",
        "weekly-review, reflection, planning, accountability",
        "Structured weekly review template that forces evidence-based reflection and concrete replanning.",
        "- Review cadence: Sunday evening (45-60 min).\n- Goal: identify what moved, what stalled, and what must change next week.",
        "- Scoreboard sections:\n  - Wins with evidence (what shipped, submitted, improved).\n  - Misses with root causes (capacity error, unclear scope, avoidance, dependency).\n  - Priority alignment check (did time match stated priorities?).\n  - Energy/recovery audit (sleep, training load, cognitive quality).\n- Planning output: top 3 outcomes for next week + blocked-time calendar draft.",
        "- Non-negotiable questions:\n  1) What mattered most and did it actually get done?\n  2) What did I avoid and why?\n  3) What must be cut next week to stay realistic?\n- Require at least one systems improvement every review (process, tooling, environment).",
        "- Avoid excessive introspection without behavioral change.\n- Keep review to 1 page unless major project pivot is needed.\n- Do not add more than 3 weekly priorities.",
        "- Which recurring bottleneck appeared again this week?\n- Did commitments exceed available deep-work capacity?\n- Where did standards slip and what correction is needed?",
        "- Fill review using factual evidence (calendar, tasks, submissions).\n- Commit next week priorities before ending review.\n- Schedule Monday first deep-work block immediately."
    ),
    "SB__DailyPlanning__IdealPromptInputs.md": doc(
        "Ideal Prompt Inputs",
        "Daily Planning",
        "Operations",
        "2026-04-21",
        "daily-planning, prompting, inputs, execution",
        "Defines the exact daily inputs that make the Second Brain GPT produce high-quality plans.",
        "- Purpose: standardize what information is provided each day for reliable planning output.\n- Use this as the morning checklist before asking for a daily plan.",
        "- Required input block:\n  - Date and day type (class day, lab day, weekend).\n  - Available work windows with start/end times.\n  - Top deadlines in next 14 days.\n  - Current energy level (1-5) and sleep quality.\n  - Active blockers.\n  - Non-negotiables (training, liturgy, meetings).\n- Optional but high-value:\n  - Current stressors/distractions.\n  - Course/project confidence ratings.\n  - Yesterday’s carry-over tasks with reason unfinished.",
        "- Ask for outputs in strict format: Situation, What matters most, Sequence, Concrete actions, Risks.\n- Require explicit deferrals: what will not be worked on today.\n- End by identifying the first 30-minute action that starts momentum.",
        "- Bad input quality leads to generic planning.\n- Overestimating available time causes cascading misses.\n- Ambiguous tasks increase procrastination probability.",
        "- Which input field is most often missing in practice?\n- How often are deep-work windows interrupted?\n- What recurring tasks should be templated to reduce planning friction?",
        "- Save a reusable daily input snippet in notes app.\n- Track planned vs completed blocks for 2 weeks and recalibrate.\n- Add an evening reset message to preload tomorrow’s context."
    ),
}

for name, content in files.items():
    (BASE / name).write_text(content, encoding="utf-8")

print(f"Generated {len(files)} knowledge base files in {BASE}")
