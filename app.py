import streamlit as st
from PIL import Image
import google.generativeai as genai

st.set_page_config(page_title="キングダム覇道 凸数読み取りツール", layout="centered")

st.title("🛡️ 凸数スクショ読み取りツール")
st.caption("キャラ一覧のスクショをアップロードすると、凸数を一覧出力します。")

# StreamlitのSecrets（環境変数）からAPIキーを読み込む
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("Gemini APIキーを入力してください", type="password")

if not api_key:
    st.warning("APIキーが設定されていません。")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# キャラテンプレート
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
    "キャラ一覧のスクショをすべて選択（複数選択可）", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"アップロードされた画像: {len(uploaded_files)} 枚")
    
    if st.button("凸数を解析する", type="primary"):
        with st.spinner("AIが武将と星の数を解析中...（10〜20秒ほどかかります）"):
            try:
                images = [Image.open(f) for f in uploaded_files]

                prompt = f"""
添付されたゲーム画面のスクリーンショットを解析し、武将の凸数（星の数: 0〜7）を特定してください。

【ルール】
- 以下の【キャラ一覧リスト】のフォーマット通りに、キャラ名の後ろに星の数を記載してください。
- 未所持（グレーアウト、未解放）またはスクショ内に見当たらないキャラは「なし」と記載してください。
- 800枠は画像判定不要で、テンプレートの記述（紫夏・オギコ なし / 他は完凸）をそのまま出力してください。
- 余計な前置きや注釈は書かず、以下のフォーマットの結果テキストのみを出力してください。

【キャラ一覧リスト】
{character_template}
"""
                response = model.generate_content([prompt, *images])
                result_text = response.text

                st.success("解析完了！")
                st.text_area("解析結果（コピー用）", value=result_text, height=400)

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
