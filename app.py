import streamlit as st
import akshare as ak
import pandas as pd
from datetime import datetime
from tqdm import tqdm

# 设置网页标题和布局
st.set_page_config(
    page_title="涨停板分析系统",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(ttl=3600)  # 缓存1小时
def get_trade_dates():
    """获取2025年交易日历"""
    trade_df = ak.tool_trade_date_hist_sina()
    return [
        datetime.strptime(d, "%Y%m%d").strftime("%Y-%m-%d")
        for d in trade_df[
            (trade_df["trade_date"] >= "20250101") & 
            (trade_df["trade_date"] <= datetime.now().strftime("%Y%m%d"))
        ]["trade_date"].astype(str)
    ]

def count_limits(date):
    """统计连板数量（按高度分类）"""
    today_df = ak.stock_zh_a_spot()
    today_limit = today_df[
        (today_df["涨跌幅"] >= 9.9) & 
        (~today_df["名称"].str.contains("ST"))
    ]["代码"].tolist()
    
    counts = {"四板+":0, "三板":0, "二板":0, "首板":0}
    
    for code in today_limit:
        try:
            hist = ak.stock_zh_a_hist(symbol=code, period="daily")
            hist["涨停"] = (hist["收盘"] / hist["前收盘"] - 1 >= 0.099)
            consecutive = sum(1 for _, row in hist.iterrows() 
                            if row["涨停"] and row["日期"] <= date)
            
            if consecutive >= 4: counts["四板+"] += 1
            elif consecutive == 3: counts["三板"] += 1
            elif consecutive == 2: counts["二板"] += 1
            else: counts["首板"] += 1
        except:
            continue
            
    return counts

# 网页界面
st.title("📈 涨停板分析系统")
date = st.sidebar.selectbox("选择日期", get_trade_dates())

if st.button("开始分析"):
    with st.spinner("正在统计数据..."):
        data = count_limits(date)
        df = pd.DataFrame.from_dict(data, orient='index', columns=["数量"])
        
        # 显示结果
        st.subheader(f"{date} 连板统计")
        st.dataframe(df.style.background_gradient(cmap="Blues"), use_container_width=True)
        
        # 可视化
        st.bar_chart(df)
        
        # 下载按钮
        csv = df.to_csv().encode('utf-8')
        st.download_button(
            "下载CSV",
            csv,
            f"涨停统计_{date}.csv",
            "text/csv"
        )