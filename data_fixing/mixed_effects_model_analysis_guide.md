# Mixed Effects Model Analysis Guide
## Teacher Perception of Student Performance Study

---

## 1. OVERVIEW OF MIXED EFFECTS MODELING FOR THIS STUDY

### Why Mixed Effects Models?

Your data has a **hierarchical/nested structure**:
```
Level 4: Region
    └── Level 3: Schools (nested in regions)
        └── Level 2: Teachers (nested in schools)
            └── Level 1: Observations/Time points (nested in teachers)
```

**Key advantages:**
- Accounts for non-independence of observations
- Separates between-group and within-group variation
- Handles unbalanced data (different numbers of teachers per school)
- Allows for repeated measures over time
- Provides more accurate standard errors and p-values
- Can model both population-level and group-specific effects

---

## 2. PROPOSED MODEL STRUCTURE

### 2.1 Basic Model Notation

**Level 1 (Observation level):**
```
Y_ijk(t) = β₀ + β₁(Intervention_ijk(t)) + β₂(Time_t) + β₃(Intervention × Time) 
           + β₄(Covariates) + u_k + v_jk + ε_ijk(t)
```

Where:
- `Y_ijk(t)` = Outcome for teacher i, in school j, in region k, at time t
- `β₀` = Overall intercept (grand mean)
- `β₁` = Fixed effect of intervention
- `β₂` = Fixed effect of time
- `β₃` = Interaction (intervention effect over time) - **KEY for your research question**
- `β₄` = Fixed effects of covariates (teacher experience, class size, etc.)
- `u_k` = Random effect for region k
- `v_jk` = Random effect for school j within region k
- `ε_ijk(t)` = Residual error

### 2.2 Fixed Effects (What You Want to Test)

**Primary Research Questions:**
1. **Intervention effect:** Do students in intervention schools perform better?
2. **Time trend:** Does performance change over time?
3. **Intervention × Time interaction:** Does the intervention effect increase over time?
4. **Regional differences:** Do regions differ in baseline performance?
5. **Region × Intervention:** Does intervention effectiveness vary by region?

**Fixed Effects to Include:**

| Variable | Type | Purpose |
|----------|------|---------|
| **Intervention** | Binary or Categorical | Main treatment effect |
| **Time** | Continuous or Categorical | Secular trends |
| **Region** | Categorical | Regional comparisons |
| **Intervention × Time** | Interaction | Change in intervention effect over time |
| **Region × Intervention** | Interaction | Does intervention work differently by region? |
| **Teacher Experience** | Categorical/Continuous | Control variable |
| **Class Size** | Continuous | Control variable |
| **Grade Level** | Categorical | Control variable |

### 2.3 Random Effects (What Varies by Group)

**Random Intercepts:**
- **School-level random intercept:** Captures baseline differences between schools
- **Region-level random intercept:** Captures baseline differences between regions
- *(Optional) Teacher-level random intercept:* If same teacher surveyed multiple times

**Random Slopes (Advanced):**
- Allow intervention effect to vary by school: `(1 + Intervention | School)`
- Allow time trend to vary by school: `(1 + Time | School)`

---

## 3. OUTCOME VARIABLES

You can run separate models for each performance dimension:

### Primary Outcomes (from Section B of questionnaire):
1. **Overall Academic Performance** (B1)
2. **Problem-Solving Skills** (B2)
3. **Critical Thinking** (B3)
4. **Collaboration/Teamwork** (B4)
5. **Communication Skills** (B5)
6. **Student Engagement** (B6)
7. **Behavior/Conduct** (B7)
8. **Persistence/Resilience** (B8)

### Secondary Outcomes (from Section C):
- **Change scores** (improvement over time)
- Can validate against Section B current performance levels

---

## 4. SAMPLE SIZE CONSIDERATIONS

For mixed effects models, you need adequate sample size at EACH LEVEL:

