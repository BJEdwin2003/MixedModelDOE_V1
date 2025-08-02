import os
import pandas as pd
import numpy as np
from itertools import combinations
from sklearn.preprocessing import StandardScaler
from patsy import dmatrix
from scipy.stats import f
import statsmodels.formula.api as smf
from statsmodels.formula.api import mixedlm
from statsmodels.stats.anova import anova_lm
from statsmodels.tools.sm_exceptions import ConvergenceWarning
import warnings

warnings.simplefilter("ignore", ConvergenceWarning)
warnings.filterwarnings("ignore")

def run_mixed_model_doe(file_path, output_dir):
    # === 1. 数据导入 ===
    df_raw = pd.read_csv(file_path)
    response_vars = ["Lvalue", "Avalue", "Bvalue"]
    predictors = ["dye1", "dye2", "Time", "Temp"]

    # === 2. 标准化用于 simplified 模型建模 ===
    scaler = StandardScaler()
    df = df_raw.copy()
    df[predictors] = scaler.fit_transform(df[predictors])

    print("✅ DEBUG: df shape =", df.shape)
    print("📏 df 均值：")
    print(df[predictors].mean())
    print("📏 df 标准差：")
    print(df[predictors].std(ddof=0))
    print("📏 Part 2 构建 X_coded 时的原始均值与标准差：")
    print("X_mean =", scaler.mean_)
    print("X_std  =", scaler.scale_)

    # === 3. 构造 RSM 项 ===
    def create_rsm_terms(terms):
        linear = terms
        square = [f"I({t}**2)" for t in terms]
        inter = [f"{a}:{b}" for a, b in combinations(terms, 2)]
        return linear + square + inter

    rsm_terms = create_rsm_terms(predictors)

    # === 4. 全模型 LogWorth 扫描 ===
    effect_summary_all = pd.DataFrame()
    for y in response_vars:
        formula = f"{y} ~ " + " + ".join(rsm_terms)
        model = smf.ols(formula, data=df).fit()
        anova_tbl = anova_lm(model, typ=3).reset_index()
        anova_tbl = anova_tbl.rename(columns={"index": "Factor"})
        anova_tbl = anova_tbl[anova_tbl["Factor"] != "Residual"]
        anova_tbl["LogWorth"] = -np.log10(anova_tbl["PR(>F)"].replace(0, 1e-16))
        temp = anova_tbl[["Factor", "LogWorth"]].copy()
        temp.columns = ["Factor", y]
        effect_summary_all = pd.merge(effect_summary_all, temp, on="Factor", how="outer") if not effect_summary_all.empty else temp

    effect_summary_all = effect_summary_all.fillna(0)
    effect_summary_all["Median_LogWorth"] = effect_summary_all[response_vars].median(axis=1)
    effect_summary_all["Max_LogWorth"] = effect_summary_all[response_vars].max(axis=1)
    effect_summary_all["Appears_Significant"] = (effect_summary_all[response_vars] > 1.3).sum(axis=1)
    effect_summary_all = effect_summary_all.sort_values("Max_LogWorth", ascending=False)

    print("\n📊 Combined Effect Summary (Full Model – LogWorth):")
    print(effect_summary_all)

    # === 5. 筛选简化因子（保持 hierarchy）===
    def get_simplified_factors(effect_matrix, threshold=1.3, min_significant=2):
        factors = effect_matrix[
            (effect_matrix["Max_LogWorth"] >= threshold) | 
            (effect_matrix["Appears_Significant"] >= min_significant)
        ]["Factor"].tolist()
        if "Intercept" in factors:
            factors.remove("Intercept")
        hierarchical_terms = set(factors)
        for f in factors:
            if ":" in f:
                a, b = f.split(":")
                hierarchical_terms |= {a.strip(), b.strip()}
            if "I(" in f:
                base = f.split("(")[1].split("**")[0].strip()
                hierarchical_terms.add(base)
        return sorted(hierarchical_terms)

    simplified_factors = get_simplified_factors(effect_summary_all)

    print("\n✅ Suggested Simplified Factors (with hierarchy):")
    print(simplified_factors)

    # === 6. 构造原始 Config 键值（JMP 对齐）===
    df_raw["Config_combo"] = df_raw[predictors].astype(str).agg("_".join, axis=1)
    df["Config_combo"] = df_raw["Config_combo"]

    # === 7. 共线性检查 ===
    try:
        x = dmatrix(" + ".join(simplified_factors), data=df, return_type="dataframe")
        xtx = x.T @ x
        condition_number = np.linalg.cond(xtx.values)
        print(f"\n📐 Alias Check – X'X condition number: {condition_number:.2f}")
    except Exception as e:
        print(f"\n❌ Error building design matrix: {str(e)}")

    # === 8. 打印输出：Full Model + Simplified Model LogWorth ===
    simplified_logworth_df = pd.DataFrame()
    for y in response_vars:
        print(f"\n🔍 Building simplified model for: {y}")
        formula = f"{y} ~ " + " + ".join(simplified_factors)
        model = smf.ols(formula=formula, data=df).fit()
        anova_tbl = anova_lm(model, typ=3).reset_index()
        anova_tbl = anova_tbl.rename(columns={"index": "Factor"})
        anova_tbl = anova_tbl[anova_tbl["Factor"] != "Residual"]
        anova_tbl["LogWorth"] = -np.log10(anova_tbl["PR(>F)"].replace(0, 1e-16))
        temp = anova_tbl[["Factor", "LogWorth"]].copy()
        temp.columns = ["Factor", y]
        simplified_logworth_df = pd.merge(simplified_logworth_df, temp, on="Factor", how="outer") if not simplified_logworth_df.empty else temp

    simplified_logworth_df = simplified_logworth_df.fillna(0)
    simplified_logworth_df["Median_LogWorth"] = simplified_logworth_df[response_vars].median(axis=1)
    simplified_logworth_df["Max_LogWorth"] = simplified_logworth_df[response_vars].max(axis=1)
    simplified_logworth_df["Appears_Significant"] = (simplified_logworth_df[response_vars] > 1.3).sum(axis=1)
    simplified_logworth_df = simplified_logworth_df.sort_values("Max_LogWorth", ascending=False)

    print("\n📊 Simplified Model – Combined Effect Summary (LogWorth):")
    print(simplified_logworth_df)

    # === Part 2: Mixed Model 建模与诊断 ===
    diagnostics_summary = []
    param_uncoded_list = []
    lof_records = []

    for y in response_vars:
        print(f"\n📈 Mixed Model 建模与诊断 – Response: {y}")
        formula = f"{y} ~ " + " + ".join(simplified_factors)
        model = mixedlm(formula, data=df, groups=df["Config_combo"])
        model_fit = model.fit(reml=True)

        y_true = df[y]
        y_pred = model_fit.fittedvalues
        resid = y_true - y_pred

        ss_total = np.sum((y_true - y_true.mean()) ** 2)
        ss_resid = np.sum((y_true - y_pred) ** 2)
        r_squared = 1 - ss_resid / ss_total
        k = model_fit.k_fe - 1
        n = len(y_true)
        adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k - 1)
        rmse = np.sqrt(np.mean(resid ** 2))

        diagnostics_summary.append({
            "Response": y,
            "R2_Approximate": r_squared,
            "Adjusted_R2_Approximate": adj_r_squared,
            "RMSE": rmse,
            "Mean_Response": y_true.mean(),
            "Observations": n
        })

        print(f"R² ≈ {r_squared:.4f}, Adjusted R² ≈ {adj_r_squared:.4f}, RMSE ≈ {rmse:.4f}")

        # === 参数反标准化 ===
        coef_tbl = model_fit.summary().tables[1].copy()
        coef_tbl.columns = ["Coef.", "Std.Err.", "z", "P>|z|", "[0.025", "0.975]"]
        coef_tbl["P>|z|"] = pd.to_numeric(coef_tbl["P>|z|"], errors="coerce").fillna(1.0)
        coef_tbl["Factor"] = coef_tbl.index
        uncoded = []

        for pname in coef_tbl.index:
            if pname == "Intercept":
                continue
            try:
                coef_coded = float(coef_tbl.loc[pname, "Coef."])
            except:
                continue

            if pname.startswith("I("):
                var = pname.split("(")[1].split("**")[0].strip()
                if var not in predictors: continue
                i = predictors.index(var)
                beta_uncoded = coef_coded / (scaler.scale_[i] ** 2)

            elif ":" in pname:
                var1, var2 = pname.split(":")
                if var1 not in predictors or var2 not in predictors: continue
                i1, i2 = predictors.index(var1), predictors.index(var2)
                beta_uncoded = coef_coded / (scaler.scale_[i1] * scaler.scale_[i2])

            else:
                var = pname.strip()
                if var not in predictors: continue
                i = predictors.index(var)
                beta_uncoded = coef_coded / scaler.scale_[i]

            uncoded.append((pname, beta_uncoded))

        intercept_uncoded = y_true.mean()
        for pname, beta_uncoded in uncoded:
            if pname.startswith("I(") or ":" in pname: continue
            var = pname.strip()
            if var not in predictors: continue
            i = predictors.index(var)
            intercept_uncoded -= beta_uncoded * scaler.mean_[i]

        uncoded.insert(0, ("Intercept", intercept_uncoded))
        uncoded_df = pd.DataFrame(uncoded, columns=["Factor", "Estimate"])
        uncoded_df["Response"] = y
        param_uncoded_list.append(uncoded_df)

        print("\n📄 Fixed Effects Estimates (Uncoded):")
        print(uncoded_df)

        # === JMP 风格 LOF 检验 ===
        df_raw["_fitted"] = y_pred
        group_df = df_raw.groupby("Config_combo").agg(
            local_avg=(y, "mean"),
            fitted_val=("_fitted", "mean"),
            count=("Config_combo", "count")
        ).reset_index()

        ss_lack = (group_df["count"] * (group_df["local_avg"] - group_df["fitted_val"])**2).sum()
        df_lack = len(group_df) - model_fit.df_modelwc - 1
        df_merge = df_raw.merge(group_df[["Config_combo", "local_avg"]], on="Config_combo", how="left")
        ss_pure = ((df_merge[y] - df_merge["local_avg"])**2).sum()
        df_pure = df_merge.shape[0] - len(group_df)

        ms_lack = ss_lack / df_lack
        ms_pure = ss_pure / df_pure
        F_lof = ms_lack / ms_pure
        p_lof = 1 - f.cdf(F_lof, df_lack, df_pure)

        lof_records.append({
            "Response": y,
            "DF_LackOfFit": df_lack,
            "SS_LackOfFit": ss_lack,
            "MS_LackOfFit": ms_lack,
            "DF_PureError": df_pure,
            "SS_PureError": ss_pure,
            "MS_PureError": ms_pure,
            "F_Ratio": F_lof,
            "p_Value": p_lof
        })

        print("\n🔬 JMP-style Lack of Fit Table:")
        print(f"Lack of Fit – DF={df_lack}, SS={ss_lack:.6f}, MS={ms_lack:.6f}")
        print(f"Pure Error – DF={df_pure}, SS={ss_pure:.6f}, MS={ms_pure:.6f}")
        print(f"F Ratio = {F_lof:.4f}, p-value = {p_lof:.5f}")

    # === Part 3: 所有结果导出为 CSV ===
    os.makedirs(output_dir, exist_ok=True)
    effect_summary_all.to_csv(os.path.join(output_dir, "fullmodel_logworth.csv"), index=False)
    simplified_logworth_df.to_csv(os.path.join(output_dir, "simplified_logworth.csv"), index=False)
    pd.DataFrame(diagnostics_summary).to_csv(os.path.join(output_dir, "diagnostics_summary.csv"), index=False)
    pd.concat(param_uncoded_list).to_csv(os.path.join(output_dir, "uncoded_parameters.csv"), index=False)
    pd.DataFrame(lof_records).to_csv(os.path.join(output_dir, "JMP_style_lof.csv"), index=False)

    pd.DataFrame({
        "Variable": predictors,
        "Mean": scaler.mean_,
        "StdDev": scaler.scale_
    }).to_csv(os.path.join(output_dir, "scaler.csv"), index=False)

    print(f"\n✅ 所有建模结果已导出为 CSV，保存在：{output_dir}")


if __name__ == "__main__":
    run_mixed_model_doe(
        file_path=r"C:\Zhanglei_Microsoft_Upgrade_by_20240905\Pytyon_Study_Local\Color_S2\DOEData_20250622.csv",
        output_dir=r"C:\Zhanglei_Microsoft_Upgrade_by_20240905\Pytyon_Study_Local\Color_S2\FunctionToGitHub"
    )


