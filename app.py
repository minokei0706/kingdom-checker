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

# 視覚認識モデル
model = genai.GenerativeModel("gemini-3.8-flash")

# 横画面に合わせて高解像度（横幅1920px）をキープ
def optimize_image(file):
    img = Image.open(file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    w, h = img.size
    # 横幅が1920pxを超える場合のみリサイズ（文字と星を鮮明に残す）
    if w > 1920:
        new_h = int(h * (1920 / w))
        img = img.resize((1920, new_h), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
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
        with st.spinner("武将カードの星と名前を照合中...（30〜50秒ほどお待ちください）"):
            try:
                processed_images = [optimize_image(f) for f in uploaded_files]

                prompt = f"""
添付されたゲーム画面（キングダム覇道）のスクリーンショットを解析し、武将ごとの星の数（凸数）を特定してください。

【画面構造のルール】
1. 各武将のカード枠の「左下の黒い半透明帯」に武将名が白文字で書かれています（例: 王騎, 麃公, 嬴政, 羌瘣, 楊端和, 騰, 昭王 など）。
2. 各武将カードの「右上（上部）」に星（★）が横一列に最大7個並んでいます。
   - 【左から黄色く点灯している星の数】を正確に数えてください（0〜7）。
   - 暗い星・灰色の星は消灯しているため数に入れません。
   - 例: 王騎は左から6個黄色で1個暗いので「6」、バジオウは7個すべて黄色なので「7」、昭王は1個だけ黄色なので「1」。
3. 右端などで半分見切れている武将は判定せず、完全に枠全体が写っている画像を優先して判定してください。
4. 【未所持（なし）の判定】
   - 画面内に名前が全く写っていないキャラは「なし」です。絶対に当てずっぽうで数字を埋めないでください。
   - グレーアウト（暗くなっている、鍵付き）している武将も「なし」です。
5. 800枠は画像判定不要で、テンプレートの固定文をそのまま出力してください。

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
