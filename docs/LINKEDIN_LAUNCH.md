# LinkedIn launch package

Uses the real screenshots already in [`docs/screenshots/`](screenshots/) — all captured
against a seeded demo account on a throwaway database schema, not production data.

**The frontend is live:** https://careerops-web-ptuv.onrender.com — replace `[link]` in
the post copy below with that URL, and `[github link]` with the repository URL.

## Screenshot picks

| Order | File | Why |
|---|---|---|
| 1 | `02-dashboard.png` | Strongest single image: charts, pipeline, upcoming interviews — shows the whole product at a glance. |
| 2 | `12-board-dragging.png` | A card mid-drag on the Kanban board — motion/interactivity reads well even as a static image. |
| 3 | `13-assistant-match.png` | The AI match score with its explanation — the most distinctive feature, and it shows the reasoning, not just a number. |
| 4 | `16-assistant-interview-prep.png` | Interview prep questions — makes the AI assistant feel concretely useful, not just a gimmick. |
| 5 | `04-interviews.png` | Interview calendar — rounds out the feature set. |
| 6 | `18-mobile-assistant.png` | One mobile shot, to show the responsive layout without using up the carousel on repeats. |

LinkedIn image posts read best as a carousel of 4–6 images or a single strong one; use
either picks 1–4 (quality over quantity) or all 6 if posting a carousel/PDF.

## Suggested 30–60 second demo video

A screen recording, not a produced video — this is a solo project, authenticity reads
better than polish. Silent with on-screen captions is fine (most LinkedIn video is
watched muted); a short voiceover works too if you're comfortable with it.

**Shot list** (~50 seconds total; cut any shot to hit 30s if needed — keep shots 2, 5 and 6, they're the ones people remember):

| # | Seconds | Shot | Caption (if silent) |
|---|---|---|---|
| 1 | 0–4 | Landing page, scroll to the feature grid | "I built a full job-search tracker from scratch" |
| 2 | 4–10 | Dashboard: hover/point at the chart and pipeline | "FastAPI + PostgreSQL backend, React frontend" |
| 3 | 10–18 | Board: drag one card from "Applied" to "Interview" | "Drag-and-drop Kanban, saved instantly" |
| 4 | 18–22 | Interview calendar: click a day with an interview | "Interview calendar with real scheduling" |
| 5 | 22–35 | AI assistant: pick a job → show the match score animating in → scroll to the missing/matched skills | "A built-in AI assistant — free, no API key, your data never leaves the server" |
| 6 | 35–45 | AI assistant: switch to the Interview prep tab, expand one question | "Generates interview questions specific to the role" |
| 7 | 45–50 | Back to landing or a GitHub repo shot | "Open source — link in the post" |

Recording tips:
- Use the browser at 1440×900 (desktop) so the recording doesn't look cramped; zoom the
  OS display scale down first if the text looks huge.
- Move the mouse deliberately and pause 1–2 seconds on each screen before moving on —
  edits feel jumpy if cuts come too fast.
  Free screen recorders: OBS Studio, or the Xbox Game Bar (Win+G) on Windows.
- Export at 1080p, keep the file under LinkedIn's 5 GB / 10-minute limit (trivial at
  this length), and add captions by hand if going silent — LinkedIn's auto-captions are
  inconsistent.

## Post copy (three lengths — pick one)

### Short

> Built CareerOps: a job-application tracker with a twist — a free, built-in AI
> assistant that scores how well your profile matches a job, reviews your CV and
> preps you for the interview. No API key, nothing sent to a third party; the
> analysis runs on the same server as everything else.
>
> FastAPI + PostgreSQL + React/TypeScript. 350+ backend tests, 65+ frontend tests,
> real browser verification, CI on every change.
>
> Live demo: [link] · Code: [github link]
>
> #buildinpublic #fastapi #react #postgresql #softwareengineering

### Medium

> I kept my job search organised the way I'd want a tool to work, so I built it:
> **CareerOps**.
>
> It tracks applications, companies and interviews — table view, Kanban board,
> calendar, dashboard — the usual. What makes it different is the AI career
> assistant: it analyses a job description, scores how well your skills match it
> (and explains *why*, not just a number), reviews your CV against that job, and
> generates interview questions specific to the role.
>
> The analyzer is **free and built-in** — no OpenAI/Anthropic key, nothing leaves
> the server. I wanted something I could run without a monthly AI bill, and that
> doesn't send a stranger's CV to a third party by default.
>
> Stack: FastAPI, PostgreSQL, SQLAlchemy/Alembic on the backend; React, TypeScript,
> TanStack Query, Tailwind on the frontend. 350+ backend tests and 65+ frontend
> tests, migrations tested for upgrade *and* rollback, CI on every PR, deployed on
> Render.
>
> Try it: [link]
> Code (it's all public): [github link]
>
> #buildinpublic #softwareengineering #fastapi #react #opensource

### Long (storytelling)

> A few months ago I was tracking job applications in a spreadsheet, like everyone
> does, and like everyone, losing track of which recruiter I'd actually replied to.
> So I built the tool I wanted instead.
>
> **CareerOps** started as a weekend CRUD API and turned into a full-stack app:
> applications, companies and interviews with a dashboard, a drag-and-drop Kanban
> board and a calendar — plus an AI career assistant I'm genuinely proud of.
>
> Paste a job description and it tells you which skills are required vs.
> nice-to-have (with the exact line it found them on), scores how well you match —
> *with the reasoning shown*, not a black-box number — reviews your CV against that
> job, and writes interview questions specific to the role, including ones about the
> skills you're missing.
>
> The analyzer is rule-based and runs entirely on my own server — no OpenAI key, no
> per-request cost, nothing sent anywhere else. I wanted to be able to run this for
> free indefinitely, and I didn't want to default to sending people's CVs to a third
> party.
>
> Under the hood: FastAPI + PostgreSQL + SQLAlchemy/Alembic, React + TypeScript +
> TanStack Query on the frontend, 350+ backend tests and 65+ frontend tests,
> database migrations tested both forward and backward, GitHub Actions CI on every
> change, deployed on Render.
>
> It's live and the code is public — would love feedback, especially on the
> matching algorithm.
>
> Live: [link]
> Source: [github link]
>
> #buildinpublic #fastapi #react #postgresql #opensource #softwareengineering #careeradvice

## Comment-ready follow-ups (post these as the first comment or save for replies)

- "What's the match score actually weighing?" → "Skills are 85% of it (required skills
  count double, soft skills count half), years of experience the other 15% when both
  sides state it. Full write-up's in the README."
- "Is this safe to put a real CV into?" → "Yes — the built-in analyzer runs on the same
  server, nothing is sent to OpenAI/Anthropic/etc. Privacy page has the details: [link]/privacy"
- "Open source?" → "Yes, MIT licensed: [github link]"

## Checklist before posting

- [x] Frontend is actually live at the link you're posting — https://careerops-web-ptuv.onrender.com
- [x] Register → full flow → delete account, manually, as a final human check (done during launch verification, with two separate accounts, including the isolation check)
- [ ] `scripts/smoke_test.py` passed against production (not run in this pass — the manual check above covered the same flows)
- [ ] Screenshots/video show no leftover test data you don't want public (the ones in `docs/screenshots/` are already clean demo data)
- [x] GitHub repo README has the live link at the top
