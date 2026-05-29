"""
✨ 緊實身材與抗下垂：每日打卡儀表板
使用 Streamlit + Pandas 開發的每日健康抗老打卡工具。
"""

import math
import os
import re
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
# 健康保養與抗下垂建議（營養素、胸部運動、臀部運動、整體原則）
# ---------------------------------------------------------------------------
# 以下數值整合自衛福部國健署「國人膳食營養素參考攝取量 (DRIs) 第八版」、
# USDA Dietary Reference Intakes、WHO 飲食指引等公開資料；皆為「成人女性」一般參考值，
# 個別情況請依專業評估調整。
AGE_GROUPS = ["18–30 歲", "31–50 歲", "51–65 歲", "65 歲以上"]

# 蛋白質欄位以「每公斤體重」表示；其餘為當日總攝取量
NUTRIENT_TABLE = {
    "蛋白質 (g／kg 體重)": {
        "18–30 歲": "1.0",
        "31–50 歲": "1.0",
        "51–65 歲": "1.2",
        "65 歲以上": "1.2–1.5",
    },
    "鈣 (mg)": {
        "18–30 歲": "1000",
        "31–50 歲": "1000",
        "51–65 歲": "1200",
        "65 歲以上": "1200",
    },
    "鐵 (mg)": {
        "18–30 歲": "15",
        "31–50 歲": "15",
        "51–65 歲": "10",
        "65 歲以上": "10",
    },
    "維生素 D (IU)": {
        "18–30 歲": "600",
        "31–50 歲": "600",
        "51–65 歲": "600",
        "65 歲以上": "800",
    },
    "維生素 C (mg)": {
        "18–30 歲": "100",
        "31–50 歲": "100",
        "51–65 歲": "100",
        "65 歲以上": "100",
    },
    "維生素 E (mg)": {
        "18–30 歲": "15",
        "31–50 歲": "15",
        "51–65 歲": "15",
        "65 歲以上": "15",
    },
    "膳食纖維 (g)": {
        "18–30 歲": "25–30",
        "31–50 歲": "25–30",
        "51–65 歲": "25",
        "65 歲以上": "21–25",
    },
    "Omega-3 EPA+DHA (mg)": {
        "18–30 歲": "250–500",
        "31–50 歲": "250–500",
        "51–65 歲": "500–1000",
        "65 歲以上": "500–1000",
    },
    "鎂 (mg)": {
        "18–30 歲": "320",
        "31–50 歲": "320",
        "51–65 歲": "320",
        "65 歲以上": "320",
    },
}

NUTRIENT_FOODS = {
    "蛋白質": "雞胸肉、魚（鮭魚／鯖魚）、雞蛋、無糖豆漿、希臘優格、毛豆、藜麥。例：100 g 雞胸肉≈22 g 蛋白質、1 顆雞蛋≈7 g。",
    "鈣": "牛奶／鈣強化無糖豆漿、起司、芝麻、小魚乾、深綠色蔬菜（芥蘭、青江菜）、板豆腐。",
    "鐵": "牛肉、豬肝、文蛤、菠菜、紅莧菜、紅藜、紅豆、黑芝麻；搭配維生素 C 食物可提升吸收率。",
    "維生素 D": "鮭魚、鯖魚、蛋黃、黑木耳、曬過的香菇、強化乳製品；每日適量曬太陽 10–15 分鐘。",
    "維生素 C": "芭樂、奇異果、柑橘、甜椒、青花菜、草莓、木瓜。一顆芭樂≈200 mg。",
    "維生素 E": "杏仁、葵花籽、酪梨、橄欖油、紅花油、深綠色蔬菜。",
    "膳食纖維": "燕麥、糙米、全麥麵包、地瓜、奇亞籽、亞麻仁籽、各色蔬菜（每餐至少 1 拳量）、莓果。",
    "Omega-3 EPA+DHA": "鮭魚、鯖魚、秋刀魚、沙丁魚（每週 2–3 次）；素食者可選亞麻仁籽油、奇亞籽、核桃（轉換 ALA）。",
    "鎂": "南瓜籽、黑巧克力（70% 以上）、杏仁、菠菜、酪梨、糙米、黑豆。",
}

