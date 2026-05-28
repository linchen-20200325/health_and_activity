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


if __name__ == "__main__":
    main()
