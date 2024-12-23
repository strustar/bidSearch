import streamlit as st
from datetime import datetime, timedelta
import re

# 사이드바 설정 (pre-processing)
def sidebar():
    st.markdown("""
        <style>
            /* 메인 헤더 상단 여백 조정 */
            .block-container {padding-top: 3rem; }
            
            /* Sidebar 상단 여백 조정 */
            [data-testid="stSidebarHeader"] {padding-top: 0rem; }        
            
        </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown('## :orange[1. 검색 기간]')
        day_str = st.radio(":green[검색 기간]", ["최근 3일", "최근 7일", "최근 15일", '최근 30일'], index=0, horizontal=True, label_visibility="collapsed")
        try:
            day = int(next(int(x) for x in re.findall(r'\d+', day_str))) - 1
        except StopIteration:
            day = 0  # 또는 raise ValueError("No digits found in day_str")
        # day = 2  ## 지우기


        col = st.columns([1.6, 1.3, 1])
        with col[0]:
            date = st.date_input(":green[검색 기간]", (datetime.now()-timedelta(days=day), datetime.now()), label_visibility="collapsed")
        with col[1]:        
            exclude_bid_close = st.checkbox(":green[입찰마감건 제외]", value=True)
        with col[2]:
            exclude_cancel = st.checkbox(":green[취소건 제외]", value=True)
        
        # 두 날짜가 모두 선택되었는지 확인
        if len(date) == 2:  # 두 날짜가 모두 선택된 경우에만 실행
            inqryBgnDt = date[0].strftime('%Y%m%d0000')
            inqryEndDt = date[1].strftime('%Y%m%d2359')
        else:
            st.info("시작일과 종료일을 모두 선택해주세요.")
            st.stop()  # 추가 실행을 중단

        st.markdown("---")
        st.markdown('## :orange[2. 검색 키워드]')
        col = st.columns(2)
        with col[0]:
            include_keyword = st.text_input(":green[✨ 포함 키워드] (공백으로 구분)", value='터널 도로').split()
            exclude_keyword = st.text_input(":blue[✨ 제외 키워드] (공백으로 구분)", value='교량', disabled=True).split()
        with col[1]:
            include_condition = st.radio(":green[✨ 포함 조건을 선택하세요]", ["and", "or"], index=1, horizontal=True)
            exclude_condition = st.radio(":blue[✨ 제외 조건을 선택하세요]", ["and", "or"], index=0, horizontal=True, disabled=True)

        st.markdown("---")
        st.markdown('## :orange[3. 가격 범위 (부가세 제외)]')
        price_range = st.slider(':green[✨ **추정가격 범위를 선택하세요 (백만원)**]', 0, 10000, (0, 2000), step=100, format="%d")
        st.write(f"###### :blue[*가격 범위 : {price_range[0]/1e2:.2f} ~ {price_range[1]/1e2:.2f}억원]")
        price_range = tuple(x * 1e6 for x in price_range)    

        st.markdown("---")
        st.markdown('## :orange[4. 기관명 등등 다른 옵션? 추가]')

        st.markdown("---")

        return inqryBgnDt, inqryEndDt, exclude_bid_close, exclude_cancel, include_keyword, exclude_keyword, include_condition, exclude_condition, price_range


# 컬럼명 한글 매핑
column_mapping = {
    ### 1. 핵심 공고 정보 ===================    
    # "srvceDivNm": "업무",  # "srvceDivNm": "업무(공고종류)",  # '공사'에서는 없음 ㅠ
    "bidNtceNo": "공고번호",
    "bidNtceOrd": "차수",
    # "reNtceYn": "재공고여부",
    "ntceKindNm": "분류",
    "bidNtceNm": "공고명",    
    
    "ntceInsttNm": "공고기관",
    "dminsttNm": "수요기관",
    "cntrctCnclsMthdNm": "계약방법",
    "bidNtceDt": "입력일시",
    "bidClseDt": "입찰마감일시",
    # "asignBdgtAmt": "사업금액(배정예산)",   # 용역 금액
    # "bdgtAmt": "사업금액(배정예산) ",       # 공사 금액
    "presmptPrce": "추정가격(부가세 제외)",  # 부가세 불포함
    
    "rgstTyNm": "등록유형",
    # "untyNtceNo": "통합공고번호",
    # "refNo": "참조번호",

    ### 2. 입찰 방식 ===================
    "bidMethdNm": "입찰방식",
    "sucsfbidMthdNm": "낙찰자결정방법",
    "dsgntCmptYn": "지명경쟁여부",
    "rbidPermsnYn": "재입찰허용여부",

    ### 3. 예정가격 결정 및 입찰금액 정보 ======================
    "prearngPrceDcsnMthdNm": "예가방법",
    "totPrdprcNum": "총예가 수",
    "drwtPrdprcNum": "추첨예가 수",
    "sucsfbidLwltRate": "낙찰하한율",
    # "presmptPrce": "추정가격(부가세 불포함)",
    # "VAT": "부가세",
    # "brffcBidprcPermsnYn": "예비가격허용여부",   
    # "rsrvtnPrceReMkngMthdNm": "예비가격재작성방법",

    ### 4. 참가 자격 및 제한 ===================
    "bidPrtcptLmtYn": "입찰참가제한여부",
    "rgnLmtBidLocplcJdgmBssNm": "참가가능지역",
    "indstrytyLmtYn": "업종제한여부",
    "prdctClsfcLmtYn": "물품분류제한여부",
    "bidPrtcptFeePaymntYn": "입찰참가수수료지급여부",
    "bidPrtcptFee": "입찰참가수수료",
    "bidGrntymnyPaymntYn": "입찰보증금납부여부",
    
    ### 5. 공동계약 관련 ===================
    "cmmnSpldmdMethdNm": "공동수급",
    "cmmnSpldmdCorpRgnLmtYn": "공동수요기관지역제한여부",
    "rgnDutyJntcontrctRt": "지역의무공동계약비율",
    "jntcontrctDutyRgnNm1": "공동계약의무지역명1",
    "jntcontrctDutyRgnNm2": "공동계약의무지역명2",
    "jntcontrctDutyRgnNm3": "공동계약의무지역명3",
    
    ### 6. 기술평가/PQ심사 ===================
    "tpEvalYn": "기술평가여부",
    "tpEvalApplMthdNm": "기술평가신청방법",
    "tpEvalApplClseDt": "기술평가신청마감일시",
    
    "pqEvalYn": "PQ심사여부",
    "pqApplDocRcptMthdNm": "PQ신청서접수방법",
    "pqApplDocRcptDt": "PQ신청서접수일시",
    
    ### 7. 품목 및 분류 ===================
    "mnfctYn": "제조여부",
    "purchsObjPrdctList": "구매대상물품목록",
    "pubPrcrmntClsfcNm": "공공조달분류",
    # "pubPrcrmntClsfcNo": "공공조달분류번호",
    "pubPrcrmntLrgClsfcNm": "공공조달대분류",
    "pubPrcrmntMidClsfcNm": "공공조달중분류",
    
    ### 8. 담당자 정보 ===================
    "ntceInsttOfclNm": "담당자",
    "ntceInsttOfclTelNo": "담당자 연락처",
    "ntceInsttOfclEmailAdrs": "담당자 이메일주소",
    
    ### 9. URL 및 첨부파일 ===================
    "bidNtceUrl": "입찰공고 URL",
    "bidNtceDtlUrl": "입찰공고상세 URL",
    "stdNtceDocUrl": "표준공고문 URL",


    # "cmmnSpldmdMethdNm": "공동수급",
    
    # # 나중에 기술평가여부(TP) == Y 이면 추가
    # "tpEvalYn": "기술평가여부",
    # "tpEvalApplMthdNm": "기술평가신청방법",
    # "tpEvalApplClseDt": "기술평가신청마감일시",

    # # 나중에 PQ심사여부(PQ) == Y 이면 추가
    # "pqEvalYn": "PQ심사여부",
    # "pqApplDocRcptMthdNm": "PQ신청서접수방법",
    # "pqApplDocRcptDt": "PQ신청서접수일시",
    
    # ### [중복 사항] ==============================
    # # "linkInsttNm": "연계기관명",
    # # "rgstDt": "등록일시",  # 입력일시와 같음
    # ### [중복 사항] ==============================
    # "cmmnSpldmdCorpRgnLmtYn": "공동수요기관지역제한여부",
    # # "sucsfbidMthdCd": "낙찰자결정방법코드",
    # "stdNtceDocUrl": "표준공고문URL",
    # "rgnLmtBidLocplcJdgmBssNm": "참가가능지역",    
    # "rgnDutyJntcontrctRt": "지역의무공동계약비율",
    # "rbidOpengDt": "재입찰개찰일시",
    # "purchsObjPrdctList": "구매대상물품목록",
    # "pubPrcrmntMidClsfcNm": "공공조달중분류명",
    # "pubPrcrmntLrgClsfcNm": "공공조달대분류명",
    # "pubPrcrmntClsfcNo": "공공조달분류번호",
    # "pubPrcrmntClsfcNm": "공공조달분류명",
    
    # "prdctClsfcLmtYn": "물품분류제한여부",
    # "ppswGnrlSrvceYn": "조달청일반서비스여부",
    # "orderPlanUntyNo": "발주계획통합번호",
    # "opengPlce": "개찰장소",
    # "opengDt": "개찰일시",

    # "ntceInsttOfclTelNo": "공고기관담당자연락처",
    # "ntceInsttOfclNm": "공고기관담당자명",
    # "ntceInsttOfclEmailAdrs": "공고기관담당자이메일주소",
    
    # "ntceInsttCd": "공고기관코드",
    # "ntceDscrptYn": "공고내용여부",
    # "mnfctYn": "제조여부",
    
    # "jntcontrctDutyRgnNm3": "공동계약의무지역명3",
    # "jntcontrctDutyRgnNm2": "공동계약의무지역명2",
    # "jntcontrctDutyRgnNm1": "공동계약의무지역명1",
    # "intrbidYn": "내자입찰여부",
    # "infoBizYn": "정보사업여부",
    # "indutyVAT": "업종별부가세",
    # "indstrytyLmtYn": "업종제한여부",
    # "exctvNm": "대표자명",
    # "dtlsBidYn": "상세입찰여부",
    # "dminsttOfclEmailAdrs": "수요기관담당자이메일주소",
    
    # "dminsttCd": "수요기관코드",
    # "dcmtgOprtnPlce": "설명회운영장소",
    # "dcmtgOprtnDt": "설명회운영일시",

    # "crdtrNm": "채권자명",
    # "cmmnSpldmdMethdCd": "공동수요방식코드",
    
    # "cmmnSpldmdAgrmntRcptdocMethd": "공동수요협정서접수방법",
    # "cmmnSpldmdAgrmntClseDt": "공동수요협정서마감일시",
    # "chgNtceRsn": "변경공고사유",
    # "chgDt": "변경일시",
    
    # "bidQlfctRgstDt": "입찰자격등록일시",
    # "bidPrtcptLmtYn": "입찰참가제한여부",
    # "bidPrtcptFeePaymntYn": "입찰참가수수료지급여부",
    # "bidPrtcptFee": "입찰참가수수료",
    # "bidNtceUrl": "입찰공고URL",

    # "bidNtceDtlUrl": "입찰공고상세URL",
    # "bidGrntymnyPaymntYn": "입찰보증금납부여부",
    # "bidBeginDt": "입찰시작일시",
    # "bfSpecRgstNo": "사양등록번호",    
    # "arsltReqstdocRcptDt": "결과요청문서접수일시",
    # "arsltCmptYn": "결과완료여부",
    # "arsltApplDocRcptMthdNm": "결과신청서접수방법명",
}

# URL 관련 컬럼은 반복문으로 처리
for i in range(1, 11):
    column_mapping[f'ntceSpecDocUrl{i}'] = f'첨부파일 URL ({i})'
    column_mapping[f'ntceSpecFileNm{i}'] = f'첨부파일명 ({i})'


# # D2B: Defense to Business 방위사업청 관리 항목들은 필요한 경우에만 별도로 추가
# d2b_related_mapping = {
#     "d2bMngUprcSstmTyNm": "조달청관리최고가체계유형명",
#     "d2bMngStdIndstryClsfcCdList": "조달청관리표준업종분류코드목록",
#     "d2bMngRsrvtnPrceBssOpenYn": "조달청관리예비가격기준공개여부",
#     "d2bMngRsrvtnPrceBssAplYn": "조달청관리예비가격기준적용여부",
#     "d2bMngRgstEvalExmpYn": "조달청관리등록심사면제여부",
#     "d2bMngRgnLmtYn": "조달청관리지역제한여부",
#     "d2bMngProgrsSttusNm": "조달청관리진행상태명",
#     "d2bMngPrdlstNm": "조달청관리제품목록명",
#     "d2bMngPrdlstCd": "조달청관리제품목록코드",
#     "d2bMngPrdctnAbltySbmsnClseDt": "조달청관리생산능력제출마감일시",
#     "d2bMngPblctPlceNm": "조달청관리발표장소명",
#     "d2bMngOrgnlbdgtDedtEndDate": "조달청관리원예산차감종료일자",
#     "d2bMngOrgnlbdgtDedtBgnDate": "조달청관리원예산차감시작일자",
#     "d2bMngNgttnStleNm": "조달청관리협상방식명",
#     "d2bMngNgttnPlanDate": "조달청관리협상계획일자",
#     "d2bMngItemNo": "조달청관리품목번호",
#     "d2bMngExetTyNm": "조달청관리집행유형명",
#     "d2bMngExetTyCd": "조달청관리집행유형코드",
#     "d2bMngDmndYear": "조달청관리수요연도",
#     "d2bMngDcsnNo": "조달청관리결정번호",
#     "d2bMngCompCorpRsrchObjYn": "조달청관리경쟁사조사대상여부",
#     "d2bMngCntrybndDedtEndDate": "조달청관리국가예산차감종료일자",
#     "d2bMngCntrybndDedtBgnDate": "조달청관리국가예산차감시작일자",
#     "d2bMngCntrctKindNm": "조달청관리계약유형명",
#     "d2bMngCnstwkScleCntnts": "조달청관리공사규모내용",
#     "d2bMngCnstwkPrdCntnts": "조달청관리공사기간내용",
#     "d2bMngCnstwkOutlnCntnts": "조달청관리공사개요내용",
#     "d2bMngCnstwkDivNm": "조달청관리공사번호",
#     "d2bMngCnstwkLctNm": "조달청관리공사위치명",
#     "d2bMngBssamt": "조달청관리기본금액",
#     "d2bMngBfEvalObjYn": "조달청관리사전평가대상여부",
#     "d2bMngBfEvalClseDt": "조달청관리사전평가마감일시",
#     "d2bMngAssmntUplmtRt": "조달청관리평가상한율",
#     "d2bMngAssmntLwstlmtRt": "조달청관리평가하한율",
# }
# column_mapping.update(d2b_related_mapping)