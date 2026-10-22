import streamlit as st
import pandas as pd
import requests
import urllib.parse
import xml.etree.ElementTree as ET
import feedparser
from datetime import datetime
import os

# ================= 기본 설정 및 보안 잠금 =================
st.set_page_config(page_title="내노예 - MR 전용 비서", page_icon="💊", layout="wide")

# 🔑 1. 나만의 비밀번호 잠금
SECRET_PIN = "1982" 
# 🔑 2. 공공데이터포털 일반 인증키 (Decoding 키를 따옴표 사이에 넣으세요)
API_KEY = "5734d7f81d4133be02adedfa7577767d7dfb90ffd00c79494354d3a6f3938bff"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center;'>🔒 내노예 (Private MR System)</h2>", unsafe_allow_html=True)
    pin = st.text_input("접속 비밀번호(PIN)를 입력하세요", type="password")
    if st.button("로그인", use_container_width=True):
        if pin == SECRET_PIN:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 일치하지 않습니다.")
    st.stop()

# ================= 로컬 데이터 저장 파일 설정 =================
ITEMS_FILE = "my_items.csv"
NOTES_FILE = "my_notes.csv"

def load_data(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False, encoding="utf-8-sig")

# ================= 메인 화면 및 탭 구성 =================
st.title("💊 내노예 (MR All-in-One System)")
st.caption("심평원·식약처 실시간 연동 & 프라이빗 매출·품절 관리 시스템")

tabs = st.tabs([
    "🚨 내 품목 & 품절관리", 
    "📊 매출·수수료 정산", 
    "🔍 약품검색 & 경쟁품비교", 
    "🏥 신규개원 & 문전약국", 
    "☕ 면담 전 스몰토크 & 노트"
])

# ---------------------------------------------------------
# 탭 1: 내 품목 & 품절(수급불안정) 관리
# ---------------------------------------------------------
with tabs[0]:
    st.subheader("🚨 내 주력 품목 및 품절/대체약 관리")
    df_items = load_data(ITEMS_FILE, ["품목명", "제약사", "성분명", "약가", "수수료율(%)", "수급상태", "대체품목", "주요거래처"])
    
    with st.expander("➕ 새 취급 품목 등록하기"):
        c1, c2, c3, c4 = st.columns(4)
        p_name = c1.text_input("품목명")
        p_comp = c2.text_input("제약사")
        p_ingr = c3.text_input("성분명(함량)")
        p_price = c4.number_input("약가(원)", min_value=0, step=10)
        
        c5, c6, c7, c8 = st.columns(4)
        p_rate = c5.number_input("수수료율(%)", min_value=0.0, max_value=100.0, step=0.5)
        p_status = c6.selectbox("수급상태", ["🟢 정상", "🟠 품절임박", "🔴 장기품절"])
        p_alt = c7.text_input("동일성분 대체품목")
        p_cli = c8.text_input("주요 처방 거래처")
        
        if st.button("품목 저장", use_container_width=True):
            new_row = pd.DataFrame([[p_name, p_comp, p_ingr, p_price, p_rate, p_status, p_alt, p_cli]], columns=df_items.columns)
            df_items = pd.concat([df_items, new_row], ignore_index=True)
            save_data(df_items, ITEMS_FILE)
            st.success(f"'{p_name}' 등록 완료!")
            st.rerun()

    sold_out = df_items[df_items["수급상태"].str.contains("품절", na=False)]
    if not sold_out.empty:
        st.error(f"⚠️ 현재 수급 불안정(품절/임박) 품목이 {len(sold_out)}건 있습니다! 거래처 코드 변경을 확인하세요.")
        st.dataframe(sold_out[["품목명", "제약사", "수급상태", "대체품목", "주요거래처"]], use_container_width=True, hide_index=True)

    st.markdown("#### 📋 전체 품목 리스트 (상태 직접 클릭하여 수정 가능)")
    edited_df = st.data_editor(
        df_items,
        column_config={
            "수급상태": st.column_config.SelectboxColumn("수급상태", options=["🟢 정상", "🟠 품절임박", "🔴 장기품절"], required=True)
        },
        num_rows="dynamic",
        use_container_width=True
    )
    if st.button("💾 변경사항 저장하기"):
        save_data(edited_df, ITEMS_FILE)
        st.success("품목 상태가 저장되었습니다!")

# ---------------------------------------------------------
# 탭 2: 내 매출 & 수수료(정산) 계산기
# ---------------------------------------------------------
with tabs[1]:
    st.subheader("📊 월별 처방 매출 및 수수료 자동 정산")
    c_up, c_sim = st.columns([1.2, 1])
    
    with c_up:
        st.markdown("##### 📁 정산 엑셀(CSV/XLSX) 업로드 분석")
        uploaded_file = st.file_uploader("정산 엑셀 파일을 끌어다 놓으세요", type=["xlsx", "csv"])
        if uploaded_file:
            df_sales = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
            st.dataframe(df_sales, use_container_width=True)
            num_cols = df_sales.select_dtypes(include=['number']).columns.tolist()
            if num_cols:
                target_col = st.selectbox("합계를 계산할 열(처방액/수수료 등) 선택", num_cols)
                st.metric(label=f"총 {target_col} 합계", value=f"{df_sales[target_col].sum():,.0f} 원")

    with c_sim:
        st.markdown("##### 🧮 면담 전 처방 수익 시뮬레이터")
        sim_price = st.number_input("약가 (1정당 원)", value=500, step=50)
        sim_rate = st.slider("내 수수료율 (%)", 0.0, 60.0, 35.0, 0.5)
        sim_daily = st.number_input("일일 예상 처방량 (정/일)", value=100, step=10)
        sim_days = st.number_input("월 처방 일수", value=25, step=1)
        
        monthly_sales = sim_price * sim_daily * sim_days
        monthly_profit = monthly_sales * (sim_rate / 100)
        st.info(f"💰 **월 예상 처방액:** {monthly_sales:,.0f} 원\n\n💎 **내 월 예상 수수료(세전):** **{monthly_profit:,.0f} 원**")

