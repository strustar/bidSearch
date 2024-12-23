import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from datetime import datetime, timedelta
from userJsCode import create_js_code

def format_datetime(datetime_str):
    if datetime_str:
        try:            
            datetime_str = datetime_str[:16]  # 초 단위가 포함된 경우 잘라냄 (12+4자리까지만 유지, 공백, -, : 포함)
            dt = datetime.strptime(datetime_str, '%Y%m%d%H%M')  # 입력 문자열을 datetime 객체로 변환            
            return dt.strftime('%Y-%m-%d %H:%M')  # "년-월-일 시:분" 형식으로 변환
        except ValueError:  # 변환 실패 시 원본 문자열 반환
            return datetime_str
    return ''  # 빈 문자열 처리

def format_price(price_str):
    try:
        return f"{int(price_str):,}원" if price_str else ''
    except:
        return price_str

def create_ag_grid(df, keywords):
    def get_column_width(df, column_name):  # """컬럼 내용 및 헤더 길이에 따라 적절한 너비 계산"""        
        max_data_length = df[column_name].astype(str).map(len).max() if not df.empty else 0 # 데이터프레임이 비어있는 경우 예외처리 추가
        header_length = len(column_name)
        max_length = max(max_data_length, header_length)   # 데이터와 헤더 중 더 긴 길이를 기준으로 너비 계산
        
        if max_length < 4:
            return 70
        elif max_length < 6:
            return 100
        elif max_length < 10:
            return 150
        elif max_length < 20:
            return 180
        else:
            return max_length / 2 * 16  # 2줄, 한자당 픽셀 14
        
    # 기본 스타일 설정
    basic_style = {
        'display': '-webkit-box',           # 웹킷 기반 박스 모델 사용
        '-webkit-line-clamp': '2',         # 텍스트 줄 수 제한
        '-webkit-box-orient': 'vertical',   # 박스 방향 세로 설정
        'overflow': 'hidden',              # 넘치는 텍스트 숨김
        'textOverflow': 'ellipsis',        # 텍스트 말줄임 (...)
        'lineHeight': '20px',              # 줄 간격 설정
        'minHeight': '40px',               # 최소 높이 설정
        'padding': '6px',                  # 여백
        'whiteSpace': 'normal',            # 텍스트 줄바꿈 허용
        'textAlign': 'center',             # 텍스트 가운데 정렬    
        'alignItems': 'center',            # 세로 중앙 정렬
        'justifyContent': 'center',        # 가로 중앙 정렬
        'wordBreak': 'break-word',         # 긴 단어 줄바꿈 처리
        'fontWeight': 'bold'               # 글자 굵기
        #'display': 'flex',                      # 플렉스 박스 사용
    }
    row_JsCode, cell_JsCode, url_JsCode, keywords_JsCode = create_js_code(basic_style, keywords)
    # df = df.reset_index()   # 인덱스 컬럼 추가    
    gb = GridOptionsBuilder.from_dataframe(df)  # GridOptionsBuilder 객체 생성

    gb.configure_default_column(editable=True, sortable=True, filter=True, resizable=True, maxWidth=400, cellStyle={**basic_style, 'display': 'flex',})

    # 그리드 옵션 설정 (페이지)
    gb.configure_grid_options(pagination=True, paginationPageSize=50, rowHeight=60, suppressRowTransform=True, rowSelection='multiple', getRowStyle=row_JsCode)
    
    # 넘버링 컬럼 추가 (맨 왼쪽 컬럼)
    gb.configure_column(field="", valueGetter="node.rowIndex + 1", maxWidth=40, pinned='left', cellStyle={**basic_style, 'fontSize': '14px', 'display': 'flex',})
    
    gb.configure_column(field="분류", cellStyle=cell_JsCode)  # 분류 == 긴급 일때, 빨간색
    gb.configure_column(field="공고명", cellRenderer=keywords_JsCode)

    # # 사이드바 설정
    # gb.configure_side_bar(        
    #     filters_panel=True,      # 필터 패널 표시
    #     columns_panel=True,      # 컬럼 패널 표시
    #     defaultToolPanel="columns",  # 기본으로 표시할 패널 ("columns", "filters", None)
    # )

    # 각 컬럼에 대해 너비 설정
    for column_name in df.columns:        
        max_width = get_column_width(df, column_name)        
        # st.write(column_name, max_width)
        gb.configure_column(
            column_name,
            maxWidth=max_width,
            # suppressSizeToFit=True if max_width < 200 else False,
            # autoSize=True if max_width >= 200 else False
            suppressSizeToFit=True,  # 항상 True로 설정
            autoSize=False  # 항상 False로 설정
        )

        if 'url' in column_name.lower():  # 컬럼명을 소문자로 변환하여 'url' 포함 여부 확인
            gb.configure_column(
                column_name,
                cellStyle=basic_style,
                cellRenderer=url_JsCode,
                width=400,
                # maxWidth=1500,
                # autoSize=True
            )
        
        if '첨부파일명' in column_name:  # 컬럼 숨기기
            gb.configure_column(
                column_name,
                hide=True
            )
    

    return AgGrid(df, gridOptions=gb.build(), theme='streamlit',  # streamlit 테마 적용
        fit_columns_on_grid_load=False, update_mode='value_changed', allow_unsafe_jscode=True,
        height=700,
        custom_css={
            ".ag-header-cell-label": {
                "justify-content": "center",                
                "color": "orange",
                "font-weight": "bold",
                "font-size": "14px"
            },
            ".ag-row-hover": {
                "background-color": "rgba(255,165,0,0.1) !important",  # rgba(255, 0, 0, 0.1)
                "transition": "all 0.3s ease-in-out"
            },
            ".ag-cell:hover": {
                "background-color": "rgba(240,230,140, 0.3)!important",
                # "color": "white !important",
                "transform": "scale(1.0)"
            },
            ".ag-header-cell": {
                # "border": "1px solid gray"
            },
            ".ag-cell": {
                # "text-align": "center",                
            }
        }
    )

