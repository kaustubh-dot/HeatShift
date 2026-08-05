# HeatShift demo recording script

Use this script to record one clean four-minute Devpost demo. Record from the deterministic saved mode so every figure shown in the video matches the committed evidence.

## Before recording

1. Build and start the production-shaped app from the repository root.

   ```powershell
   cd frontend
   npm run build
   cd ..
   .\.venv\Scripts\python.exe -m uvicorn backend.heatshift.api:app --host 127.0.0.1 --port 8000
   ```

2. Open `http://127.0.0.1:8000/?fallback=true` in a normal browser window.
3. Set the browser zoom to 100 percent. Close unrelated tabs, notifications, terminals, and private information.
4. Start the screen recording. Capture the browser window only, with microphone audio enabled.
5. Wait for the brief to finish loading before speaking.

## Four-minute script

| Time | On-screen action | Spoken script |
|---|---|---|
| 0:00 to 0:20 | Start on Tomorrow's Brief. Keep the temperature, crews, work-order count, and policy notice visible. | "This is HeatShift, a planning tool for municipal maintenance during extreme heat. Tomorrow's synthetic Demo City scenario reaches 41°C. It has three crews and twelve work orders." |
| 0:20 to 0:40 | Point to the policy disclosure or Trust Bar. | "The policy shown here is synthetic and organization-supplied. HeatShift applies the policy to a plan. It does not provide medical advice, certify compliance, or replace supervisor judgment." |
| 0:40 to 1:05 | Click Plan Transformation. Pause on the service-first view. | "First, I ask what happens if we prioritize service before applying the heat-policy constraints. This counterfactual serves all four critical jobs and reaches service value 400, but it creates 11 policy conflicts. That makes it useful as a comparison, not as a recommendation." |
| 1:05 to 1:45 | Trigger or reveal the policy-constrained plan. Show the proof card, headline metrics, timeline, and schematic map. | "Now HeatShift solves the same day under the policy. This result is OPTIMAL. It serves three of four critical jobs, has service value 368, zero policy conflicts, 160 travel minutes, and zero overtime. The timeline and schematic map show where crews work, travel, and recover. The solver status is visible because the wording of the result depends on what was actually proven." |
| 1:45 to 2:10 | Point out the deferred bus-route repair and its plan difference. | "One job, the bus-route pavement repair, is deferred. HeatShift does not call that job impossible just because it is missing from this plan. Instead, it treats the deferral as a question that needs evidence." |
| 2:10 to 2:55 | Click Why / What-if. Open the bus-route diagnosis and let the proof and interventions appear. | "I force the bus-route repair into a new solve while retaining the stated commitments. The diagnosis is proven infeasible, with an INFEASIBLE proof. HeatShift also shows the rules that bind and four bounded interventions it tested. That is the difference between saying a job was not selected and showing why it cannot be retained under this version of the plan." |
| 2:55 to 3:30 | Click Apply +2°C Heat Shock. Keep the resulting metrics and changed decision visible. | "Next, I apply a synthetic two-degree heat shock. The re-plan is still OPTIMAL and still has zero policy conflicts. It adds 60 eligible recovery minutes, and the interface lists the decision that changed. The shift is visible instead of being hidden behind a new total." |
| 3:30 to 4:00 | Return attention to solver proof, the headline, or the architecture link in the repository. | "HeatShift uses a React and TypeScript interface, a FastAPI service, and an OR-Tools CP-SAT model. The scenario, policy, and saved solver outputs are versioned in the repository, so judges can reproduce the demo without accounts, API keys, or external data services." |
| 4:00 to 4:20 | End with the policy disclosure or limits section. | "This is a one-day synthetic prototype. It is not a medical, legal, safety, or routing certification system. Its purpose is to make the service trade-offs created by an approved heat policy clear and testable." |

## If something goes wrong while recording

- If the page takes more than a few seconds to settle, reload the same `?fallback=true` URL and restart the recording.
- If a click misses, restart from the beginning. A clean single take is more credible than a jump cut between states.
- If audio is too low, record a short ten-second test, listen once with headphones, then record the full take.
- If you need a shorter video, remove the architecture paragraph but keep the safety boundary in the closing.

## Review before upload

Watch the finished recording twice.

1. First pass with sound: confirm every number is spoken correctly and the explanation sounds natural.
2. Second pass muted: confirm the important figures, solver statuses, and plan changes remain readable.
3. Confirm there is no unrelated notification, personal data, API token, or terminal output on screen.
4. Confirm the video shows the opening brief, constrained plan, diagnosis, and heat shock in one continuous story.

Upload the final file to YouTube as Unlisted. Copy its watch URL into Devpost's required Video demo link field. Do not use a local file path or a localhost URL in Devpost.
