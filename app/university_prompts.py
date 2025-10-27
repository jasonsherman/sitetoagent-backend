from typing import Optional


GENERAL_PROMPT_TEMPLATE = """
You are a higher-education research analyst. Review the scraped website text and return a JSON object that fills the schema below with grounded insights. Do not hallucinate. Use empty strings or empty arrays when you cannot find information.

{
    "type": "object",
    "title": "UniversityGeneralKnowledge",
    "properties": {
        "institutionOverview":          { "type": "string" },
        "keyDifferentiators":           { "type": "array",  "items": { "type": "string" } },
        "availableProgramsAndDegrees":  { "type": "array",  "items": { "type": "string" } },
        "admissionsProcess":            { "type": "string" },
        "tuitionAndFees":               { "type": "string" },
        "campusSafety":                 { "type": "string" },
        "campusLife":                   { "type": "string" },
        "financialAidOptions":          { "type": "string" },
        "scholarshipsAndGrants":        { "type": "string" },
        "studentSupportServices":       { "type": "string" },
        "communicationTone":            { "type": "string" },
        "aiGreetings":                  { "type": "array",  "items": { "type": "string" } },
        "frequentlyAskedQuestions":     { "type": "array",
                                          "items": {
                                              "type": "object",
                                              "properties": {
                                                  "question": { "type": "string" },
                                                  "answer":   { "type": "string" }
                                              },
                                              "required": ["question", "answer"]
                                          }
                                        },
        "resourceLinks":                { "type": "array",
                                          "items": {
                                              "type": "object",
                                              "properties": {
                                                  "label": { "type": "string" },
                                                  "url":   { "type": "string" }
                                              },
                                              "required": ["label", "url"]
                                          }
                                        }
    },
    "required": [
        "institutionOverview",
        "keyDifferentiators",
        "availableProgramsAndDegrees",
        "admissionsProcess",
        "tuitionAndFees",
        "campusSafety",
        "campusLife",
        "financialAidOptions",
        "scholarshipsAndGrants",
        "studentSupportServices",
        "communicationTone",
        "aiGreetings",
        "frequentlyAskedQuestions",
        "resourceLinks"
    ]
}

Rules:
- Every array must contain 3 concise items unless a field naturally needs more. For aiGreetings, provide exactly 5 friendly one-line greetings and you may reference ${domain}.
- Frequently asked questions must contain at least 5 relevant Q&A pairs; keep answers to 2 short paragraphs or fewer.
- Resource links should list up to 5 useful URLs with descriptive labels pulled from the site.
- If a value is not available, use "" or [] as appropriate.
- Output JSON only (no markdown, no commentary).

---SCRAPED TEXT START---
{{WEBSITE_SCRAPED_CONTENT}}
---SCRAPED TEXT END---
""".strip()


def get_university_general_prompt(scraped_content: str, domain: str) -> str:
    """Build the prompt for shared university knowledge."""
    return (
        GENERAL_PROMPT_TEMPLATE
        .replace("{{WEBSITE_SCRAPED_CONTENT}}", scraped_content)
        .replace("${domain}", domain)
    )


RECRUITER_PROMPT = """
You curate specialized insights for the Recruiter AI agent. Study the scraped text and populate the JSON schema below with grounded data. Do not add extra keys. Use empty strings or arrays when details are unavailable.

{
    "type": "object",
    "title": "RecruiterAISpecialization",
    "properties": {
        "recruitmentHighlights":    { "type": "array", "items": { "type": "string" } },
        "strategicEnrollmentGoals": { "type": "array", "items": { "type": "string" } },
        "targetDemographics":       { "type": "array", "items": { "type": "string" } },
        "keyMessaging":             { "type": "array", "items": { "type": "string" } },
        "featuredCoursesOrMajors":  { "type": "array", "items": { "type": "string" } },
        "applicationDeadlines":     { "type": "array", "items": { "type": "string" } },
        "regionalEventsAndVisits":  { "type": "array", "items": { "type": "string" } }
    },
    "required": [
        "recruitmentHighlights",
        "strategicEnrollmentGoals",
        "targetDemographics",
        "keyMessaging",
        "featuredCoursesOrMajors",
        "applicationDeadlines",
        "regionalEventsAndVisits"
    ]
}

Rules:
- Each array should list 3-5 concise bullet points summarizing the topic.
- Use explicit term names, regions, or audiences whenever available.
- Output JSON only (no markdown, no commentary).

---SCRAPED TEXT START---
{{WEBSITE_SCRAPED_CONTENT}}
---SCRAPED TEXT END---
""".strip()


