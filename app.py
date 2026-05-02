import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# ---------------------------------------------------------
# 1. 기본 설정 및 UI 테마
# ---------------------------------------------------------
st.set_page_config(page_title="Easy Holdings Finance Hub", page_icon="🏢", layout="wide")

# 사이드바 구성
st.sidebar.title("🏢 Easy Holdings")
st.sidebar.markdown("**Group Finance & FP&A Hub**")
st.sidebar.caption("이지홀딩스 통합 재무/경영관리 시스템 v2.0")

# 통합 메뉴 선택
menu = st.sidebar.radio(
    "🔄 프로세스 선택",
    [
        "1. 그룹 연결결산 요약", 
        "2. 계열사 내부거래 자동 대사", 
        "3. K-IFRS 연결수정분개 자동생성",
        "4. 환율/곡물가 리스크 시뮬레이터" 
    ]
)

# ---------------------------------------------------------
# 2. 데이터 로드 함수 (캐싱 적용)
# ---------------------------------------------------------
# [데이터 1] 내부거래 결산용 데이터 (Project 1)
@st.cache_data
def load_intercompany_data():
    seller_data = pd.DataFrame({
        '거래ID': ['TRX-2605-01', 'TRX-2605-02', 'TRX-2605-03', 'TRX-2605-04', 'TRX-2605-05'],
        '매출법인(Seller)': ['이지바이오', '팜스토리', '정다운', '옵티팜', '이지바이오'],
        '매입법인(Buyer)': ['마니커', '마니커', '팜스토리', '이지바이오', '해외법인(USA)'],
        '거래유형': ['배합사료 납품', '생계(종계) 납품', '오리육 납품', '동물백신 납품', '사료첨가제 수출'],
        '매출액(장부)': [500000000, 320000000, 150000000, 85000000, 120000000],
        '매출채권 잔액': [50000000, 0, 150000000, 8500000, 120000000]
    })
    
    buyer_data = pd.DataFrame({
        '거래ID': ['TRX-2605-01', 'TRX-2605-02', 'TRX-2605-03', 'TRX-2605-04', 'TRX-2605-05'],
        '매입액(장부)': [500000000, 315000000, 150000000, 0, 118500000], 
        '매입채무 잔액': [50000000, 0, 150000000, 0, 118500000]
    })
    
    # 두 데이터 병합 및 차액 계산
    df = pd.merge(seller_data, buyer_data, on='거래ID', how='outer').fillna(0)
    df['매출_매입_차액'] = df['매출액(장부)'] - df['매입액(장부)']
    df['채권_채무_차액'] = df['매출채권 잔액'] - df['매입채무 잔액']
    
    # 상태 분류
    conditions = [
        (df['매출_매입_차액'] == 0) & (df['채권_채무_차액'] == 0),
        df['매입액(장부)'] == 0,
        df['매출_매입_차액'] != 0
    ]
    choices = ['🟢 일치 (상계가능)', '🔴 매입전표 누락', '🟡 금액 불일치(확인요망)']
    df['상태결과'] = np.select(conditions, choices, default='기타 오류')
    
    return df

# [데이터 2] 계열사 원가구조 시뮬레이션용 데이터 (Project 2)
@st.cache_data
def load_subsidiary_data():
    data = {
        '계열사': ['이지바이오(사료첨가제)', '팜스토리(배합사료/육가공)', '정다운(오리육)', '마니커(닭고기)'],
        '연간매출액': [1500, 12000, 3000, 2800],
        '기존_매출원가': [1000, 10800, 2600, 2500],
        '매출원가중_원재료비_비중': [0.60, 0.85, 0.65, 0.70], 
        '원재료중_수입산_비중': [0.70, 0.95, 0.40, 0.50]      
    }
    return pd.DataFrame(data)

df_inter = load_intercompany_data()