### Minimum Recommendations:
- **Level 1 (Observations):** At least 10-20 per teacher/school
- **Level 2 (Teachers):** At least 5-10 per school
- **Level 3 (Schools):** At least 20-30 schools per region (for reliable random effects)
- **Level 4 (Regions):** At least 4-6 regions (more is better)
- **Time points:** At least 3-4 time points for longitudinal models

### Power Considerations:
- Main effects (intervention, time): Need 80+ schools total
- Cross-level interactions: Need 30+ schools per condition
- Random slopes: Need 50+ higher-level units

**Action:** Calculate your actual sample size and adjust model complexity accordingly.

---

## 5. MODEL BUILDING STRATEGY

### Step 1: Null Model (Unconditional Means Model)
**Purpose:** Partition variance, calculate ICC

```
Model 0: Y = β₀ + u_k + v_jk + ε
```

**Calculate ICC (Intraclass Correlation):**
- ICC_school = Var(school) / [Var(school) + Var(region) + Var(residual)]
- ICC_region = Var(region) / [Var(school) + Var(region) + Var(residual)]

**Interpretation:** 
- ICC = proportion of variance due to clustering
- Justifies use of mixed effects model if ICC > 0.05

### Step 2: Add Level-1 Predictors
**Purpose:** Test basic intervention and time effects

```
Model 1: Y = β₀ + β₁(Intervention) + β₂(Time) + u_k + v_jk + ε
```

### Step 3: Add Cross-Level Interactions
**Purpose:** Test if intervention effect varies by region or time

```
Model 2: Y = β₀ + β₁(Intervention) + β₂(Time) + β₃(Region) 
           + β₄(Intervention × Time) + β₅(Region × Intervention) 
           + u_k + v_jk + ε
```

### Step 4: Add Covariates
**Purpose:** Control for confounds, improve precision

```
Model 3: Y = β₀ + β₁(Intervention) + β₂(Time) + β₃(Region)
           + β₄(Intervention × Time) + β₅(Covariates)
           + u_k + v_jk + ε
```

### Step 5: Consider Random Slopes (if sample size allows)
**Purpose:** Allow intervention effect to vary by school

```
Model 4: Y = β₀ + β₁(Intervention) + β₂(Time) + ... 
           + u₀k + u₁k(Intervention) + v_jk + ε
```

### Step 6: Model Comparison
- Compare models using likelihood ratio tests (LRT)
- Use AIC/BIC for non-nested comparisons
- Check assumptions and diagnostics

---

## 6. KEY ASSUMPTIONS TO CHECK

### 6.1 Residual Assumptions
- **Normality:** Q-Q plots of residuals
- **Homoscedasticity:** Residuals vs fitted values
- **Independence:** Should be satisfied by random effects structure

### 6.2 Random Effects Assumptions
- **Normality of random effects:** Q-Q plots of BLUPs (Best Linear Unbiased Predictors)
- **Independence of random effects:** Check correlation between random intercepts/slopes

### 6.3 Other Checks
- **Linearity:** For continuous predictors
- **No extreme outliers:** Influence diagnostics
- **No multicollinearity:** Check VIF for fixed effects

---

## 7. INTERPRETATION GUIDE

### Fixed Effects Interpretation

**Main Effect of Intervention:**
- β₁ = difference in outcome between intervention and control groups
- "Students in intervention schools score β₁ points higher on [outcome] compared to control schools"

**Main Effect of Time:**
- β₂ = change in outcome per unit time (e.g., per year)
- "Performance increases by β₂ points per year"

**Intervention × Time Interaction (CRITICAL):**
- β₃ = differential change over time between intervention and control
- "The intervention effect increases by β₃ points per year"
- Positive β₃ = intervention getting more effective over time
- This addresses your research question about intervention influence over time

**Regional Differences:**
- Dummy code regions (e.g., Region 1 = reference)
- βᵣ = difference between Region r and reference region

### Random Effects Interpretation