ADMISSIONS_PROMPT = """
You curate specialized insights for the Admissions AI agent. Study the scraped text and populate the JSON schema below with grounded data. Do not add extra keys. Use empty strings or arrays when details are unavailable.

{
    "type": "object",
    "title": "AdmissionsAISpecialization",
    "properties": {
        "admissionsRequirements":        { "type": "array",  "items": { "type": "string" } },
        "applicationProcessSteps":       { "type": "array",  "items": { "type": "string" } },
        "requiredDocuments":             { "type": "array",  "items": { "type": "string" } },
        "internationalStudentGuidelines":{ "type": "string" },
        "standardizedTestPolicies":      { "type": "string" },
        "transferCreditsPolicy":         { "type": "string" }
    },
    "required": [
        "admissionsRequirements",
        "applicationProcessSteps",
        "requiredDocuments",
        "internationalStudentGuidelines",
        "standardizedTestPolicies",
        "transferCreditsPolicy"
    ]
}

Rules:
- Provide applicationProcessSteps as an ordered list describing each step succinctly.
- Use bullet-style strings for requirements and required documents.
- Summaries should stay within two short paragraphs when a field is a string.
- Output JSON only (no markdown, no commentary).

---SCRAPED TEXT START---
{{WEBSITE_SCRAPED_CONTENT}}
---SCRAPED TEXT END---
""".strip()


FINANCIAL_AID_PROMPT = """
You curate specialized insights for the Financial Aid AI agent. Study the scraped text and populate the JSON schema below with grounded data. Do not add extra keys. Use empty strings or arrays when details are unavailable.

{
    "type": "object",
    "title": "FinancialAidAISpecialization",
    "properties": {
        "typesOfAidAvailable":          { "type": "array",  "items": { "type": "string" } },
        "financialAidApplicationProcess":{ "type": "string" },
        "FAFSADetails":                 { "type": "string" },
        "scholarshipCriteria":          { "type": "array",  "items": { "type": "string" } },
        "paymentPlans":                 { "type": "string" },
        "financialAidDeadlines":        { "type": "array",  "items": { "type": "string" } },
        "workStudyPrograms":            { "type": "string" }
    },
    "required": [
        "typesOfAidAvailable",
        "financialAidApplicationProcess",
        "FAFSADetails",
        "scholarshipCriteria",
        "paymentPlans",
        "financialAidDeadlines",
        "workStudyPrograms"
    ]
}

Rules:
- Highlight concrete program names, eligibility criteria, and deadlines whenever they appear.
- For arrays, include 3-5 focused bullet points.
- Keep string fields to two short paragraphs or fewer.
- Output JSON only (no markdown, no commentary).

---SCRAPED TEXT START---
{{WEBSITE_SCRAPED_CONTENT}}
---SCRAPED TEXT END---
""".strip()


