import streamlit as st
from wordcloud import WordCloud
import jieba
import sqlite3
import qrcode
from PIL import Image
from io import BytesIO

# 页面配置，必须写在最顶部
st.set_page_config(
    page_title="扫码收集-词云生成器",
    page_icon="☁️",
    layout="wide"
)

# 数据库，用来保存所有人提交的文字，多手机共享
conn = sqlite3.connect("message_db.db", check_same_thread=False)
cur = conn.cursor()
# 创建数据表
cur.execute('''CREATE TABLE IF NOT EXISTS data_table (content TEXT)''')
conn.commit()


# 生成二维码函数
def generate_qr_code(link: str):
    qr = qrcode.QRCode(
        version=2,
        box_size=8,
        border=2
    )
    qr.add_data(link)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)
    return Image.open(buf)


# 获取当前网页访问链接（二维码里面的地址）
web_url = st.runtime.get_url()

# 左右分栏：左边二维码，右边控制台
col_qr, col_panel = st.columns([1, 2])

with col_qr:
    st.header("📱 扫码提交内容")
    if web_url:
        qr_image = generate_qr_code(web_url)
        st.image(qr_image, caption="微信/浏览器扫码填写", use_column_width=True)
    else:
        st.warning("部署上线后二维码才会正常显示！本地预览看不到")
    st.info("多人扫码提交，内容自动汇总，刷新页面数据不丢失")

with col_panel:
    st.header("☁️ 词云控制台")
    # 输入框（扫码打开也是这个输入界面）
    input_text = st.text_area("请输入内容：")
    if st.button("✅ 提交"):
        if input_text.strip():
            cur.execute("INSERT INTO data_table VALUES (?)", (input_text.strip(),))
            conn.commit()
            st.success("提交成功！")
        else:
            st.warning("内容不能为空！")

    # 读取全部收集到的内容
    cur.execute("SELECT * FROM data_table")
    all_result = cur.fetchall()
    all_words_text = "\n".join([item[0] for item in all_result])

    st.subheader("📋 已收集全部文字")
    st.text(all_words_text if all_words_text else "暂无提交记录")

    # 生成词云按钮
    if st.button("🔮 生成汇总词云"):
        if not all_words_text.strip():
            st.warning("还没有收集到内容，请先扫码提交！")
        else:
            cut_word_list = jieba.lcut(all_words_text)
            cut_string = " ".join(cut_word_list)
            wc = WordCloud(
                font_path="SourceHanSansSC-Regular.otf",  # 字体文件名，不要改错！
                background_color="white",
                width=1000,
                height=600
            ).generate(cut_string)
            cloud_img = wc.to_image()
            st.image(cloud_img, caption="全员汇总词云")

    # 清空数据按钮（答辩重置用）
    if st.button("🗑️ 清空所有记录，重新收集"):
        cur.execute("DELETE FROM data_table")
        conn.commit()
        st.rerun()