# ---------------------------------------------------------
# 3. 화면 1: 그룹 연결결산 요약 (Overview)
# ---------------------------------------------------------
if menu == "1. 그룹 연결결산 요약":
    st.title("📊 이지홀딩스 그룹 연결결산 통합 상황판")
    st.markdown("지주회사 및 60여 개 종속회사의 **내부거래 정합성**을 실시간으로 모니터링합니다.")
    
    col1, col2, col3, col4 = st.columns(4)
    total_sales = df_inter['매출액(장부)'].sum()
    total_diff = df_inter['매출_매입_차액'].abs().sum()
    error_cnt = len(df_inter[df_inter['상태결과'] != '🟢 일치 (상계가능)'])
    
    col1.metric("내부거래 총 매출액", f"₩{total_sales/100000000:,.1f}억", "그룹 내 밸류체인")
    col2.metric("내부거래 불일치 차액", f"₩{total_diff:,.0f}", f"-{error_cnt}건 발생", delta_color="inverse")
    col3.metric("결산 대사 진행률", "85.4%", "+12% (전일 대비)")
    col4.metric("수작업 소요 시간", "10 min", "-24 hours (자동화 적용)", delta_color="normal")
    
    st.divider()
    
    st.subheader("📈 주요 계열사별 내부매출 규모")
    sales_by_comp = df_inter.groupby('매출법인(Seller)')['매출액(장부)'].sum().reset_index()
    
    bar_chart = alt.Chart(sales_by_comp).mark_bar(color="#1f77b4", size=50).encode(
        x=alt.X('매출법인(Seller):N', axis=alt.Axis(labelAngle=0, title='매출법인')),
        y=alt.Y('매출액(장부):Q', axis=alt.Axis(title='매출액(원)')),
        # 💡 수정된 부분: alt.Tooltip을 사용하여 format 지정
        tooltip=[
            alt.Tooltip('매출법인(Seller):N', title='매출법인(Seller)'),
            alt.Tooltip('매출액(장부):Q', title='매출액(장부)', format=',') 
        ]
    ).properties(height=350)
    
    st.altair_chart(bar_chart, use_container_width=True)

# ---------------------------------------------------------
# 4. 화면 2: 계열사 내부거래 자동 대사 (Reconciliation)
# ---------------------------------------------------------
elif menu == "2. 계열사 내부거래 자동 대사":
    st.title("🔍 계열사 간 내부거래 대사표 (Reconciliation)")
    st.info("💡 **[문제해결]** 엑셀 VLOOKUP으로 수일이 걸리던 계열사 상호 거래 내역을 고유 ID 기반으로 1초 만에 병합합니다.")
    
    status_filter = st.selectbox("대사 상태 필터링", ['전체 내역 보기', '🔴 매입전표 누락', '🟡 금액 불일치(확인요망)', '🟢 일치 (상계가능)'])
    filtered_df = df_inter if status_filter == '전체 내역 보기' else df_inter[df_inter['상태결과'] == status_filter]
    
    st.dataframe(
        filtered_df[['상태결과', '거래ID', '매출법인(Seller)', '매입법인(Buyer)', '거래유형', '매출액(장부)', '매입액(장부)', '매출_매입_차액']],
        column_config={
            "매출액(장부)": st.column_config.NumberColumn(format="₩ %,d"),
            "매입액(장부)": st.column_config.NumberColumn(format="₩ %,d"),
            "매출_매입_차액": st.column_config.NumberColumn(format="₩ %,d")
        },
        use_container_width=True, height=300, hide_index=True
    )
    
    st.subheader("🚨 불일치 거래 세부 분석 및 조치 사항")
    err_df = filtered_df[filtered_df['상태결과'] != '🟢 일치 (상계가능)']
    
    for idx, row in err_df.iterrows():
        with st.expander(f"[{row['상태결과']}] {row['매출법인(Seller)']} ➔ {row['매입법인(Buyer)']} ({row['거래유형']})"):
            st.markdown(f"- **매출법인 기록:** {row['매출액(장부)']:,.0f} 원\n- **매입법인 기록:** {row['매입액(장부)']:,.0f} 원\n- **차액:** **{row['매출_매입_차액']:,.0f} 원**")
            if '누락' in row['상태결과']:
                st.warning(f"**조치 제안:** {row['매입법인(Buyer)']} 재무팀에 매입 전표(AP) 입력 요청")
            elif '수출' in row['거래유형']:
                st.error(f"**조치 제안:** 환율 적용일자 차이로 인한 외환차손익 발생 의심. 환율 재적용 필요.")
            else:
                st.info(f"**조치 제안:** 운임비 또는 부대비용 포함 여부 양사 확인 필요.")

