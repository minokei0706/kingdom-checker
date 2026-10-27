import streamlit as st
from PIL import Image
import io
import google.generativeai as genai

st.set_page_config(page_title="キングダム覇道 凸数読み取りツール", layout="centered")

st.title("🛡️ 凸数スクショ読み取りツール")
st.caption("キャラ一覧のスクショをアップロードすると、凸数を一覧出力します。")

# StreamlitのSecretsからAPIキーを取得
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.text_input("Gemini APIキーを入力してください", type="password")

if not api_key:
    st.warning("APIキーが設定されていません。")
    st.stop()

genai.configure(api_key=api_key)

# 利用可能な最新モデルを自動判別する関数（404エラー防止）
def get_best_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # 最新の高速モデルを優先的に探す
        for pref in ["gemini-2.5-flash", "gemini-2.0-flash", "flash"]:
            for m in models:
                if pref in m:
                    return genai.GenerativeModel(m)
        if models:
            return genai.GenerativeModel(models[0])
    except Exception:
        pass
    return genai.GenerativeModel("gemini-2.5-flash")

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
    "キャラ一覧のスクショを選択（複数まとめて選択可能）", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

# 画像を自動圧縮する関数（複数枚アップロード時の容量オーバー対策）
def resize_image(file):
    img = Image.open(file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((1000, 1000))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=80)
    buffer.seek(0)
    return Image.open(buffer)

if uploaded_files:
    st.write(f"📁 アップロードされた画像: {len(uploaded_files)} 枚")
    
    if st.button("凸数を解析する", type="primary"):
        with st.spinner("画像を軽量化して最新AIが解析中...（15〜30秒ほどかかります）"):
            try:
                processed_images = [resize_image(f) for f in uploaded_files]
                model = get_best_model()

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
                response = model.generate_content([prompt, *processed_images])
                result_text = response.text

                st.success("解析完了！")
                st.text_area("解析結果（コピー用）", value=result_text, height=450)

            except Exception as e:
                st.error(f"エラー内容: {e}")
