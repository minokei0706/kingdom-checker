import streamlit as st
from PIL import Image
import io
import re
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

# 上位モデルを使用
model = genai.GenerativeModel(
    "gemini-3.8-flash",
    generation_config={"temperature": 0.0}
)

def optimize_image(file):
    img = Image.open(file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    w, h = img.size
    if w > 1280:
        new_h = int(h * (1280 / w))
        img = img.resize((1280, new_h), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)
    return Image.open(buffer)

# マスターリスト
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
    "キャラ一覧のスクショを選択（複数まとめてOK）", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"📁 アップロードされた画像: {len(uploaded_files)} 枚")
    
    if st.button("凸数を解析する", type="primary"):
        with st.spinner("AIが画面に見えている武将だけを抽出中...（30秒ほどお待ちください）"):
            try:
                processed_images = [optimize_image(f) for f in uploaded_files]

                prompt = """
添付されたゲーム画面（キングダム覇道）を見て、【画面内に実際に写っている武将だけ】をリストアップしてください。
画面に写っていない武将は絶対に書かないでください。

【書き出しルール】
武将名: 星の数（0〜7）

【星の数え方】
各カードの右上にある星は横一列に合計7個です。
右側の暗い（灰色の）星の数を数えて引き算してください。
- 灰色0個（全点灯） ➡️ 7
- 灰色1個 ➡️ 6
- 灰色2個 ➡️ 5
- 灰色3個 ➡️ 4
- 灰色4個 ➡️ 3
- 灰色5個 ➡️ 2
- 灰色6個 ➡️ 1
- すべて灰色 ➡️ 0

【注意】
- 新旧のある武将（信、楊端和、嬴政、羌瘣、河了貂）は、外見や天賦を見て必ず「(新)信」や「(旧)楊端和」のように新旧をつけて書いてください。
- 暗くグレーアウト（鍵付き）している未所持武将はリストに書かないでください。
解説は一切不要です。リストの行だけを出力してください。
"""
                response = model.generate_content([prompt, *processed_images])
                result_raw = response.text
                
                # AIが読み取った武将辞書
                found_stars = {}

                for line in result_raw.split("\n"):
                    if ":" in line or "：" in line:
                        parts = re.split(r"[:：]", line, maxsplit=1)
                        if len(parts) == 2:
                            raw_name = parts[0].strip()
                            raw_val = parts[1].strip()
                            
                            # 数字を抽出（0〜7）
                            num_match = re.search(r"[0-7]", raw_val)
                            if num_match:
                                star_val = num_match.group(0)
                                
                                # 完全一致でマスターリストと照合
                                for target in list_900 + list_850:
                                    # 1. 新旧表記がある場合は完全一致
                                    if target == raw_name:
                                        found_stars[target] = star_val
                                    # 2. 新旧なしのキャラは名前完全一致
                                    elif "(" not in target and target == raw_name:
                                        found_stars[target] = star_val
                                    # 3. AIが新旧をつけ忘れた場合の救済（画像に写っていた側を採用）
                                    elif target.replace("(新)", "").replace("(旧)", "") == raw_name:
                                        if target not in found_stars:
                                            found_stars[target] = star_val

                # テンプレート通りに組み立て（見つからなかったキャラはすべて「なし」）
                output = "【900】\n"
                for c in list_900:
                    star = found_stars.get(c, "なし")
                    output += f"{c} {star}\n"

                output += "\n【850】\n"
                for c in list_850:
                    star = found_stars.get(c, "なし")
                    output += f"{c} {star}\n"

                output += "\n【800】\n紫夏・オギコ　なし\n他は完凸\n"

                st.success("解析完了！")
                st.text_area("解析結果（コピー用）", value=output, height=450)

            except Exception as e:
                st.error(f"エラー詳細: {e}")
