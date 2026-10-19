# claude-motion

**A motion design toolkit for coding agents.** Remotion skills teach your agent the API. This teaches it taste, makes it check its own frames, and gives it a sound engine. And when the idea is a simulation, not a motion graphic, it renders web sims frame by frame to 60 fps video.

Works with Claude Code and Cursor out of the box (skills in `.claude/skills/`), and with Codex, OpenCode or anything else that reads `AGENTS.md`.

<p align="center">
  <img src="media/preview.gif" width="480" alt="22-second motion graphic made by Claude with this toolkit" />
</p>

<p align="center"><sub>Made by Claude with this toolkit from one prompt and one revision. No After Effects, no stock sounds. <a href="examples/01-effort/">How it was made →</a></sub></p>

<!-- For the version with sound: open this README in the GitHub editor, drag out/effort.mp4 in, and GitHub will turn it into an inline player. -->

## New: web sims → 60 fps video

<p align="center">
  <img src="media/sims/crawlers.gif" width="250" alt="256 spider agents crawling a wall of websites" />
  <img src="media/sims/dossier.gif" width="250" alt="Agents turning one username into a dossier with red threads" />
  <img src="media/sims/engine.gif" width="250" alt="Camera flying through a running rocket engine's chamber" />
</p>

<p align="center"><sub>Made by Claude with this toolkit. Left: <a href="https://x.com/whaleyxbt/status/2106099822088331481">the crawler swarm</a> (340K+ views on X). Middle: <a href="https://x.com/whaleyxbt/status/2106420024286031963">one username → a dossier</a>. Right: a rocket engine explorer with a fly-through and an exploded view.</sub></p>

Some videos are simulations: 256 agents doubling on the beat, a rocket engine the camera flies through. Those are easier to write as a web page than as React, so [`sims/`](sims/) is a second pipeline:

- **One HTML page per piece**, three.js and fonts inlined, works offline. Open it and it plays live.
- **`render(t)` is a pure function of time.** Agents and physics are simulated once at load, so any frame can be drawn on demand.
- **Frame-exact capture.** Headless Chromium steps the page frame by frame into ffmpeg: 60 fps at 1440×1800 (or any size), no matter how slow a frame is.
- **Cuts on the beat.** `beats.py` finds the tempo, bars and drop of a track and hands them to the sim.
- **Three examples to take apart:** [`crawlers`](sims/crawlers/), [`dossier`](sims/dossier/), [`engine`](sims/engine/) (with its sound generated in Python).

```bash
npm install && npx playwright install chromium
npm run sims                                                    # → sims/dist/<name>.html
npm run capture -- engine --size 1080x1350 --out out/engine.mp4  # 1440×1800, 60 fps
```

Ask your agent:

```text
Read sims/README.md and the web-sims skill. Build a 20-second sim of <your idea>
as one HTML page at 1080×1350. Review it with --stills before you render,
then capture it to a 60 fps mp4.
```

## What your agent gets

**Motion rules with numbers.** Easing curves, spring presets, stagger, reading holds, type scale, one-accent color, texture, motivated transitions. Not "make it smooth": `bezier(0.16, 1, 0.3, 1)` for entrances, exits at half the duration, 0.09 s between words. → [`motion-design`](.claude/skills/motion-design/SKILL.md)

**A self-review loop.** Agents can't watch video, but they can look at frames. The agent renders a draft, gets a contact sheet with one timestamped frame per beat, checks it against a list (collisions, clipping, holds, safe area, phone readability) and fixes what it finds before saying it's done. → [`review-loop`](.claude/skills/review-loop/SKILL.md)

**A sound engine.** Pure Python stdlib, no samples, no licenses. Generators for typing, clicks, pops, whooshes, risers, chimes, impacts, textures and pads; a mixer that places sounds on the same timeline as the picture; mastering that hits −14 LUFS by itself. The agent writes one cue sheet per video and adds generators when it needs a new sound. → [`sound-design`](.claude/skills/sound-design/SKILL.md)

**One timeline for everything.** Every beat is a named timestamp in a JSON file. Scenes, sound and review all read it, so retiming the video retimes the sound and the checks with it.

**A reference piece to take apart.** The video above, with reusable components: masked text reveals, rolling numbers, film grain, hand-drawn line boil, a background with drifting grid and glow.

## Quick start

**Let your agent set it up.** Paste this into Claude Code, Cursor, Codex or OpenCode:

```text
Clone https://github.com/whaleyxbt/claude-motion and cd into it.
Check that Node 20+, Python 3 and ffmpeg are installed; install whatever is missing.
Run `npm install` and `npm run build`, then show me out/effort.mp4.
Then read AGENTS.md and the skills in .claude/skills/, and ask me what video I want to make next.
(For simulations and 3D, also run `npx playwright install chromium` and read sims/README.md.)
```

