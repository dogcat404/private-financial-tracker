import os
from datetime import date, datetime
import pandas as pd
import streamlit as st
import plotly.express as px
from supabase import create_client, Client

st.set_page_config(page_title="Arthur's Private Financial Tracker", page_icon="🌿", layout="wide")

GREEN = "#176B45"
LIGHT_GREEN = "#E8F5EC"
DARK = "#173B2D"

st.markdown(f"""
<style>
.stApp {{ background: #F7FBF8; color: {DARK}; }}
[data-testid="stSidebar"] {{ background: #EAF5EE; }}
h1, h2, h3 {{ color: {GREEN}; }}
div.stButton > button {{ background: {GREEN}; color: white; border: 0; border-radius: 10px; }}
div.stButton > button:hover {{ background: #0F5132; color: white; }}
div[data-testid="stMetric"] {{ background: white; border: 1px solid #D7E9DC; padding: 16px; border-radius: 14px; }}
div[data-testid="stForm"] {{ background: white; padding: 16px; border: 1px solid #D7E9DC; border-radius: 14px; }}
</style>
""", unsafe_allow_html=True)

st.title("🌿 Arthur's Private Financial Tracker")
st.caption("Personal finance dashboard · Green & white · Private account-based tracking")

# Set these in Streamlit Community Cloud → App → Settings → Secrets.
def get_supabase():
    try:
        url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
        key = st.secrets.get("SUPABASE_ANON_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
        if not url or not key:
            return None
        return create_client(url, key)
    except Exception:
        return None

supabase = get_supabase()
if not supabase:
    st.error("Database belum terhubung. Ikuti README.md untuk menyiapkan Supabase dan menambahkan Secrets.")
    st.stop()

if "user" not in st.session_state:
    st.session_state.user = None

def sign_out():
    st.session_state.user = None
    st.rerun()

if st.session_state.user is None:
    st.markdown("### Welcome back")
    login_tab, signup_tab = st.tabs(["Sign in", "Create account"])
    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)
        if submitted:
            try:
                result = supabase.auth.sign_in_with_password({"email": email.strip(), "password": password})
                st.session_state.user = result.user
                st.session_state.access_token = result.session.access_token
                st.success("Signed in successfully.")
                st.rerun()
            except Exception as e:
                st.error("Login gagal. Periksa email/password atau konfirmasi email jika diwajibkan.")
    with signup_tab:
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password (minimal 6 karakter)", type="password", key="signup_password")
            submitted_signup = st.form_submit_button("Create account", use_container_width=True)
        if submitted_signup:
            if len(new_password) < 6:
                st.warning("Gunakan password minimal 6 karakter.")
            else:
                try:
                    supabase.auth.sign_up({"email": new_email.strip(), "password": new_password})
                    st.success("Akun dibuat. Jika email confirmation aktif, cek email lalu sign in.")
                except Exception:
                    st.error("Pembuatan akun gagal. Periksa email atau pengaturan Supabase Auth.")
    st.info("Data transaksi disimpan di database Supabase milikmu. Jangan pernah membagikan password atau API secret.")
    st.stop()

# Apply the user's JWT so Supabase Row Level Security scopes data to the signed-in user.
try:
    supabase.postgrest.auth(st.session_state.access_token)
except Exception:
    pass

with st.sidebar:
    st.markdown("## 🌱 Navigation")
    page = st.radio("Open page", ["Overview", "Transactions", "Insights", "Export data"])
    st.divider()
    st.caption(f"Signed in: {st.session_state.user.email}")
    if st.button("Sign out", use_container_width=True):
        sign_out()

user_id = st.session_state.user.id

def load_transactions():
    response = supabase.table("transactions").select("*").order("transaction_date", desc=True).execute()
    df = pd.DataFrame(response.data)
    if df.empty:
        return pd.DataFrame(columns=["id", "user_id", "transaction_date", "kind", "category", "description", "amount"])
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    return df

def money(value):
    return "Rp " + f"{float(value):,.0f}".replace(",", ".")

try:
    df = load_transactions()
except Exception:
    st.error("Tidak bisa mengambil transaksi. Pastikan tabel dan Row Level Security sudah dibuat sesuai README.md.")
    st.stop()