# 胸部緊實運動：強化胸大肌與肩胛後收肌群，改善下垂視覺與駝背體態
CHEST_EXERCISES = [
    {
        "emoji": "🧱",
        "title": "牆推 (Wall Push)　[初階]",
        "target": "胸大肌、三角肌前束、核心",
        "steps": [
            "站於距牆一大步遠，雙手與肩同高、與肩同寬扶牆。",
            "吸氣將身體緩慢前傾貼近牆面，手肘向外約 45 度。",
            "吐氣推回起始位置，全程保持核心收緊、身體從頭到腳成一直線。",
        ],
        "reps": "12–15 下 × 3 組",
    },
    {
        "emoji": "🤸",
        "title": "跪姿伏地挺身　[中階]",
        "target": "胸大肌、肱三頭肌",
        "steps": [
            "雙手撐地略寬於肩，膝蓋跪地、腳踝交叉或勾起。",
            "身體從膝蓋到肩膀成一直線，緩慢下降胸口至離地 5–10 cm。",
            "吐氣推起；避免肩膀聳起、腰部塌陷。",
        ],
        "reps": "8–12 下 × 3 組",
    },
    {
        "emoji": "🏋️‍♀️",
        "title": "啞鈴胸推 (Dumbbell Press)",
        "target": "胸大肌、肱三頭肌",
        "steps": [
            "仰躺於瑜伽墊或胸推椅，雙手握啞鈴於胸側，手肘約 90 度。",
            "吐氣垂直上推至兩啞鈴接近，保持手腕中立、肩胛貼地。",
            "吸氣緩慢回到起點，控制下放速度。",
        ],
        "reps": "10–12 下 × 3 組（從 2–4 kg 起，循序漸進）",
    },
    {
        "emoji": "🦋",
        "title": "啞鈴胸飛鳥 (Dumbbell Fly)",
        "target": "胸大肌（內外側塑形）",
        "steps": [
            "仰躺，雙手握啞鈴於胸前正上方，手肘微彎並固定角度。",
            "吸氣畫弧線向兩側打開至肩平面（不超過）。",
            "吐氣以胸部力量收回，想像「擁抱大樹」、頂端輕擠胸肌。",
        ],
        "reps": "10–12 下 × 3 組",
    },
    {
        "emoji": "🪢",
        "title": "肩胛後收划船 (Scapular Row)　[挺胸關鍵]",
        "target": "中下斜方肌、菱形肌（改善駝背）",
        "steps": [
            "雙手握彈力帶或啞鈴，髖部微前傾、背部打直。",
            "想像夾緊兩側肩胛骨，將手肘往身體後方拉。",
            "頂端停留 1–2 秒再緩慢放回，避免聳肩。",
        ],
        "reps": "12–15 下 × 3 組",
    },
]

# 臀部緊實運動：抗久坐臀肌失憶 (gluteal amnesia)，恢復髖伸展力量
GLUTE_EXERCISES = [
    {
        "emoji": "🌉",
        "title": "臀橋 (Glute Bridge)　[初階核心動作]",
        "target": "臀大肌、後大腿、核心",
        "steps": [
            "仰臥屈膝，雙腳掌貼地，與髖同寬，腳跟靠近臀部。",
            "吐氣以臀部發力將髖部上推，至肩、髖、膝成一直線。",
            "頂端夾緊臀部停留 2 秒，再緩慢放下；避免腰部代償。",
        ],
        "reps": "15 下 × 3 組",
    },
    {
        "emoji": "🚀",
        "title": "髖推 (Hip Thrust)　[進階負重]",
        "target": "臀大肌（最高活化動作）",
        "steps": [
            "上背靠沙發或床沿，雙腳踩地與肩同寬，髖部可放置啞鈴或槓鈴。",
            "吐氣髖部上推，肩到膝呈水平，臀部頂端用力夾緊。",
            "吸氣緩慢放下；下背避免過度伸展。",
        ],
        "reps": "10–12 下 × 3 組",
    },
    {
        "emoji": "🪑",
        "title": "徒手深蹲 (Bodyweight Squat)",
        "target": "臀大肌、股四頭肌、後大腿",
        "steps": [
            "雙腳與肩同寬或略寬，腳尖略外開 15–30 度。",
            "髖部往後推（像坐椅子），膝蓋方向對齊腳尖。",
            "下蹲至大腿接近水平後，吐氣推地起身、頂端夾緊臀部。",
        ],
        "reps": "12–15 下 × 3 組",
    },
    {
        "emoji": "🏹",
        "title": "弓箭步 (Lunge)",
        "target": "臀大肌、股四頭肌（單側強化）",
        "steps": [
            "雙腳前後站約一大步距，雙手叉腰或自然下垂。",
            "緩慢下蹲至前後腿膝關節皆 90 度，前膝不超過腳尖。",
            "吐氣後腳推地回到起點，左右交替；保持骨盆穩定。",
        ],
        "reps": "每側 10 下 × 3 組",
    },
    {
        "emoji": "🦵",
        "title": "驢踢 (Donkey Kick)　[臀大肌孤立)",
        "target": "臀大肌（單側集中刺激）",
        "steps": [
            "四足跪姿，手腕在肩正下方，膝蓋在髖正下方。",
            "單腳保持 90 度屈膝，由臀部發力向後上方踢起至大腿與地面平行。",
            "緩慢回到起點，避免腰部代償；全程腹部收緊。",
        ],
        "reps": "每側 12–15 下 × 3 組",
    },
]