# ---------------------------------------------------------
# 5. 화면 3: K-IFRS 연결수정분개 자동 생성 (Elimination)
# ---------------------------------------------------------
elif menu == "3. K-IFRS 연결수정분개 자동생성":
    st.title("📝 K-IFRS 연결수정분개 자동 생성기")
    st.success("💡 **[핵심 역량]** 대사가 완료된 거래에 대해, 지주사 연결재무제표 작성을 위한 상계 분개를 자동으로 산출합니다.")
    
    valid_df = df_inter[df_inter['상태결과'] == '🟢 일치 (상계가능)']
    
    for idx, row in valid_df.iterrows():
        st.write(f"**[{row['거래ID']}] {row['매출법인(Seller)']} ➔ {row['매입법인(Buyer)']} ({row['거래유형']})**")
        col1, col2 = st.columns(2)
        with col1:
            st.code(f"(차) 내부매출액   {row['매출액(장부)']:,.0f}", language="text")
        with col2:
            st.code(f"(대) 내부매출원가 {row['매입액(장부)']:,.0f}", language="text")
            
        if row['매출채권 잔액'] > 0:
            col3, col4 = st.columns(2)
            with col3:
                st.code(f"(차) 내부매입채무 {row['매입채무 잔액']:,.0f}", language="text")
            with col4:
                st.code(f"(대) 내부매출채권 {row['매출채권 잔액']:,.0f}", language="text")
        st.divider()

