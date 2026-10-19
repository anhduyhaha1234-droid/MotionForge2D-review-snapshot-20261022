"""
Reddit Auto-Poster for Gumroad Product Distribution
Uses PRAW (Python Reddit API Wrapper) to post value-first content
to relevant subreddits with Gumroad product links.

Usage:
    from reddit_poster import post_to_reddit
    result = post_to_reddit(
        title="I built 3 free N8N workflows that saved me 20hrs/week",
        body="Here's what they do...",
        subreddit="Solopreneur",
        link="https://duyhoivu.gumroad.com/l/xxx",
    )
"""

import os
import sys
import json
import time
import random

try:
    import praw
except ImportError:
    praw = None

# Load .env from parent dir
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "gumroad_products", ".env")
    load_dotenv(_env_path)
except Exception:
    pass


# === Subreddit presets by niche ===
SUBREDDIT_PRESETS = {
    "n8n": ["n8n", "Automation", "Solopreneur", "SideHustle", "NoCode"],
    "automation": ["Automation", "n8n", "Make", "Zapier", "Solopreneur"],
    "midjourney": ["Midjourney", "AIArt", "StableDiffusion", "ArtificialIntelligence"],
    "chatgpt": ["ChatGPT", "ClaudeAI", "Solopreneur", "Entrepreneur"],
    "solopreneur": ["Solopreneur", "SideHustle", "Entrepreneur", "Freelance"],
    "creator": ["CreatorEconomy", "TikTokCreators", "YouTubeStartups", "ContentCreation"],
    "prompt_packs": ["PromptEngineering", "ChatGPT", "Midjourney", "Solopreneur"],
}


def _get_reddit_client():
    """Create and return a PRAW Reddit client from env vars."""
    if praw is None:
        raise ImportError("praw not installed. Run: pip install praw")

    client_id = os.environ.get("REDDIT_CLIENT_ID", "")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")
    username = os.environ.get("REDDIT_USERNAME", "")
    password = os.environ.get("REDDIT_PASSWORD", "")
    user_agent = os.environ.get("REDDIT_USER_AGENT", "AIProductBot/1.0")

    if not all([client_id, client_secret, username, password]):
        missing = []
        if not client_id: missing.append("REDDIT_CLIENT_ID")
        if not client_secret: missing.append("REDDIT_CLIENT_SECRET")
        if not username: missing.append("REDDIT_USERNAME")
        if not password: missing.append("REDDIT_PASSWORD")
        raise ValueError(f"Missing Reddit credentials: {', '.join(missing)}")

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        username=username,
        password=password,
        user_agent=user_agent,
    )


def format_value_post(title, body, link, cta=None):
    """Format a Reddit value-first post with Gumroad link.

    Reddit rules:
    - 80% value, 20% promotion
    - Link goes at the bottom, not the title
    - Title should be intriguing, not salesy
    """
    if cta is None:
        cta = "If you want the full PDF + all workflow templates, I put them here (free/PWYW):"

    formatted = f"""{body}

---

{cta}
{link}

---

*If this was helpful, an upvote helps others find it too. Happy to answer questions about N8N/automation in the comments!*"""

    return formatted


def post_to_reddit(title, body, subreddit, link=None, flair=None,
                   dry_run=False, niche=None):
    """Post a value-first article to a subreddit.

    Args:
        title: post title (keep under 300 chars, no clickbait)
        body: markdown body (80% value content)
        subreddit: target subreddit name (without r/)
        link: optional Gumroad link to include at bottom
        flair: optional flair text
        dry_run: if True, format but don't actually post
        niche: niche key for auto-subreddit selection (overrides subreddit)

    Returns:
        dict with: success, subreddit, url (if posted), id
    """
    result = {
        "success": False,
        "subreddit": subreddit,
        "url": None,
        "post_id": None,
        "dry_run": dry_run,
    }

    # Format the post
    if link:
        full_body = format_value_post(title, body, link)
    else:
        full_body = body

    if dry_run:
        print(f"[DRY RUN] Would post to r/{subreddit}:")
        print(f"  Title: {title}")
        print(f"  Body length: {len(full_body)} chars")
        print(f"  Link: {link or 'none'}")
        result["success"] = True
        result["body_preview"] = full_body[:500]
        return result

    # Actually post
    try:
        reddit = _get_reddit_client()
        sub = reddit.subreddit(subreddit)

        submission = sub.submit(
            title=title,
            selftext=full_body,
            flair_text=flair,
        )

        result["success"] = True
        result["url"] = f"https://reddit.com{submission.permalink}"
        result["post_id"] = submission.id
        print(f"Posted to r/{subreddit}: {result['url']}")

    except Exception as e:
        result["error"] = str(e)
        print(f"Post failed to r/{subreddit}: {e}")

    return result