HEALTH_PRINCIPLES = [
    "🛌 **規律作息與優質睡眠**：每晚 7–9 小時，盡量於 23 點前入睡。深層睡眠期是生長激素分泌與膠原修復高峰。",
    "🥗 **均衡飲食原則**：每餐「掌心蛋白質 + 拳頭全穀 + 兩拳蔬菜 + 拇指好油」，控制精緻糖與加工食品（高 AGEs 加速糖化老化）。",
    "💧 **充足飲水**：每日 體重 × 30–35 ml，分次小口飲用；脫水會使皮膚乾癟並影響代謝。",
    "🏃‍♀️ **規律運動**：每週 ≥150 分鐘中強度有氧 + 至少 2 次全身阻力訓練，可同時兼顧心肺、肌肉、骨密度。",
    "🧘‍♀️ **壓力管理**：深呼吸、冥想、瑜伽 10–15 分鐘可降低皮質醇；長期慢性壓力會加速膠原流失與腹部脂肪堆積。",
    "🚭 **戒菸限酒**：菸品破壞真皮層彈力纖維與微循環；酒精促進糖化反應 (AGEs)，兩者皆加速皮膚下垂。",
    "🩺 **定期健檢**：30 歲後每 1–2 年血液常規、肝腎功能；40 歲後加上骨密度、乳房超音波／攝影、子宮頸抹片；50 歲後注意大腸鏡篩檢。",
    "⚖️ **維持穩定體重**：避免短期劇烈減重，體重波動超過 ±5 kg 會造成皮膚、胸部與臀部組織彈性疲乏而下垂。",
]


def _render_exercise_list(exercises: list) -> None:
    """以結構化清單呈現運動項目（標題、目標肌群、步驟、建議組數）。"""
    for i, ex in enumerate(exercises):
        st.markdown(f"**{ex['emoji']} {ex['title']}**　— _{ex['target']}_")
        for step in ex["steps"]:
            st.markdown(f"- {step}")
        st.caption(f"建議組數：{ex['reps']}")
        if i < len(exercises) - 1:
            st.markdown("")  # 視覺間距


def render_wellness_guide() -> None:
    """整體健康與抗下垂保養建議：營養、胸部運動、臀部運動、生活原則。"""
    st.divider()
    st.header("🌿 整體健康與抗下垂保養建議")
    st.caption(
        "⚠️ 以下內容為衛福部 DRIs 與一般醫學／健身指引整理之「參考資訊」，"
        "不能取代專業醫療診斷。有特定疾病、用藥、懷孕哺乳或運動傷害病史者，"
        "請先諮詢醫師、營養師或物理治療師。"
    )

    tab_n, tab_c, tab_g, tab_h = st.tabs(
        [
            "🍽️ 每日食物與營養素",
            "👗 胸部緊實運動",
            "🍑 臀部緊實運動",
            "💡 整體健康原則",
        ]
    )

    # --- 營養素與食物 ---
    with tab_n:
        st.subheader("依年齡層的女性每日營養素參考量")
        df_n = pd.DataFrame(NUTRIENT_TABLE).T
        df_n.index.name = "營養素"
        st.dataframe(df_n, use_container_width=True)
        st.caption(
            "蛋白質欄位以「每公斤體重」表示；其餘為當日總攝取量。"
            "50 歲後因肌少症與停經，蛋白質、鈣、維生素 D 建議向上修正，"
            "鐵則因經期停止而下調。"
        )
        st.markdown("---")
        st.markdown("**🥗 各營養素優質食物來源**")
        for nutrient, foods in NUTRIENT_FOODS.items():
            st.markdown(f"- **{nutrient}**：{foods}")

    # --- 胸部運動 ---
    with tab_c:
        st.subheader("改善胸部下垂：胸肌與姿勢訓練")
        st.caption(
            "胸部本身無肌肉，下垂視覺主因為「胸大肌支撐力下降 + 駝背姿勢」。"
            "強化胸大肌與肩胛後收肌群，可挺起胸線、改善體態。"
            "建議每週 2–3 次，組間休息 30–60 秒。"
        )
        _render_exercise_list(CHEST_EXERCISES)

    # --- 臀部運動 ---
    with tab_g:
        st.subheader("緊實臀部：臀肌訓練")
        st.caption(
            "久坐會抑制臀大肌活性 (gluteal amnesia)，導致臀部扁塌下垂並加重腰痛。"
            "下列動作著重於髖伸展與外展；建議每週 3 次，動作品質優先於次數。"
        )
        _render_exercise_list(GLUTE_EXERCISES)

    # --- 整體健康原則 ---
    with tab_h:
        st.subheader("維持抗老體質的 8 個原則")
        for item in HEALTH_PRINCIPLES:
            st.markdown(f"- {item}")


# ---------------------------------------------------------------------------
# AI 抗老減重顧問（Google Gemini）
# ---------------------------------------------------------------------------
GEMINI_MODELS = {
    "gemini-2.5-flash": "Gemini 2.5 Flash（快速、預設）",
    "gemini-2.5-pro": "Gemini 2.5 Pro（深度回答、較慢）",
}

