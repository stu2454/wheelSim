import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Enable wide mode
st.set_page_config(layout="wide")

# Custom CSS to remove padding and margins
st.markdown("""
    <style>
        .css-18e3th9 {padding: 1rem 1rem 1rem 1rem;}  /* Adjust content padding */
        .css-1d391kg {padding-top: 1rem;}  /* Remove padding at the top */
    </style>
    """, unsafe_allow_html=True)

# Set up the page title
st.title("Wheelchair Funding Model Simulator")

# Set up two columns with a larger right column for outputs and plots
col1, col2 = st.columns([1, 2])  # Adjust column ratios for balanced layout

# Left column for input fields
with col1:
    st.header("Parameters")
    lifespan = st.number_input("Wheelchair Lifespan (years):", min_value=1, max_value=50, value=7)
    initial_cost = st.number_input("Initial Purchase Cost ($):", min_value=0.0, value=5000.0)
    maintenance_budget = st.number_input("Annual Maintenance Budget ($):", min_value=0.0, value=500.0)
    major_repair_cost = st.number_input("Major Repair Cost ($):", min_value=0.0, value=1000.0)
    repair_prob = st.slider("Probability of Major Repair:", min_value=0.0, max_value=1.0, value=0.15)
    replacement_cost = st.number_input("Replacement Cost ($):", min_value=0.0, value=5000.0)
    replacement_threshold = st.slider("Replacement Threshold (%):", min_value=0, max_value=100, value=80) / 100
    insurance_contribution = st.number_input("Annual Insurance Contribution ($):", min_value=0.0, value=500.0)
    user_intensity = st.number_input("User Intensity (1 = Light, >1 = Heavy):", min_value=1.0, value=1.0)
    decision_margin = st.slider("Decision Margin (%):", min_value=0, max_value=100, value=5) / 100
    depreciation_rate = st.slider("Depreciation Rate (%):", min_value=0, max_value=100, value=20) / 100

# Button to run the simulation, placed in left column for user convenience
run_simulation = st.button("Run Simulation")

# Right column for output
if run_simulation:
    with col2:
        st.header("Simulation Results")

        # Simulation function
        minor_repair_cost_range = (200 * user_intensity, 400 * user_intensity)
        adjusted_repair_prob = repair_prob * user_intensity
        cumulative_repairs = []
        pool_balance = 0
        current_value = initial_cost
        results = {
            "Year": [], "Minor Repairs ($)": [], "Major Repairs ($)": [], 
            "Total Repairs ($)": [], "Cumulative Repair Cost ($)": [],
            "Replacement Decision": [], "Pool Balance ($)": [], "Current Value ($)": []
        }

        # Run the simulation over the defined lifespan
        for year in range(1, lifespan + 1):
            minor_repair = np.random.randint(int(minor_repair_cost_range[0]), int(minor_repair_cost_range[1]))
            major_repair = major_repair_cost if np.random.rand() < adjusted_repair_prob else 0
            total_repair = minor_repair + major_repair
            cumulative_cost = total_repair + (cumulative_repairs[-1] if cumulative_repairs else 0)
            cumulative_repairs.append(cumulative_cost)

            # Apply depreciation
            current_value *= (1 - depreciation_rate)
            current_value = max(0, current_value)

            # Replacement decision logic
            if cumulative_cost >= replacement_cost * replacement_threshold or current_value < replacement_cost * decision_margin:
                replace = "Yes"
            elif cumulative_cost >= replacement_cost * replacement_threshold * (1 - decision_margin):
                replace = "Review Needed"
            else:
                replace = "No"

            pool_balance += insurance_contribution - total_repair
            if replace == "Yes":
                pool_balance -= replacement_cost

            # Collect the results for each year
            results["Year"].append(year)
            results["Minor Repairs ($)"].append(minor_repair)
            results["Major Repairs ($)"].append(major_repair)
            results["Total Repairs ($)"].append(total_repair)
            results["Cumulative Repair Cost ($)"].append(cumulative_cost)
            results["Replacement Decision"].append(replace)
            results["Pool Balance ($)"].append(pool_balance)
            results["Current Value ($)"].append(current_value)

        # Convert results to DataFrame
        df = pd.DataFrame(results)
        st.write("### Detailed Results")
        st.dataframe(df)  # Display with full width and scrolling for better visibility

        # New row for side-by-side plots
        plot_col1, plot_col2 = st.columns(2)

        # Plot Cumulative Repair Cost in the left plot column
        with plot_col1:
            fig1, ax1 = plt.subplots(figsize=(5, 4))
            ax1.plot(df["Year"], df["Cumulative Repair Cost ($)"], label="Cumulative Repair Cost", color='blue', marker='o')
            ax1.axhline(y=replacement_cost * replacement_threshold, color='red', linestyle='--', label="Replacement Threshold")
            ax1.set_xlabel("Year")
            ax1.set_ylabel("Cumulative Repair Cost ($)")
            ax1.legend()
            st.pyplot(fig1)

        # Plot Insurance Pool Balance in the right plot column
        with plot_col2:
            fig2, ax2 = plt.subplots(figsize=(5, 4))
            ax2.plot(df["Year"], df["Pool Balance ($)"], label="Insurance Pool Balance", color='green', marker='o')
            ax2.set_xlabel("Year")
            ax2.set_ylabel("Insurance Pool Balance ($)")
            ax2.legend()
            st.pyplot(fig2)

