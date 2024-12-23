import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from datetime import datetime, timedelta
import json

def create_js_code(basic_style, keywords):
    # 조건부 스타일링을 위한 JS 코드
    row_JsCode = JsCode(f"""
        function(params) {{
            const baseStyle = {json.dumps(basic_style)};
            return params.data?.등록구분 === '연계기관 공고건' ? 
                {{ ...baseStyle, color: 'green' }} : null;
        }}
    """)

    cell_JsCode = JsCode(f"""
        function(params) {{
            const baseStyle = {json.dumps({**basic_style, 'display': 'flex'})};
            return params.value === '긴급' ? 
                {{ ...baseStyle, color: 'red' }} : baseStyle;
        }}
    """)

    # URL 렌더러 JsCode 정의
    url_JsCode = JsCode("""
        class UrlRenderer {
            init(params) {
                this.eGui = document.createElement('div');
                
                // 값이 비어있거나 null인 경우 '-' 표시
                if (!params.value || params.value.trim() === '') {
                    this.eGui.innerHTML = '-';
                    return;
                }
                
                // 현재 컬럼 이름에서 숫자 추출 (예: '첨부파일URL (1)' -> '1')
                const columnNumber = params.colDef.field.match(/\((\d+)\)/)?.[1] || '';
                
                // 대응되는 첨부파일명 컬럼의 값 가져오기
                const fileNameColumn = `첨부파일명 (${columnNumber})`;
                const displayText = params.data[fileNameColumn] || params.value;
                
                // URL이 있는 경우 링크로 표시
                this.eGui.innerHTML = `
                    <a href="${params.value}" target="_blank" rel="noopener noreferrer"
                        style="color: royalblue; text-decoration: underline;">
                        ${displayText}
                    </a>
                `;
            }
            getGui() { return this.eGui; }
            refresh() { return false; }
        }
    """)

    # 키워드 수에 따른 색상 스타일 정의
    style_sets = {
        'single': {  # 키워드가 1개일 때
            'backgroundColor': '#FFD700',  # 골드
            'color': '#000000'
        },
        'double': [  # 키워드가 2개일 때
            {'backgroundColor': '#FF9999', 'color': '#000000'},  # 연한 빨강
            {'backgroundColor': '#99FF99', 'color': '#000000'}   # 연한 초록
        ],
        'multiple': [  # 키워드가 3개 이상일 때
            {'backgroundColor': '#FF9999', 'color': '#000000'},  # 연한 빨강
            {'backgroundColor': '#99FF99', 'color': '#000000'},  # 연한 초록
            {'backgroundColor': '#9999FF', 'color': '#000000'}   # 연한 파랑
        ]
    }

    # 키워드 수에 따라 적절한 스타일 선택
    if len(keywords) == 1:
        keywords_style = {keywords[0]: {**style_sets['single'], 'padding': '2px 6px', 'margin': '0 2px', 'borderRadius': '3px', 'fontWeight': 'bold'}}
    elif len(keywords) == 2:
        keywords_style = {
            keywords[i]: {**style_sets['double'][i], 'padding': '2px 6px', 'margin': '0 2px', 'borderRadius': '3px', 'fontWeight': 'bold'}
            for i in range(2)
        }
    else:
        keywords_style = {
            keywords[i]: {**style_sets['multiple'][i % 3], 'padding': '2px 6px', 'margin': '0 2px', 'borderRadius': '3px', 'fontWeight': 'bold'}
            for i in range(len(keywords))
        }

    # JSON 변환
    keywords_json = json.dumps(keywords_style)

    # Renderer
    keywords_JsCode = JsCode(f"""
    class KeywordRenderer {{
        init(params) {{
            this.eGui = document.createElement('div');
            let text = params.value || '';
            
            // 기본 스타일 적용
            const baseStyle = {json.dumps(basic_style)};
            const keywordStyles = {keywords_json};
            
            // 기본 스타일을 div에 적용
            Object.entries(baseStyle).forEach(function(entry) {{
                const property = entry[0];
                const value = entry[1];
                this.eGui.style[property] = value;
            }}, this);

            // 키워드가 있는지 확인
            let hasKeyword = false;
            Object.keys(keywordStyles).forEach(function(keyword) {{
                if (text.includes(keyword)) {{
                    hasKeyword = true;
                }}
            }});
            
            if (hasKeyword) {{
                // 키워드 강조 처리
                Object.entries(keywordStyles).forEach(function(entry) {{
                    const keyword = entry[0];
                    const style = entry[1];
                    const regex = new RegExp(keyword, 'g');
                    text = text.replace(
                        regex, 
                        `<span style="background-color: ${{style.backgroundColor}}; 
                            color: ${{style.color}}; 
                            padding: ${{style.padding}}; 
                            margin: ${{style.margin}};
                            border-radius: ${{style.borderRadius}};
                            font-weight: ${{style.fontWeight}}">${{keyword}}</span>`
                    );
                }});
            }}
            
            this.eGui.innerHTML = text;
        }}

        getGui() {{
            return this.eGui;
        }}
    }}
    """)

    return row_JsCode, cell_JsCode, url_JsCode, keywords_JsCode