GEMINI_SYSTEM_PROMPT = """你是一位專精「健康減重」與「抗老化」的繁體中文 AI 顧問。

請依下列原則回答使用者問題：
1. 語言風格：全程繁體中文，親切、條理清晰，善用小標題與條列方便閱讀。
2. 實證導向：以實證醫學、營養科學與運動科學為基礎；避免推薦極端節食、未經證實的偏方、藥物濫用或快速減重產品。
3. 整體生活型態：回答中盡量同時涵蓋「飲食、運動、睡眠、壓力管理、肌膚／姿勢」面向。
4. 可執行步驟：適時提供具體可量化的建議（例如：每日蛋白質克數、運動組數次數、食物份量、入睡時間）。
5. 醫療界線：若問題涉及疾病、用藥、孕哺、嚴重肥胖或極端體重變化，請明確建議諮詢醫師、營養師或物理治療師。
6. 個人化：若提供使用者最新打卡資料，請結合資料給出客製化建議；資料缺失時禮貌詢問或先給通用建議。

建議回答格式：
- 開頭以 1–2 句總結重點。
- 中段以小標題分段（例如：飲食原則／運動安排／睡眠調整／注意事項）。
- 結尾附 1 行重要提醒（如必要再諮詢專業）。
"""


# Gemini Key 在 secrets/env 中常見的變數名稱（涵蓋大小寫與相似命名）
GEMINI_KEY_NAMES = (
    "GEMINI_API_KEY",
    "gemini_api_key",
    "GOOGLE_API_KEY",
    "google_api_key",
)


def _mask_key(k: str) -> str:
    """以遮罩方式顯示 Key 字串，避免完整曝光。"""
    if not k:
        return "(空字串)"
    n = len(k)
    if n <= 8:
        return "•" * n
    return f"{k[:4]}…{k[-4:]}"


# Gemini Key 本身不含逗號／分號／pipe／空白／換行，因此可用這些當分隔符
# 把「多把 Key 串成一個字串」（例如 "k1, k2, k3"）拆回多個候選
_KEY_SPLIT_RE = re.compile(r"[,;|\s]+")


def _split_key_string(val: str) -> list[str]:
    """以常見分隔符拆解可能包含多把 Key 的字串，過濾空字串。"""
    return [p for p in _KEY_SPLIT_RE.split(val.strip()) if p]


def _is_geminiish_name(name: str) -> bool:
    """判斷一個變數名稱是否屬於 Gemini Key 系列（含複數 KEYS、編號後綴 _1 等）。"""
    upper = name.upper()
    for base in GEMINI_KEY_NAMES:
        b = base.upper()
        if upper == b or upper == b + "S" or upper.startswith(b + "_"):
            return True
    return False


def _collect_candidates(mapping, container_label: str = "") -> list[tuple[str, str]]:
    """從 mapping（st.secrets 或 section）擷取所有符合命名的字串／字串陣列值。"""
    out: list[tuple[str, str]] = []
    try:
        keys = list(mapping.keys())
    except Exception:
        return out
    prefix = f"{container_label}." if container_label else ""
    for k in keys:
        if not _is_geminiish_name(k):
            continue
        try:
            val = mapping[k]
        except Exception:
            continue
        if isinstance(val, str):
            parts = _split_key_string(val)
            if len(parts) == 1:
                out.append((f"{prefix}{k}", parts[0]))
            elif len(parts) > 1:
                # 多把 Key 串接在一個字串內：拆成多筆候選
                for i, p in enumerate(parts, start=1):
                    out.append((f"{prefix}{k}#{i}", p))
        elif isinstance(val, (list, tuple)):
            for i, item in enumerate(val):
                if not isinstance(item, str):
                    continue
                parts = _split_key_string(item)
                if len(parts) == 1:
                    out.append((f"{prefix}{k}[{i}]", parts[0]))
                else:
                    for j, p in enumerate(parts, start=1):
                        out.append((f"{prefix}{k}[{i}]#{j}", p))
        # dict-like 值會在 caller 的巢狀掃描中處理
    return out


