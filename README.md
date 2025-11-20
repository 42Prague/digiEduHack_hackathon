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
3.  **Pitch Deck:** Add your final pitch **in PDF format** to the `pitch/` folder.

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