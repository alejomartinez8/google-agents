"""SEO and Blog Writing Skills Agent module.

This module initializes the root ADK agent (`seo_skills_agent`) equipped with a
`SkillToolset` containing four reusable skills for blog writing, SEO optimization,
content research, and autonomous skill creation following the agentskills.io specification.

Lab Reference:
    Google Cloud Skills Lab GENAI154: "Use Skills with ADK Agents"
    Course: "Craft ADK Agents with Persistent Memories"
    Path: "Build and Deploy Agents with Agent Development Kit (ADK)"

Key Components:
    - `seo_skill`: Inline skill containing an 9-point on-page SEO optimization checklist.
    - `blog_writer_skill`: Directory skill loaded from `skills/blog-writer/` (style guide reference).
    - `content_research_writer_skill`: Directory skill loaded from `skills/content-research-writer/` (SEO guidelines reference).
    - `skill-creator`: Inline meta-skill with embedded resource specification for authoring new `SKILL.md` files.
    - `skill_toolset`: ADK `SkillToolset` instance bundling all skills into dynamic tools for the agent.
    - `root_agent`: Root ADK `Agent` instance configured with model `gemini-3.5-flash`.
"""
import pathlib
import sys
from google.adk import Agent
from google.adk.skills import load_skill_from_dir, models
from google.adk.tools.skill_toolset import SkillToolset

# ==============================================================================
# 1. Inline Skill: SEO Checklist
# ==============================================================================
# Demonstrates defining a Skill directly in code using models.Skill.
# Provides a structured 9-step checklist for evaluating blog posts for SEO best practices.
seo_skill = models.Skill(
    frontmatter=models.Frontmatter(
        name="seo-checklist",
        description=(
            "SEO optimization checklist for blog posts. Covers title tags,"
            " meta descriptions, heading structure, keyword placement,"
            " and readability best practices."
        ),
    ),
    instructions=(
        "When optimizing a blog post for SEO, check each item:\n\n"
        "1. **Title**: 50-60 chars, primary keyword near the start\n"
        "2. **Meta description**: 150-160 chars, includes a call-to-action\n"
        "3. **Headings**: H2/H3 hierarchy, keywords in 2-3 headings\n"
        "4. **First paragraph**: Primary keyword in first 100 words\n"
        "5. **Keyword density**: 1-2%, never forced or awkward\n"
        "6. **Paragraphs**: 2-3 sentences max, use bullet lists often\n"
        "7. **Links**: 2-3 internal + 3-5 external to authoritative sources\n"
        "8. **Images**: Alt text with keywords, compressed, descriptive names\n"
        "9. **URL slug**: Short, keyword-rich, hyphenated\n\n"
        "Review the content against each item and suggest specific improvements."
    ),
)

# Base path pointing to the local skills directory containing directory-based skills
SKILLS_PATH = pathlib.Path(__file__).parent / "skills"


# ==============================================================================
# Helper Function: Load Directory Skill
# ==============================================================================
def _load_skill(name: str) -> models.Skill:
    """Loads a directory-based skill from the local `skills/` folder by directory name.

    Directory-based skills must contain a `SKILL.md` file with YAML frontmatter
    (name, description) and instructions, plus an optional `references/` subfolder.

    Args:
        name: The folder name of the skill within the `skills/` directory.

    Returns:
        models.Skill: The loaded ADK Skill object.

    Raises:
        Prints a warning to stderr if the specified skill directory does not exist.
    """
    path = SKILLS_PATH / name
    if not path.exists():
        print(f"Warning: Skill directory '{name}' not found at {path}", file=sys.stderr)
    return load_skill_from_dir(path)


# ==============================================================================
# 2. Directory-Based Skills Loading
# ==============================================================================
# Load blog-writer skill from skills/blog-writer/ (includes references/style-guide.md)
blog_writer_skill = _load_skill("blog-writer")

# Load content-research-writer skill from skills/content-research-writer/ (includes references/seo-guidelines.md)
content_research_writer_skill = _load_skill("content-research-writer")


