import streamlit as st
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Offset Mortgage & Credit Strategy Tool", layout="centered")
st.title("🏠 Offset Mortgage & Revolving Credit Strategy Calculator")

st.markdown("Use this tool to see how an offset account and strategic credit card use can reduce your mortgage interest and loan term.")

# --- SECTION 1: Offset Inputs ---
st.header("1. Offset Setup")

emergency_fund = st.number_input(
    "Your Emergency Fund ($)", 
    min_value=0, 
    value=15000,
    help="This is your emergency savings that stays in your offset account to reduce interest, but isn’t used to repay loans."
)

annual_savings = st.number_input(
    "Estimated Annual Savings for Lump Sum Mortgage Repayment ($)", 
    min_value=0, 
    value=10000,
    help="How much you expect to save and apply as a lump sum toward your mortgage annually."
)

bank_floating_rate = st.number_input(
    "Your Bank's Floating Mortgage Rate (%)", 
    min_value=0.0, 
    value=6.5,
    help="Used to compare interest savings and evaluate fixed vs floating rate differences."
) / 100

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

    estimated_card_spend = st.number_input(
        "Monthly Expenses You Could Put on a Credit Card ($)", 
        min_value=0, 
        value=3000,
        help="Monthly expenses you can delay using a credit card to keep cash in your offset account longer."
    )

    interest_free_days = st.slider(
        "Card’s Full Interest-Free Period (Days)",
        min_value=0,
        max_value=60,
        value=45,
        help="We’ll assume the money stays in your offset account for half of this period, on average."
    )

    # --- Credit Card Fee Toggle ---
    fee_mode = st.radio(
        "How is your credit card fee charged?",
        options=["Annual", "Monthly"],
        horizontal=True,
        help="Choose whether your card fee is charged yearly or monthly."
    )

    if fee_mode == "Annual":
        credit_card_fee_input = st.number_input(
            "Annual Credit Card Fee ($)", 
            min_value=0, 
            value=150,
            help="The yearly fee for your credit card. This is subtracted from your estimated savings."
        )
        credit_card_fee = credit_card_fee_input
    else:
        monthly_fee = st.number_input(
            "Monthly Credit Card Fee ($)", 
            min_value=0, 
            value=12,
            help="The monthly fee for your credit card. It will be multiplied by 12 to estimate yearly impact."
        )
        credit_card_fee = monthly_fee * 12

    # Calculate buffer (but don’t display)
    average_offset_days = interest_free_days / 2
    credit_card_buffer = estimated_card_spend * (average_offset_days / 30)

# --- SECTION 2: Recommended Offset Total (excluding credit card buffer) ---
st.header("2. Recommended Offset Balance (Base Only)")
recommended_offset = emergency_fund + annual_savings
st.markdown(f"✅ **Total Recommended Offset Account Balance**: **${recommended_offset:,.2f}**")
st.caption("🛈 This is your base offset amount, made up of your emergency fund and annual savings.")

# --- SECTION 3: Input/Edit Mortgages ---
st.header("3. Your Mortgage Portions")

if 'mortgages' not in st.session_state:
    st.session_state.mortgages = []

st.markdown("Add or edit your current mortgage portions:")

with st.form("mortgage_entry_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        balance = st.number_input(
            "Loan Balance ($)", 
            min_value=0, 
            value=300000,
            help="Enter the outstanding balance of this mortgage portion."
        )
        rate = st.number_input(
            "Interest Rate (%)", 
            min_value=0.0, 
            value=5.5,
            help="Interest rate for this mortgage portion."
        ) / 100
    with col2:
        expiry_date = st.date_input(
            "Fixed Term Expiry Date", 
            value=datetime.today(),
            help="When this fixed loan portion expires. Helps prioritize lump sum repayment."
        )
        loan_type = st.selectbox(
            "Loan Type", 
            ["Fixed", "Floating"],
            help="Only Fixed loans are prioritized for lump sum application."
        )
    edit_index = st.selectbox(
        "Edit existing portion?", 
        options=[None] + list(range(len(st.session_state.mortgages))), 
        format_func=lambda x: f"Portion {x+1}" if x is not None else "Add New",
        help="Choose an existing loan to edit, or leave as 'Add New' to create a new one."
    )
    submit_mortgage = st.form_submit_button("Save Mortgage Portion")

    if submit_mortgage:
        new_entry = {"balance": balance, "rate": rate, "expiry_date": expiry_date, "type": loan_type}
        if edit_index is None:
            st.session_state.mortgages.append(new_entry)
        else:
            st.session_state.mortgages[edit_index] = new_entry

if st.session_state.mortgages:
    st.subheader("📋 Mortgage List")
    for i, m in enumerate(st.session_state.mortgages):
        st.markdown(f"**Portion {i+1}:** ${m['balance']:,.2f} @ {m['rate']*100:.2f}% — {m['type']} (Expires: {m['expiry_date'].strftime('%B %d, %Y')})")

# --- SECTION 4: Run Calculation ---
st.header("4. Calculate Strategy Impact")

if st.button("Run Calculation"):
    st.subheader("🔍 Applying Offset to Expiring Portions")
    offset_remaining = recommended_offset
    updated_mortgages = sorted(st.session_state.mortgages, key=lambda x: x['expiry_date'])

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
    st.caption("🛈 Total offset funds applied to reduce fixed mortgage portions early.")

    st.subheader("Updated Mortgage Balances")
    st.caption("🛈 Mortgage balances after offset lump sum is applied.")
    for i, r in enumerate(results):
        st.markdown(f"**Portion {i+1}:** ${r['balance']:,.2f} @ {r['rate']*100:.2f}% — {r['type']} (Expires: {r['expiry_date'].strftime('%B %d, %Y')})")
        if r['lump_sum_applied'] > 0:
            st.markdown(f"➡️ ${r['lump_sum_applied']:,.2f} lump sum applied")

    fixed_rates = [r['rate'] for r in results if r['type'] == 'Fixed']
    avg_fixed_rate = np.mean(fixed_rates) if fixed_rates else bank_floating_rate
    floating_cost = (bank_floating_rate - avg_fixed_rate) * total_applied
    net_benefit = total_applied * bank_floating_rate - credit_card_fee - floating_cost

    st.subheader(f"📈 Estimated Net Interest Benefit: ${net_benefit:,.2f}")
    st.caption(
        "🛈 This is an estimate of how much interest you could save by using your offset strategy. "
        "It includes the base offset, the credit card buffer effect, and subtracts your card fee."
    )

    with st.expander("📘 See Calculation Breakdown"):
        st.markdown(f"""
        - **Offset Base Amount**: ${recommended_offset:,.2f}  
        - **Credit Card Buffer (monthly average)**: ~${credit_card_buffer:,.2f}  
        - **Card Fee (annualized)**: ${credit_card_fee:,.2f}  
        - **Floating vs Fixed Adjustment**: ${floating_cost:,.2f}
        """)

    # --- Summary Plan ---
    st.header("📝 Setup Plan Based on Your Results")
    first_expiry_date = updated_mortgages[0]['expiry_date']
    first_balance = updated_mortgages[0]['balance'] + results[0]['lump_sum_applied']
    reduced_balance = updated_mortgages[0]['balance']
    st.markdown(
        f"To maximize your strategy, consider applying a lump sum of **${total_applied:,.2f}** "
        f"to the first expiring fixed loan before **{first_expiry_date.strftime('%B %d, %Y')}**, "
        f"reducing its balance from **${first_balance:,.2f}** to **${reduced_balance:,.2f}**."
    )
    st.caption("🛈 This step-by-step plan shows you how to time and apply your lump sum effectively.")

