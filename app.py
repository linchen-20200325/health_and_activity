"""
✨ 緊實身材與抗下垂：每日打卡儀表板
使用 Streamlit + Pandas 開發的每日健康抗老打卡工具。
"""

import math
import os
from datetime import date

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# 全域設定
# ---------------------------------------------------------------------------
CSV_FILE = "health_and_activity.csv"

# 欄位分類（決定向後相容時的預設填補值）：
# 數值型補 0.0、計數型補 0（整數）、布林型補 False
NUMERIC_COLUMNS = ["Weight", "Sitting_Hours", "Protein_g", "Water_ml"]
COUNT_COLUMNS = ["Active_Breaks_Count"]
BOOLEAN_COLUMNS = [
    "Sunscreen_Done",
    "Good_Sleep_Done",
    "Face_Exercise_Done",
    "Lotion_Applied_Done",
]
# 完整欄位順序（與 CSV 標頭一致）
ALL_COLUMNS = [
    "Date",
    "Weight",
    "Sitting_Hours",
    "Protein_g",
    "Water_ml",
    "Sunscreen_Done",
    "Good_Sleep_Done",
    "Active_Breaks_Count",
    "Face_Exercise_Done",
    "Lotion_Applied_Done",
]


def calc_break_goal(sitting_hours: float) -> int:
    """
    依久坐時數計算建議的起來走動次數目標：ceil(久坐時數 × 1.2)。
    久坐時數為 0 時回傳最低標準 1 次，避免後續達成率計算發生除以零。
    """
    return max(1, math.ceil(sitting_hours * 1.2))


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

    # 向後相容：補齊缺失的計數欄位（預設 0，整數）
    for col in COUNT_COLUMNS:
        if col not in df.columns:
            df[col] = 0
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

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

        # --- 運動與活動（重啟燃脂酶、緊實肌肉） ---
        st.subheader("運動與活動")
        # 依久坐時數動態計算建議走動次數目標
        break_goal = calc_break_goal(sitting_hours)
        st.caption(
            f"🎯 今日建議起來走動：{break_goal} 次"
            "（每 50 分鐘久坐應中斷一次，重啟燃脂酶 LPL）"
        )
        active_breaks = st.number_input(
            "今日起來走動次數", min_value=0, max_value=50, value=0, step=1
        )
        face_exercise_done = st.checkbox("今日已完成臉部肌肉拉提運動 🧘‍♀️")

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

        # --- 細胞修復與肌膚屏障 ---
        st.subheader("細胞修復與肌膚屏障")
        sunscreen_done = st.checkbox("今日有確實防曬 (SPF30+ 或物理防曬) ☀️")
        good_sleep_done = st.checkbox("昨晚睡眠大於 7 小時 (細胞修復) 💤")
        lotion_applied_done = st.checkbox("早晚完成洗臉後乳液鎖水保濕 🧴")

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
            "Active_Breaks_Count": int(active_breaks),
            "Face_Exercise_Done": bool(face_exercise_done),
            "Lotion_Applied_Done": bool(lotion_applied_done),
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

    # 第一排：量化指標（st.metric + 進度條）
    col1, col2, col3 = st.columns(3)

    # 1. 蛋白質
    with col1:
        protein = float(latest["Protein_g"])
        st.metric(
            label="蛋白質 (g)",
            value=f"{protein:.0f}",
            delta=f"目標 {target_protein:.0f}",
            delta_color="off",
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
            delta_color="off",
        )
        # 極重要：限制進度條最大值為 1.0
        water_ratio = water / target_water if target_water > 0 else 0
        st.progress(min(1.0, water_ratio))

    # 3. 起來走動次數
    with col3:
        breaks = int(latest["Active_Breaks_Count"])
        # 依當日久坐時數計算目標（已內建避免除以零的最低值 1）
        break_goal = calc_break_goal(float(latest["Sitting_Hours"]))
        st.metric(
            label="起來走動 (次)",
            value=f"{breaks}",
            delta=f"目標 {break_goal}",
            delta_color="off",
        )
        # 極重要：限制進度條最大值為 1.0
        break_ratio = breaks / break_goal if break_goal > 0 else 0
        st.progress(min(1.0, break_ratio))

    # 第二排：行為打卡指標（達成 / 未達成）
    col4, col5, col6, col7 = st.columns(4)

    # 4. 防曬抗老
    with col4:
        st.metric(
            label="防曬抗老",
            value="達成 🛡️" if bool(latest["Sunscreen_Done"]) else "未達成 ⚠️",
        )

    # 5. 深層修復
    with col5:
        st.metric(
            label="深層修復",
            value="達成 💤" if bool(latest["Good_Sleep_Done"]) else "未達成 ⚠️",
        )

    # 6. 臉部拉提
    with col6:
        st.metric(
            label="臉部拉提",
            value="達成 🧘‍♀️" if bool(latest["Face_Exercise_Done"]) else "未達成 ⚠️",
        )

    # 7. 乳液鎖水
    with col7:
        st.metric(
            label="乳液鎖水",
            value="達成 🧴" if bool(latest["Lotion_Applied_Done"]) else "未達成 ⚠️",
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
# 建議臉部運動圖解
# ---------------------------------------------------------------------------
# 每項動作以簡易 SVG 臉部示意圖 + 粉色箭頭標示出力/拉提方向，搭配文字步驟。
# arrows 為箭頭座標清單 (x1, y1, x2, y2)，箭頭由起點指向終點（即出力方向）。
FACE_EXERCISES = [
    {
        "title": "蘋果肌上提（顴大肌 / 顴小肌）",
        "mouth": "smile",
        "cheek_fill": "#ffe9d6",
        "arrows": [(70, 152, 62, 110), (130, 152, 138, 110)],
        "steps": [
            "微笑露出上排牙齒，感受蘋果肌自然鼓起。",
            "雙手食指輕貼蘋果肌最高點，沿箭頭往太陽穴方向輕推。",
            "維持 5 秒後放鬆，避免用力下壓肌膚。",
        ],
        "reps": "10 次 × 2 組",
    },
    {
        "title": "緊實下顎線（頸闊肌）",
        "mouth": "pout",
        "cheek_fill": "#ffe9d6",
        "arrows": [(74, 184, 62, 150), (126, 184, 138, 150)],
        "steps": [
            "頭部微抬、視線朝斜上方天花板。",
            "下唇用力包住上唇，做出「嘟嘴上推」表情。",
            "感受下巴與頸部繃緊，沿箭頭向上提，維持 5 秒。",
        ],
        "reps": "10 次 × 2 組",
    },
    {
        "title": "撫平法令紋（提上唇肌）",
        "mouth": "wide",
        "cheek_fill": "#ffe3d0",
        "arrows": [(86, 150, 80, 120), (114, 150, 120, 120)],
        "steps": [
            "鼓起雙頰含住一口空氣。",
            "將空氣在左右臉頰與上下唇之間緩慢推移。",
            "每個方向停留 3 秒，撐開法令紋凹陷處。",
        ],
        "reps": "10 循環",
    },
    {
        "title": "明亮緊緻眼周（眼輪匝肌）",
        "mouth": "flat",
        "cheek_fill": "#ffe9d6",
        "arrows": [(74, 96, 58, 86), (126, 96, 142, 86)],
        "steps": [
            "食指輕壓眼尾、無名指輕貼眼頭固定肌膚。",
            "用力閉眼 2 秒，再緩緩睜大眼 2 秒。",
            "全程避免拉扯眼周皮膚，動作輕柔。",
        ],
        "reps": "10 次 × 2 組",
    },
]

# 不同表情對應的嘴型 SVG 片段
_MOUTH_SHAPES = {
    "smile": '<path d="M72 158 Q100 184 128 158" fill="none" stroke="#c0392b" stroke-width="3" stroke-linecap="round"/>',
    "pout": '<ellipse cx="100" cy="162" rx="13" ry="9" fill="#c0392b"/>',
    "wide": '<path d="M66 156 Q100 192 134 156" fill="none" stroke="#c0392b" stroke-width="3" stroke-linecap="round"/>',
    "flat": '<line x1="80" y1="162" x2="120" y2="162" stroke="#c0392b" stroke-width="3" stroke-linecap="round"/>',
}


def _face_svg(uid: str, arrows: list, mouth: str, cheek_fill: str) -> str:
    """產生單張臉部示意 SVG；uid 確保各圖箭頭 marker 的 id 不衝突。"""
    lines = "".join(
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#e84393" '
        f'stroke-width="3.5" stroke-linecap="round" marker-end="url(#arr{uid})"/>'
        for (x1, y1, x2, y2) in arrows
    )
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="160" height="200" viewBox="0 0 200 240">
  <defs>
    <marker id="arr{uid}" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#e84393"/>
    </marker>
  </defs>
  <ellipse cx="100" cy="118" rx="66" ry="90" fill="{cheek_fill}" stroke="#e0a87e" stroke-width="2.5"/>
  <ellipse cx="76" cy="100" rx="6.5" ry="9" fill="#5d4037"/>
  <ellipse cx="124" cy="100" rx="6.5" ry="9" fill="#5d4037"/>
  <path d="M97 112 Q100 132 105 132" fill="none" stroke="#e0a87e" stroke-width="2" stroke-linecap="round"/>
  {_MOUTH_SHAPES.get(mouth, _MOUTH_SHAPES['smile'])}
  {lines}
</svg>"""


def render_face_exercise_guide() -> None:
    """以可展開區塊呈現建議臉部運動的圖解與步驟。"""
    with st.expander("🧘‍♀️ 建議臉部運動圖解（每日 1 組，由內撐起下垂組織）", expanded=False):
        st.caption(
            "依據 JAMA Dermatology (2018) 臉部阻抗運動研究，持續執行可提升中下臉肌肉豐滿度。"
            "粉色箭頭代表肌肉出力／拉提方向，請以輕柔力道進行，避免過度拉扯肌膚。"
        )
        for i, ex in enumerate(FACE_EXERCISES):
            svg = _face_svg(str(i), ex["arrows"], ex["mouth"], ex["cheek_fill"])
            col_img, col_txt = st.columns([1, 2])
            with col_img:
                components.html(svg, height=210)
            with col_txt:
                st.markdown(f"**{ex['title']}**")
                for step in ex["steps"]:
                    st.markdown(f"- {step}")
                st.caption(f"建議頻率：{ex['reps']}")
            if i < len(FACE_EXERCISES) - 1:
                st.divider()


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
    # 臉部運動圖解：空資料或已有紀錄皆顯示，方便隨時參考
    render_face_exercise_guide()


if __name__ == "__main__":
    main()
