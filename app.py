import streamlit as st
from PIL import Image
import io
import google.generativeai as genai

st.set_page_config(page_title="キングダム覇道 凸数読み取りツール", layout="centered")

st.title("🛡️ 凸数スクショ読み取りツール")
st.caption("キャラ一覧のスクショをアップロードすると、凸数を正確に出力します。")

api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("Gemini APIキーを入力してください", type="password")

if not api_key:
    st.warning("APIキーが設定されていません。")
    st.stop()

genai.configure(api_key=api_key)

# 一番精度が高かったモデル（当てずっぽうを排除する設定）
model = genai.GenerativeModel(
    "gemini-3.8-flash",
    generation_config={"temperature": 0.0}
)

# あの時の「星がくっきり見えて通信も速い」最適サイズ
def optimize_image(file):
    img = Image.open(file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    w, h = img.size
    if w > 1280:
        new_h = int(h * (1280 / w))
        img = img.resize((1280, new_h), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=80)
    buffer.seek(0)
    return Image.open(buffer)

character_template = """
【900】
王騎 
(旧)楊端和 
麃公 
騰 
バジオウ 
(旧)嬴政 
(旧)羌瘣 
呉慶 
輪虎 
(新)信 
蒙恬 
王賁 
蒙驁 
摎 
廉頗 
王翦 
オルド 
汗明 
李牧 
呉鳳明 
桓騎 
呂不韋 
春申君 
(新)嬴政 
介億 
カイネ 
傅抵 
(新)河了貂 
(新)楊端和 
龐煖 
蒙武 
万極 
趙荘 
李白 
(新)羌瘣 
昭王 

【850】
(旧)信 
漂 
壁 
録嗚未 
タジフ 
ランカイ 
シュンメン 
成蟜 
縛虎申 
宮元 
介子坊 
姜燕 
関常 
陸仙 
成恢 
臨武君 
項翼 
張唐 
岳雷 
晋成常 
蔡沢 
白麗 
渉孟 
馮忌 
公孫龍 
李斯 
羌象 

【800】
紫夏・オギコ　なし
他は完凸
"""

uploaded_files = st.file_uploader(
    "キャラ一覧のスクショを選択（複数まとめてOK）", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"📁 アップロードされた画像: {len(uploaded_files)} 枚")
    
    if st.button("凸数を解析する", type="primary"):
        with st.spinner("画像を最適化してAIが高速・精密解析中...（約15〜20秒）"):
            try:
                processed_images = [optimize_image(f) for f in uploaded_files]

                prompt = f"""
添付されたキングダム覇道のスクリーンショットを解析し、武将ごとの凸数（星の数）を正確に特定してください。

【星の判定ルール（最重要）】
各武将カードの右上にある星は横一列に「合計7個」並んでいます。
密集した黄色い星を見誤らないよう、必ず「右側の暗い（灰色の）星の数」を数えて引き算してください。
- 灰色の星が0個（全点灯） ➡️ 「7」
- 灰色の星が1個だけ ➡️ 「6」（※成蟜や王騎など、灰色が1個なら絶対に6です）
- 灰色の星が2個 ➡️ 「5」
- 灰色の星が3個 ➡️ 「4」（※麃公など）
- 灰色の星が4個 ➡️ 「3」
- 灰色の星が5個 ➡️ 「2」
- 灰色の星が6個 ➡️ 「1」
- 7個すべて灰色 ➡️ 「0」

【未所持のルール（推測禁止）】
- 画像のどこにも名前が写っていないキャラ、または暗くグレーアウト（鍵付き）しているキャラは、絶対に推測で数字を埋めず「なし」と記載してください。
- 例: 呉慶や新楊端和が画像内にいない場合は、必ず「なし」です。

【出力フォーマット】
以下の【キャラ一覧リスト】のフォーマット通りに出力してください。余計な解説は不要です。

【キャラ一覧リスト】
{character_template}
"""
                response = model.generate_content([prompt, *processed_images])
                result_text = response.text

                st.success("解析完了！")
                st.text_area("解析結果（コピー用）", value=result_text, height=450)

            except Exception as e:
                st.error(f"エラー詳細: {e}")
