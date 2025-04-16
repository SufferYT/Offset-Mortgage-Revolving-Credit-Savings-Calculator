# calculator.py
import streamlit as st
import numpy as np

st.title("Offset Mortgage & Revolving Credit Savings Tool")

st.markdown("""
This calculator estimates how much interest you can save and how quickly you can pay off your mortgage by using an offset account and credit card strategy.
""")

# ------------------------------
# Section: Offset Calculation Inputs
# ------------------------------
st.header("1. Offset Account Setup")

monthly_expenses = st.number_input("Monthly Living Expenses ($)", value=4000)
months_emergency = st.slider("Emergency Fund (Months)", 1, 12, 3)
annual_savings = st.number_input("Estimated Annual Savings ($)", value=10000)

credit_card_spend = st.number_input("Monthly Expenses on Credit Card ($)", value=3000)
interest_free_days = st.slider("Credit Card Interest-Free Period (days)", 0, 60, 45)
cc_fee = st.number_input("Credit Card Annual Fee ($)", value=150)

emergency_fund = monthly_expenses * months_emergency
credit_card_buffer = credit_card_spend * (interest_free_days / 30)
recommended_offset_balance = emergency_fund + annual_savings

st.markdown(f"💰 **Recommended Offset Account Balance**: ${recommended_offset_balance:,.2f}")
st.markdown(f"⏳ **Average Monthly Offset Buffer from Credit Card Use**: ${credit_card_buffer:,.2f}")

# ------------------------------
# Section: Mortgage Inputs
# ------------------------------
st.header("2. Mortgage Portions")

num_loans = st.number_input("Number of Mortgage Portions", min_value=1, max_value=5, value=2)
mortgage_parts = []

for i in range(num_loans):
    st.subheader(f"Portion #{i+1}")
    balance = st.number_input(f"Loan Balance #{i+1} ($)", value=300000, key=f"balance_{i}")
    rate = st.number_input(f"Interest Rate #{i+1} (%)", value=5.5, key=f"rate_{i}") / 100
    term = st.slider(f"Term Remaining #{i+1} (Years)", 1, 30, 25, key=f"term_{i}")
    loan_type = st.selectbox(f"Loan Type #{i+1}", ["Fixed", "Floating"], key=f"type_{i}")
    mortgage_parts.append({"balance": balance, "rate": rate, "term": term, "type": loan_type})

# ------------------------------
# Section: Calculations
# ------------------------------

st.header("3. Results")

total_balance = sum(part['balance'] for part in mortgage_parts)
floating_balance = sum(part['balance'] for part in mortgage_parts if part['type'] == 'Floating')

# Annual interest saved on floating via offset
effective_offset = recommended_offset_balance + credit_card_buffer
floating_rate = next((p['rate'] for p in mortgage_parts if p['type'] == 'Floating'), 0)
annual_interest_saved = min(effective_offset, floating_balance) * floating_rate
net_annual_benefit = annual_interest_saved - cc_fee

st.markdown(f"🏠 **Total Mortgage Balance**: ${total_balance:,.2f}")
st.markdown(f"💸 **Annual Interest Saved via Offset**: ${annual_interest_saved:,.2f}")
st.markdown(f"💳 **Less Credit Card Fee**: ${cc_fee:,.2f}")
st.markdown(f"✅ **Net Annual Benefit**: ${net_annual_benefit:,.2f}")
