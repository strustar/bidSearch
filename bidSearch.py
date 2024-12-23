import requests
import streamlit as st
import pandas as pd
import numpy as np
import re
import time
from datetime import datetime
from userSidebar import column_mapping, sidebar
from userFcn import create_ag_grid, format_datetime, format_price
from userDownload import create_download_buttons

st.set_page_config(page_title = "입찰정보 검색", page_icon = "🔎", layout = "wide", initial_sidebar_state="expanded")
t0 = time.time()

# 사이드바 설정 (pre-processing)
inqryBgnDt, inqryEndDt, exclude_bid_close, exclude_cancel, include_keyword, exclude_keyword, include_condition, exclude_condition, price_range = sidebar()


def search_data(url, category):
    api_key = '7zlGeseoSpY/9+ojWkAw6tHGEszXEfJ68VQr9HnJ9Rv8f53xhJDRJxLm7TxsklAAYwaJysCGcXYee6SMBZhSVg=='
    params = {
        'serviceKey': api_key,
        # 'numOfRows': '30',     # 한 페이지 결과 수
        # 'pageNo': '1',        # 페이지 번호
        # 'totalCount': '1000',
        'inqryDiv': '1',      # 조회구분 (1: 공고게시일시, 2: 개찰일시)
        'inqryBgnDt': inqryBgnDt,  # 조회 시작 일시 (1-1)
        'inqryEndDt': inqryEndDt,  # 조회 종료 일시 (1-1)
        # 'bidNtceNm': include_keyword,   # 검색 키워드
        # 'bidClseExcpYn': 'Y' if bid_close else 'N',  # 입찰마감건을 제외하고 검색하고자 하는 경우 Y
        'type': 'json',       # 응답 형식
    }

    # @st.cache_data(ttl=60*60)  # 캐시 유지 시간: 1시간
    def get_all_data():
        all_items = []    
        response = requests.get(url, params)
        data = response.json()
        total_count = int(data['response']['body']['totalCount'])
        
        # 적절한 numOfRows 설정 (로딩 시간과 관련 있음)
        num = 700
        params['numOfRows'] = str(num)
        total_pages = -(-total_count // num)  # 올림 나눗셈
        
        for page in range(1, total_pages + 1):
            params['pageNo'] = str(page)
            response = requests.get(url, params)
            data = response.json()
            items = data.get('response', {}).get('body', {}).get('items', [])
            if items:
                all_items.extend(items)
        
        return all_items

    try:        
        items = get_all_data()     # 전체 데이터 가져오기
        if items:
            df = pd.DataFrame(items)  # 데이터프레임으로 변환

            # 금액 형식 스타일 컬럼
            amount_columns = ['presmptPrce', 'asignBdgtAmt', 'bdgtAmt', 'VAT', 'bidPrtcptFee']
            for col in amount_columns:
                if col in df.columns:
                    df[col] = df[col].apply(format_price)
            
            # 날짜 형식 스타일 컬럼
            date_columns = ['bidNtceDt', 'bidClseDt', 'opengDt', 'rbidOpengDt', 'pqApplDocRcptDt', 'tpEvalApplClseDt', 'd2bMngBfEvalClseDt']
            for col in date_columns:
                if col in df.columns:
                    df[col] = df[col].apply(format_datetime)

            # 1-2. 입찰마감건 제외 : 입찰마감일시(bidClseDt)
            if exclude_bid_close:
                now = datetime.now().strftime('%Y-%m-%d %H:%M')                
                df = df[df['bidClseDt'] > now]  # 현재시간 이후의 건만 필터링
            
            # 1-3. 취소건 제외 : 분류(ntceKindNm)
            if exclude_cancel:
                df = df[~df['ntceKindNm'].str.contains('취소', na=False)]  # 공고명에 '취소'가 포함되지 않은 건만 필터링


            # 2. 검색 키워드 : 공고명 필터링            
            if include_keyword:
                # 리스트 컴프리헨션과 numpy를 활용한 최적화된 필터링
                if include_condition == "and":
                    # AND 조건: all() 사용하여 모든 키워드 포함 확인
                    mask = np.logical_and.reduce([
                        df['bidNtceNm'].str.contains(keyword, case=False, na=False)
                        for keyword in include_keyword
                    ])
                else:
                    # OR 조건: 정규식 패턴을 한 번에 적용
                    pattern = '|'.join(map(re.escape, include_keyword))
                    mask = df['bidNtceNm'].str.contains(pattern, case=False, na=False)
                
                df = df[mask]

            # 3. 가격범위 : "추정가격(부가세 제외)"이 포함된 컬럼 찾기
            # price_columns = [col for col in df.columns if 'asignBdgtAmt' in col or 'bdgtAmt' in col]
            price_columns = [col for col in df.columns if 'presmptPrce' in col]
            if price_columns:
                df = df[
                    pd.to_numeric(
                        df[price_columns[0]].str.replace(',', '').str.replace('원', '').str.strip(), 
                        errors='coerce'
                    ).between(price_range[0], price_range[1])
                ]

            # 컬럼명 변경
            df = df.rename(columns=column_mapping)

            # column_mapping에 정의된 한글 컬럼명 순서 리스트
            desired_order = list(column_mapping.values())

            # df에 존재하는 컬럼들만 필터링
            final_cols = [col for col in desired_order if col in df.columns]

            # 컬럼 순서 재정렬
            df = df[final_cols]

            # '수요기관'만 '공고기관'과 비교하여 동일하면 '좌동'으로 표시
            df['수요기관'] = df.apply(lambda row: '-' if row['공고기관'] == row['수요기관'] else row['수요기관'], axis=1)
            # '등록구분명' 컬럼의 값이 '자체'를 포함하면 '자체 공고건'으로 변경
            if '등록구분' in df.columns:
                df['등록구분'] = df['등록구분'].apply(lambda x: '자체 공고' if '자체' in str(x) else x)
            
            # 정렬 후 인덱스 재설정 (1부터 시작)
            df = df.sort_values(by='입력일시', ascending=False)
            df = df.reset_index(drop=True)  # 기존 인덱스 삭제
            df.index = df.index + 1  # 인덱스를 1부터 시작하도록 변경

            # '차수' 열을 삭제하고 '공고번호'에 추가
            df['공고번호'] = df['공고번호'] + ' (' + df['차수'] + ')'
            df = df.drop('차수', axis=1)            
            df.rename(columns={'공고번호': '공고번호 (차수)'}, inplace=True)  # 컬럼 이름 변경

            # 빈 컬럼 제거
            df = df.replace(r'^\s*$', None, regex=True)  # 공백만 있는 경우 None으로 변환
            df = df.replace('', None)                    # 빈 문자열을 None으로 변환        
            df = df.dropna(axis=1, how='all')            # 모든 값이 None/NaN인 컬럼 제거

            create_ag_grid(df, include_keyword)
            create_download_buttons(df, category)

            return items, df
        else:
            st.warning("검색된 입찰공고가 없음")

    except Exception as e:
        st.error(f"오류 발생: {str(e)}")


condition = ' (모두 포함된 공고명)' if include_condition == 'and' else ' (하나라도 포함된 공고명)'
condition = ' (포함된 공고명)' if len(include_keyword) == 1 else condition
col = st.columns([1,4])
with col[0]:
    view_type = st.radio("💼 용역 / 🏗️ 공사", ["💼 용역", "🏗️ 공사"], horizontal=True, label_visibility='collapsed')
with col[1]:
    st.write(f"###### 🔎 검색 유형 : :green[[{view_type}]]", f",&nbsp;&nbsp;&nbsp; 검색어 : :green[{include_keyword}] {condition}", f",&nbsp;&nbsp;&nbsp; 가격 범위 : :green[{price_range[0]/1e8:.2f} ~ {price_range[1]/1e8:.2f}억원]")

base_url =  'http://apis.data.go.kr/1230000/BidPublicInfoService05'
# service_url = '/getBidPblancListInfoServcPPSSrch02'
service_url = '/getBidPblancListInfoServc02'
# construction_url = '/getBidPblancListInfoCnstwkPPSSrch02'
construction_url = '/getBidPblancListInfoCnstwk02'
if '용역' in view_type:
    url = base_url + service_url
    items, df = search_data(url, 'service')

else:  # 공사
    url = base_url + construction_url
    items, df = search_data(url, 'construction')


# 사이드바 설정 (post-processing)
with st.sidebar:
    t1 = time.time()
    st.write(f"기간내 :green[총 {len(items)}건 중]에서 조건에 맞는 :blue[{len(df)}건 검색]")
    st.write(f"총 컬럼 수 (정보 갯수) : {len(df.columns)}개", f",&nbsp;&nbsp;&nbsp; 검색 시간: {t1-t0:.2f}초")

    


# #######################################################################
# option_map = {
#     0: ":material/add:",
#     1: ":material/zoom_in:",
#     2: ":material/zoom_out:",
#     3: ":material/zoom_out_map:",
#     4: ":material/content_copy:",
# }
# selection = st.pills(
#     "Tool",
#     options=option_map.keys(),
#     format_func=lambda option: option_map[option],
#     selection_mode="single",
# )
# st.write(
#     "Your selected option: "
#     f"{None if selection is None else option_map[selection]}"
# )

