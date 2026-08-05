# HeatShift Devpost submission guide

This is the exact upload sequence for the OrionHackathon Devpost form shown in the attached screens. Finish the video and screenshots first. Then complete the form in one sitting, preview it, and submit.

## 1. Prepare the final assets before opening Devpost

Keep these items in one folder before you start the form:

| Asset | What to prepare | Where it goes |
|---|---|---|
| Project name | `HeatShift: Policy-Constrained Service Optimizer` | General info |
| Elevator pitch | The 180-character line below | General info |
| About text | The Markdown block below | About the project |
| Repository link | `https://github.com/kaustubh-dot/HeatShift` | Try it out links |
| Video | One unlisted YouTube recording, 3 to 5 minutes | Video demo link |
| Screenshots | 5 to 6 PNG images at 3:2, each under 5 MB | Image gallery |
| Team details | Full name, role, and Devpost account for every teammate | Team section |

Do not use `localhost`, a file path, an unpushed branch, a private repository, or a temporary share link in Devpost. A judge must be able to open every submitted link without your computer.

## 2. Start the app for screenshots and video

Use saved mode for the recording. It is deterministic and visibly labelled as a saved result presentation.

```powershell
cd C:\Kaustubh\Projects\HeatShift\frontend
npm run build
cd ..
.\.venv\Scripts\python.exe -m uvicorn backend.heatshift.api:app --host 127.0.0.1 --port 8000
```

Open this exact address in a normal browser window:

```text
http://127.0.0.1:8000/?fallback=true
```

Set browser zoom to 100 percent. Close terminals, personal tabs, notifications, and any password manager popup before recording. The complete spoken script is in [release/demo-rehearsal.md](release/demo-rehearsal.md).

## 3. Fill General info

### Project name

Paste this into Project name:

```text
HeatShift: Policy-Constrained Service Optimizer
```

This is 47 characters, so it fits the 60-character field shown in Devpost.

### Elevator pitch

Paste this into Elevator pitch:

```text
HeatShift helps municipal teams plan essential maintenance during extreme heat. It finds the highest service level that meets an approved heat policy, then explains each trade-off.
```

This is 180 characters, so it fits the 200-character field.

Do not add claims about preventing heat illness, guaranteeing compliance, or saving a particular percentage. The project does not have evidence for those claims.

## 4. Fill About the project

Devpost asks for inspiration, what the project does, how it was built, challenges, accomplishments, lessons, and next steps. Paste the following Markdown as one block.

```markdown
## Inspiration

Extreme heat does not pause public maintenance. Roads still need repairs, drainage still needs clearing, and crews still need a schedule that respects the limits their organization has approved. A weather alert tells a supervisor that the day will be difficult. It does not tell them which work order should move, where recovery belongs, or whether a deferred repair can still fit without breaking the policy.

We built HeatShift around that operational gap.

## What it does

HeatShift plans one day of municipal maintenance for a synthetic Demo City. It starts with a service-first counterfactual, then produces a policy-constrained plan using the same crews, jobs, travel times, and heat conditions. The interface makes the trade-off visible through timelines, a schematic service map, route order, recovery, travel, overtime, service value, and solver proof.

The most important interaction starts after a job has been deferred. Selecting that job launches a forced-inclusion counterfactual. HeatShift either finds a feasible alternative, shows the work that would need to move, or proves that no feasible plan exists under the retained commitments. A synthetic +2°C heat shock then re-plans the same day and shows the exact changes.

## How we built it

The frontend is React and TypeScript. FastAPI serves the API and the compiled single-page app. The scheduling engine uses OR-Tools CP-SAT with deterministic inputs, a fixed seed, one search worker, and versioned saved results for repeatable demos.

The model schedules crews, equipment, travel, work, and recovery in 15-minute slots. It first maximizes critical jobs served, then service value, then minimizes travel and overtime. The final tie-breaker minimizes standalone recovery. The frontend receives solver-derived metrics, route sequences, timelines, differences, and proof states instead of recreating planning logic in the browser.

## Challenges we ran into

The hard part was avoiding a polished but misleading planner. A job omitted from one schedule is not necessarily impossible, so we built a separate forced-inclusion solve instead of labelling every deferral as infeasible. We also had to enforce rolling work and recovery rules across a crew's full day, not just inside individual jobs.

We kept the demo reproducible by committing the scenario, policy, and saved solver outputs. That makes the result inspectable and gives judges a reliable fallback if live solving is unavailable.

## Accomplishments that we are proud of

HeatShift turns an abstract safety constraint into a concrete operational decision. In the bundled scenario, the service-first plan handles all four critical jobs but creates 11 policy conflicts. The policy-constrained plan is `OPTIMAL`, has zero conflicts, serves three of four critical jobs, and shows exactly what changed.

The deferred bus-route repair is classified as `proven_infeasible` only after a forced-inclusion solve returns `INFEASIBLE` under stated commitments. The +2°C scenario keeps the plan policy-constrained while adding 60 eligible recovery minutes. These are synthetic-demo results, not estimates of real municipal performance.

## What we learned

The useful output is not a black-box schedule. A supervisor needs to understand why work moved and what a change would cost. Showing proof status, constraints, and plan differences made the optimization easier to inspect without pretending the model can replace human judgment.

## What's next for HeatShift

A production version would need an organization-approved policy, local operational data, worker participation, privacy review, worksite measurements, emergency escalation, and jurisdiction-specific validation. Those are deliberately outside this prototype.
```