ATHLETICS_PROMPT = """
You curate specialized insights for the Athletics AI agent. Study the scraped text and populate the JSON schema below with grounded data. Do not add extra keys. Use empty strings or arrays when details are unavailable.

{
    "type": "object",
    "title": "AthleticsAISpecialization",
    "properties": {
        "athleticProgramsOffered":        { "type": "array",  "items": { "type": "string" } },
        "scholarshipOpportunities":       { "type": "string" },
        "recruitmentProcessForAthletes":  { "type": "string" },
        "athleticFacilitiesInfo":         { "type": "string" },
        "eligibilityRequirements":        { "type": "array",  "items": { "type": "string" } },
        "gameSchedulesAndResults":        { "type": "string" }
    },
    "required": [
        "athleticProgramsOffered",
        "scholarshipOpportunities",
        "recruitmentProcessForAthletes",
        "athleticFacilitiesInfo",
        "eligibilityRequirements",
        "gameSchedulesAndResults"
    ]
}

Rules:
- When possible, call out specific sports, facilities, or events.
- Limit string fields to two concise paragraphs.
- Output JSON only (no markdown, no commentary).

---SCRAPED TEXT START---
{{WEBSITE_SCRAPED_CONTENT}}
---SCRAPED TEXT END---
""".strip()


CAMPUS_LIFE_PROMPT = """
You curate specialized insights for the Campus Life AI agent. Study the scraped text and populate the JSON schema below with grounded data. Do not add extra keys. Use empty strings or arrays when details are unavailable.

{
    "type": "object",
    "title": "CampusLifeAISpecialization",
    "properties": {
        "housingAndDiningOptions":      { "type": "string" },
        "studentOrganizations":         { "type": "array",  "items": { "type": "string" } },
        "campusEventsCalendar":         { "type": "string" },
        "wellnessAndHealthServices":    { "type": "string" },
        "campusRecreationOptions":      { "type": "string" },
        "diversityAndInclusionPrograms":{ "type": "string" },
        "studentConductAndSupport":     { "type": "string" }
    },
    "required": [
        "housingAndDiningOptions",
        "studentOrganizations",
        "campusEventsCalendar",
        "wellnessAndHealthServices",
        "campusRecreationOptions",
        "diversityAndInclusionPrograms",
        "studentConductAndSupport"
    ]
}

Rules:
- Arrays should list 3-5 notable items or groups.
- Keep narrative fields within two short paragraphs.
- Output JSON only (no markdown, no commentary).

---SCRAPED TEXT START---
{{WEBSITE_SCRAPED_CONTENT}}
---SCRAPED TEXT END---
""".strip()


UNIVERSITY_AGENT_TYPES = {
    "recruiter_ai": {
        "display_name": "Recruiter AI",
        "aliases": ["recruiter", "recruiter ai", "recruitment"],
        "prompt": RECRUITER_PROMPT,
    },
    "admissions_ai": {
        "display_name": "Admissions AI",
        "aliases": ["admissions", "admissions ai", "admission"],
        "prompt": ADMISSIONS_PROMPT,
    },
    "financial_aid_ai": {
        "display_name": "Financial Aid AI",
        "aliases": ["financial aid", "financial_aid", "financial aid ai"],
        "prompt": FINANCIAL_AID_PROMPT,
    },
    "athletics_ai": {
        "display_name": "Athletics AI",
        "aliases": ["athletics", "athletics ai", "sports"],
        "prompt": ATHLETICS_PROMPT,
    },
    "campus_life_ai": {
        "display_name": "Campus Life AI",
        "aliases": ["campus life", "campus", "campus life ai"],
        "prompt": CAMPUS_LIFE_PROMPT,
    },
}


def resolve_agent_key(agent_type: str) -> Optional[str]:
    """Normalize various agent labels to the canonical dictionary key."""
    if not agent_type:
        return None
    normalized = " ".join(agent_type.lower().replace("_", " ").replace("-", " ").split())
    for key, meta in UNIVERSITY_AGENT_TYPES.items():
        if normalized == key.replace("_", " "):
            return key
        if normalized == meta["display_name"].lower():
            return key
        if any(normalized == alias for alias in meta.get("aliases", [])):
            return key
    return None


def get_university_specialized_prompt(agent_key: str, scraped_content: str, domain: str) -> str:
    """Build the prompt for a specific university agent."""
    template = UNIVERSITY_AGENT_TYPES[agent_key]["prompt"]
    return (
        template
        .replace("{{WEBSITE_SCRAPED_CONTENT}}", scraped_content)
        .replace("${domain}", domain)
    )