**School-level variance (σ²_school):**
- How much schools differ from each other
- Large variance = substantial between-school differences

**Region-level variance (σ²_region):**
- How much regions differ from each other

**Residual variance (σ²_ε):**
- Within-school/teacher variation

### Model Fit

**Marginal R²:** Variance explained by fixed effects only
**Conditional R²:** Variance explained by fixed + random effects

---

## 8. REPORTING RESULTS

### 8.1 Model Summary Table (Example)

| Fixed Effect | Estimate | SE | df | t-value | p-value | 95% CI |
|--------------|----------|----|----|---------|---------|--------|
| Intercept | 3.45 | 0.12 | 48 | 28.75 | <.001 | [3.21, 3.69] |
| Intervention | 0.35 | 0.15 | 48 | 2.33 | .024 | [0.05, 0.65] |
| Time (years) | 0.10 | 0.05 | 120 | 2.00 | .048 | [0.00, 0.20] |
| Intervention × Time | 0.25 | 0.08 | 120 | 3.13 | .002 | [0.09, 0.41] |

**Random Effects:**
- School variance: 0.42 (SD = 0.65)
- Region variance: 0.18 (SD = 0.42)
- Residual variance: 0.55 (SD = 0.74)

**Model Fit:**
- Marginal R² = 0.23
- Conditional R² = 0.58
- ICC_school = 0.37

### 8.2 Visualization Recommendations

1. **Spaghetti plot:** Individual school trajectories over time
2. **Mean trajectories by condition:** Intervention vs control over time
3. **Regional comparison plot:** Performance by region with error bars
4. **Caterpillar plot:** School-level random effects with confidence intervals
5. **Interaction plot:** Intervention effect by time or region

---

## 9. ALTERNATIVE/COMPLEMENTARY ANALYSES

### 9.1 Multiple Outcomes Simultaneously
**Multivariate Mixed Effects Model:**
- Model all 8 performance dimensions together
- Accounts for correlations between outcomes
- Tests whether intervention affects some outcomes more than others

### 9.2 Structural Equation Modeling (SEM)
- Can include latent variables (e.g., "Overall Performance" from B1-B8)
- Test mediation (e.g., does engagement mediate intervention → performance?)
- More complex but more flexible

### 9.3 Growth Curve Models
- If you have 3+ time points per teacher
- Model individual growth trajectories
- Test if intervention affects growth rate

### 9.4 Propensity Score Matching
- Before mixed effects model
- Balance covariates between intervention and control schools
- Strengthens causal inference

---

## 10. DATA STRUCTURE REQUIREMENTS

### 10.1 Long Format (Required for Mixed Effects)

Each row = one observation (teacher-time combination)

| teacher_id | school_id | region | time_point | intervention | outcome_b1 | outcome_b2 | teacher_exp | class_size |
|------------|-----------|--------|------------|--------------|------------|------------|-------------|------------|
| T001 | S01 | Region1 | 2024-Fall | 1 | 4 | 4 | 10 | 25 |
| T001 | S01 | Region1 | 2025-Spring | 1 | 5 | 4 | 10 | 25 |
| T002 | S01 | Region1 | 2024-Fall | 1 | 3 | 3 | 5 | 30 |
| T003 | S02 | Region1 | 2024-Fall | 0 | 3 | 3 | 15 | 22 |

### 10.2 Variable Coding

**Intervention:**
- 0 = Control (no intervention)
- 1 = Intervention

**Time:**
- Option A: Continuous (0, 0.5, 1, 1.5, 2, ... years from baseline)
- Option B: Categorical (Fall2024, Spring2025, Fall2025, ...)
- Recommendation: Use continuous for linear trends, categorical if non-linear

**Region:**
- Create dummy variables or use factor coding
- Ensure sufficient sample size per region

---

## 11. SOFTWARE IMPLEMENTATION

### 11.1 R (Recommended)

