"""
✨ 緊實身材與抗下垂：每日打卡儀表板
使用 Streamlit + Pandas 開發的每日健康抗老打卡工具。
"""

import os
from datetime import date

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# 全域設定
# ---------------------------------------------------------------------------
CSV_FILE = "health_and_activity.csv"

# 數值型欄位（缺失時補 0.0）與布林型欄位（缺失時補 False）
NUMERIC_COLUMNS = ["Weight", "Sitting_Hours", "Protein_g", "Water_ml"]
BOOLEAN_COLUMNS = ["Sunscreen_Done", "Good_Sleep_Done"]
# 完整欄位順序
ALL_COLUMNS = ["Date"] + NUMERIC_COLUMNS + BOOLEAN_COLUMNS


# ---------------------------------------------------------------------------
# 資料存取層（模組化）
# ---------------------------------------------------------------------------
def load_data() -> pd.DataFrame:
    """
    載入打卡資料。
    - 若檔案不存在，回傳僅含欄位的空 DataFrame。
    - 若檔案存在，確保向後相容性：自動補齊缺失欄位
      （數值型補 0.0、布林型補 False），避免後續操作報錯。
    """
    if not os.path.exists(CSV_FILE):
        # 檔案不存在 → 建立含預期欄位的空 DataFrame
        return pd.DataFrame(columns=ALL_COLUMNS)

    df = pd.read_csv(CSV_FILE)

    # 向後相容：補齊缺失的數值欄位（預設 0.0）
    for col in NUMERIC_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # 向後相容：補齊缺失的布林欄位（預設 False）
    for col in BOOLEAN_COLUMNS:
        if col not in df.columns:
            df[col] = False
        else:
            df[col] = df[col].fillna(False).astype(bool)

    # 確保 Date 欄位存在
    if "Date" not in df.columns:
        df["Date"] = ""

    # 統一欄位順序
    return df[ALL_COLUMNS]


def save_data(df: pd.DataFrame, new_row: dict) -> pd.DataFrame:
    """
    合併新打卡資料並存檔。
    - 以 Date 為鍵，保留最後一筆（keep='last'）覆蓋同日重複紀錄。
    - 依日期升冪排序後寫回 CSV。
    """
    new_df = pd.DataFrame([new_row])
    combined = pd.concat([df, new_df], ignore_index=True)

    # 同日只留最後一次打卡
    combined = combined.drop_duplicates(subset=["Date"], keep="last")

    # 依日期排序，方便趨勢呈現
    combined = combined.sort_values(by="Date").reset_index(drop=True)
    combined.to_csv(CSV_FILE, index=False)
    return combined


# ---------------------------------------------------------------------------
# 側邊欄：今日抗老打卡表單
# ---------------------------------------------------------------------------
def render_sidebar(df: pd.DataFrame) -> None:
    """繪製側邊欄打卡表單並處理送出行為。"""
    st.sidebar.header("📝 今日抗老打卡")

    with st.sidebar.form("daily_checkin", clear_on_submit=False):
        # --- 基礎數據 ---
        st.subheader("基礎數據")
        input_date = st.date_input("日期", value=date.today())
        weight = st.number_input(
            "體重 (kg)", min_value=30.0, max_value=150.0, value=60.0, step=0.1
        )
        sitting_hours = st.number_input(
            "今日預估久坐時數", min_value=0.0, max_value=24.0, value=8.0, step=0.5
        )

        # --- 營養與代謝 ---
        st.subheader("營養與代謝")
        # 依體重動態計算當日目標
        target_protein = weight * 1.2
        target_water = weight * 35
        st.caption(f"🎯 今日目標蛋白質：約 {target_protein:.0f} g（體重 × 1.2）")
        st.caption(f"🎯 今日目標飲水量：約 {target_water:.0f} ml（體重 × 35）")

        protein_g = st.number_input(
            "今日攝取蛋白質 (g)", min_value=0.0, value=0.0, step=1.0
        )
        water_ml = st.number_input(
            "今日飲水量 (ml)", min_value=0.0, value=0.0, step=50.0
        )

        # --- 細胞修復 ---
        st.subheader("細胞修復")
        sunscreen_done = st.checkbox("今日有確實防曬 (SPF30+ 或物理防曬) ☀️")
        good_sleep_done = st.checkbox("昨晚睡眠大於 7 小時 (細胞修復) 💤")

        submitted = st.form_submit_button("儲存今日打卡")

    if submitted:
        new_row = {
            "Date": input_date.strftime("%Y-%m-%d"),
            "Weight": float(weight),
            "Sitting_Hours": float(sitting_hours),
            "Protein_g": float(protein_g),
            "Water_ml": float(water_ml),
            "Sunscreen_Done": bool(sunscreen_done),
            "Good_Sleep_Done": bool(good_sleep_done),
        }
        save_data(df, new_row)
        st.sidebar.success("✅ 今日打卡已儲存！")
        st.rerun()