def _scan_secrets_for_candidates() -> tuple[list[tuple[str, str]], dict]:
    """掃描 st.secrets 的所有 Gemini Key 候選（頂層 + 巢狀 section），回傳 (候選清單, 診斷)。"""
    cwd = os.getcwd()
    project_path = os.path.join(cwd, ".streamlit", "secrets.toml")
    home_path = os.path.expanduser("~/.streamlit/secrets.toml")
    diag: dict = {
        "cwd": cwd,
        "project_secrets_path": project_path,
        "project_secrets_exists": os.path.exists(project_path),
        "home_secrets_path": home_path,
        "home_secrets_exists": os.path.exists(home_path),
        "secrets_load_error": None,
        "top_level_keys": [],
        "nested_sections": {},
    }
    candidates: list[tuple[str, str]] = []
    try:
        top_keys = list(st.secrets.keys())
        diag["top_level_keys"] = top_keys
        # 1. 頂層
        candidates.extend(_collect_candidates(st.secrets))
        # 2. 巢狀 section
        for k in top_keys:
            try:
                section = st.secrets[k]
                if hasattr(section, "keys") and not isinstance(section, (str, bytes)):
                    sub_keys = list(section.keys())
                    diag["nested_sections"][k] = sub_keys
                    # ① section 內也按命名規則掃
                    candidates.extend(_collect_candidates(section, container_label=k))
                    # ② section 名稱本身就和 gemini/google 有關時，額外接受泛用名
                    if k.lower() in (
                        "gemini", "google", "google_gemini", "google_ai", "ai", "llm",
                    ):
                        for inner in sub_keys:
                            if inner.lower() in ("api_key", "key", "secret", "keys"):
                                v = section[inner]
                                if isinstance(v, str):
                                    parts = _split_key_string(v)
                                    if len(parts) == 1:
                                        candidates.append((f"{k}.{inner}", parts[0]))
                                    elif len(parts) > 1:
                                        for j, p in enumerate(parts, start=1):
                                            candidates.append((f"{k}.{inner}#{j}", p))
                                elif isinstance(v, (list, tuple)):
                                    for i, item in enumerate(v):
                                        if not isinstance(item, str):
                                            continue
                                        parts = _split_key_string(item)
                                        if len(parts) == 1:
                                            candidates.append(
                                                (f"{k}.{inner}[{i}]", parts[0])
                                            )
                                        else:
                                            for j, p in enumerate(parts, start=1):
                                                candidates.append(
                                                    (f"{k}.{inner}[{i}]#{j}", p)
                                                )
            except Exception:
                continue
    except Exception as e:
        diag["secrets_load_error"] = f"{type(e).__name__}: {e}"
    return candidates, diag


def _collect_env_candidates() -> list[tuple[str, str]]:
    """從 os.environ 擷取 Gemini Key 候選（含 GEMINI_API_KEY_1 等變體；支援多 Key 串接）。"""
    out: list[tuple[str, str]] = []
    for k, v in os.environ.items():
        if not isinstance(v, str) or not v.strip():
            continue
        if not _is_geminiish_name(k):
            continue
        parts = _split_key_string(v)
        if len(parts) == 1:
            out.append((f"env:{k}", parts[0]))
        elif len(parts) > 1:
            for i, p in enumerate(parts, start=1):
                out.append((f"env:{k}#{i}", p))
    return out


def _get_gemini_candidates() -> tuple[list[tuple[str, str]], dict]:
    """聚合所有 Gemini Key 候選並回傳診斷。
    順序：session 手動輸入 → st.secrets → 環境變數；重複 Key 值僅保留首次出現。"""
    diag: dict = {"session_set": False, "secrets": {}, "env_count": 0}
    raw: list[tuple[str, str]] = []

    manual = st.session_state.get("_gemini_key_manual")
    if manual:
        diag["session_set"] = True
        raw.append(("session(手動輸入)", manual))

    secrets_cands, sdiag = _scan_secrets_for_candidates()
    diag["secrets"] = sdiag
    raw.extend([(f"secrets:{l}", v) for l, v in secrets_cands])

    env_cands = _collect_env_candidates()
    diag["env_count"] = len(env_cands)
    raw.extend(env_cands)

    # 依 Key 值去重，保留第一筆
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for lbl, val in raw:
        if val in seen:
            continue
        seen.add(val)
        unique.append((lbl, val))
    return unique, diag


def _build_user_context(df: pd.DataFrame) -> str:
    """將使用者最新一筆打卡資料整理為文字摘要，供 AI 個人化使用。"""
    if df.empty:
        return "（使用者尚未開始打卡，無個人化資料。）"
    latest = df.sort_values("Date").iloc[-1]
    yn = lambda v: "✅ 已完成" if bool(v) else "❌ 未完成"
    return (
        f"- 最新打卡日期：{latest['Date']}\n"
        f"- 體重：{float(latest['Weight']):.1f} kg\n"
        f"- 今日久坐：{float(latest['Sitting_Hours']):.1f} 小時\n"
        f"- 蛋白質攝取：{float(latest['Protein_g']):.0f} g\n"
        f"- 飲水量：{float(latest['Water_ml']):.0f} ml\n"
        f"- 起來走動：{int(latest['Active_Breaks_Count'])} 次\n"
        f"- 防曬：{yn(latest['Sunscreen_Done'])}\n"
        f"- 睡眠 > 7 小時：{yn(latest['Good_Sleep_Done'])}\n"
        f"- 臉部運動：{yn(latest['Face_Exercise_Done'])}\n"
        f"- 乳液鎖水：{yn(latest['Lotion_Applied_Done'])}\n"
    )


