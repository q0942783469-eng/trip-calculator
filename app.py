import streamlit as st
import pandas as pd

# ================= 核心計算邏輯 =================
def calculate_trip_expenses(expenses, people_list):
    balances = {p: 0 for p in people_list}
    total_paid = {p: 0 for p in people_list}
    total_consumed = {p: 0 for p in people_list}
    itemized_details = {p: [] for p in people_list} 

    for item in expenses:
        desc = item["description"]
        payer = item["payer"]
        amount = int(round(item["amount"]))
        participants = item["participants"]

        if not participants:
            continue

        total_paid[payer] += amount
        balances[payer] += amount

        n = len(participants)
        base_split = amount // n
        remainder = amount % n

        for i, person in enumerate(participants):
            actual_split = base_split + 1 if i < remainder else base_split
            total_consumed[person] += actual_split
            balances[person] -= actual_split
            itemized_details[person].append((desc, actual_split))

    debtors, creditors = [], []
    for person, bal in balances.items():
        if bal < 0:
            debtors.append([person, -bal])
        elif bal > 0:
            creditors.append([person, bal])

    debtors.sort(key=lambda x: x[1], reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)

    transactions = []
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        debtor_name, debt_amt = debtors[i]
        creditor_name, credit_amt = creditors[j]
        settle_amt = min(debt_amt, credit_amt)

        transactions.append({
            "from": debtor_name,
            "to": creditor_name,
            "amount": settle_amt
        })

        debtors[i][1] -= settle_amt
        creditors[j][1] -= settle_amt

        if debtors[i][1] == 0: i += 1
        if creditors[j][1] == 0: j += 1

    return balances, transactions, total_paid, total_consumed, itemized_details

# ================= 網頁介面設計 =================
st.set_page_config(page_title="旅遊分帳計算器", page_icon="💸", layout="centered")
st.title("💸 旅遊自動分帳計算器")
st.write("手機、電腦皆可完美操作的網頁版")

# 狀態管理 (紀錄網頁重新整理時的資料)
if 'people' not in st.session_state:
    st.session_state.people = []
if 'expenses' not in st.session_state:
    st.session_state.expenses = []

# --- 步驟 1：建立出遊名單 (支援單獨移除成員) ---
st.header("步驟 1：建立出遊名單")

with st.form("person_form", clear_on_submit=True):
    new_person = st.text_input("新增成員名稱", placeholder="輸入成員名字...")
    submitted_person = st.form_submit_button("➕ 加入名單")
    
    if submitted_person:
        name = new_person.strip()
        if not name:
            st.warning("請輸入成員名稱！")
        elif name in st.session_state.people:
            st.warning(f"「{name}」已經在名單中了！")
        else:
            st.session_state.people.append(name)
            st.success(f"已加入成員：{name}")

if st.session_state.people:
    st.markdown("**目前名單與管理：**")
    # 讓每個成員以小區塊或標籤形式呈現，並附帶刪除按鈕
    for person in list(st.session_state.people):
        col_p1, col_p2 = st.columns([3, 1])
        col_p1.write(f"👤 {person}")
        if col_p2.button("❌ 移除", key=f"del_person_{person}"):
            # 檢查該成員是否已經被使用在消費紀錄中（代墊人或分擔人）
            in_use = False
            for exp in st.session_state.expenses:
                if exp["payer"] == person or person in exp["participants"]:
                    in_use = True
                    break
            
            if in_use:
                st.error(f"無法移除「{person}」，因已有相關的消費紀錄！請先刪除該消費紀錄。")
            else:
                st.session_state.people.remove(person)
                st.rerun()

st.divider()

# --- 步驟 2：新增消費項目 ---
st.header("步驟 2：新增消費項目")
if not st.session_state.people:
    st.warning("請先在上方建立出遊名單！")
else:
    with st.form("expense_form", clear_on_submit=True):
        desc = st.text_input("項目名稱 (例如：晚餐熱炒)")
        amount = st.number_input("金額 (整數)", min_value=1, step=10)
        payer = st.selectbox("代墊人", options=st.session_state.people)
        
        participants = st.multiselect("分擔人 (點選取消不要分擔的人)", 
                                      options=st.session_state.people, 
                                      default=st.session_state.people)
        
        submitted = st.form_submit_button("➕ 新增這筆費用")
        if submitted:
            if not desc:
                st.error("請填寫項目名稱！")
            elif not participants:
                st.error("請至少選擇一位分擔人！")
            else:
                st.session_state.expenses.append({
                    "description": desc,
                    "amount": int(amount),
                    "payer": payer,
                    "participants": participants
                })
                st.success(f"已新增：{desc} (${int(amount)})")

st.divider()

# --- 步驟 3：確認與刪除費用清單 ---
st.header("步驟 3：已記錄的消費")
if st.session_state.expenses:
    col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([2, 1, 1.5, 3, 1.5])
    col_h1.markdown("**項目名稱**")
    col_h2.markdown("**金額**")
    col_h3.markdown("**代墊人**")
    col_h4.markdown("**分擔人**")
    col_h5.markdown("**操作**")
    st.markdown("---")

    for i, exp in enumerate(st.session_state.expenses):
        c1, c2, c3, c4, c5 = st.columns([2, 1, 1.5, 3, 1.5])
        c1.write(exp["description"])
        c2.write(f"${exp['amount']}")
        c3.write(exp["payer"])
        c4.write(", ".join(exp["participants"]))
        
        if c5.button("❌ 刪除", key=f"del_btn_{i}"):
            st.session_state.expenses.pop(i)
            st.rerun()
            
    st.markdown("---")
    st.write("")
    if st.button("🗑️ 清空所有消費紀錄", type="secondary"):
        st.session_state.expenses = []
        st.rerun()
else:
    st.write("目前尚無消費紀錄。")

st.divider()

# --- 步驟 4：動態報表與結算 ---
st.header("步驟 4：最終結算報告")
if st.button("🧮 產生結算報表", type="primary", use_container_width=True):
    if not st.session_state.expenses:
        st.warning("沒有任何消費記錄可以結算！")
    else:
        balances, transactions, total_paid, total_consumed, itemized_details = calculate_trip_expenses(
            st.session_state.expenses, st.session_state.people
        )

        st.subheader("📊 結算明細總表 (可向右滑動查看各項目)")
        
        report_data = []
        for person in st.session_state.people:
            bal = balances[person]
            if bal > 0:
                bal_str = f"📥 收回 ${bal}"
            elif bal < 0:
                bal_str = f"📤 支付 ${abs(bal)}"
            else:
                bal_str = "✔️ 結清 $0"
                
            row = {
                "成員": person,
                "總代墊": f"${total_paid[person]}",
                "總分擔": f"${total_consumed[person]}",
                "👉 最終收付": bal_str
            }
            
            person_items = {desc: amt for desc, amt in itemized_details[person]}
            for i, exp in enumerate(st.session_state.expenses):
                desc_key = f"{i+1}. {exp['description']}"
                if exp["description"] in person_items:
                    row[desc_key] = f"${person_items[exp['description']]}"
                else:
                    row[desc_key] = "-"
                    
            report_data.append(row)

        df_report = pd.DataFrame(report_data)
        st.dataframe(df_report, use_container_width=True)

        st.subheader("💡 最佳化轉帳路徑")
        if not transactions:
            st.info("所有人皆已收支平衡，無需進行任何轉帳！")
        else:
            for idx, t in enumerate(transactions, 1):
                st.success(f"**第 {idx} 步：** 【**{t['from']}**】 應轉帳給 【**{t['to']}**】 **${t['amount']}** 元")
