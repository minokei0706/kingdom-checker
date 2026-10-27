import streamlit as st
from PIL import Image
import io
import re
import google.generativeai as genai

st.set_page_config(page_title="キングダム覇道 凸数読み取りツール", layout="centered")

st.title("🛡️ 凸数スクショ読み取りツール")
st.caption("キャラ一覧のスクショをアップロードすると、凸数を一覧出力します。")

api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("Gemini APIキーを入力してください", type="password")

if not api_key:
    st.warning("APIキーが設定されていません。")
    st.stop()

genai.configure(api_key=api_key)

# Googleの指定に従い最新の gemini-3.8-flash を取得
def get_best_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for pref in ["gemini-3.8-flash", "gemini-3", "flash"]:
            for m in models:
                if pref in m:
                    return genai.GenerativeModel(m)
        if models:
            return genai.GenerativeModel(models[0])
    except Exception:
        pass
    return genai.GenerativeModel("gemini-3.8-flash")

# 画像を軽量化（長辺700px）
def resize_image(file):
    img = Image.open(file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((700, 700))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=70)
    buffer.seek(0)
    return Image.open(buffer)

# 定義リスト
list_900 = [
    "王騎", "(旧)楊端和", "麃公", "騰", "バジオウ", "(旧)嬴政", "(旧)羌瘣", "呉慶",
    "輪虎", "(新)信", "蒙恬", "王賁", "蒙驁", "摎", "廉頗", "王翦", "オルド",
    "汗明", "李牧", "呉鳳明", "桓騎", "呂不韋", "春申君", "(新)嬴政", "介億",
    "カイネ", "傅抵", "(新)河了貂", "(新)楊端和", "龐煖", "蒙武", "万極",
    "趙荘", "李白", "(新)羌瘣", "昭王"
]

list_850 = [
    "(旧)信", "漂", "壁", "録嗚未", "タジフ", "ランカイ", "シュンメン", "成蟜",
    "縛虎申", "宮元", "介子坊", "姜燕", "関常", "陸仙", "成恢", "臨武君",
    "項翼", "張唐", "岳雷", "晋成常", "蔡沢", "白麗", "渉孟", "馮忌",
    "公孫龍", "李斯", "羌象"
]

uploaded_files = st.file_uploader(
    "キャラ一覧のスクショを選択（何枚でもまとめてOK）", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"📁 アップロードされた画像: {len(uploaded_files)} 枚")
    
    if st.button("凸数を解析する", type="primary"):
        model = get_best_model()
        char_stars = {}
        progress_bar = st.progress(0)
        status_text = st.empty()

        # 3枚ずつ分割して解析
        chunk_size = 3
        chunks = [uploaded_files[i:i + chunk_size] for i in range(0, len(uploaded_files), chunk_size)]
        
        try:
            for idx, chunk in enumerate(chunks):
                status_text.text(f"解析中...（グループ {idx + 1} / {len(chunks)} を処理しています）")
                processed_chunk = [resize_image(f) for f in chunk]

                prompt = """
添付されたゲーム画面から武将の名前と星の数（凸数）を読み取り、以下の形式で武将ごとに1行ずつ出力してください。
武将名: 星の数（0〜7、未所持やグレーアウトは「なし」）

※新旧がある武将（信、楊端和、嬴政、羌瘣、河了貂）は、衣装や属性で新旧を区別してください。
余計な解説は不要です。行のリストのみを出力してください。
例:
王騎: 6
(旧)楊端和: 6
呉慶: なし
"""
                response = model.generate_content([prompt, *processed_chunk])
                
                for line in response.text.split("\n"):
                    if ":" in line or "：" in line:
                        parts = re.split(r"[:：]", line, maxsplit=1)
                        if len(parts) == 2:
                            name = parts[0].strip()
                            val = parts[1].strip()
                            for target in list_900 + list_850:
                                clean_target = target.replace("(新)", "").replace("(旧)", "")
                                if clean_target in name:
                                    if "(新)" in target and "(新)" in name:
                                        char_stars[target] = val
                                    elif "(旧)" in target and "(旧)" in name:
                                        char_stars[target] = val
                                    elif target not in char_stars:
                                        char_stars[target] = val

                progress_bar.progress((idx + 1) / len(chunks))

            status_text.text("解析完了！")

            output = "【900】\n"
            for c in list_900:
                star = char_stars.get(c, "なし")
                output += f"{c} {star}\n"

            output += "\n【850】\n"
            for c in list_850:
                star = char_stars.get(c, "なし")
                output += f"{c} {star}\n"

            output += "\n【800】\n紫夏・オギコ　なし\n他は完凸\n"

            st.success("すべての解析が完了しました！")
            st.text_area("解析結果（コピー用）", value=output, height=450)

        except Exception as e:
            st.error(f"エラー内容: {e}")
