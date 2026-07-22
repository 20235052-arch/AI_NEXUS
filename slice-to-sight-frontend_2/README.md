# From Slice to Sight — Frontend (Dev A's part)

This is a **fully working app right now**, running entirely on fake data.
No backend needed yet — that's intentional, so you can build/demo/test your
whole part independently while C/D/E finish their real endpoints.

## How to run it

```bash
npm install
npm run dev
```

Open the URL it prints (usually `http://localhost:5173`). You should be able to:
1. Click the upload box, pick any file (content doesn't matter yet, it's mocked)
2. Watch it "process" for a couple seconds
3. Land in the workspace: see a fake CT slice with a slider, a placeholder 3D icon, measurements, and the AI Trust Panel
4. Click the placeholder icon -> see the anatomy explanation panel appear
5. Type a question and hit Ask -> get a mock answer back

That's your entire pipeline, steps 1-5, working end to end.

## File map

```
src/
  api.js                    <- EVERY backend call lives here. One switch: MOCK_MODE.
  App.jsx                   <- decides which screen to show (upload/status/workspace)
  index.css                 <- all styling
  components/
    UploadScreen.jsx         <- Step 1: upload
    StatusScreen.jsx         <- Step 2: identify (polls status)
    Workspace.jsx            <- Steps 3-5: layout that holds everything below
    SliceViewer.jsx          <- 2D slider
    Placeholder3DViewer.jsx  <- STAND-IN for Dev B's real 3D component
    MeasurementsPanel.jsx    <- Step 4: volume/area/etc
    TrustPanel.jsx           <- confidence score + flags
    AnatomyPanel.jsx         <- Step 5: click explanation + ask a question
```

## What to do next, in order

1. **Run it, click through it, get familiar** - nothing to change yet, just see how it behaves.
2. **Show it to the team** - this proves your whole flow to everyone before real data exists.
3. **When Dev C's `/api/upload` and `/api/status` endpoints are actually running:**
   open `src/api.js`, change:
   ```js
   export const MOCK_MODE = true;
   ```
   to:
   ```js
   export const MOCK_MODE = false;
   ```
   That's it - every component automatically switches to real fetch calls. No other file needs to change.
4. **When Dev B's real 3D component is ready:** open `src/components/Workspace.jsx`,
   replace the `<Placeholder3DViewer ... />` line with Dev B's real component.
   Keep the same two props (`meshUrl`, `onStructureClick`) and nothing else breaks.
5. **When Dev E's `/api/ask` and `/api/quiz` are ready:** they already match the
   shape `askQuestion()` and `getQuiz()` expect in `api.js` - just flip MOCK_MODE.

## If something breaks when you flip MOCK_MODE off

- **CORS error in the browser console** -> not your bug, tell Dev C (their FastAPI
  server needs `CORSMiddleware` enabled - it's in the backend starter code)
- **404 on a specific endpoint** -> check `API_CONTRACT.json`, confirm the URL path matches exactly
- **Response shape looks different than expected** -> the component expects the exact
  JSON keys shown in the mock functions in `api.js` - compare against what the real
  backend actually returns