After pasting, use Devpost preview and check that each heading is visible. Make sure `+2°C`, `OPTIMAL`, `INFEASIBLE`, and `proven_infeasible` render correctly.

## 5. Fill Build with

The form accepts up to 25 tags. Add these one at a time. Stop after the first 15. More tags do not make the project clearer.

```text
Python
TypeScript
React
FastAPI
OR-Tools
CP-SAT
Pydantic
Vite
Uvicorn
Vitest
React Testing Library
Operations Research
Optimization
Climate Tech
Sustainability
```

Do not tag tools that are not part of the project. In particular, do not add OpenAI, GPT, LLM, Google Maps, Docker, or a cloud provider unless you actually used it in the submitted build.

## 6. Add Try it out links

Add the repository first:

```text
https://github.com/kaustubh-dot/HeatShift
```

If you deploy a public demo before submission, add it as a second link. Open that public link in an incognito browser before adding it. If you do not deploy one, leave the second link empty. The repository and video are better than a broken demo link.

Do not put `http://127.0.0.1:8000`, `localhost`, a LAN address, or an internal preview URL here. Devpost judges cannot use them.

## 7. Capture and upload the image gallery

Devpost accepts JPG, PNG, or GIF images, up to 5 MB each. The form recommends a 3:2 ratio and allows up to 15 images. Use 5 or 6 strong images instead of filling every slot.

Capture at 1500 by 1000 pixels or 1200 by 800 pixels. PNG is a safe choice for text-heavy UI. If a file is over 5 MB, export it as a high-quality JPG or reduce it to 1200 by 800 pixels.

Capture these images in this order:

| File name | Screen to capture | Why it earns its place |
|---|---|---|
| `01-heatshift-brief.png` | Tomorrow's Brief with the 41°C alert, crew cards, and policy notice | This is the gallery cover. It explains the problem in one frame. |
| `02-service-first-conflicts.png` | Service-first view with 4 of 4 critical jobs and 11 conflicts | It creates the tension before the solution. |
| `03-policy-constrained-plan.png` | `OPTIMAL` constrained plan with zero conflicts and key metrics | It proves that HeatShift generates a concrete recommendation. |
| `04-timeline-and-map.png` | Full timeline with the schematic service map | It shows the product is a real planning interface, not a metric card. |
| `05-forced-inclusion-diagnosis.png` | Bus-route `proven_infeasible` diagnosis and intervention evidence | This is the strongest differentiator. |
| `06-heat-shock-replan.png` | +2°C heat-shock result with the recovery-added change | It shows the plan can respond to changing conditions. |

For every screenshot:

