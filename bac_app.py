import streamlit as st
import time
import datetime

# --- Constants ---
MALE_R = 0.73
FEMALE_R = 0.66
WIDMARK_FACTOR = 5.14 # Converts alcohol oz to grams, lbs to grams, and accounts for % BAC
METABOLISM_RATE_PER_HOUR = 0.015 # Average BAC reduction per hour
REFRESH_INTERVAL_SECONDS = 10 # How often to update the clock and BAC (e.g., every 10 seconds)

# --- Functions ---
def calculate_bac_value(total_alcohol_oz, weight_lbs, r_value, food_factor, current_elapsed_hours):
    """Calculates estimated BAC using a simplified Widmark formula."""
    if total_alcohol_oz <= 0:
        return 0.0
    
    # Calculate theoretical peak BAC
    peak_bac = (total_alcohol_oz * WIDMARK_FACTOR / (weight_lbs * r_value)) * food_factor
    
    # Subtract metabolism over time
    current_bac = peak_bac - (METABOLISM_RATE_PER_HOUR * current_elapsed_hours)
    
    return max(0.0, current_bac) # BAC cannot be negative, ensure float 0.0

def get_bac_status(bac):
    """Returns a tuple of (message, color, icon) based on BAC level."""
    if bac >= 0.08:
        return "Legal Limit Exceeded - DO NOT DRIVE!", "danger", "🚨"
    elif bac >= 0.05:
        return "Impaired - Avoid risky activities!", "warning", "⚠️"
    elif bac > 0.0:
        return "Some effects present - Drink responsibly.", "info", "✅"
    else:
        return "Sober - Enjoy responsibly!", "success", "🧘"

# --- Initialize Session State ---
if 'drinks' not in st.session_state:
    st.session_state.drinks = []
if 'start_monitoring' not in st.session_state:
    st.session_state.start_monitoring = False
if 'monitoring_start_time' not in st.session_state:
    st.session_state.monitoring_start_time = None
if 'first_drink_offset_hours' not in st.session_state: # This will store the initial "hours since first drink" input
    st.session_state.first_drink_offset_hours = 0.0
if 'last_calculated_bac_time' not in st.session_state:
    st.session_state.last_calculated_bac_time = None

# --- Streamlit UI ---
st.set_page_config(page_title="Dynamic BAC Estimator", layout="centered", initial_sidebar_state="auto")
st.title("🥂 Dynamic BAC Estimator")

st.markdown("""
    _This tool provides a **real-time estimation** of Blood Alcohol Content (BAC) based on common formulas. 
    It is **not a substitute for a breathalyzer or medical advice**. 
    Individual results can vary significantly due to metabolism, hydration, health conditions, and more. 
    **Always drink responsibly and never drink and drive.**_
""")

st.sidebar.header("Your Information")

with st.sidebar:
    # Gender selection
    gender = st.radio(
        "Gender", 
        ["Male", "Female"], 
        help="Biological gender affects average body water content (r value)."
    )
    r = MALE_R if gender == "Male" else FEMALE_R

    # Weight input
    weight_lbs = st.number_input(
        "Weight (lbs)", 
        min_value=50.0, 
        max_value=500.0, 
        value=160.0, 
        step=5.0
    )

    # Food intake
    food = st.radio(
        "Food Intake", 
        ["Empty Stomach", "Light Meal", "Heavy Meal"],
        help="Food can slow alcohol absorption, potentially lowering peak BAC. These factors are approximations."
    )
    food_factor = 1.0 if food == "Empty Stomach" else 0.8 if food == "Light Meal" else 0.5

    # Initial hours since first drink (before monitoring starts)
    st.session_state.first_drink_offset_hours = st.number_input(
        "Initial hours since first drink", 
        min_value=0.0, 
        max_value=24.0, 
        value=0.0, # Default to 0, implying "just started"
        step=0.5,
        help="This is the time elapsed *before* you start monitoring. Once monitoring starts, the clock takes over."
    )

st.header("Drinks Consumed")

def add_drink_callback():
    st.session_state.drinks.append({"volume": 0.0, "abv": 0.0})

def remove_drink_callback(index):
    if index < len(st.session_state.drinks):
        st.session_state.drinks.pop(index)

st.button("➕ Add Drink", on_click=add_drink_callback)

if st.session_state.drinks:
    with st.expander(f"Edit {len(st.session_state.drinks)} Drink(s) Details"):
        for i, drink in enumerate(st.session_state.drinks):
            st.markdown(f"**Drink {i+1}**")
            col1, col2, col3 = st.columns([0.4, 0.4, 0.2])
            with col1:
                st.session_state.drinks[i]["volume"] = st.number_input(
                    f"Volume (oz)", 
                    min_value=0.0, 
                    max_value=40.0, 
                    value=drink["volume"],
                    key=f"vol_{i}",
                    help="Typical beer is 12oz, wine is 5oz, spirits (shot) is 1.5oz."
                )
            with col2:
                st.session_state.drinks[i]["abv"] = st.number_input(
                    f"ABV (%)", 
                    min_value=0.0, 
                    max_value=100.0, 
                    value=drink["abv"],
                    key=f"abv_{i}",
                    help="Alcohol By Volume percentage."
                )
            with col3:
                st.markdown("<br>", unsafe_allow_html=True) # Spacer for alignment
                st.button("➖", key=f"remove_{i}", on_click=remove_drink_callback, args=(i,))
