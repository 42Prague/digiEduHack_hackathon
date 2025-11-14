# ====================================================================
# MIXED EFFECTS MODEL ANALYSIS
# Teacher Perception of Student Performance Study
# ====================================================================

# Load required packages
# Install if needed: install.packages(c("lme4", "lmerTest", "ggplot2", "dplyr", "tidyr", "performance", "sjPlot"))

library(lme4)       # Mixed effects models
library(lmerTest)   # P-values for mixed models
library(ggplot2)    # Visualization
library(dplyr)      # Data manipulation
library(tidyr)      # Data reshaping
library(performance) # Model diagnostics and R-squared
library(sjPlot)     # Nice model tables and plots

# ====================================================================
# 1. LOAD AND PREPARE DATA
# ====================================================================

# Load data
df <- read.csv("data_structure_template.csv", stringsAsFactors = FALSE)

# Convert variables to appropriate types
df <- df %>%
  mutate(
    # Convert to factors
    teacher_id = as.factor(teacher_id),
    school_id = as.factor(school_id),
    region = as.factor(region),
    intervention_status = as.factor(intervention_status),
    teaching_experience_years = as.numeric(teaching_experience_years),
    class_size = as.numeric(class_size),
    
    # Convert date
    survey_date = as.Date(survey_date),
    
    # Create time variable (years from first survey)
    time_years = as.numeric(difftime(survey_date, min(survey_date), units = "days")) / 365.25,
    
    # Recode intervention status (Treatment=1, Control=0)
    intervention = ifelse(intervention_status == "Treatment", 1, 0)
  )

# Check data structure
str(df)
summary(df)

# Check for missing data
sum(is.na(df))
colSums(is.na(df))

# ====================================================================
# 2. DESCRIPTIVE STATISTICS
# ====================================================================

# Sample sizes
cat("\n=== SAMPLE SIZES ===\n")
cat("Total responses:", nrow(df), "\n")
cat("Number of teachers:", length(unique(df$teacher_id)), "\n")
cat("Number of schools:", length(unique(df$school_id)), "\n")
cat("Number of regions:", length(unique(df$region)), "\n")

# By intervention status
table(df$intervention_status)
table(df$region, df$intervention_status)

# Means by group
cat("\n=== DESCRIPTIVE STATISTICS BY INTERVENTION STATUS ===\n")
df %>%
  group_by(intervention_status) %>%
  summarise(
    n = n(),
    mean_b1 = mean(b1_overall_performance, na.rm = TRUE),
    sd_b1 = sd(b1_overall_performance, na.rm = TRUE),
    mean_b2 = mean(b2_problem_solving, na.rm = TRUE),
    sd_b2 = sd(b2_problem_solving, na.rm = TRUE),
    mean_b6 = mean(b6_engagement, na.rm = TRUE),
    sd_b6 = sd(b6_engagement, na.rm = TRUE)
  )

# By region
cat("\n=== DESCRIPTIVE STATISTICS BY REGION ===\n")
df %>%
  group_by(region) %>%
  summarise(
    n = n(),
    mean_b1 = mean(b1_overall_performance, na.rm = TRUE),
    sd_b1 = sd(b1_overall_performance, na.rm = TRUE)
  )

# ====================================================================
# 3. NULL MODEL (Unconditional Means Model)
# ====================================================================

cat("\n\n=== NULL MODEL: Partitioning Variance ===\n")

# Outcome: Overall Performance (B1)
model0_b1 <- lmer(b1_overall_performance ~ 1 + (1|region/school_id), 
                  data = df, REML = TRUE)
summary(model0_b1)

# Calculate ICC (Intraclass Correlation Coefficient)
variance_components <- as.data.frame(VarCorr(model0_b1))
var_region <- variance_components$vcov[1]
var_school <- variance_components$vcov[2]
var_residual <- variance_components$vcov[3]

ICC_region <- var_region / (var_region + var_school + var_residual)
ICC_school <- var_school / (var_region + var_school + var_residual)
ICC_total <- (var_region + var_school) / (var_region + var_school + var_residual)

cat("\n--- Variance Components ---\n")
cat("Region variance:", round(var_region, 3), "\n")
cat("School variance:", round(var_school, 3), "\n")
cat("Residual variance:", round(var_residual, 3), "\n")
cat("\n--- Intraclass Correlations ---\n")
cat("ICC (Region):", round(ICC_region, 3), "- proportion of variance due to regions\n")
cat("ICC (School):", round(ICC_school, 3), "- proportion of variance due to schools\n")
cat("ICC (Total):", round(ICC_total, 3), "- proportion of variance due to clustering\n")