**Or by hand:**

```bash
git clone https://github.com/whaleyxbt/claude-motion && cd claude-motion
npm install
npm run build        # the example video with sound → out/effort.mp4
npm run studio       # live preview
```

Then ask for a video:

```text
Make a 15-second 1080×1080 motion graphic announcing <your thing>.
Follow AGENTS.md: storyboard first, then the timeline, review loop, sound.
```

## How the agent works

```
 idea ─► storyboard ─► timeline.json ─┬─► scenes ─► draft ─► contact sheet ─► look, fix ─┐
                       (every beat)   │                                                  │
                                      │                  ◄──────── repeat ───────────────┘
                                      └─► cue sheet ─► python3 -m sfx ─► waveform + LUFS
                                                                │
                                                 render + mux ─► final MP4
```

| Tool | |
|---|---|
| `npm run studio` | live preview of every composition |
| `npm run sheet -- --video <mp4>` | contact sheets at every beat (`--from 3 --to 5 --every 0.2` to scrub a transition) |
| `python3 -m sfx --list` | sound generators and what each is for |
| `python3 -m sfx sfx/cues/<name>.py` | render a cue sheet to a mastered WAV |
| `npm run wave -- <wav or mp4>` | waveform with beat markers, LUFS and true peak |
| `npm run build` | the example, end to end: sound, render, mux |

<p align="center">
  <img src="media/sheet.png" width="720" alt="Contact sheet the agent reviews: one frame per timeline beat" /><br/>
  <sub>What the agent looks at: one tile per beat, labelled with its timestamp.</sub>
</p>

## The sound engine

A cue sheet is one Python function. Every time comes from the timeline:

```python
from sfx.synth import pop, whoosh

def score(mix, tl):
    s1 = tl["s1"]
    mix.put(s1["title"], whoosh(0.4, 500, 2400, peak=0.45), 0.12)
    for i, t in enumerate(s1["items"]):
        mix.put(t, pop(900 + i * 150, 400), 0.3, pan=-0.4 + i * 0.3)
    mix.typing(s1["typeStart"], s1["typeEnd"], chars=24)
```

`python3 -m sfx sfx/cues/<name>.py` renders it, masters it to −14 LUFS with the true peak kept under −2 dBFS, and writes the WAV. [`sfx/cues/effort.py`](sfx/cues/effort.py) is the full sound design of the example: 128 sounds and a pad.

<p align="center">
  <img src="media/wave.png" width="720" alt="Waveform with timeline beats in coral" /><br/>
  <sub>Sync check: every coral line is a beat from the timeline, and every hit sits on one.</sub>
</p>

## Effort levels for motion work

What works with Claude Opus 5.5 (`/effort` in Claude Code):

| Stage | Effort | Why |
|---|---|---|
| Storyboard, message, hook | `low` | fast back-and-forth, you're in the loop |
| Building scenes | `medium` | the default, good enough for most component work |
| Review loop, retiming, final polish | `high` | this is where checking every frame pays off |
| "Make the whole thing, I'm going for coffee" | `xhigh` / `max` | autonomous end to end, slower and pricier |

## Optional MCP servers

Nothing here needs MCP. These add real capabilities; copy `.mcp.json.example` to `.mcp.json` and keep what you want.

| Server | Adds |
|---|---|
| [`@remotion/mcp`](https://www.remotion.dev/docs/ai/mcp) | searchable Remotion docs, fewer API hallucinations |
| [ElevenLabs](https://github.com/elevenlabs/elevenlabs-mcp) | voiceover and sounds you can't synthesize |
| [Playwright](https://github.com/microsoft/playwright-mcp) | screenshots of a real product UI to animate |
| [Figma](https://help.figma.com/hc/en-us/articles/32132100833559) | pull frames and design tokens straight from your file |

Pair it with the official [Remotion agent skills](https://www.remotion.dev/docs/ai/skills) for API coverage; this toolkit is the design layer on top.

## Gallery

| | |
|---|---|
| [**01 · Spending your effort**](examples/01-effort/) | Claude Code `/effort` explained. 22 s, one prompt + one revision. |
| *yours?* | [Add it →](CONTRIBUTING.md) |

## Requirements

Node 20+, Python 3, ffmpeg. A system Chromium at `/usr/bin/chromium` (or `$REMOTION_BROWSER`) is used if present; otherwise Remotion downloads one on first render.

## License

Code in this repo: [MIT](LICENSE). Remotion itself has its own license: free for individuals and small teams, companies above the threshold need a [company license](https://www.remotion.dev/license).
