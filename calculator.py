import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Offset Mortgage & Credit Strategy Tool", layout="centered")
st.title("🏠 Offset Mortgage & Revolving Credit Strategy Calculator")

st.markdown("Use this tool to see how an offset account and strategic credit card use can reduce your mortgage interest and loan term.")

# --- SECTION 1: Offset Inputs ---
st.header("1. Offset Setup")

emergency_fund = st.number_input("Your Emergency Fund ($)", min_value=0, value=15000)
annual_savings = st.number_input("Estimated Annual Savings for Lump Sum Mortgage Repayment ($)", min_value=0, value=10000)
bank_floating_rate = st.number_input("Your Bank's Floating Mortgage Rate (%)", min_value=0.0, value=6.5) / 100

# --- Optional Credit Card Strategy ---
use_credit_card = st.checkbox(
    "Include Credit Card Strategy?", 
    value=True,
    help="Use a credit card to delay paying expenses, keeping cash in your offset account longer to reduce mortgage interest."
)

credit_card_buffer = 0
credit_card_fee = 0

if use_credit_card:
    st.subheader("Credit Card Use for Expense Delays")

    estimated_card_spend = st.number_input("Monthly Expenses You Could Put on a Credit Card ($)", min_value=0, value=3000)
    interest_free_days = st.slider("Card’s Full Interest-Free Period (Days)", min_value=0, max_value=60, value=45)
    fee_mode = st.radio("How is your credit card fee charged?", options=["Annual", "Monthly"], horizontal=True)

    if fee_mode == "Annual":
        credit_card_fee = st.number_input("Annual Credit Card Fee ($)", min_value=0, value=150)
    else:
        monthly_fee = st.number_input("Monthly Credit Card Fee ($)", min_value=0, value=12)
        credit_card_fee = monthly_fee * 12

    average_offset_days = interest_free_days / 2
    credit_card_buffer = estimated_card_spend * (average_offset_days / 30)

# --- SECTION 2: Recommended Offset Total ---
st.header("2. Recommended Offset Balance")
recommended_offset = emergency_fund + annual_savings
st.markdown(f"✅ **Total Recommended Offset Account Balance**: **${recommended_offset:,.2f}**")
st.caption("🛈 This is the total of your emergency fund plus the amount you expect to save for lump sum repayment.")

# --- SECTION 3: Input/Edit Mortgages ---
st.header("3. Your Mortgage Portions")

if 'mortgages' not in st.session_state:
    st.session_state.mortgages = []

edit_index = st.selectbox(
    "Edit existing portion?", 
    options=[None] + list(range(len(st.session_state.mortgages))),
    format_func=lambda x: f"Portion {x+1}" if x is not None else "Add New"
)

if edit_index is not None:
    selected = st.session_state.mortgages[edit_index]
    default_balance = selected["balance"]
    default_rate = selected["rate"] * 100
    default_expiry = selected["expiry_date"]
    default_type = selected["type"]
else:
    default_balance = 300000
    default_rate = 5.5
    default_expiry = datetime.today()
    default_type = "Fixed"

with st.form("mortgage_entry_form"):
    col1, col2 = st.columns(2)
    with col1:
        balance = st.number_input("Loan Balance ($)", min_value=0, value=default_balance)
        rate = st.number_input("Interest Rate (%)", min_value=0.0, value=default_rate) / 100
    with col2:
        expiry_date = st.date_input("Fixed Term Expiry Date", value=default_expiry)
        loan_type = st.selectbox("Loan Type", ["Fixed", "Floating"], index=0 if default_type == "Fixed" else 1)

    submit_mortgage = st.form_submit_button("Save Mortgage Portion")

    if submit_mortgage:
        new_entry = {"balance": balance, "rate": rate, "expiry_date": expiry_date, "type": loan_type}
        if edit_index is None:
            st.session_state.mortgages.append(new_entry)
        else:
            st.session_state.mortgages[edit_index] = new_entry
        st.success("✅ Mortgage portion saved successfully.")

# --- Display List with Delete Buttons ---
if st.session_state.mortgages:
    st.subheader("📋 Mortgage List")
    for i, m in enumerate(st.session_state.mortgages):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"**Portion {i+1}:** ${m['balance']:,.2f} @ {m['rate']*100:.2f}% — {m['type']} (Expires: {m['expiry_date'].strftime('%B %d, %Y')})")
        with col2:
            if st.button("🗑️ Delete", key=f"delete_{i}"):
                st.session_state.deleted_index = i

# --- Safely Delete Mortgage (outside loop) ---
if "deleted_index" in st.session_state:
    idx = st.session_state.pop("deleted_index")
    st.session_state.mortgages.pop(idx)
    st.success(f"Deleted Portion {idx + 1}")
    st.experimental_rerun()

# --- SECTION 4: Run Calculation ---
st.header("4. Calculate Strategy Impact")

if st.button("Run Calculation"):
    today = datetime.today().date()
    offset_remaining = recommended_offset
    updated_mortgages = sorted(st.session_state.mortgages, key=lambda x: x['expiry_date'])

    results = []
    for m in updated_mortgages:
        applied = 0
        if (
            offset_remaining > 0 
            and m['type'] == "Fixed" 
            and m['expiry_date'] > today
        ):
            applied = min(offset_remaining, m['balance'])
            m['balance'] -= applied
            offset_remaining -= applied
        results.append({**m, "lump_sum_applied": applied})

    total_applied = sum(r["lump_sum_applied"] for r in results)

    # --- Final Results Table ---
    original_loan_amount = 300000
    original_interest_rate = 0.055
    loan_term_years = 25

    monthly_rate = original_interest_rate / 12
    num_payments = loan_term_years * 12
    monthly_payment = original_loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    total_paid = monthly_payment * num_payments
    original_total_interest = total_paid - original_loan_amount

    new_loan_amount = original_loan_amount - total_applied
    if new_loan_amount <= 0:
        new_total_interest = 0
        years_saved = loan_term_years
    else:
        new_num_months = -np.log(1 - new_loan_amount * monthly_rate / monthly_payment) / np.log(1 + monthly_rate)
        new_total_paid = monthly_payment * new_num_months
        new_total_interest = new_total_paid - new_loan_amount
        years_saved = loan_term_years - new_num_months / 12

    interest_saved = original_total_interest - new_total_interest

    results_df_final = pd.DataFrame({
        "Metric": [
            "Total Interest Over Loan Term",
            "Net Interest Saved",
            "Estimated Years Saved on Mortgage"
        ],
        "Before Strategy": [
            f"${original_total_interest:,.2f}",
            "-",
            "-"
        ],
        "After Strategy": [
            f"${new_total_interest:,.2f}",
            f"${interest_saved:,.2f}",
            f"{years_saved:.1f} years"
        ]
    })

    st.subheader("📊 Full Strategy Comparison")
    st.dataframe(results_df_final, use_container_width=True)
