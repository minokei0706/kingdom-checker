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

# 視覚認識モデル（温度を低くして当てずっぽうを完全排除）
model = genai.GenerativeModel(
    "gemini-3.8-flash",
    generation_config={"temperature": 0.1}
)

# 星の色や形をハッキリ残しつつ、通信がフリーズしない最適サイズ（横幅1280px）に調整
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
        with st.spinner("画像を最適化してAIが精密解析中...（20秒ほどお待ちください）"):
            try:
                processed_images = [optimize_image(f) for f in uploaded_files]

                prompt = f"""
添付されたゲーム画面（キングダム覇道）から、武将カードの星の数（凸数）を正確に特定してください。

【星の判定ルール】
各武将カードの右上にある星は「必ず横一列に合計7個」並んでいます。
左から順に黄色い星が並び、途中から灰色の暗い星になります。
必ず「右側の暗い（灰色の）星の数」を数えて、引き算で正確に算出してください。

- 灰色の星が0個（すべて黄色） ➡️ 「7」
- 灰色の星が1個だけ（黄色が6個） ➡️ 「6」
- 灰色の星が2個（黄色が5個） ➡️ 「5」
- 灰色の星が3個（黄色が4個） ➡️ 「4」
- 灰色の星が4個（黄色が3個） ➡️ 「3」
- 灰色の星が5個（黄色が2個） ➡️ 「2」
- 灰色の星が6個（黄色が1個だけ） ➡️ 「1」
- 7個すべて灰色（黄色が0個） ➡️ 「0」

※推測は禁止です。各カードの星の実際の点灯状態を見て判定してください。

【未所持の判定】
- 画面内に名前が写っていないキャラ、または暗くグレーアウト（鍵付き）しているキャラは「なし」と記載してください。

【出力フォーマット】
以下の【キャラ一覧リスト】のフォーマット通りに出力してください。余計な解説・前置きは一切不要です。

【キャラ一覧リスト】
{character_template}
"""
                response = model.generate_content([prompt, *processed_images])
                result_text = response.text

                st.success("解析完了！")
                st.text_area("解析結果（コピー用）", value=result_text, height=450)

            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg:
                    st.error("⚠️ アクセス制限です。30秒ほど待ってから再度ボタンを押してください。")
                else:
                    st.error(f"エラー内容: {e}")
