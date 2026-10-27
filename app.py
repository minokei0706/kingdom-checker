import streamlit as st
from PIL import Image
import io
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

# 最新モデルを指定
model = genai.GenerativeModel("gemini-3.8-flash")

# 画像を極力軽量化する（1枚あたり数十KBにする）
def resize_image(file):
    img = Image.open(file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((700, 700))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=70)
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
    "キャラ一覧のスクショを選択（何枚でもまとめてOK）", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"📁 アップロードされた画像: {len(uploaded_files)} 枚")
    
    if st.button("凸数を解析する", type="primary"):
        with st.spinner("画像を最適化してAIが一括解析中...（10〜20秒ほどお待ちください）"):
            try:
                # すべての画像を軽量化
                processed_images = [resize_image(f) for f in uploaded_files]

                prompt = f"""
添付されたゲーム画面のスクリーンショットをすべて確認し、武将の凸数（星の数: 0〜7）を特定してください。

【出力ルール】
- 以下の【キャラ一覧リスト】のフォーマット通りに、キャラ名の後ろに星の数（半角数字）を記載してください。
- 未所持（グレーアウト、未解放）またはスクショ内に写っていないキャラは「なし」と記載してください。
- 800枠は画像判定不要で、テンプレートの記述（紫夏・オギコ なし / 他は完凸）をそのまま出力してください。
- 余計な解説は不要です。以下のフォーマットの結果テキストのみを出力してください。

【キャラ一覧リスト】
{character_template}
"""
                # 1回のリクエストですべてまとめて送信（制限に引っかからない）
                response = model.generate_content([prompt, *processed_images])
                result_text = response.text

                st.success("解析完了！")
                st.text_area("解析結果（コピー用）", value=result_text, height=450)

            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg:
                    st.error("⚠️ 無料枠のアクセス制限（1分間に5回まで）に引っかかりました。30秒ほど待ってからもう一度ボタンを押してください。")
                else:
                    st.error(f"エラー内容: {e}")