def post_to_subreddits(title, body, subreddits, link=None, flair=None,
                       delay_between=300, dry_run=False):
    """Post the same content to multiple subreddits with delays.

    Reddit rate limits: max 1 post per subreddit per 10 minutes.
    """
    results = []
    for i, sub in enumerate(subreddits):
        if i > 0 and not dry_run:
            wait = delay_between + random.randint(0, 60)
            print(f"Waiting {wait}s before posting to r/{sub}...")
            time.sleep(wait)

        print(f"\n[{i+1}/{len(subreddits)}] Posting to r/{sub}...")
        r = post_to_reddit(title, body, sub, link=link, flair=flair, dry_run=dry_run)
        results.append(r)

    passed = sum(1 for r in results if r["success"])
    print(f"\nDone: {passed}/{len(results)} posts successful")
    return results


# === Pre-built post templates ===

TEMPLATES = {
    "n8n_workflow_share": {
        "title": "I automated my entire solopreneur workflow with 3 free N8N templates",
        "body": """After spending 6+ months building automation workflows for my solo business, I distilled everything into 3 templates that handle the repetitive stuff:

**Workflow 1: Lead Capture → CRM → Email Sequence**
- Triggers on new form submission (Typeform/Google Forms)
- Validates email, checks for duplicates
- Adds to CRM (Notion/Airtable)
- Sends welcome email sequence

**Workflow 2: Content Repurposing Engine**
- Takes one long-form blog post
- Auto-generates: 5 tweet threads, LinkedIn post, email newsletter
- Schedules via Buffer/Hootsuite API

**Workflow 3: Client Onboarding Automation**
- Triggers on new Gumroad sale
- Creates project in Notion
- Sends welcome packet via email
- Adds to invoicing system

Each workflow is a JSON import file — just drag into N8N and configure your API keys.""",
        "subreddits": SUBREDDIT_PRESETS["n8n"],
    },
    "midjourney_prompts": {
        "title": "42 Midjourney v6 prompts that actually produce photorealistic results",
        "body": """I tested hundreds of prompt variations and found the specific structure that consistently produces photorealistic images in Midjourney v6 and Flux.1.

**The formula:**
[Subject] + [Camera/lens] + [Lighting] + [Mood] + [Technical params]

**Examples that work:**

Portrait: "Portrait of a woman, Rembrandt lighting, 85mm f/1.4, shallow DOF, warm tones --ar 3:4 --v 6"

Product: "Hero shot of a watch on marble, 90mm macro, three-point studio lighting, dark background --ar 1:1 --v 6"

Architecture: "Modern house at twilight, 24mm wide angle, interior lights glowing, blue hour sky --ar 16:9 --v 6"

The key insight: Midjourney v6 responds to real photography terminology. Use actual lens focal lengths, specific lighting setups, and real camera settings.""",
        "subreddits": SUBREDDIT_PRESETS["midjourney"],
    },
    "solopreneur_prompts": {
        "title": "37 system prompts that run my entire solopreneur business on autopilot",
        "body": """I built a library of system prompts for ChatGPT and Claude that automate every part of my solo business. Here are the categories:

**Copywriting (8 prompts):** Landing pages, email sequences, ad copy, sales letters
**Marketing (7 prompts):** Content calendars, SEO strategy, competitor analysis
**Funnel Building (6 prompts):** Lead magnets, upsell sequences, webinar scripts
**Content Creation (6 prompts):** Blog posts, social media, newsletter
**Business Ops (5 prompts):** SOPs, pricing strategy, financial projections
**Client Comms (5 prompts):** Proposals, onboarding, feedback collection

The trick is in the system prompt structure:
"You are a [ROLE] with [X years] of experience in [DOMAIN]. Your task is to [SPECIFIC ACTION]. Format your output as [SPECIFIC FORMAT]."

Each prompt includes [VARIABLE] placeholders so you can customize them for any niche.""",
        "subreddits": SUBREDDIT_PRESETS["solopreneur"],
    },
}


if __name__ == "__main__":
    # Demo: format a post
    t = TEMPLATES["n8n_workflow_share"]
    result = post_to_reddit(
        title=t["title"],
        body=t["body"],
        subreddit="Solopreneur",
        link="https://duyhoivu.gumroad.com/l/xxx",
        dry_run=True,
    )
    print(f"\nResult: {json.dumps(result, indent=2)}")
