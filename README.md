# 42Prague DigiEduHack Hackathon

> Welcome! This is the main repository for submitting your team's solution for the DigiEduHack Hackathon at 42Prague.

## ⚠️ First Steps: Read the Guidelines & Get Data

Before you start, please **carefully read all documents** in the `resources/` folder. They contain the rules, guidelines, data samples, and the template you must fill out.

* `resources/DigiEduHack_solution_guidelines.pdf`: Contains all rules, guidelines, and judging criteria.
* `resources/Digi_Edu_Hack_Solution_Canvas_2025.pdf`: This is the **mandatory template** you must fill out and send to the [DigiEduHack submission platform](https://digieduhack.com/host/submit-solution?relatedChallenge=106879). Only 1 team member is submitting the solution.
* **[Download Data Samples](https://drive.google.com/drive/folders/1KVzBOg1ktjgJd16rlyVDPniwRMDWNYYt?usp=sharing)**: Contains data samples provided for the challenge.

---

## 🚀 How to Submit Your Solution

We use the standard GitHub **Fork & Pull Request** workflow. This is the only way to submit your project. Follow these steps carefully.



### Step 1: Fork This Repository

Click the **"Fork"** button at the top-right corner of this page. This will create a complete copy of this repository under your personal GitHub account.

### Step 2: Create Your Branch

On **your forked repository**, create a new branch to hold your work. **Please name this branch after your team.**

You can do this locally on your computer after cloning your fork:

```bash
# Clone your fork (replace YOUR-USERNAME)
git clone [https://github.com/YOUR-USERNAME/42Prague_digiEduHack_hackathon.git](https://github.com/YOUR-USERNAME/42Prague_digiEduHack_hackathon.git)
cd 42Prague_digiEduHack_hackathon

# Create and switch to your new branch (replace with your team name)
git checkout -b your-team-name
```

### Step 3: Add Your Project Files

Now it's time to build! Add all your project components to your branch:

1.  **Your Solution:** Add all your source code, folders, dependencies (e.g., `requirements.txt`, `package.json`), and any files needed to run your solution. You can use the `srcs/` folder or create your own structure.
2.  **Solution Canvas:** Fill out the `Digi_Edu_Hack_Solution_Canvas_2025.pdf` template. Add the completed PDF to the root of your branch.
3.  **Pitch Deck:** Add your final pitch (PDF or PPTX format) to the `pitch/` folder.

### Step 4: Commit & Push Your Work

As you work, commit your changes and push them to your fork on GitHub.

```bash
# After making your changes
git add .
git commit -m "Add project files and solution canvas"

# Push your branch to your fork (replace with your team name)
git push origin your-team-name
```

### Step 5: Open a Pull Request

When your submission is complete, it's time to create the Pull Request.

1.  Go to your forked repository on GitHub.
2.  You will see a green button that says **"Compare & pull request"**. Click it.
3.  **Important:** Make sure the "base repository" is `42Prague/42Prague_digiEduHack_hackathon` and the "head repository" is `YOUR-USERNAME/42Prague_digiEduHack_hackathon` (from your team branch).
4.  Use your **Team Name** as the title for the Pull Request.
5.  Click **"Create pull request"**.

That's it! Your submission is now in the queue for review.

## 🔧 Agent Service Configuration

To run the FastAPI service in `srcs/agentic_analysis`, create a `.env` file (or export variables) with the OpenAI settings. The service now uses a single client that switches between the public OpenAI API and Azure OpenAI just by changing the base URL.

```
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://api.openai.com
AZURE_OPENAI_MODEL=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2024-09-01-preview
```

- For the public OpenAI service, keep the endpoint as `https://api.openai.com` (or omit it if you provide it another way) and use a standard API key.
- For Azure OpenAI, set `AZURE_OPENAI_ENDPOINT` to your resource URL, e.g. `https://YOUR-RESOURCE.openai.azure.com`, and `AZURE_OPENAI_MODEL` to your deployment name. Keep the API version aligned with your Azure deployment.
- No other code changes are required—switching the endpoint toggles the correct authentication/URL wiring internally.

You can also override the agent's reasoning depth on a per-request basis by adding a `max_steps` field to the JSON payload sent to `/analyze`. It accepts integers between 1 and 20 and falls back to the server default defined in `.env` if omitted.

### Session-based workflow

The `/analyze` endpoint now orchestrates long-running conversations. Each request returns a `session_id` and streams progress into a lightweight JSON store located at `app/tmp_db.json`:

1. Send a POST to `/analyze` with a `query`. Omit `session_id` to start a fresh session; the response will include the generated identifier.
2. Poll `GET /session/{session_id}` from the frontend (for example, every second) to retrieve the growing message history while the agent reasons and calls tools.
3. For follow-up questions, include the previously issued `session_id` in the next `/analyze` request so the agent retrieves the full conversation context.

The on-disk storage is intentionally simple. Swap out `app/session_store.py` with your production database integration when ready.