# Interpretation
if (ICC_total > 0.05) {
  cat("\n✓ ICC > 0.05: Mixed effects model is justified!\n")
} else {
  cat("\n⚠ ICC < 0.05: Consider whether mixed effects model is necessary\n")
}

# ====================================================================
# 4. MODEL 1: INTERVENTION AND TIME EFFECTS
# ====================================================================

cat("\n\n=== MODEL 1: Main Effects of Intervention and Time ===\n")

model1_b1 <- lmer(b1_overall_performance ~ intervention + time_years + 
                    (1|region/school_id), 
                  data = df, REML = FALSE)
summary(model1_b1)

# Model fit
performance::r2(model1_b1)

# ====================================================================
# 5. MODEL 2: ADD INTERVENTION × TIME INTERACTION
# ====================================================================

cat("\n\n=== MODEL 2: Intervention × Time Interaction ===\n")

model2_b1 <- lmer(b1_overall_performance ~ intervention * time_years + 
                    (1|region/school_id), 
                  data = df, REML = FALSE)
summary(model2_b1)

# Model fit
performance::r2(model2_b1)

# Test if interaction improves model
anova(model1_b1, model2_b1)

# ====================================================================
# 6. MODEL 3: ADD REGIONAL DIFFERENCES
# ====================================================================

cat("\n\n=== MODEL 3: Add Region as Fixed Effect ===\n")

model3_b1 <- lmer(b1_overall_performance ~ intervention * time_years + region + 
                    (1|school_id), 
                  data = df, REML = FALSE)
summary(model3_b1)

# Model comparison
anova(model2_b1, model3_b1)

# ====================================================================
# 7. MODEL 4: ADD COVARIATES (FULL MODEL)
# ====================================================================

cat("\n\n=== MODEL 4: Full Model with Covariates ===\n")

# Center continuous predictors for easier interpretation
df <- df %>%
  mutate(
    teaching_exp_centered = teaching_experience_years - mean(teaching_experience_years, na.rm = TRUE),
    class_size_centered = class_size - mean(class_size, na.rm = TRUE)
  )

model4_b1 <- lmer(b1_overall_performance ~ 
                    intervention * time_years + 
                    region + 
                    teaching_exp_centered + 
                    class_size_centered +
                    (1|school_id), 
                  data = df, REML = FALSE)
summary(model4_b1)

# Model fit
performance::r2(model4_b1)

# Model comparison
anova(model3_b1, model4_b1)

# ====================================================================
# 8. MODEL 5: TEST REGION × INTERVENTION INTERACTION
# ====================================================================

cat("\n\n=== MODEL 5: Region × Intervention Interaction ===\n")

model5_b1 <- lmer(b1_overall_performance ~ 
                    intervention * time_years + 
                    intervention * region +
                    teaching_exp_centered + 
                    class_size_centered +
                    (1|school_id), 
                  data = df, REML = FALSE)
summary(model5_b1)

# Test if interaction is significant
anova(model4_b1, model5_b1)

# ====================================================================
# 9. MODEL DIAGNOSTICS
# ====================================================================

cat("\n\n=== MODEL DIAGNOSTICS ===\n")

# Choose best model (e.g., model4_b1)
best_model <- model4_b1

# Residual plots
par(mfrow=c(2,2))

# 1. Residuals vs Fitted
plot(fitted(best_model), residuals(best_model),
     xlab="Fitted Values", ylab="Residuals",
     main="Residuals vs Fitted")
abline(h=0, col="red", lty=2)

# 2. Q-Q plot of residuals
qqnorm(residuals(best_model))
qqline(residuals(best_model), col="red")

# 3. Scale-Location plot
plot(fitted(best_model), sqrt(abs(residuals(best_model))),
     xlab="Fitted Values", ylab="√|Residuals|",
     main="Scale-Location")

# 4. Q-Q plot of random effects (school)
school_ranef <- ranef(best_model)$school_id[,1]
qqnorm(school_ranef, main="Q-Q Plot: School Random Effects")
qqline(school_ranef, col="red")

par(mfrow=c(1,1))

# Check for influential observations
# Influence diagnostics (if needed)
# library(influence.ME)
# influence_data <- influence(best_model, obs = TRUE)

