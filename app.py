import streamlit as st
import pandas as pd
import os

# 웹페이지 기본 제목 설정
st.set_page_config(page_title="내노예 - 제약 영업 비서", page_icon="💊", layout="wide")

# 데이터 저장을 위한 CSV 파일 이름
CRM_FILE = "crm_data.csv"

def load_crm_data():
    if os.path.exists(CRM_FILE):
        return pd.read_csv(CRM_FILE)
    else:
        # 파일이 없으면 빈 데이터폼 생성
        return pd.DataFrame(columns=["날짜", "병의원명", "담당원장", "브리핑품목", "면담내용", "중요도"])

def save_crm_data(df):
    df.to_csv(CRM_FILE, index=False, encoding="utf-8-sig")

# 메인 화면 제목
st.title("💊 내노예: 제약 영업 통합 관리 시스템")
st.write("환영합니다, 민규 님! 오늘도 알찬 영업 활동을 응원합니다.")

# 사이드바 메뉴 만들기
st.sidebar.title("📌 메뉴")
menu = st.sidebar.radio("이동할 페이지:", ["대시보드", "매출 및 정산", "품절 및 대체품", "거래처 CRM"])

# 메뉴에 따른 화면 전환
if menu == "대시보드":
    st.subheader("📊 오늘의 요약 대시보드")
    col1, col2, col3 = st.columns(3)
    col1.metric("이번 달 총 매출", "0 원", "전월 대비 +0%")
    col2.metric("오늘 방문 거래처", "0 곳", "완료 0 / 남음 0")
    col3.metric("등록된 품절 품목", "0 개", "주의 필요")

elif menu == "매출 및 정산":
    st.subheader("💰 매출 및 정산 자동 계산")
    st.write("보유하고 계신 영업 실적 또는 정산 엑셀 파일(.xlsx)을 업로드해 주세요.")
    
    uploaded_file = st.file_uploader("엑셀 파일 업로드", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.success("엑셀 파일을 성공적으로 불러왔습니다!")
        st.write("📋 **업로드된 데이터 미리보기**")
        st.dataframe(df)
        st.write("📊 **데이터 요약 정보**")
        st.write(df.describe())
    else:
        st.info("💡 팁: 테스트용 엑셀 파일을 드래그해서 넣거나 찾아보기 버튼으로 업로드해 보세요.")

elif menu == "품절 및 대체품":
    st.subheader("🚨 실시간 품절 현황 및 대체품 추천")
    st.write("현재 품절된 품목과 동일 성분의 대체 처방 가능 약품을 조회합니다.")

elif menu == "거래처 CRM":
    st.subheader("🏥 거래처(병·의원/약국) 면담 기록")
    st.write("담당 병원장 성향, 최근 브리핑 내용, 방문 일정을 기록하고 관리하는 공간입니다.")
    
    crm_df = load_crm_data()
    
    # 입력 폼 만들기
    with st.form("crm_form", clear_on_submit=True):
        st.write("### ✍️ 새로운 면담 기록 추가")
        col1, col2 = st.columns(2)
        with col1:
            visit_date = st.date_input("방문 날짜")
            hospital = st.text_input("병·의원명", placeholder="예: 서울내과의원")
        with col2:
            doctor = st.text_input("원장님 성함 / 성향", placeholder="예: 김원장님 (꼼꼼함, 임상 근거 중시)")
            importance = st.selectbox("중요도", ["⭐", "⭐⭐", "⭐⭐⭐"])
            
        product = st.text_input("주요 브리핑 품목", placeholder="예: OOO 정 10mg")
        content = st.text_area("면담 내용 및 특이사항", placeholder="원장님 반응, 요구사항, 다음 약속일 등 입력")
        
        submitted = st.form_submit_button("기록 저장하기")
        
        if submitted:
            if hospital:
                new_row = pd.DataFrame([{
                    "날짜": str(visit_date),
                    "병의원명": hospital,
                    "담당원장": doctor,
                    "브리핑품목": product,
                    "면담내용": content,
                    "중요도": importance
                }])
                crm_df = pd.concat([crm_df, new_row], ignore_index=True)
                save_crm_data(crm_df)
                st.success(f"[{hospital}] 면담 기록이 안전하게 저장되었습니다!")
            else:
                st.warning("병·의원명은 반드시 입력해 주세요.")

    st.markdown("---")
    st.write("### 📋 전체 거래처 면담 기록장")
    if not crm_df.empty:
        st.dataframe(crm_df, use_container_width=True)
    else:
        st.info("아직 저장된 면담 기록이 없습니다. 위에서 첫 기록을 남겨보세요!")