else:
    st.info("Click 'Add Drink' to start adding your beverages.")

st.markdown("---")
st.header("Real-time BAC Monitoring")

# Calculate total alcohol upfront
total_alcohol_oz = sum(drink["volume"] * (drink["abv"] / 100) for drink in st.session_state.drinks)

if total_alcohol_oz == 0 and len(st.session_state.drinks) > 0:
    st.warning("Please ensure all drinks have a valid volume and ABV to calculate BAC.")
elif total_alcohol_oz == 0 and len(st.session_state.drinks) == 0:
    st.info("Add drinks above to enable BAC monitoring.")

col_start, col_stop = st.columns(2)
with col_start:
    if st.button("▶️ Start Monitoring", disabled=(total_alcohol_oz == 0) or st.session_state.start_monitoring, use_container_width=True):
        st.session_state.start_monitoring = True
        st.session_state.monitoring_start_time = datetime.datetime.now()
        st.session_state.last_calculated_bac_time = datetime.datetime.now() # Initialize for first calculation
        st.rerun()
with col_stop:
    if st.button("⏹️ Stop Monitoring", disabled=not st.session_state.start_monitoring, use_container_width=True):
        st.session_state.start_monitoring = False
        st.session_state.monitoring_start_time = None
        st.session_state.last_calculated_bac_time = None
        st.rerun()

# Placeholder for dynamic output
bac_placeholder = st.empty()
clock_placeholder = st.empty()
status_placeholder = st.empty()
gauge_placeholder = st.empty() # For a simple gauge visualization

if st.session_state.start_monitoring and st.session_state.monitoring_start_time:
    while st.session_state.start_monitoring:
        # Calculate elapsed time
        current_time = datetime.datetime.now()
        
        # Total elapsed time includes initial offset + time since monitoring started
        time_since_monitor_start = (current_time - st.session_state.monitoring_start_time).total_seconds()
        total_elapsed_hours = st.session_state.first_drink_offset_hours + (time_since_monitor_start / 3600.0)

        # Recalculate BAC
        current_bac = calculate_bac_value(total_alcohol_oz, weight_lbs, r, food_factor, total_elapsed_hours)
        
        message, color, icon = get_bac_status(current_bac)

        with bac_placeholder.container():
            st.markdown(f"### Current Estimated BAC: <span style='color: {'red' if current_bac >= 0.08 else 'orange' if current_bac >= 0.05 else 'green'};'>{current_bac:.3f}%</span>", unsafe_allow_html=True)
            
            # Simple progress bar as a visual gauge
            # Max BAC for gauge is somewhat arbitrary, 0.20% is a very high level
            gauge_value = min(current_bac / 0.20, 1.0) 
            st.progress(gauge_value)
            st.caption(f"BAC Gauge: {current_bac:.3f}% out of ~0.20% Max")


        with clock_placeholder.container():
            st.metric(
                label="Total Time Elapsed (since first drink)", 
                value=f"{int(total_elapsed_hours)}h {int((total_elapsed_hours * 60) % 60)}m {int((total_elapsed_hours * 3600) % 60)}s"
            )

        with status_placeholder.container():
            if color == "danger":
                st.error(f"{icon} {message}")
                if current_bac >= 0.08:
                    st.image('https://i.imgur.com/rN9e9G8.png', caption='Do Not Drive!', width=150) # Placeholder image
            elif color == "warning":
                st.warning(f"{icon} {message}")
                st.image('https://i.imgur.com/gK2g0Z2.png', caption='Impaired', width=150) # Placeholder image
            elif color == "info":
                st.info(f"{icon} {message}")
            else:
                st.success(f"{icon} {message}")
        
        time.sleep(REFRESH_INTERVAL_SECONDS)
        st.rerun() # Force rerun to update UI if time.sleep is used

else: # If monitoring is not active
    bac_placeholder.empty()
    clock_placeholder.empty()
    status_placeholder.empty()
    gauge_placeholder.empty()
    
    if total_alcohol_oz > 0:
        # Show a static calculation if monitoring is off but drinks are entered
        initial_bac_estimate = calculate_bac_value(total_alcohol_oz, weight_lbs, r, food_factor, st.session_state.first_drink_offset_hours)
        message, color, icon = get_bac_status(initial_bac_estimate)
        st.markdown(f"### Initial Estimated BAC: <span style='color: {'red' if initial_bac_estimate >= 0.08 else 'orange' if initial_bac_estimate >= 0.05 else 'green'};'>{initial_bac_estimate:.3f}%</span>", unsafe_allow_html=True)
        if color == "danger":
                st.error(f"{icon} {message}")
        elif color == "warning":
            st.warning(f"{icon} {message}")
        elif color == "info":
            st.info(f"{icon} {message}")
        else:
            st.success(f"{icon} {message}")


st.markdown("---")
st.caption("Disclaimer: This calculator is for educational purposes only and should not be used to determine fitness to drive or operate machinery. The real-time updates are still estimations.")