# ====================================================================
# 10. ANALYZE ALL OUTCOME VARIABLES
# ====================================================================

cat("\n\n=== MODELS FOR ALL OUTCOMES ===\n")

# List of outcome variables
outcomes <- c("b1_overall_performance", "b2_problem_solving", 
              "b3_critical_thinking", "b4_collaboration",
              "b5_communication", "b6_engagement", 
              "b7_behavior", "b8_persistence")

# Store results
results_list <- list()

for (outcome in outcomes) {
  cat("\n--- Outcome:", outcome, "---\n")
  
  # Create formula
  formula_str <- paste(outcome, "~ intervention * time_years + region + 
                       teaching_exp_centered + class_size_centered + (1|school_id)")
  
  # Fit model
  model <- lmer(as.formula(formula_str), data = df, REML = FALSE)
  
  # Store results
  results_list[[outcome]] <- model
  
  # Print summary
  print(summary(model))
  print(performance::r2(model))
}

# ====================================================================
# 11. CREATE RESULTS TABLE
# ====================================================================

# Extract key coefficients from all models
results_table <- data.frame(
  Outcome = outcomes,
  Intercept = numeric(length(outcomes)),
  Intervention_Effect = numeric(length(outcomes)),
  Intervention_p = numeric(length(outcomes)),
  Time_Effect = numeric(length(outcomes)),
  Time_p = numeric(length(outcomes)),
  Interaction_Effect = numeric(length(outcomes)),
  Interaction_p = numeric(length(outcomes)),
  Marginal_R2 = numeric(length(outcomes)),
  Conditional_R2 = numeric(length(outcomes))
)

for (i in seq_along(outcomes)) {
  model <- results_list[[outcomes[i]]]
  coefs <- summary(model)$coefficients
  r2_values <- performance::r2(model)
  
  results_table$Intercept[i] <- round(coefs[1, 1], 3)
  results_table$Intervention_Effect[i] <- round(coefs[2, 1], 3)
  results_table$Intervention_p[i] <- round(coefs[2, 5], 4)
  results_table$Time_Effect[i] <- round(coefs[3, 1], 3)
  results_table$Time_p[i] <- round(coefs[3, 5], 4)
  
  # Check if interaction exists
  if (nrow(coefs) >= 4) {
    results_table$Interaction_Effect[i] <- round(coefs[4, 1], 3)
    results_table$Interaction_p[i] <- round(coefs[4, 5], 4)
  }
  
  results_table$Marginal_R2[i] <- round(r2_values$R2_marginal, 3)
  results_table$Conditional_R2[i] <- round(r2_values$R2_conditional, 3)
}

cat("\n\n=== SUMMARY RESULTS TABLE ===\n")
print(results_table)

# Save results
write.csv(results_table, "mixed_effects_results_summary.csv", row.names = FALSE)

# ====================================================================
# 12. VISUALIZATIONS
# ====================================================================

cat("\n\n=== CREATING VISUALIZATIONS ===\n")

# 1. Mean trajectories by intervention group
plot1 <- ggplot(df, aes(x = time_years, y = b1_overall_performance, 
                        color = intervention_status, group = intervention_status)) +
  stat_summary(fun = mean, geom = "line", size = 1.2) +
  stat_summary(fun = mean, geom = "point", size = 3) +
  stat_summary(fun.data = mean_se, geom = "errorbar", width = 0.1) +
  labs(title = "Student Performance Over Time by Intervention Status",
       x = "Time (Years)", 
       y = "Overall Performance Rating",
       color = "Group") +
  theme_bw() +
  theme(text = element_text(size = 12))

print(plot1)
ggsave("plot1_trajectories.png", plot1, width = 8, height = 6)

# 2. Performance by region
plot2 <- ggplot(df, aes(x = region, y = b1_overall_performance, fill = intervention_status)) +
  geom_boxplot(alpha = 0.7) +
  labs(title = "Student Performance by Region and Intervention Status",
       x = "Region", 
       y = "Overall Performance Rating",
       fill = "Group") +
  theme_bw() +
  theme(text = element_text(size = 12))

print(plot2)
ggsave("plot2_regional.png", plot2, width = 8, height = 6)

# 3. Interaction plot
# Predicted values
df$predicted_b1 <- predict(model4_b1)

plot3 <- ggplot(df, aes(x = time_years, y = predicted_b1, 
                        color = intervention_status, group = intervention_status)) +
  geom_line(size = 1.2) +
  labs(title = "Predicted Performance: Intervention × Time Interaction",
       subtitle = "Based on Mixed Effects Model",
       x = "Time (Years)", 
       y = "Predicted Performance Rating",
       color = "Group") +
  theme_bw() +
  theme(text = element_text(size = 12))

print(plot3)
ggsave("plot3_interaction.png", plot3, width = 8, height = 6)

# 4. Caterpillar plot of school random effects
ranef_df <- as.data.frame(ranef(model4_b1)$school_id)
ranef_df$school_id <- rownames(ranef_df)
ranef_df <- ranef_df %>% arrange(`(Intercept)`)
ranef_df$school_id <- factor(ranef_df$school_id, levels = ranef_df$school_id)

plot4 <- ggplot(ranef_df, aes(x = `(Intercept)`, y = school_id)) +
  geom_point(size = 2) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "red") +
  labs(title = "School-Level Random Effects (Caterpillar Plot)",
       subtitle = "Deviation from overall mean",
       x = "Random Effect (Intercept)", 
       y = "School ID") +
  theme_bw() +
  theme(text = element_text(size = 10))