# ==============================================================================
# 3. Inline Meta-Skill: Skill Creator
# ==============================================================================
# Meta-skill equipped with embedded reference documentation (skill specification and working example).
# Enables the LLM to generate new, fully compliant SKILL.md files upon request.
skill_creator = models.Skill(
    frontmatter=models.Frontmatter(
        name="skill-creator",
        description=(
            "Creates new ADK-compatible skill definitions from requirements."
            " Generates complete SKILL.md files following the Agent Skills"
            " specification at agentskills.io."
        ),
    ),
    instructions=(
        "When asked to create a new skill, generate a complete SKILL.md file.\n\n"
        "Read `references/skill-spec.md` for the format specification.\n"
        "Read `references/example-skill.md` for a working example.\n\n"
        "Follow these rules:\n"
        "1. Name must be kebab-case, max 64 characters\n"
        "2. Description must be under 1024 characters\n"
        "3. Instructions should be clear, step-by-step\n"
        "4. Reference files in references/ for detailed domain knowledge\n"
        "5. Keep SKILL.md under 500 lines — put details in references/\n"
        "6. Output the complete file content the user can save directly\n"
    ),
    resources=models.Resources(
        references={
            "skill-spec.md": (
                "# Agent Skills Specification (agentskills.io)\n\n"
                "## SKILL.md Format\n"
                "Every skill directory must contain a SKILL.md file.\n\n"
                "### Frontmatter (YAML)\n"
                "```yaml\n"
                "---\n"
                "name: my-skill-name          # kebab-case, max 64 chars\n"
                "description: What this skill does.  # max 1024 chars\n"
                "---\n"
                "```\n\n"
                "### Body (Markdown)\n"
                "The body contains the skill instructions. Write clear,\n"
                "step-by-step instructions the agent will follow.\n\n"
                "### Directory Structure\n"
                "```\n"
                "my-skill-name/\n"
                "  SKILL.md           # Required: metadata + instructions\n"
                "  references/        # Optional: detailed reference docs\n"
                "  assets/            # Optional: templates, data files\n"
                "  scripts/           # Optional: executable scripts\n"
                "```\n\n"
                "### Key Rules\n"
                "- Directory name MUST match the `name` field in frontmatter\n"
                "- Name must be kebab-case: ^[a-z0-9]+(-[a-z0-9]+)*$\n"
                "- Description is what the LLM uses to decide when to load the skill\n"
                "- Keep instructions actionable — tell the agent WHAT to do\n"
                "- Use `load_skill_resource` references for detailed docs\n"
            ),
            "example-skill.md": (
                "# Example: Code Review Skill\n\n"
                "```markdown\n"
                "---\n"
                "name: code-review\n"
                "description: Reviews Python code for correctness, style, "
                "and performance. Checks for common bugs, PEP 8 compliance, "
                "and suggests optimizations.\n"
                "---\n\n"
                "# Code Review Instructions\n\n"
                "When asked to review code:\n\n"
                "## Step 1: Read the Guidelines\n"
                "Use `load_skill_resource` to read `references/review-checklist.md`.\n\n"
                "## Step 2: Analyze\n"
                "Check the code against each item in the checklist.\n\n"
                "## Step 3: Report\n"
                "Provide findings organized by severity:\n"
                "- **Critical**: Bugs, security issues\n"
                "- **Warning**: Style violations, performance concerns\n"
                "- **Info**: Suggestions for improvement\n"
                "```\n"
            ),
        }
    ),
)

# ==============================================================================
# 4. Skill Toolset Assembly
# ==============================================================================
# Wrap all four skills into a SkillToolset, exposing skill selection and resource reading tools to the agent
skill_toolset = SkillToolset(
    skills=[
        seo_skill,
        blog_writer_skill,
        content_research_writer_skill,
        skill_creator,
    ]
)

# ==============================================================================
# 5. Root ADK Agent Definition
# ==============================================================================
# Define the root LLM agent that handles user interactions and utilizes skill_toolset
root_agent = Agent(
    model="gemini-3.5-flash",
    name="seo_skills_agent",
    description="A blog-writing and SEO optimization agent powered by reusable skills.",
    instruction=(
        "You are a blog-writing and SEO assistant with specialized skills.\n\n"
        "You have four skills available:\n"
        "- **seo-checklist**: SEO optimization rules (load for SEO review)\n"
        "- **blog-writer**: Writing structure and style guide (load for writing)\n"
        "- **content-research-writer**: Content research, competitive analysis, and SEO guidelines\n"
        "- **skill-creator**: Generate new skill definitions (load to create skills)\n\n"
        "When the user asks you to write, research, or optimize a blog post:\n"
        "1. Load the relevant skill(s) to get detailed instructions\n"
        "2. Use `load_skill_resource` to access reference materials\n"
        "3. Follow the skill's step-by-step instructions\n"
        "4. Apply multiple skills together when appropriate\n\n"
        "When the user asks you to create a new skill:\n"
        "1. Load the skill-creator skill\n"
        "2. Read the specification and example references\n"
        "3. Generate a complete SKILL.md that follows the spec\n\n"
        "Always explain which skill you're using and why."
    ),
    tools=[skill_toolset],
)