# ---------------------------------------------------------------------------
# 主畫面：儀表板
# ---------------------------------------------------------------------------
def render_dashboard(df: pd.DataFrame) -> None:
    """繪製主畫面儀表板內容。"""
    st.title("✨ 緊實身材與抗下垂：每日打卡儀表板")

    # 空資料狀態
    if df.empty:
        st.info("👋 請從左側邊欄開始您的抗老打卡第一天！")
        return

    # 取最新一筆資料（資料已依日期升冪排序）
    latest = df.sort_values(by="Date").iloc[-1]
    latest_date = latest["Date"]
    latest_weight = float(latest["Weight"])

    # 依最新體重計算目標
    target_protein = latest_weight * 1.2
    target_water = latest_weight * 35

    # --- 達成率區塊 ---
    st.header(f"🎯 {latest_date} 打卡達成率")
    col1, col2, col3, col4 = st.columns(4)

    # 1. 蛋白質
    with col1:
        protein = float(latest["Protein_g"])
        st.metric(
            label="蛋白質 (g)",
            value=f"{protein:.0f}",
            delta=f"目標 {target_protein:.0f}",
        )
        # 極重要：以 min(1.0, 比例) 限制進度條最大值，避免 StreamlitAPIException
        protein_ratio = protein / target_protein if target_protein > 0 else 0
        st.progress(min(1.0, protein_ratio))

    # 2. 飲水量
    with col2:
        water = float(latest["Water_ml"])
        st.metric(
            label="飲水量 (ml)",
            value=f"{water:.0f}",
            delta=f"目標 {target_water:.0f}",
        )
        # 極重要：限制進度條最大值為 1.0
        water_ratio = water / target_water if target_water > 0 else 0
        st.progress(min(1.0, water_ratio))

    # 3. 防曬抗老
    with col3:
        sunscreen_ok = bool(latest["Sunscreen_Done"])
        st.metric(
            label="防曬抗老",
            value="達成 🛡️" if sunscreen_ok else "未達成 ⚠️",
        )

    # 4. 深層修復
    with col4:
        sleep_ok = bool(latest["Good_Sleep_Done"])
        st.metric(
            label="深層修復",
            value="達成 💤" if sleep_ok else "未達成 ⚠️",
        )

    st.divider()

    # --- 長期趨勢分析 ---
    st.header("📉 長期趨勢分析")
    tab_weight, tab_records = st.tabs(["體重趨勢", "打卡紀錄表"])

    with tab_weight:
        # 以日期為索引繪製體重趨勢線
        weight_df = df[["Date", "Weight"]].copy()
        weight_df = weight_df.sort_values(by="Date").set_index("Date")
        st.line_chart(weight_df["Weight"])

    with tab_records:
        # 依日期降冪排序顯示歷史資料
        display_df = df.sort_values(by="Date", ascending=False).reset_index(drop=True)
        st.dataframe(display_df, use_container_width=True)


# ---------------------------------------------------------------------------
# 程式進入點
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="緊實身材與抗下垂：每日打卡儀表板",
        page_icon="✨",
        layout="wide",
    )

    df = load_data()
    render_sidebar(df)
    render_dashboard(df)


if __name__ == "__main__":
    main()