1. Keep the browser at 100 percent zoom.
2. Wait until the page has finished any animation.
3. Capture only the application window. Do not include the address bar, desktop, terminal, or browser extensions.
4. Check that text is large enough to read on a laptop.
5. Open the exported image once before uploading it.

Upload `01-heatshift-brief.png` first. Devpost commonly uses the first gallery image as the visual introduction to the project.

## 8. Record, upload, and add the video demo

Record the complete flow in [release/demo-rehearsal.md](release/demo-rehearsal.md). Aim for 4 minutes and 20 seconds. That gives you room for a clean intro and closing without risking a rushed five-minute video.

### Recording checklist

1. Record one continuous take from `?fallback=true`.
2. Show the brief, service-first counterfactual, constrained plan, deferred-job diagnosis, and +2°C response.
3. Keep the policy boundary visible when you make safety-related statements.
4. State the exact figures only when they are visible on screen.
5. Avoid background music. Clear narration and readable UI are more useful.
6. Do not show code for more than a few seconds. The video should demonstrate the product.

### Upload to YouTube

1. Sign in to the team's YouTube account.
2. Click Create, then Upload videos.
3. Upload the final MP4.
4. Use this title:

   ```text
   HeatShift | OrionHackathon 2026 Demo
   ```

5. Use this description:

   ```text
   HeatShift is a municipal maintenance planning prototype for extreme heat. It compares service-first and policy-constrained plans, diagnoses deferred work with counterfactual optimization, and re-plans after a synthetic +2°C heat shock.

   Source code: https://github.com/kaustubh-dot/HeatShift

   The demo scenario and policy are synthetic. HeatShift is not medical, legal, safety, or compliance guidance.
   ```

6. Set visibility to Unlisted. Do not set it to Private, because judges need the URL to watch it.
7. Wait until YouTube finishes HD processing.
8. Open the watch URL in a private or incognito window. Watch the first 30 seconds and the diagnosis section.
9. Copy the watch URL, not the YouTube Studio editing URL.
10. Paste it into Devpost's required Video demo link field.

## 9. Additional info for judges and organizers

The Additional info file upload in the screenshot is optional. Leave it blank unless the organizer specifically asks for a file or you have a polished one-page PDF. Do not upload a random repository ZIP or a rough draft simply because the field exists.

If you do create a one-page PDF, it should contain only the title, the 180-character pitch, the five evidence figures, the stack, the repository URL, the video URL, and the synthetic-policy disclosure. Keep it under 35 MB.

## 10. Add team details

For each teammate, add the correct Devpost account and one specific role. Good role labels are:

- Product, optimization, and backend
- Frontend and interaction design
- Testing, demo, and submission

Do not list a person who did not consent to be on the submission. The hackathon page currently allows teams of up to five people. Check the live rule once more before adding anyone.

## 11. Preview and final audit

Before clicking Submit, open Devpost preview and check every item below.

### Content

- [ ] Project name is exactly `HeatShift: Policy-Constrained Service Optimizer`.
- [ ] Elevator pitch is present and not over 200 characters.
- [ ] The About section has all seven headings and no unfinished template text.
- [ ] The wording says the scenario and policy are synthetic.
- [ ] The wording does not claim medical validation, legal compliance, prevention of heat illness, or a real-world impact percentage.
- [ ] Build tags match the actual stack.

### Links and media

- [ ] The GitHub repository opens while logged out.
- [ ] The repository default branch is `main` and contains the current documentation.
- [ ] The video URL opens in a private or incognito window.
- [ ] The video is unlisted or public, never private.
- [ ] The video has audible narration and readable on-screen text.
- [ ] The first gallery image is the Tomorrow's Brief cover image.
- [ ] Every gallery image is 3:2 or close to it and under 5 MB.
- [ ] No screenshot contains a token, email, notification, personal data, terminal, or unrelated browser tab.

### Final click

- [ ] Every teammate has confirmed their inclusion.
- [ ] You have checked the deadline on the live OrionHackathon page.
- [ ] You have saved the Devpost draft before the final review.
- [ ] You are ready to make the public submission.

Click Submit only after this list is complete. Then open the public project page once, check the gallery, the video, and the GitHub link, and save that public URL for your team.