**Package: lme4**
```r
library(lme4)
library(lmerTest)  # for p-values

# Basic model
model1 <- lmer(outcome_b1 ~ intervention + time + 
               intervention:time + teacher_experience + 
               (1 | region/school), 
               data = df)

summary(model1)
```

**Package: nlme**
```r
library(nlme)

model1 <- lme(outcome_b1 ~ intervention * time + teacher_experience,
              random = ~ 1 | region/school,
              data = df)
```

### 11.2 Python

**Package: statsmodels**
```python
import statsmodels.formula.api as smf

model = smf.mixedlm("outcome_b1 ~ intervention + time + intervention:time",
                    data=df,
                    groups=df["school"],
                    re_formula="~1")
result = model.fit()
print(result.summary())
```

### 11.3 SPSS
- MIXED command
- GUI: Analyze → Mixed Models → Linear

### 11.4 Stata
```stata
mixed outcome_b1 intervention##time teacher_experience || region: || school:
```

---

## 12. COMMON PITFALLS TO AVOID

1. **Not checking ICC first:** If ICC is very low (<0.05), might not need mixed effects
2. **Overfitting random effects:** With small samples, keep random effects simple
3. **Ignoring convergence warnings:** May indicate model is too complex
4. **Not centering predictors:** Center continuous variables for easier interpretation
5. **Wrong reference coding:** Be clear what group comparisons mean
6. **Forgetting about multiple comparisons:** Adjust p-values if testing many outcomes
7. **Causal language without design support:** Emphasize association vs causation
8. **Not reporting random effects:** These are important for understanding variation

---

## 13. SAMPLE SIZE CALCULATIONS

### Current Sample Size Needed for 80% Power:

**To detect small intervention effect (d = 0.3):**
- 30 schools per condition (60 total)
- 5 teachers per school
- 2-3 time points

**To detect medium intervention effect (d = 0.5):**
- 20 schools per condition (40 total)
- 5 teachers per school
- 2-3 time points

**To detect Intervention × Time interaction:**
- Need 50-100 schools total
- 3+ time points

**Rule of thumb:** 
- Need at least 30 higher-level units (schools) for reliable random effects
- More time points = more power for longitudinal effects

---

## 14. NEXT STEPS FOR YOUR RESEARCH

### Before Data Collection:
1. ☐ Finalize intervention definition and measurement
2. ☐ Confirm regional classification scheme
3. ☐ Calculate target sample size for adequate power
4. ☐ Determine data collection timeline (how many waves?)
5. ☐ Create data entry template with variable coding
6. ☐ Pilot test questionnaire with 5-10 teachers

### After Data Collection:
1. ☐ Clean and organize data in long format
2. ☐ Calculate descriptive statistics by region/school/intervention
3. ☐ Check for missing data patterns
4. ☐ Run null model to calculate ICC
5. ☐ Build models sequentially (Steps 1-6 above)
6. ☐ Check assumptions and diagnostics
7. ☐ Create visualizations
8. ☐ Interpret and report results

---

## 15. REFERENCES & RESOURCES

### Key Textbooks:
- Snijders, T. A. B., & Bosker, R. J. (2012). *Multilevel Analysis* (2nd ed.)
- Raudenbush, S. W., & Bryk, A. S. (2002). *Hierarchical Linear Models* (2nd ed.)
- Singer, J. D., & Willett, J. B. (2003). *Applied Longitudinal Data Analysis*

### Online Resources:
- IDRE UCLA Stats Consulting: https://stats.osu.edu/resources/mixed-models
- Cross Validated (Stack Exchange): For specific questions
- lme4 documentation: https://cran.r-project.org/web/packages/lme4/

### Journal Articles (Example Studies):
- Search for "mixed effects model education intervention" in Google Scholar
- Look for similar hierarchical education studies in your field

---

**Good luck with your analysis! Mixed effects modeling is the right choice for your complex, nested data structure.**