def _call_gemini(
    api_key: str, model: str, history: list, user_context: str
) -> str:
    """以對話歷史 + 個人化資料呼叫 Gemini API，回傳 AI 文字回應。"""
    # 延遲匯入：缺少套件時不影響整個 app 啟動
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    system_text = (
        GEMINI_SYSTEM_PROMPT
        + "\n\n【使用者最新打卡資料】\n"
        + user_context
    )

    contents = [
        types.Content(
            role=("user" if m["role"] == "user" else "model"),
            parts=[types.Part(text=m["content"])],
        )
        for m in history
    ]

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(system_instruction=system_text),
    )
    return response.text or "（AI 未能生成回應，請重試或換個問題。）"


# ---- 錯誤分類與自動換 Key ----
_ERROR_LABELS = {
    "KEY_INVALID": "Key 無效 (400)",
    "QUOTA": "配額耗盡 (429)",
    "KEY_NO_PERMISSION": "Key 無權限 (403)",
    "MODEL_OVERLOAD": "模型忙線 (503)",
    "MODEL_INTERNAL": "伺服器內部錯誤 (500)",
    "OTHER": "其他錯誤",
}
# 換 Key 才有用的錯誤類別（屬於這把 Key 本身的問題）
_KEY_SWITCH_CLASSES = {"QUOTA", "KEY_INVALID", "KEY_NO_PERMISSION"}
# 屬於 Google 端模型/伺服器暫時錯誤；換 Key 無效，僅同 Key 重試 1 次
_RETRY_SAME_KEY_CLASSES = {"MODEL_OVERLOAD", "MODEL_INTERNAL"}


def _classify_gemini_error(exc: Exception) -> str:
    """依錯誤訊息分類 Gemini 失敗類型，決定後續處置。"""
    s = str(exc).upper()
    if "API_KEY_INVALID" in s or "API KEY NOT VALID" in s:
        return "KEY_INVALID"
    if "RESOURCE_EXHAUSTED" in s or "QUOTA" in s or " 429" in s or "'CODE': 429" in s:
        return "QUOTA"
    if "PERMISSION_DENIED" in s or " 403" in s or "'CODE': 403" in s:
        return "KEY_NO_PERMISSION"
    if "UNAVAILABLE" in s or " 503" in s or "'CODE': 503" in s:
        return "MODEL_OVERLOAD"
    if " 500" in s or "'CODE': 500" in s or "INTERNAL" in s:
        return "MODEL_INTERNAL"
    return "OTHER"


def _fmt_model_overload(model: str, klass: str) -> str:
    if klass == "MODEL_OVERLOAD":
        return (
            f"⏳ **`{model}` 模型目前忙線中（503 UNAVAILABLE）**\n\n"
            "這是 **Google 端模型過載**，與你的 API Key 或配額**無關**，"
            "因此自動切換 Key 也救不了（相同模型不論用哪把 Key 都受同一波負載影響）。\n\n"
            "建議處理：\n"
            "- 稍等 30–60 秒後重新送出問題\n"
            "- 切換到另一個模型（上方下拉改選 Gemini 2.5 Pro 或回到 Flash）"
        )
    return (
        f"⚠️ **`{model}` 伺服器內部錯誤（500 INTERNAL）**\n\n"
        "Google 端內部錯誤，與你的 Key 無關。請稍後重試或改用其他模型。"
    )


def _fmt_unknown_error(e: Exception) -> str:
    return (
        f"❌ 呼叫 Gemini API 失敗：`{type(e).__name__}: {str(e)[:300]}`\n\n"
        "未能歸類的錯誤；請檢查網路或稍後再試。"
    )


def _fmt_all_failed(attempts: list[dict]) -> str:
    lines = ["❌ **所有可用的 API Key 都嘗試失敗**", "", "嘗試紀錄："]
    for a in attempts:
        lines.append(f"- `{a['label']}` → {_ERROR_LABELS.get(a['class'], a['class'])}")
    lines.append("")
    lines.append(
        "請到 https://aistudio.google.com/apikey 確認 Key 狀態與配額，"
        "或到 Google Cloud Console 檢查專案是否被停用。"
    )
    return "\n".join(lines)


