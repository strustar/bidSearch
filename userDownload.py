import streamlit as st
import pandas as pd
import requests, re
from pathlib import Path
from datetime import datetime
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment

def get_column_width(text):  # """열 너비 계산 (한글 2칸, 영문 1칸)"""    
    if not text:
        return 0
    length = 0
    for c in str(text):
        length += 2 if ord(c) > 127 else 1
    return length

def save_df_to_excel(df, excel_path):   #  데이터프레임을 엑셀로 저장 (맨 좌측 번호 포함)
    # DataFrame 복사 및 index 초기화 (1부터 시작)
    df_excel = df.copy()
    df_excel.index = range(1, len(df) + 1)
    
    # URL-파일명 쌍 찾기
    url_filename_pairs = []
    for i in range(1, 11):
        url_col = f'첨부파일 URL ({i})'
        filename_col = f'첨부파일명 ({i})'
        if url_col in df.columns and filename_col in df.columns:
            url_filename_pairs.append((url_col, filename_col))
    
    # 파일명 컬럼 삭제
    filename_cols = [pair[1] for pair in url_filename_pairs]
    df_excel = df_excel.drop(columns=filename_cols)
    
    # 엑셀 파일 생성 (index 포함)
    df_excel.to_excel(excel_path, index=True, index_label='No')
    
    # 엑셀 파일 열기
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active

    # 스타일 설정
    url_style = Font(color="0563C1", underline="single")
    center_align = Alignment(horizontal='center', vertical='center')

    # 열 너비 계산용 딕셔너리
    column_widths = {}

    # No 열 너비 계산
    column_widths['A'] = get_column_width('No')

    # 헤더 처리 (No 열 포함)
    for col_idx, cell in enumerate(ws[1], 1):
        column_widths[get_column_letter(col_idx)] = max(
            get_column_width(str(cell.value)),
            column_widths.get(get_column_letter(col_idx), 0)
        )
        cell.alignment = center_align

    # 데이터 처리
    for row_idx, row in enumerate(list(ws.rows)[1:], 1):  # 헤더 제외
        for col_idx, cell in enumerate(row):
            col_name = ws.cell(row=1, column=cell.column).value  # 해당 열의 헤더
            
            # URL 컬럼 처리
            for url_col, filename_col in url_filename_pairs:
                if col_name == url_col and pd.notna(cell.value):
                    filename = df.iloc[row_idx-1][filename_col]
                    cell.value = filename
                    cell.hyperlink = df.iloc[row_idx-1][url_col]  # URL을 하이퍼링크로 설정
                    cell.font = url_style
                    break
            
            # 열 너비 업데이트
            width = get_column_width(str(cell.value))
            col_letter = get_column_letter(cell.column)
            if width > column_widths.get(col_letter, 0):
                column_widths[col_letter] = width

            # 가운데 정렬
            cell.alignment = center_align

    # 열 너비 설정
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width + 4

    # 저장
    wb.save(excel_path)

def download_files(df, option):  # 데이터프레임의 각 행별로 첨부파일 다운로드
    # URL과 파일명 쌍 찾기
    url_file_pairs = []
    for i in range(1, 11):
        url_col = f'첨부파일 URL ({i})'
        filename_col = f'첨부파일명 ({i})'
        if url_col in df.columns and filename_col in df.columns:
            url_file_pairs.append((url_col, filename_col))
    
    if not url_file_pairs:
        st.error("다운로드할 첨부파일이 없습니다.")
        return
    
    total_files = len(df) * len(url_file_pairs)
    files_processed = 0
    
    if option == '파일 다운':
        progress_bar = st.progress(0)
    else:  # 목록 보기        
        expander = st.expander(":green[🔍 첨부파일 목록 보기]")

    # 각 행별로 처리
    for idx, row in df.iterrows():
        # 공고명으로 폴더 생성 (특수문자 처리)
        folder_name = str(row['공고명'])
        for char in '<>:"/\\|?*':
            folder_name = folder_name.replace(char, '_')
        folder_name = str(idx) + '. ' + folder_name

        if option == '파일 다운':
            download_dir = Path.home() / 'Downloads' / folder_name
            download_dir.mkdir(parents=True, exist_ok=True)
        else:  # 목록 보기
            expander.write(f"📁 {folder_name}")
        
        # 각 URL-파일명 쌍 처리
        for url_col, filename_col in url_file_pairs:            
            num = int(re.findall(r'\d+', url_col)[0])
            if pd.notna(row[url_col]) and pd.notna(row[filename_col]):
                filename = f"{num}) {row[filename_col]}"  # 파일명에 번호 추가
            
                if option == '파일 다운':
                    try:
                        response = requests.get(row[url_col])
                        if response.status_code == 200:
                            file_path = download_dir / filename
                            file_path.write_bytes(response.content)
                        else:
                            st.write(f"❌ {filename} 다운로드 실패: {response.status_code}")
                    except Exception as e:
                        st.write(f"❌ {filename} 다운로드 중 오류 발생: {str(e)}")
                else:  # 목록 보기
                    expander.write(f"&nbsp; &nbsp; &nbsp; &nbsp; 📄 {filename}")
        
                if option == '파일 다운':
                    files_processed += 1
                    progress_bar.progress(files_processed / total_files)

    if option == '파일 다운':
        progress_bar.empty()
        st.success(f"모든 파일이 Downloads 폴더의 각각 '공고명' 폴더에 저장되었습니다.")

def create_download_buttons(df, category):  # tab_key 매개변수 추가
    col1, col2 = st.columns([1,2])    
    with col1:
        if st.button("📊 엑셀 다운로드", key=f"{category}_excel"):
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f"입찰정보 목록 ({now}).xlsx"
            excel_path = Path.home() / 'Downloads' / excel_filename
            
            try:
                save_df_to_excel(df, str(excel_path))
                st.success(f"'{excel_filename}'이 다운로드 되었습니다. (Downloads 폴더)")
            except Exception as e:
                st.error(f"엑셀 저장 중 오류 발생: {str(e)}")
    
    with col2:
        if st.button("📁 첨부파일 일괄 다운로드", key=f"{category}_files"):
            with st.spinner('첨부파일 다운로드 중...'):
                download_files(df, '파일 다운')

        download_files(df, '목록 보기')
