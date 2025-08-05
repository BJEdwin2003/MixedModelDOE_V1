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
    """
    封装自 Mixed_DOE_Model_ColorS2_V2_7_1_20250802_Final Version with Part3a and Var and XMean_for GitHub.py
    保留所有注释、分段说明、print语句、输出文件结构。
    """
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
    print(df[["Temp", "Time", "dye1", "dye2"]].mean(), flush=True)
    print("📏 df 标准差：")
    print(df[["Temp", "Time", "dye1", "dye2"]].std(ddof=0), flush=True)

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

    # === 5. 筛选简化因子（保持 hierarchy）===
    def get_simplified_factors(effect_matrix, threshold=1.3, min_significant=2):
        factors = effect_matrix[
            (effect_matrix["Max_LogWorth"] >= threshold) | 
            (effect_matrix["Appears_Significant"] >= min_significant)
        ]["Factor"].tolist()
        if "Intercept" in factors:
            factors.remove("Intercept")
        hierarchical_terms = set(factors)
        for factor in factors:
            if ":" in factor:
                a, b = factor.split(":")
                hierarchical_terms |= {a.strip(), b.strip()}
            if "I(" in factor:
                base = factor.split("(")[1].split("**")[0].strip()
                hierarchical_terms.add(base)
        return sorted(hierarchical_terms)

    simplified_factors = get_simplified_factors(effect_summary_all)

    # === 6. 构造原始 Config 键值（JMP 对齐）===
    df_raw["Config_combo"] = df_raw[["dye1", "dye2", "Time", "Temp"]].astype(str).agg("_".join, axis=1)
    df["Config_combo"] = df_raw["Config_combo"]

    # === 7. 共线性检查 ===
    try:
        x = dmatrix(" + ".join(simplified_factors), data=df, return_type="dataframe")
        xtx = x.T @ x
        condition_number = np.linalg.cond(xtx.values)
        print(f"\n📐 Alias Check – X'X condition number: {condition_number:.2f}")
    except Exception as e:
        print(f"\n❌ Error building design matrix: {str(e)}")

    print(f"\n📐 Alias Check – X'X condition number: {condition_number:.2f}")

    # === 8. 打印输出：Full Model + Simplified Model LogWorth ===
    print("\n📊 Combined Effect Summary (Full Model – LogWorth):")
    print(effect_summary_all)

    print("\n✅ Suggested Simplified Factors (with hierarchy):")
    print(simplified_factors)

    print(f"\n📐 Alias Check – X'X condition number: {condition_number:.2f}")

    # 构建 simplified_logworth_df
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

    # =================== Part 2：建模与诊断逻辑（基于 Mixed Model） ===================
    models = {}
    param_coded_list = []
    param_uncoded_list = []
    diagnostics_summary = []
    var_records = []  # 🆕 用于收集每个响应变量的 Group Var 和 Residual Var
    lof_records = []

    for y in response_vars:
        try:
            # 构建 Mixed Model（含 Config_combo 为随机组变量）
            formula = f"{y} ~ " + " + ".join(simplified_factors)
            model = mixedlm(formula, data=df, groups=df["Config_combo"])
            model_fit = model.fit(reml=True)
            # 📊 Variance Components（用于 Part 5、JMP Profiler 对比）
            group_var = model_fit.cov_re.iloc[0, 0] if model_fit.cov_re.shape[0] > 0 else np.nan
            residual_var = model_fit.scale  # == RMSE²
            print(f"\n📊 Variance Components for {y}:")
            print(f" - Group Var (Config)   = {group_var:.4f}")
            print(f" - Residual Var (Error) = {residual_var:.4f}   (RMSE ≈ {np.sqrt(residual_var):.4f})")

            var_records.append({
                "Response": y,
                "Group_Var": group_var,
                "Residual_Var": residual_var,
                "RMSE_from_Var": np.sqrt(residual_var)
            })

            models[y] = model_fit

            y_true = df[y]
            y_pred = model_fit.fittedvalues
            resid = y_true - y_pred

            # 🎯 近似 R²（external approximation）
            ss_total = np.sum((y_true - y_true.mean()) ** 2)
            ss_resid = np.sum((y_true - y_pred) ** 2)
            r_squared = 1 - ss_resid / ss_total

            # 🎯 Adjusted R² 近似（基于固定效应自由度修正）
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

            # 🔢 解析固定效应参数表，构建含 P 值与 LogWorth 的输出
            coef_tbl = model_fit.summary().tables[1].copy()
            coef_tbl.columns = ["Coef.", "Std.Err.", "z", "P>|z|", "[0.025", "0.975]"]
            coef_tbl["P>|z|"] = pd.to_numeric(coef_tbl["P>|z|"], errors="coerce").fillna(1.0)
            coef_tbl["Response"] = y
            coef_tbl["Factor"] = coef_tbl.index
            coef_tbl["LogWorth"] = -np.log10(coef_tbl["P>|z|"].replace(0, 1e-16))
            param_coded_list.append(coef_tbl[["Response", "Factor", "Coef.", "P>|z|", "LogWorth"]])

            # 🔁 参数反标准化（解码）
            X_mean = scaler.mean_
            X_scale = scaler.scale_
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
                    beta_uncoded = coef_coded / (X_scale[i] ** 2)

                elif ":" in pname:
                    var1, var2 = pname.split(":")
                    if var1 not in predictors or var2 not in predictors: continue
                    i1, i2 = predictors.index(var1), predictors.index(var2)
                    beta_uncoded = coef_coded / (X_scale[i1] * X_scale[i2])

                else:
                    var = pname.strip()
                    if var not in predictors: continue
                    i = predictors.index(var)
                    beta_uncoded = coef_coded / X_scale[i]

                uncoded.append((pname, beta_uncoded))

            intercept_uncoded = y_true.mean()
            for pname, beta_uncoded in uncoded:
                if pname.startswith("I(") or ":" in pname: continue
                var = pname.strip()
                if var not in predictors: continue
                i = predictors.index(var)
                intercept_uncoded -= beta_uncoded * X_mean[i]

            uncoded.insert(0, ("Intercept", intercept_uncoded))
            uncoded_df = pd.DataFrame(uncoded, columns=["Factor", "Estimate"])
            uncoded_df["Response"] = y
            param_uncoded_list.append(uncoded_df)

            # 📐 JMP 风格 LOF：基于 config_combo 聚合后计算 lack-of-fit F 统计量
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

        except Exception as e:
            print(f"❌ 模型拟合失败 - {y}: {e}")

    # === Part 3a: 模型结果导出（CSV 多文件版本）===
    os.makedirs(output_dir, exist_ok=True)

    # === ✅ 在所有模型构建完毕后统一导出 fixed Intercept ===
    fixed_intercepts = []
    for y in response_vars:
        beta_0 = models[y].fe_params["Intercept"]
        fixed_intercepts.append({"Response": y, "Fixed_Intercept": beta_0})
    fixed_df = pd.DataFrame(fixed_intercepts)
    fixed_df.to_csv(os.path.join(output_dir, "fixed_intercepts.csv"), index=False)

    # 1️⃣ LogWorth 表
    effect_summary_all.to_csv(os.path.join(output_dir, "fullmodel_logworth.csv"), index=False)
    simplified_logworth_df.to_csv(os.path.join(output_dir, "simplified_logworth.csv"), index=False)

    # 2️⃣ 参数估计（Coded / Uncoded 空间）
    pd.concat(param_coded_list).to_csv(os.path.join(output_dir, "coded_parameters.csv"), index=False)
    pd.concat(param_uncoded_list).to_csv(os.path.join(output_dir, "uncoded_parameters.csv"), index=False)

    # 3️⃣ 模型诊断指标（含近似 R² 和 Adjusted R²）
    diagnostics_df = pd.DataFrame(diagnostics_summary)
    diagnostics_df = diagnostics_df.rename(columns={
        "R2_Approximate": "R2_Approximate",
        "Adjusted_R2_Approximate": "Adjusted_R2_Approximate"
    })
    diagnostics_df.to_csv(os.path.join(output_dir, "diagnostics_summary.csv"), index=False)

    # 4️⃣ JMP 风格 Lack-of-Fit 分解表
    pd.DataFrame(lof_records).to_csv(os.path.join(output_dir, "JMP_style_lof.csv"), index=False)

    # 5️⃣ 变量标准化信息（用于解码）
    pd.DataFrame({
        "Variable": predictors,
        "Mean": scaler.mean_,
        "StdDev": scaler.scale_
    }).to_csv(os.path.join(output_dir, "scaler.csv"), index=False)

    # 6️⃣ 模型公式文本（逐响应变量）
    with open(os.path.join(output_dir, "model_formulas.txt"), "w") as file:
        for y in response_vars:
            formula = f"{y} ~ " + " + ".join(simplified_factors)
            file.write(f"{y} formula:\n{formula}\n\n")

    # 7️⃣ 基于 Mixed Model 的预测值 & 残差（输出图形所用 CSV）
    for y in response_vars:
        try:
            model_fit = models[y]
            y_true = df[y]
            y_pred = model_fit.fittedvalues
            resid = y_true - y_pred
            rmse = np.sqrt(np.mean(resid ** 2))
            pseudo_stud_resid = resid / rmse if rmse > 0 else resid
            df_out = pd.DataFrame({
                "Config_combo": df["Config_combo"],
                "Actual": y_true,
                "Predicted": y_pred,
                "Residual": resid,
                "Pseudo_Studentized_Residual": pseudo_stud_resid
            })
            df_out.index.name = "ID"
            out_path = os.path.join(output_dir, f"residual_data_{y}_from_MixedModel.csv")
            df_out.to_csv(out_path)
        except Exception as e:
            print(f"❌ 残差输出失败 [{y}]: {e}")

    # 8️⃣ 建模输入数据导出（供 JMP 使用 Fit Model 脚本）
    df_raw.to_csv(os.path.join(output_dir, "design_data.csv"), index=False)

    # === 📁 输出结构方差摘要表：mixed_model_variance_summary.csv ===
    df_var = pd.DataFrame(var_records)
    df_var.to_csv(os.path.join(output_dir, "mixed_model_variance_summary.csv"), index=False)

    # === 🆕 输出标准化信息至 CSV (InputDataBrief.csv) ===
    brief_path = os.path.join(output_dir, "InputDataBrief.csv")
    brief_df = pd.DataFrame({
        "Variable": predictors,
        "Mean (after standardization)": df[predictors].mean().values,
        "StdDev (after standardization)": df[predictors].std(ddof=0).values,
        "Original Mean (X_mean)": scaler.mean_,
        "Original StdDev (X_std)": scaler.scale_
    })
    brief_df.to_csv(brief_path, index=False)

    print(f"\n✅ 所有建模结果已基于 Mixed Model 导出为 CSV，保存在：{output_dir}")

# 直接运行脚本时的入口
if __name__ == "__main__":
    run_mixed_model_doe(
        r"C:\Zhanglei_Microsoft_Upgrade_by_20240905\Pytyon_Study_Local\Color_S2\DOEData_20250622.csv",
        r"C:\Zhanglei_Microsoft_Upgrade_by_20240905\Pytyon_Study_Local\Color_S2\DOE_MixedModel_Outputs"
    )