def _call_gemini_with_fallback(
    candidates: list[tuple[str, str]],
    starting_label: str,
    model: str,
    history: list,
    user_context: str,
) -> dict:
    """依候選 Key 列表呼叫 Gemini，必要時自動換 Key。

    處置策略：
    - QUOTA / KEY_INVALID / KEY_NO_PERMISSION：屬於 Key 本身問題 → 換下一把
    - MODEL_OVERLOAD / MODEL_INTERNAL：屬於 Google 端 → 同 Key 等待後重試 1 次；
      仍失敗則不換 Key（換了無效），直接回報模型/伺服器忙線
    - OTHER：立即回報，不浪費其他 Key
    """
    import time

    # 從使用者選定的 Key 開始，其餘依候選順序作為備援
    ordered = [(l, v) for l, v in candidates if l == starting_label]
    ordered += [(l, v) for l, v in candidates if l != starting_label]

    attempts: list[dict] = []

    for label, api_key in ordered:
        try:
            reply = _call_gemini(api_key, model, history, user_context)
            return {"reply": reply, "label_used": label, "attempts": attempts, "final_class": None}
        except ModuleNotFoundError:
            return {
                "reply": "❌ 尚未安裝 Gemini 套件。請執行 `pip install google-genai` 後重啟應用程式。",
                "label_used": None,
                "attempts": attempts,
                "final_class": "MODULE_MISSING",
            }
        except Exception as e:
            klass = _classify_gemini_error(e)
            attempts.append({"label": label, "class": klass, "raw": str(e)[:300]})

            if klass in _RETRY_SAME_KEY_CLASSES:
                # 換 Key 無效；同 Key 等 2 秒重試 1 次
                time.sleep(2)
                try:
                    reply = _call_gemini(api_key, model, history, user_context)
                    return {"reply": reply, "label_used": label, "attempts": attempts, "final_class": None}
                except Exception as e2:
                    klass2 = _classify_gemini_error(e2)
                    attempts.append({"label": label, "class": klass2, "raw": str(e2)[:300]})
                    return {
                        "reply": _fmt_model_overload(model, klass2),
                        "label_used": label,
                        "attempts": attempts,
                        "final_class": klass2,
                    }
            elif klass in _KEY_SWITCH_CLASSES:
                continue  # 換下一把 Key
            else:
                return {
                    "reply": _fmt_unknown_error(e),
                    "label_used": label,
                    "attempts": attempts,
                    "final_class": klass,
                }

    # 全部候選都失敗
    return {
        "reply": _fmt_all_failed(attempts),
        "label_used": None,
        "attempts": attempts,
        "final_class": "ALL_FAILED",
    }


