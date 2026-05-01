import streamlit as st
from supabase import create_client
import datetime

# =========================
# SUPABASE CONNECTION
# =========================
SUPABASE_URL = "https://rxcdwvlfxbilkizimmoj.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_ANON_KEY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# SETTINGS
# =========================
VALID_USERS = ["Babu", "babun"]

# =========================
# FUNCTIONS
# =========================
def get_week(date):
    year, week, _ = date.isocalendar()
    return f"{year}-W{week}"

def calculate_score(entry):
    score = 0
    if entry.get("healthy_meals"):
        score += 2
    if entry.get("fruits"):
        score += 1
    if entry.get("water"):
        score += 1
    if entry.get("overeat"):
        score -= 1

    score += 0 if entry.get("junk_day") else 1
    return score

def fetch_week_data(week):
    response = supabase.table("daily_logs").select("*").eq("week", week).execute()
    return response.data or []

# =========================
# LOGIN SYSTEM
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

st.title("💑 Healthy Love Game (Supabase Version)")

if st.session_state.user is None:
    name = st.text_input("Enter your name 💕")

    if st.button("Login"):
        if name in VALID_USERS:
            st.session_state.user = name
            st.rerun()
        else:
            st.error("Access Denied 🚫")

    st.stop()

user = st.session_state.user
st.success(f"Logged in as {user} 💖")

# =========================
# DATE + WEEK
# =========================
selected_date = st.date_input("Select Date 📅", datetime.date.today())
date_str = str(selected_date)
week = get_week(selected_date)

# =========================
# CHECK IF ALREADY LOGGED
# =========================
existing = supabase.table("daily_logs") \
    .select("*") \
    .eq("user", user) \
    .eq("date", date_str) \
    .execute()

already_logged = len(existing.data or []) > 0

if already_logged:
    st.warning("⚠️ You already logged this date!")

# =========================
# DAILY INPUT
# =========================
st.header("📝 Daily Log")

healthy = st.checkbox("Healthy meals 🥗")
fruits = st.checkbox("Fruits/veggies 🍎")
water = st.checkbox("Enough water 💧")
overeat = st.checkbox("Overeating 😅")

st.subheader("🍔 Junk Food")

junk_choice = st.radio(
    "Did you eat junk food today?",
    ["No Junk 🚫", "Yes Junk 🍔"]
)

junk_day = junk_choice == "Yes Junk 🍔"

# =========================
# SAVE ENTRY
# =========================
if st.button("Save Entry 💾", disabled=already_logged):

    entry = {
        "user": user,
        "date": date_str,
        "week": week,
        "healthy_meals": healthy,
        "fruits": fruits,
        "water": water,
        "overeat": overeat,
        "junk_day": junk_day,
    }

    entry["score"] = calculate_score(entry)

    supabase.table("daily_logs").insert(entry).execute()

    st.success(f"Saved! ✨ Score: {entry['score']}")
    st.rerun()

# =========================
# WEEKLY SUMMARY
# =========================
st.header("📊 Weekly Summary")

rows = fetch_week_data(week)

results = {}

for player in VALID_USERS:

    entries = [r for r in rows if r.get("user") == player]

    total = sum((e or {}).get("score", 0) for e in entries)
    junk_days = sum(1 for e in entries if e.get("junk_day"))
    healthy_days = sum(1 for e in entries if (e.get("score") or 0) >= 4)

    extra_junk = max(0, junk_days - 1)
    junk_penalty = extra_junk * -3
    healthy_bonus = 2 if healthy_days >= 5 else 0
    no_junk_bonus = 3 if junk_days == 0 else 0

    final = total + junk_penalty + healthy_bonus + no_junk_bonus
    results[player] = final

    st.subheader(f"💖 {player}")
    st.write(f"Total Score: {total}")
    st.write(f"Junk Days: {junk_days}")
    st.write(f"Healthy Days: {healthy_days}")
    st.write(f"Penalty: {junk_penalty}")
    st.write(f"Bonus: {healthy_bonus + no_junk_bonus}")
    st.success(f"Final Score: {final}")

# =========================
# WINNER LOGIC
# =========================
if results:
    winner = max(results, key=results.get)
    loser = min(results, key=results.get)

    st.header("🏆 Result")
    st.success(f"{winner} wins! 🎉")
    st.warning(f"{loser} owes a punishment 😈")
    st.info("Ideas: Cook 🍳 | Walk 🚶 | Surprise date 🌹")
else:
    st.info("No data yet this week 😢")