print(plot4)
ggsave("plot4_caterpillar.png", plot4, width = 8, height = 10)

# 5. All outcomes comparison
outcomes_long <- df %>%
  select(teacher_id, intervention_status, time_years, all_of(outcomes)) %>%
  pivot_longer(cols = all_of(outcomes), names_to = "Outcome", values_to = "Rating")

plot5 <- ggplot(outcomes_long, aes(x = intervention_status, y = Rating, fill = intervention_status)) +
  geom_boxplot(alpha = 0.7) +
  facet_wrap(~ Outcome, scales = "free_y") +
  labs(title = "All Performance Outcomes by Intervention Status",
       x = "Intervention Status", 
       y = "Rating",
       fill = "Group") +
  theme_bw() +
  theme(text = element_text(size = 10),
        axis.text.x = element_text(angle = 45, hjust = 1))

print(plot5)
ggsave("plot5_all_outcomes.png", plot5, width = 12, height = 8)

# ====================================================================
# 13. PUBLICATION-READY TABLE
# ====================================================================

# Use sjPlot for nice HTML table
sjPlot::tab_model(model4_b1, 
                  show.re.var = TRUE,
                  show.icc = TRUE,
                  show.r2 = TRUE,
                  file = "model_table.html")

cat("\n✓ HTML table saved as 'model_table.html'\n")

# ====================================================================
# 14. INTERPRETATION HELPER
# ====================================================================

cat("\n\n=== INTERPRETATION GUIDE ===\n")

coefs <- summary(model4_b1)$coefficients

cat("\nKey Findings:\n")
cat("1. Intervention Effect:", round(coefs["intervention", "Estimate"], 3), 
    " (p =", round(coefs["intervention", "Pr(>|t|)"], 4), ")\n")
cat("   → Students in intervention schools score", round(coefs["intervention", "Estimate"], 2), 
    "points higher on performance rating\n")

cat("\n2. Time Effect:", round(coefs["time_years", "Estimate"], 3), 
    " (p =", round(coefs["time_years", "Pr(>|t|)"], 4), ")\n")
cat("   → Performance changes by", round(coefs["time_years", "Estimate"], 2), 
    "points per year\n")

if ("intervention:time_years" %in% rownames(coefs)) {
  cat("\n3. Intervention × Time Interaction:", 
      round(coefs["intervention:time_years", "Estimate"], 3), 
      " (p =", round(coefs["intervention:time_years", "Pr(>|t|)"], 4), ")\n")
  cat("   → The intervention effect changes by", 
      round(coefs["intervention:time_years", "Estimate"], 2), 
      "points per year\n")
  
  if (coefs["intervention:time_years", "Pr(>|t|)"] < 0.05) {
    cat("   → ✓ SIGNIFICANT: Intervention effectiveness changes over time!\n")
  }
}

r2_vals <- performance::r2(model4_b1)
cat("\n4. Model Fit:\n")
cat("   Marginal R² =", round(r2_vals$R2_marginal, 3), 
    "(variance explained by fixed effects)\n")
cat("   Conditional R² =", round(r2_vals$R2_conditional, 3), 
    "(variance explained by entire model)\n")

cat("\n\n=== ANALYSIS COMPLETE ===\n")
cat("Check your working directory for saved plots and tables.\n")