def render_ai_advisor(df: pd.DataFrame) -> None:
    """AI 抗老減重顧問對話介面（使用 Google Gemini API）。"""
    st.divider()
    st.header("🤖 AI 抗老減重顧問（Google Gemini）")
    st.caption(
        "⚠️ 本顧問由生成式 AI 提供建議，僅供一般保健參考，不能取代專業醫療診斷。"
        "AI 可能出錯，請以個人健康狀況與專業意見為準。"
    )

    candidates, diag = _get_gemini_candidates()

    # --- 未設定 API Key：引導設定 + 顯示診斷 ---
    if not candidates:
        st.info(
            "🔑 尚未設定 Gemini API Key。可任選下列其一：\n\n"
            "- 在 `.streamlit/secrets.toml` 加入 `GEMINI_API_KEY = \"...\"`（推薦）\n"
            "- 設定環境變數 `GEMINI_API_KEY`\n"
            "- 或於下方欄位貼上 API Key（僅儲存於目前瀏覽器 session）"
        )

        # 診斷：協助使用者判斷 secrets 為何讀不到
        with st.expander("🔍 為何 secrets 沒被讀到？（診斷資訊）", expanded=True):
            s = diag.get("secrets", {})
            st.markdown(f"- **目前工作目錄**：`{s.get('cwd')}`")
            st.markdown(
                f"- **專案層 secrets.toml**：`{s.get('project_secrets_path')}`　"
                f"{'✅ 存在' if s.get('project_secrets_exists') else '❌ 不存在'}"
            )
            st.markdown(
                f"- **使用者層 secrets.toml**：`{s.get('home_secrets_path')}`　"
                f"{'✅ 存在' if s.get('home_secrets_exists') else '❌ 不存在'}"
            )
            if s.get("secrets_load_error"):
                st.error(
                    f"⚠️ 載入 secrets 失敗：`{s['secrets_load_error']}`"
                    "（請檢查 TOML 語法，例如字串是否以雙引號包住）"
                )
            if s.get("top_level_keys"):
                st.markdown(f"- **secrets 內偵測到的頂層鍵**：`{s['top_level_keys']}`")
            if s.get("nested_sections"):
                st.markdown(f"- **巢狀 section 內的鍵**：`{s['nested_sections']}`")
            if (
                (s.get("project_secrets_exists") or s.get("home_secrets_exists"))
                and not s.get("secrets_load_error")
                and (s.get("top_level_keys") or s.get("nested_sections"))
            ):
                st.warning(
                    "📌 secrets.toml 有讀到，但找不到符合名稱的 Gemini Key。"
                    f"已嘗試的鍵名：`{list(GEMINI_KEY_NAMES)}`（含巢狀 section 的 `api_key`）。"
                    "請確認 `.streamlit/secrets.toml` 內有下列其中一種寫法："
                )
                st.code(
                    'GEMINI_API_KEY = "你的 Key 字串"\n'
                    "\n# 或巢狀寫法：\n"
                    "[gemini]\n"
                    'api_key = "你的 Key 字串"',
                    language="toml",
                )
            elif not (s.get("project_secrets_exists") or s.get("home_secrets_exists")):
                st.warning(
                    "📌 兩個位置都沒有 secrets.toml。請把檔案放在「執行 "
                    "`streamlit run` 的資料夾」下的 `.streamlit/secrets.toml`，"
                    "或放在 `~/.streamlit/secrets.toml`，並重啟 Streamlit。"
                )
            st.markdown(
                f"- **檢查過的環境變數**：嘗試名稱包含 `{list(GEMINI_KEY_NAMES)}`、"
                f"`*_S`（複數）與 `*_<suffix>`（編號）；找到 `{diag.get('env_count', 0)}` 個"
            )

        with st.expander("如何取得 Gemini API Key？"):
            st.markdown(
                "1. 前往 Google AI Studio：https://aistudio.google.com/apikey\n"
                "2. 以 Google 帳號登入後點選「Create API key」\n"
                "3. 複製產生的 Key 後，貼到下方欄位或寫進 secrets.toml\n\n"
                "免費方案有每日使用額度，正式商用請評估付費方案。"
            )
        manual_key = st.text_input(
            "Gemini API Key（手動輸入備援）",
            type="password",
            key="_gemini_key_input",
            placeholder="貼上 API Key 後按 Enter 送出",
        )
        if manual_key:
            st.session_state["_gemini_key_manual"] = manual_key
            st.rerun()
        return

    # --- 有 API Key 候選：必要時讓使用者挑選要使用的 Key ---
    label_to_value = {lbl: val for lbl, val in candidates}
    if len(candidates) > 1:
        labels = [lbl for lbl, _ in candidates]
        prev = st.session_state.get("_gemini_key_label")
        default_idx = labels.index(prev) if prev in labels else 0
        chosen_label = st.selectbox(
            f"🔑 Gemini Key 來源（偵測到 {len(candidates)} 把 Key，可任意切換）",
            labels,
            index=default_idx,
            format_func=lambda lbl: f"{lbl}　→　{_mask_key(label_to_value[lbl])}",
        )
        st.session_state["_gemini_key_label"] = chosen_label
    else:
        chosen_label = candidates[0][0]
        st.caption(
            f"🔑 使用的 Key 來源：`{chosen_label}`　→　`{_mask_key(label_to_value[chosen_label])}`"
        )
    api_key = label_to_value[chosen_label]

    # --- 模型選擇 + 對話介面 ---
    top_cols = st.columns([3, 1, 1])
    with top_cols[0]:
        model_label = st.selectbox(
            "模型",
            options=list(GEMINI_MODELS.keys()),
            format_func=lambda k: GEMINI_MODELS[k],
            key="_gemini_model",
        )
    with top_cols[1]:
        st.write("")  # 對齊按鈕高度
        if st.button("🔄 清除對話", use_container_width=True):
            st.session_state["ai_history"] = []
            st.rerun()
    with top_cols[2]:
        st.write("")
        # 僅當 Key 來自手動輸入時，才顯示重設 Key 按鈕
        if st.session_state.get("_gemini_key_manual") and st.button(
            "🔑 重設 Key", use_container_width=True
        ):
            st.session_state.pop("_gemini_key_manual", None)
            st.session_state["ai_history"] = []
            st.rerun()

    # 初始化對話歷史
    if "ai_history" not in st.session_state:
        st.session_state["ai_history"] = []

    # 顯示既有對話
    for msg in st.session_state["ai_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 接收新輸入
    user_input = st.chat_input(
        "輸入你的健康減重或抗老問題，例如：「我 45 歲想瘦小腹該怎麼吃？」"
    )
    if user_input:
        st.session_state["ai_history"].append(
            {"role": "user", "content": user_input}
        )
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("AI 思考中..."):
                result = _call_gemini_with_fallback(
                    candidates,
                    chosen_label,
                    model_label,
                    st.session_state["ai_history"],
                    _build_user_context(df),
                )
            reply = result["reply"]
            # 若實際成功使用的 Key 與選定不同，顯著標註發生過自動切換
            if (
                result["label_used"]
                and result["label_used"] != chosen_label
                and result["final_class"] is None
            ):
                reply = (
                    f"_（🔁 `{chosen_label}` 失敗，已自動切換到 `{result['label_used']}`）_\n\n"
                    + reply
                )
            st.markdown(reply)
            # 透明化：列出所有重試／切換嘗試與分類
            if result["attempts"]:
                with st.expander(
                    f"🔍 自動切換／重試紀錄（{len(result['attempts'])} 次）"
                ):
                    for a in result["attempts"]:
                        st.markdown(
                            f"- `{a['label']}` → **{_ERROR_LABELS.get(a['class'], a['class'])}**"
                        )
                        st.caption(a["raw"])

        st.session_state["ai_history"].append(
            {"role": "assistant", "content": reply}
        )


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
    # 健康保養與抗下垂建議：營養素、胸／臀運動、生活原則
    render_wellness_guide()
    # AI 抗老減重顧問：使用 Google Gemini，依使用者最新打卡資料給個人化建議
    render_ai_advisor(df)


if __name__ == "__main__":
    main()
