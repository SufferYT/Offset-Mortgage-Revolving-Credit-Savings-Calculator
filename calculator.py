import streamlit as st
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Offset Mortgage & Credit Strategy Tool", layout="centered")
st.title("🏠 Offset Mortgage & Revolving Credit Strategy Calculator")

st.markdown("Use this tool to see how an offset account and strategic credit card use can reduce your mortgage interest and loan term.")

# --- SECTION 1: Emergency Fund & Savings ---
st.header("1. Offset Account Preparation")

emergency_fund = st.number_input("Your Emergency Fund ($)", min_value=0, value=15000)
annual_savings = st.number_input("Estimated Annual Savings for Lump Sum Mortgage Repayment ($)", min_value=0, value=10000)

# --- SECTION 2: Optional Credit Card Strategy ---
use_credit_card = st.checkbox("Include Credit Card Strategy?", value=True,
    help="This strategy involves using a credit card to delay paying regular expenses, keeping more cash in your offset account longer.")

credit_card_buffer = 0
credit_card_fee = 0

if use_credit_card:
    st.subheader("Credit Card Use for Expense Delays")
    st.markdown("💳 *Estimate how much of your monthly expenses could be delayed using a credit card, even if you don’t currently have one.*")

    estimated_card_spend = st.number_input(
        "Monthly Expenses You Could Pay with a Credit Card ($)", min_value=0, value=3000
    )
    interest_free_days = st.slider(
        "Average Interest-Free Period (days)", min_value=0, max_value=60, value=45
    )
    credit_card_fee = st.number_input("Annual Credit Card Fee ($)", min_value=0, value=150)
    credit_card_buffer = estimated_card_spend * (interest_free_days / 30)
    st.markdown(f"📊 Estimated Monthly Offset Benefit from Card Use: **${credit_card_buffer:,.2f}**")

# --- SECTION 3: Recommended Offset Total ---
st.header("2. Recommended Offset Balance")

recommended_offset = emergency_fund + annual_savings + credit_card_buffer
st.markdown(f"✅ **Total Recommended Offset Account Balance**: **${recommended_offset:,.2f}**")

# --- SECTION 4: Input Current Mortgages ---
st.header("3. Your Mortgage Portions")
st.markdown("Add all current mortgage portions, including fixed and floating components.")

if 'mortgages' not in st.session_state:
    st.session_state.mortgages = []

with st.form("add_mortgage_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        balance = st.number_input("Loan Balance ($)", min_value=0, value=300000, key="balance")
    with col2:
        rate = st.number_input("Interest Rate (%)", min_value=0.0, value=5.5, key="rate") / 100
    with col3:
        fixed_term = st.number_input("Years Until Fixed Term Ends", min_value=0, value=3, key="term")
    loan_type = st.selectbox("Loan Type", ["Fixed", "Floating"], key="type")
    submitted = st.form_submit_button("Add Mortgage Portion")
    if submitted:
        st.session_state.mortgages.append({
            "balance": balance,
            "rate": rate,
            "fixed_term_years": fixed_term,
            "type": loan_type
        })

# Show current mortgage table
if st.session_state.mortgages:
    st.subheader("Current Mortgage Structure")
    for i, m in enumerate(st.session_state.mortgages):
        st.markdown(f"**Portion {i+1}:** ${m['balance']:,.2f} @ {m['rate']*100:.2f}% — {m['type']} (Fixed ends in {m['fixed_term_years']} yrs)")

# --- SECTION 5: Run Calculation ---
st.header("4. Calculate Strategy Impact")

if st.button("Run Calculation"):
    st.subheader("🔍 Applying Offset to Expiring Portions")

    offset_remaining = recommended_offset
    updated_mortgages = sorted(st.session_state.mortgages, key=lambda x: x['fixed_term_years'])

    results = []
    for m in updated_mortgages:
        applied = 0
        if offset_remaining > 0 and m['type'] == "Fixed":
            applied = min(offset_remaining, m['balance'])
            m['balance'] -= applied
            offset_remaining -= applied
        results.append({**m, "lump_sum_applied": applied})

    total_applied = sum(r["lump_sum_applied"] for r in results)
    st.markdown(f"💵 **Lump Sum Applied to Mortgage**: **${total_applied:,.2f}**")

    st.subheader("Updated Mortgage Balances")
    for i, r in enumerate(results):
        st.markdown(f"**Portion {i+1}:** ${r['balance']:,.2f} @ {r['rate']*100:.2f}% — {r['type']} (Fixed ends in {r['fixed_term_years']} yrs)")
        if r['lump_sum_applied'] > 0:
            st.markdown(f"➡️ ${r['lump_sum_applied']:,.2f} lump sum applied")

    net_benefit = total_applied * np.mean([r['rate'] for r in results]) - credit_card_fee
    st.subheader(f"📈 Estimated Net Interest Benefit: ${net_benefit:,.2f} (minus card fee)")

    # --- Step-by-Step Instructional Summary ---
    st.header("📝 Setup Plan Based on Your Results")
    first_expiry = updated_mortgages[0]['fixed_term_years']
    first_expiry_date = datetime.today() + timedelta(days=int(first_expiry * 365.25))
    first_balance = updated_mortgages[0]['balance'] + results[0]['lump_sum_applied']
    reduced_balance = updated_mortgages[0]['balance']
    next_term = updated_mortgages[1]['fixed_term_years'] if len(updated_mortgages) > 1 else first_expiry + 1
    next_expiry_date = datetime.today() + timedelta(days=int(next_term * 365.25))

    instruction = f'''
    When your first fixed-term mortgage expires on **{first_expiry_date.strftime('%B %d, %Y')}**, open an **offset account** and deposit **${recommended_offset:,.2f}** into it.  
    This will allow you to make a **lump sum repayment**, reducing your mortgage balance from **${first_balance:,.2f}** to **${reduced_balance:,.2f}**.  

    Your offset account should include:
    - Emergency fund: **${emergency_fund:,.2f}**
    - Annual savings: **${annual_savings:,.2f}**
    - {'Credit card buffer: **${:,.2f}**'.format(credit_card_buffer) if use_credit_card else ''}

    Continue growing your offset account by contributing **${annual_savings:,.2f}** over the next year.  
    Your next opportunity to make a repayment will be around **{next_expiry_date.strftime('%B %d, %Y')}**, when the next fixed term expires.
    '''
    st.markdown(instruction)