# ---------------------------------------------------------
# 탭 3: 식약처·심평원 약품 검색 & 경쟁품 비교
# ---------------------------------------------------------
with tabs[2]:
    st.subheader("🔍 의약품 검색 및 경쟁품 비교 (공공데이터 연동)")
    drug_q = st.text_input("제품명 또는 성분명을 입력하세요 (예: 리피토, 아토르바스타틴)")
    if st.button("약품 조회") and drug_q:
        url = "http://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList"
        params = {"serviceKey": API_KEY, "itemName": drug_q, "type": "json", "numOfRows": 10}
        try:
            res = requests.get(url, params=params, timeout=5).json()
            items = res.get("body", {}).get("items", [])
            if items:
                for it in items:
                    with st.expander(f"💊 {it.get('itemName')} ({it.get('entpName')})"):
                        st.write(f"**[효능·효과]** {it.get('efcyQesitm', '정보없음')}")
                        st.write(f"**[용법·용량]** {it.get('useMethodQesitm', '정보없음')}")
                        st.write(f"**[주의사항]** {it.get('atpnQesitm', '정보없음')}")
            else:
                st.warning("검색 결과가 없거나 API 키 동기화 전입니다.")
        except Exception as e:
            st.error("공공데이터포털 인증키(Decoding)를 코드 상단 API_KEY에 입력해 주세요.")

# ---------------------------------------------------------
# 탭 4: 지역 병원(신규 개원) & 문전약국 조회
# ---------------------------------------------------------
with tabs[3]:
    st.subheader("🏥 지역 병·의원 및 문전약국 조회 (심평원 연동)")
    col_h1, col_h2 = st.columns(2)
    region_q = col_h1.text_input("시·군·구 또는 동 이름 (예: 서산시, 예천동)")
    hosp_q = col_h2.text_input("병원/약국명 키워드 (선택)")
    search_type = st.radio("조회 대상", ["병·의원 조회", "약국 조회"], horizontal=True)
    
    if st.button("검색 실행"):
        endpoint = "getHospBasisList" if search_type == "병·의원 조회" else "getParmacyBasisList"
        service = "hospInfoServicev2" if search_type == "병·의원 조회" else "B551182/pharmacyInfoService"
        url = "http://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList" if search_type == "병·의원 조회" else "http://apis.data.go.kr/B551182/pharmacyInfoService/getParmacyBasisList"
        params = {"serviceKey": API_KEY, "emdongNm": region_q, "yadmNm": hosp_q, "numOfRows": 20}
        try:
            res = requests.get(url, params=params, timeout=5)
            root = ET.fromstring(res.text)
            rows = []
            for item in root.iter("item"):
                rows.append({
                    "기관명": item.findtext("yadmNm"),
                    "종별": item.findtext("clCdNm"),
                    "주소": item.findtext("addr"),
                    "전화번호": item.findtext("telno"),
                    "개설일자": item.findtext("estbDd")
                })
            if rows:
                df_res = pd.DataFrame(rows).sort_values(by="개설일자", ascending=False)
                st.dataframe(df_res, use_container_width=True, hide_index=True)
            else:
                st.warning("조회된 데이터가 없습니다. API 키나 지역명을 확인해 주세요.")
        except Exception:
            st.error("API 키를 확인해 주세요.")

# ---------------------------------------------------------
# 탭 5: 면담 1분 전 스몰토크 뉴스 & 거래처 노트
# ---------------------------------------------------------
with tabs[4]:
    col_n1, col_n2 = st.columns([1, 1])
    with col_n1:
        st.subheader("☕ 면담 1분 전 실시간 스몰토크")
        topic = st.selectbox("원장님 관심 분야 선택", ["⛳ 골프/LPGA/PGA", "🏥 의료계/의정갈등/개원가", "💰 주식/경제/부동산", "⚾ 스포츠/축구/야구"])
        kw_map = {"⛳ 골프/LPGA/PGA": "골프+투어", "🏥 의료계/의정갈등/개원가": "의협+의료계+개원가", "💰 주식/경제/부동산": "코스피+금리+부동산", "⚾ 스포츠/축구/야구": "손흥민+프로야구"}
        rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(kw_map[topic])}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:8]:
            st.markdown(f"- [{entry.title}]({entry.link})")
            
    with col_n2:
        st.subheader("📒 프라이빗 원장님 면담 노트")
        df_notes = load_data(NOTES_FILE, ["날짜", "거래처(원장님)", "면담내용 및 성향 메모"])
        n_cli = st.text_input("거래처명 / 원장님 성함")
        n_memo = st.text_area("면담 기록 / 스몰토크 소재 / 요청사항")
        if st.button("노트 저장", use_container_width=True):
            new_n = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M"), n_cli, n_memo]], columns=df_notes.columns)
            df_notes = pd.concat([new_n, df_notes], ignore_index=True)
            save_data(df_notes, NOTES_FILE)
            st.rerun()
        st.dataframe(df_notes, use_container_width=True, hide_index=True)
