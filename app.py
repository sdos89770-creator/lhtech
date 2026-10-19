import os
from datetime import datetime
import pandas as pd
import streamlit as st

# 데이터 저장용 CSV 파일 경로
DATA_FILE = "overtime_orders.csv"

# 초기 기본 명단 (앱 내 관리자 모드에서 언제든 수정 가능)
DEFAULT_WORKERS = ["김철수", "이영희", "박민수", "정지영", "오민석", "김도현"]


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            if "메뉴 선택" not in df.columns or "이름" not in df.columns:
                os.remove(DATA_FILE)
                return load_data()
            df["이름"] = df["이름"].astype(str)
            df["메뉴 선택"] = df["메뉴 선택"].fillna("").astype(str)
            return df
        except Exception:
            os.remove(DATA_FILE)
            return load_data()
    else:
        initial_data = {
            "이름": DEFAULT_WORKERS,
            "메뉴 선택": [""] * len(DEFAULT_WORKERS),
        }
        df = pd.DataFrame(initial_data)
        df["이름"] = df["이름"].astype(str)
        df["메뉴 선택"] = df["메뉴 선택"].astype(str)
        df.to_csv(DATA_FILE, index=False)
        return df


st.set_page_config(page_title="잔업 식사 주문 시스템", page_icon="🍱", layout="centered")

st.title("🍱 이화테크원 잔업근무 식사 주문")
st.write(
    "본인 이름을 선택하고 메뉴를 입력하여 저장해 주세요!, :red[(메뉴 이름만!!)]"
)

# 데이터 불러오기
df = load_data()

# 사이드바: 관리자 모드 설정
st.sidebar.header("⚙️ 관리자 설정")
admin_mode = st.sidebar.checkbox("관리자 모드 켜기")

if admin_mode:
    st.sidebar.subheader("👥 오늘 근무자 명단 관리")
    st.sidebar.write("오늘 잔업 후보 명단을 수정할 수 있습니다.")

    current_names = "\n".join(df["이름"].tolist())
    edited_names_text = st.sidebar.text_area(
        "이름을 줄바꿈으로 입력하세요", current_names, height=150
    )

    if st.sidebar.button("명단 일괄 업데이트"):
        new_names = [
            n.strip() for n in edited_names_text.split("\n") if n.strip()
        ]
        if new_names:
            old_dict = dict(zip(df["이름"], df["메뉴 선택"]))
            new_data = []
            for name in new_names:
                menu = old_dict.get(name, "")
                new_data.append(
                    {
                        "이름": str(name),
                        "메뉴 선택": str(menu)
                        if pd.notna(menu)
                        else "",
                    }
                )

            df = pd.DataFrame(new_data)
            df["이름"] = df["이름"].astype(str)
            df["메뉴 선택"] = df["메뉴 선택"].astype(str)
            df.to_csv(DATA_FILE, index=False)
            st.sidebar.success("명단이 성공적으로 업데이트되었습니다!")
            st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 전체 주문 초기화 (메뉴 리셋)"):
        df["메뉴 선택"] = ""
        df.to_csv(DATA_FILE, index=False)
        st.sidebar.success("모든 메뉴 데이터가 초기화되었습니다.")
        st.rerun()


# 1. 작업자 주문 입력 섹션
st.subheader("✍️ 내 메뉴 입력하기")
worker_names = df["이름"].tolist()

if not worker_names:
    st.warning(
        "등록된 작업자가 없습니다. 왼쪽 사이드바 '관리자 모드'에서 명단을 추가해주세요."
    )
else:
    selected_name = st.selectbox("본인의 이름을 선택하세요", worker_names)

    current_row = df.loc[df["이름"] == selected_name]
    current_menu = (
        str(current_row["메뉴 선택"].values[0])
        if not current_row.empty
        else ""
    )
    if current_menu == "nan" or pd.isna(current_menu):
        current_menu = ""

    # 메뉴를 제한 없이 자유롭게 타이핑할 수 있는 텍스트 입력창
    input_menu = st.text_input(
        "메뉴를 자유롭게 입력하세요 (예: 짜장면,짬뽕,볶음밥)",
        value=current_menu,
        key=f"menu_{selected_name}",
    )

    if st.button("내 주문 저장하기"):
        df.loc[df["이름"] == selected_name, "메뉴 선택"] = str(input_menu)
        df.to_csv(DATA_FILE, index=False)
        st.success(f"[{selected_name}]님의 메뉴가 정상적으로 저장되었습니다!")
        st.rerun()

# 2. 전체 현황 및 카카오톡 공유 섹션
st.markdown("---")
st.subheader("📊 오늘 잔업 식사 현황 전체보기")

current_df = pd.read_csv(DATA_FILE)
st.dataframe(current_df, use_container_width=True)

st.markdown("---")
st.subheader("💬 카카오톡 단체방 공유용 텍스트")
st.write(
    "아래 박스의 복사 버튼을 눌러 카카오톡 단체방에 그대로 붙여넣으세요."
)

today_str = datetime.now().strftime("%Y년 %m월 %d일")

valid_orders = []
for idx, row in current_df.iterrows():
    menu = str(row["메뉴 선택"])
    if menu and menu != "nan" and menu.strip() != "":
        valid_orders.append((row["이름"], menu.strip()))

# 메뉴별 개수 카운팅 집계
menu_counts = {}
for name, menu in valid_orders:
    menu_counts[menu] = menu_counts.get(menu, 0) + 1

kakao_text = f"[ {today_str} 잔업 식사 주문 현황 ]\n\n[개인별 주문]\n"

if len(valid_orders) == 0:
    kakao_text += "아직 메뉴를 입력한 인원이 없습니다."
else:
    for name, menu in valid_orders:
        kakao_text += f"• {name}: {menu}\n"

    kakao_text += f"\n[메뉴별 총 수량]\n"
    for menu_name, count in menu_counts.items():
        kakao_text += f"• {menu_name}: {count}개\n"

    kakao_text += f"\n총 주문인원: {len(valid_orders)}명"

st.code(kakao_text, language="text")