"""
====================================================================
MIXED EFFECTS MODEL ANALYSIS - PYTHON VERSION
Teacher Perception of Student Performance Study
====================================================================

Required packages:
pip install pandas numpy statsmodels matplotlib seaborn scipy
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.formula.api import mixedlm
import scipy.stats as stats
from datetime import datetime

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)

# ====================================================================
# 1. LOAD AND PREPARE DATA
# ====================================================================

print("=" * 70)
print("LOADING DATA")
print("=" * 70)

# Load data
df = pd.read_csv("data_structure_template.csv")

# Convert date
df['survey_date'] = pd.to_datetime(df['survey_date'])

# Calculate time variable (years from first survey)
min_date = df['survey_date'].min()
df['time_years'] = (df['survey_date'] - min_date).dt.days / 365.25

# Recode intervention (Treatment=1, Control=0)
df['intervention'] = (df['intervention_status'] == 'Treatment').astype(int)

# Center continuous predictors
df['teaching_exp_centered'] = df['teaching_experience_years'] - df['teaching_experience_years'].mean()
df['class_size_centered'] = df['class_size'] - df['class_size'].mean()

# Check data
print("\nData shape:", df.shape)
print("\nFirst few rows:")
print(df[['teacher_id', 'school_id', 'region', 'intervention', 'time_years', 
          'b1_overall_performance']].head())

# ====================================================================
# 2. DESCRIPTIVE STATISTICS
# ====================================================================

print("\n" + "=" * 70)
print("DESCRIPTIVE STATISTICS")
print("=" * 70)

print("\n--- Sample Sizes ---")
print(f"Total responses: {len(df)}")
print(f"Number of teachers: {df['teacher_id'].nunique()}")
print(f"Number of schools: {df['school_id'].nunique()}")
print(f"Number of regions: {df['region'].nunique()}")

print("\n--- By Intervention Status ---")
print(df['intervention_status'].value_counts())

print("\n--- Cross-tabulation: Region x Intervention ---")
print(pd.crosstab(df['region'], df['intervention_status']))

print("\n--- Means by Intervention Status ---")
summary_by_intervention = df.groupby('intervention_status').agg({
    'b1_overall_performance': ['count', 'mean', 'std'],
    'b2_problem_solving': ['mean', 'std'],
    'b6_engagement': ['mean', 'std']
}).round(3)
print(summary_by_intervention)

print("\n--- Means by Region ---")
summary_by_region = df.groupby('region').agg({
    'b1_overall_performance': ['count', 'mean', 'std']
}).round(3)
print(summary_by_region)

# ====================================================================
# 3. NULL MODEL (Variance Partitioning)
# ====================================================================

print("\n" + "=" * 70)
print("NULL MODEL: VARIANCE PARTITIONING")
print("=" * 70)

# Note: Python's statsmodels doesn't easily handle nested random effects
# We'll use school nested in region by creating a composite grouping variable

# Create a composite school identifier that accounts for nesting
df['school_in_region'] = df['region'].astype(str) + "_" + df['school_id'].astype(str)

# Fit null model (random intercept for schools only)
model0 = mixedlm("b1_overall_performance ~ 1", 
                 data=df, 
                 groups=df["school_id"])
result0 = model0.fit(reml=True)

print(result0.summary())

# Calculate ICC
var_school = float(result0.cov_re.iloc[0, 0])
var_residual = result0.scale
ICC_school = var_school / (var_school + var_residual)

print("\n--- Variance Components ---")
print(f"School variance: {var_school:.3f}")
print(f"Residual variance: {var_residual:.3f}")
print(f"\n--- Intraclass Correlation ---")
print(f"ICC (School): {ICC_school:.3f}")

if ICC_school > 0.05:
    print("\n✓ ICC > 0.05: Mixed effects model is justified!")
else:
    print("\n⚠ ICC < 0.05: Consider whether mixed effects model is necessary")

# ====================================================================
# 4. MODEL 1: MAIN EFFECTS
# ====================================================================

print("\n" + "=" * 70)
print("MODEL 1: MAIN EFFECTS OF INTERVENTION AND TIME")
print("=" * 70)

model1 = mixedlm("b1_overall_performance ~ intervention + time_years", 
                 data=df, 
                 groups=df["school_id"])
result1 = model1.fit(reml=False)

print(result1.summary())

# ====================================================================
# 5. MODEL 2: INTERVENTION × TIME INTERACTION
# ====================================================================

print("\n" + "=" * 70)
print("MODEL 2: INTERVENTION × TIME INTERACTION")
print("=" * 70)

model2 = mixedlm("b1_overall_performance ~ intervention * time_years", 
                 data=df, 
                 groups=df["school_id"])
result2 = model2.fit(reml=False)

print(result2.summary())

# Likelihood ratio test
lr_stat = -2 * (result1.llf - result2.llf)
df_diff = len(result2.params) - len(result1.params)
p_value = stats.chi2.sf(lr_stat, df_diff)

print("\n--- Model Comparison ---")
print(f"Likelihood Ratio Test: χ² = {lr_stat:.3f}, df = {df_diff}, p = {p_value:.4f}")

# ====================================================================
# 6. MODEL 3: ADD COVARIATES (FULL MODEL)
# ====================================================================

print("\n" + "=" * 70)
print("MODEL 3: FULL MODEL WITH COVARIATES")
print("=" * 70)

model3 = mixedlm("b1_overall_performance ~ intervention * time_years + "
                 "C(region) + teaching_exp_centered + class_size_centered", 
                 data=df, 
                 groups=df["school_id"])
result3 = model3.fit(reml=False)

print(result3.summary())

# Calculate marginal and conditional R²
# Marginal R² (fixed effects only)
y_pred_fixed = result3.fittedvalues
y_actual = df['b1_overall_performance'].dropna()
# Align indices
y_pred_fixed = y_pred_fixed[y_actual.index]
r2_marginal = 1 - np.var(y_actual - y_pred_fixed) / np.var(y_actual)

print(f"\n--- Model Fit ---")
print(f"Marginal R² (fixed effects): {r2_marginal:.3f}")

# ====================================================================
# 7. ANALYZE ALL OUTCOMES
# ====================================================================

print("\n" + "=" * 70)
print("MODELS FOR ALL OUTCOMES")
print("=" * 70)

outcomes = ['b1_overall_performance', 'b2_problem_solving', 
            'b3_critical_thinking', 'b4_collaboration',
            'b5_communication', 'b6_engagement', 
            'b7_behavior', 'b8_persistence']

results_dict = {}
results_summary = []

for outcome in outcomes:
    print(f"\n--- Outcome: {outcome} ---")
    
    formula = f"{outcome} ~ intervention * time_years + C(region) + teaching_exp_centered + class_size_centered"
    
    try:
        model = mixedlm(formula, data=df, groups=df["school_id"])
        result = model.fit(reml=False, method='powell')  # Use powell for better convergence
        results_dict[outcome] = result
        
        # Extract key coefficients
        params = result.params
        pvalues = result.pvalues
        
        results_summary.append({
            'Outcome': outcome,
            'Intercept': params.get('Intercept', np.nan),
            'Intervention_Effect': params.get('intervention', np.nan),
            'Intervention_p': pvalues.get('intervention', np.nan),
            'Time_Effect': params.get('time_years', np.nan),
            'Time_p': pvalues.get('time_years', np.nan),
            'Interaction_Effect': params.get('intervention:time_years', np.nan),
            'Interaction_p': pvalues.get('intervention:time_years', np.nan)
        })
        
        print(f"✓ Model converged successfully")
        print(f"  Intervention effect: {params.get('intervention', np.nan):.3f} (p = {pvalues.get('intervention', np.nan):.4f})")
        
    except Exception as e:
        print(f"✗ Model failed: {str(e)}")
        results_summary.append({
            'Outcome': outcome,
            'Intercept': np.nan,
            'Intervention_Effect': np.nan,
            'Intervention_p': np.nan,
            'Time_Effect': np.nan,
            'Time_p': np.nan,
            'Interaction_Effect': np.nan,
            'Interaction_p': np.nan
        })

# Create summary dataframe
results_df = pd.DataFrame(results_summary)
print("\n" + "=" * 70)
print("SUMMARY RESULTS TABLE")
print("=" * 70)
print(results_df.round(4))

# Save results
results_df.to_csv("mixed_effects_results_summary_python.csv", index=False)
print("\n✓ Results saved to 'mixed_effects_results_summary_python.csv'")

# ====================================================================
# 8. VISUALIZATIONS
# ====================================================================

print("\n" + "=" * 70)
print("CREATING VISUALIZATIONS")
print("=" * 70)

# 1. Mean trajectories by intervention group
plt.figure(figsize=(10, 6))
for status in df['intervention_status'].unique():
    subset = df[df['intervention_status'] == status]
    grouped = subset.groupby('time_years')['b1_overall_performance'].agg(['mean', 'sem'])
    plt.errorbar(grouped.index, grouped['mean'], yerr=grouped['sem'], 
                 marker='o', markersize=8, linewidth=2, capsize=5, 
                 label=status)

plt.xlabel('Time (Years)', fontsize=12)
plt.ylabel('Overall Performance Rating', fontsize=12)
plt.title('Student Performance Over Time by Intervention Status', fontsize=14, fontweight='bold')
plt.legend(title='Group', fontsize=11)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('plot1_trajectories_python.png', dpi=300, bbox_inches='tight')
print("✓ Saved plot1_trajectories_python.png")
plt.close()

# 2. Performance by region
plt.figure(figsize=(10, 6))
df_plot = df[['region', 'intervention_status', 'b1_overall_performance']].copy()
sns.boxplot(data=df_plot, x='region', y='b1_overall_performance', 
            hue='intervention_status', palette='Set2')
plt.xlabel('Region', fontsize=12)
plt.ylabel('Overall Performance Rating', fontsize=12)
plt.title('Student Performance by Region and Intervention Status', fontsize=14, fontweight='bold')
plt.legend(title='Group', fontsize=11)
plt.tight_layout()
plt.savefig('plot2_regional_python.png', dpi=300, bbox_inches='tight')
print("✓ Saved plot2_regional_python.png")
plt.close()

# 3. Predicted values plot (from best model)
plt.figure(figsize=(10, 6))
df_pred = df.copy()
df_pred['predicted'] = result3.fittedvalues

for status in df_pred['intervention_status'].unique():
    subset = df_pred[df_pred['intervention_status'] == status]
    grouped = subset.groupby('time_years')['predicted'].mean()
    plt.plot(grouped.index, grouped.values, marker='o', markersize=8, 
             linewidth=2, label=status)

plt.xlabel('Time (Years)', fontsize=12)
plt.ylabel('Predicted Performance Rating', fontsize=12)
plt.title('Predicted Performance: Intervention × Time Interaction', fontsize=14, fontweight='bold')
plt.legend(title='Group', fontsize=11)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('plot3_interaction_python.png', dpi=300, bbox_inches='tight')
print("✓ Saved plot3_interaction_python.png")
plt.close()

# 4. All outcomes comparison
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
axes = axes.flatten()

for i, outcome in enumerate(outcomes):
    df_plot = df[['intervention_status', outcome]].copy()
    df_plot = df_plot.dropna()
    
    sns.boxplot(data=df_plot, x='intervention_status', y=outcome, 
                palette='Set2', ax=axes[i])
    axes[i].set_title(outcome.replace('_', ' ').title(), fontsize=10)
    axes[i].set_xlabel('')
    axes[i].set_ylabel('Rating', fontsize=9)
    axes[i].tick_params(axis='x', rotation=45, labelsize=8)

plt.suptitle('All Performance Outcomes by Intervention Status', 
             fontsize=14, fontweight='bold', y=1.00)
plt.tight_layout()
plt.savefig('plot4_all_outcomes_python.png', dpi=300, bbox_inches='tight')
print("✓ Saved plot4_all_outcomes_python.png")
plt.close()

# 5. Heatmap of results
plt.figure(figsize=(10, 6))
heatmap_data = results_df[['Outcome', 'Intervention_Effect', 'Time_Effect', 'Interaction_Effect']].copy()
heatmap_data = heatmap_data.set_index('Outcome')
heatmap_data.index = [x.replace('_', ' ').replace('b1 ', '').replace('b2 ', '').replace('b3 ', '').replace('b4 ', '').replace('b5 ', '').replace('b6 ', '').replace('b7 ', '').replace('b8 ', '').title() for x in heatmap_data.index]

sns.heatmap(heatmap_data.T, annot=True, fmt='.3f', cmap='RdBu_r', center=0, 
            cbar_kws={'label': 'Effect Size'}, linewidths=0.5)
plt.title('Effect Sizes Across All Outcomes', fontsize=14, fontweight='bold')
plt.xlabel('')
plt.ylabel('Effect Type', fontsize=12)
plt.tight_layout()
plt.savefig('plot5_heatmap_python.png', dpi=300, bbox_inches='tight')
print("✓ Saved plot5_heatmap_python.png")
plt.close()

# ====================================================================
# 9. INTERPRETATION
# ====================================================================

print("\n" + "=" * 70)
print("INTERPRETATION GUIDE")
print("=" * 70)

params = result3.params
pvalues = result3.pvalues

print("\nKey Findings:")
print(f"1. Intervention Effect: {params.get('intervention', np.nan):.3f} "
      f"(p = {pvalues.get('intervention', np.nan):.4f})")
print(f"   → Students in intervention schools score {params.get('intervention', 0):.2f} "
      f"points higher on performance rating")

print(f"\n2. Time Effect: {params.get('time_years', np.nan):.3f} "
      f"(p = {pvalues.get('time_years', np.nan):.4f})")
print(f"   → Performance changes by {params.get('time_years', 0):.2f} points per year")

if 'intervention:time_years' in params.index:
    print(f"\n3. Intervention × Time Interaction: "
          f"{params.get('intervention:time_years', np.nan):.3f} "
          f"(p = {pvalues.get('intervention:time_years', np.nan):.4f})")
    print(f"   → The intervention effect changes by "
          f"{params.get('intervention:time_years', 0):.2f} points per year")
    
    if pvalues.get('intervention:time_years', 1) < 0.05:
        print("   → ✓ SIGNIFICANT: Intervention effectiveness changes over time!")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
print("\nCheck your working directory for saved plots and results.")
print("\nFiles created:")
print("  - mixed_effects_results_summary_python.csv")
print("  - plot1_trajectories_python.png")
print("  - plot2_regional_python.png")
print("  - plot3_interaction_python.png")
print("  - plot4_all_outcomes_python.png")
print("  - plot5_heatmap_python.png")