# ---------------------------------------------------------
# 6. 화면 4: 환율/곡물가 리스크 시뮬레이터 (오류 수정 완료)
# ---------------------------------------------------------
elif menu == "4. 환율/곡물가 리스크 시뮬레이터":
    # 사이드바 슬라이더 추가
    st.sidebar.subheader("🎛️ 매크로 지표 시뮬레이션 설정")
    current_fx = 1350
    sim_fx = st.sidebar.slider("USD/KRW 환율 (원)", min_value=1100, max_value=1500, value=1350, step=10)
    fx_change_rate = (sim_fx - current_fx) / current_fx

    st.sidebar.markdown("---")
    grain_change_rate = st.sidebar.slider("국제 곡물가(대두/옥수수) 변동률 (%)", min_value=-30, max_value=50, value=0, step=5) / 100

    st.title("🌾 이지홀딩스 매크로 리스크 시뮬레이터 (FP&A)")
    st.markdown("수입 곡물(옥수수, 대두박 등) 의존도가 높은 핵심 계열사의 **매크로 지표 변동에 따른 영업이익 타격**을 실시간으로 산출합니다.")
    st.divider()

    # 데이터 연산
    df_sim = load_subsidiary_data()
    df_sim['기존_영업이익'] = df_sim['연간매출액'] - df_sim['기존_매출원가']
    df_sim['기존_원재료비'] = df_sim['기존_매출원가'] * df_sim['매출원가중_원재료비_비중']
    df_sim['기타_고정원가'] = df_sim['기존_매출원가'] - df_sim['기존_원재료비']

    df_sim['시뮬레이션_원재료비'] = df_sim['기존_원재료비'] * (1 + grain_change_rate) * (1 + (fx_change_rate * df_sim['원재료중_수입산_비중']))
    df_sim['시뮬레이션_매출원가'] = df_sim['시뮬레이션_원재료비'] + df_sim['기타_고정원가']
    df_sim['시뮬레이션_영업이익'] = df_sim['연간매출액'] - df_sim['시뮬레이션_매출원가']
    df_sim['영업이익_증감액'] = df_sim['시뮬레이션_영업이익'] - df_sim['기존_영업이익']

    # KPI 지표 표시
    col1, col2, col3, col4 = st.columns(4)
    total_op_before = df_sim['기존_영업이익'].sum()
    total_op_after = df_sim['시뮬레이션_영업이익'].sum()
    total_op_diff = total_op_after - total_op_before

    col1.metric("시뮬레이션 적용 환율", f"₩ {sim_fx:,.0f}", f"{(sim_fx-current_fx):+,.0f} 원")
    col2.metric("국제 곡물가 변동", f"{grain_change_rate*100:+.0f} %", "대두/옥수수 기준")
    col3.metric("그룹 합산 영업이익 (기존)", f"₩ {total_op_before:,.0f} 억", "")
    col4.metric("그룹 합산 영업이익 (예측)", f"₩ {total_op_after:,.0f} 억", f"{total_op_diff:,.0f} 억", delta_color="normal" if total_op_diff >= 0 else "inverse")

    st.divider()

    # ---------------------------------------------------------
    # [수정된 부분] Altair 차트: xOffset을 사용하여 기업명 가려짐 완벽 해결
    # ---------------------------------------------------------
    st.subheader("📉 주요 계열사별 영업이익 시뮬레이션 결과")
    melt_df = pd.melt(df_sim, id_vars=['계열사'], value_vars=['기존_영업이익', '시뮬레이션_영업이익'], 
                      var_name='구분', value_name='영업이익(억원)')
    melt_df['구분'] = melt_df['구분'].replace({'기존_영업이익': '1. 기존 영업이익', '시뮬레이션_영업이익': '2. 시뮬레이션 예측치'})

    chart = alt.Chart(melt_df).mark_bar().encode(
        x=alt.X('계열사:N', title='', axis=alt.Axis(labelAngle=0, labelPadding=10)), # X축에 계열사명 직접 배치
        y=alt.Y('영업이익(억원):Q', title='영업이익 (단위: 억원)'),
        xOffset='구분:N', # 막대그래프를 옆으로 나란히 분리하는 핵심 로직
        color=alt.Color('구분:N', scale=alt.Scale(range=['#B0BEC5', '#FF7043']), legend=alt.Legend(orient='top'))
    ).properties(height=400)

    st.altair_chart(chart, use_container_width=True)
    st.divider()

    # 세부 표
    st.subheader("📋 세부 원가/이익 분석표 및 재무 리스크 헤지(Hedge) 제안")
    display_df = df_sim[['계열사', '연간매출액', '기존_매출원가', '시뮬레이션_매출원가', '기존_영업이익', '시뮬레이션_영업이익', '영업이익_증감액']].copy().set_index('계열사')
    
    # 데이터프레임 출력 (스타일링 적용)
    if hasattr(display_df.style, 'map'):
        st.dataframe(display_df.style.format("{:,.0f} 억").map(lambda x: "color: red;" if x < 0 else "color: blue;", subset=['영업이익_증감액']), use_container_width=True)
    else:
        st.dataframe(display_df.style.format("{:,.0f} 억").applymap(lambda x: "color: red;" if x < 0 else "color: blue;", subset=['영업이익_증감액']), use_container_width=True)

    # AI 조치 제안
    st.markdown("### 💡 AI 기반 재무 조치 제안")
    if fx_change_rate > 0.05 or grain_change_rate > 0.05:
        st.error(f"⚠️ **원가 상승 경고:** 환율 및 곡물가 동반 상승으로 인해 특히 **'팜스토리(수입산 비중 95%)'**의 영업이익 타격이 가장 큽니다. 그룹 총 영업이익이 **{abs(total_op_diff):,.0f}억원 감소**할 것으로 예측됩니다.")
        st.markdown("**[재무팀 조치 제안]**\n1. **통화선도(Forward) 계약 체결 검토:** 향후 3~6개월 치 수입 대금 환헤지 비율 상향 조정\n2. **판매가(판가) 인상 시뮬레이션:** 배합사료 판매 단가 인상 협의\n3. **곡물 재고 확보:** 저가 매입분 비중 확대")
    elif fx_change_rate < -0.05:
        st.success(f"📈 **원가 절감 호재:** 환율 하락으로 수입 원재료 비중이 높은 계열사의 영업이익률이 개선되고 있습니다.")
        st.markdown("**[재무팀 조치 제안]**\n1. **외환차익 실현:** 결제일 미도래 외화매입채무 조기 결제 검토\n2. **환율 변동성 모니터링:** 일시적 하락일 수 있으므로 목표 환율 도달 시 헷지 물량 락인(Lock-in) 고려.")
    else:
        st.info("🔄 현재 환율 및 곡물가 변동 수준은 그룹의 예산 통제 범위 내에 있습니다.")