if page == "Overview":
    st.subheader("Your financial overview")
    today = pd.Timestamp(date.today())
    month_df = df[(df["transaction_date"].dt.year == today.year) & (df["transaction_date"].dt.month == today.month)] if not df.empty else df
    income = month_df.loc[month_df["kind"] == "Income", "amount"].sum()
    expenses = month_df.loc[month_df["kind"] == "Expense", "amount"].sum()
    balance = income - expenses
    savings_rate = (balance / income * 100) if income > 0 else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Income this month", money(income))
    c2.metric("Expenses this month", money(expenses))
    c3.metric("Net cash flow", money(balance), delta="Positive" if balance >= 0 else "Negative")
    c4.metric("Savings rate", f"{savings_rate:.1f}%")
    st.markdown("### Add a transaction")
    with st.form("quick_add", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            kind = st.selectbox("Type", ["Expense", "Income"])
            amount = st.number_input("Amount (IDR)", min_value=0, step=10000, value=50000)
        with col2:
            category = st.selectbox("Category", ["Food", "Transport", "Bills", "Shopping", "Health", "Education", "Salary", "Business", "Savings", "Entertainment", "Other"])
            transaction_date = st.date_input("Date", value=date.today())
        with col3:
            description = st.text_input("Description", placeholder="e.g. Lunch or monthly salary")
        save = st.form_submit_button("＋ Save transaction", use_container_width=True)
    if save:
        if amount <= 0:
            st.warning("Amount must be greater than zero.")
        else:
            try:
                supabase.table("transactions").insert({
                    "user_id": user_id, "transaction_date": transaction_date.isoformat(),
                    "kind": kind, "category": category, "description": description.strip(), "amount": float(amount)
                }).execute()
                st.success("Transaction saved.")
                st.rerun()
            except Exception:
                st.error("Could not save transaction. Check the database setup.")
    st.markdown("### Recent transactions")
    if df.empty:
        st.info("Belum ada transaksi. Tambahkan transaksi pertamamu di atas.")
    else:
        view = df.head(8).copy()
        view["transaction_date"] = view["transaction_date"].dt.strftime("%d %b %Y")
        view["amount"] = view["amount"].map(money)
        st.dataframe(view[["transaction_date", "kind", "category", "description", "amount"]], use_container_width=True, hide_index=True)

elif page == "Transactions":
    st.subheader("Transactions")
    if df.empty:
        st.info("Belum ada transaksi.")
    else:
        filter_col, filter_kind = st.columns(2)
        categories = ["All"] + sorted(df["category"].dropna().unique().tolist())
        selected_category = filter_col.selectbox("Filter category", categories)
        selected_kind = filter_kind.selectbox("Filter type", ["All", "Income", "Expense"])
        filtered = df.copy()
        if selected_category != "All":
            filtered = filtered[filtered["category"] == selected_category]
        if selected_kind != "All":
            filtered = filtered[filtered["kind"] == selected_kind]
        display = filtered.copy()
        display["transaction_date"] = display["transaction_date"].dt.strftime("%Y-%m-%d")
        display["amount"] = display["amount"].map(money)
        st.dataframe(display[["transaction_date", "kind", "category", "description", "amount", "id"]], use_container_width=True, hide_index=True)
        st.markdown("#### Delete a transaction")
        id_options = filtered["id"].astype(str).tolist()
        if id_options:
            chosen_id = st.selectbox("Select transaction ID", id_options)
            confirm = st.checkbox("I understand this permanently deletes the selected transaction.")
            if st.button("Delete selected transaction", disabled=not confirm):
                try:
                    supabase.table("transactions").delete().eq("id", chosen_id).eq("user_id", user_id).execute()
                    st.success("Transaction deleted.")
                    st.rerun()
                except Exception:
                    st.error("Could not delete transaction.")

elif page == "Insights":
    st.subheader("Spending insights")
    if df.empty:
        st.info("Tambahkan beberapa transaksi untuk melihat insight.")
    else:
        expenses_df = df[df["kind"] == "Expense"].copy()
        if expenses_df.empty:
            st.info("Belum ada transaksi pengeluaran.")
        else:
            by_category = expenses_df.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
            left, right = st.columns(2)
            with left:
                st.markdown("#### Expense by category")
                fig = px.pie(by_category, names="category", values="amount", hole=0.55,
                             color_discrete_sequence=["#176B45", "#3C8D63", "#83C99B", "#B7E4C7", "#D8F3DC"])
                fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), legend_title_text="")
                st.plotly_chart(fig, use_container_width=True)
            with right:
                st.markdown("#### Monthly cash flow")
                monthly = df.copy()
                monthly["month"] = monthly["transaction_date"].dt.to_period("M").astype(str)
                grouped = monthly.pivot_table(index="month", columns="kind", values="amount", aggfunc="sum", fill_value=0).reset_index()
                for col in ["Income", "Expense"]:
                    if col not in grouped:
                        grouped[col] = 0
                fig2 = px.bar(grouped, x="month", y=["Income", "Expense"], barmode="group",
                              color_discrete_map={"Income": "#176B45", "Expense": "#9AC7A8"})
                fig2.update_layout(margin=dict(t=10, b=10, l=10, r=10), legend_title_text="")
                st.plotly_chart(fig2, use_container_width=True)
            total_expense = expenses_df["amount"].sum()
            top = by_category.iloc[0]
            st.success(f"Insight: kategori pengeluaran terbesar adalah **{top['category']}** sebesar **{money(top['amount'])}**. Total pengeluaran tercatat: **{money(total_expense)}**.")
            st.caption("Insights are based only on transactions you have entered; they are not financial advice.")

else:
    st.subheader("Export your data")
    st.write("Unduh salinan transaksi sebagai CSV untuk backup atau analisis lanjutan.")
    if df.empty:
        st.info("Belum ada transaksi untuk diekspor.")
    else:
        export_df = df.copy()
        export_df["transaction_date"] = export_df["transaction_date"].dt.strftime("%Y-%m-%d")
        export_df = export_df[["transaction_date", "kind", "category", "description", "amount"]]
        st.download_button("⬇ Download transactions.csv", export_df.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"arthurs_transactions_{date.today().isoformat()}.csv", mime="text/csv")
        st.warning("Simpan file backup di lokasi pribadi. Jangan mengunggah CSV ke repositori publik.")
