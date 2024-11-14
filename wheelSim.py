import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Enable wide mode
st.set_page_config(layout="wide")

# Custom CSS to center the table output and wrap header cells
st.markdown("""
    <style>
        /* Center the entire dataframe table */
        .dataframe-container {
            display: flex;
            justify-content: center;
        }

        /* Wrap table headers and center-align them */
        .dataframe th {
            white-space: normal !important;
            text-align: center !important;
            overflow-wrap: break-word;
        }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state for tab navigation
if "show_simulator" not in st.session_state:
    st.session_state.show_simulator = False

# Tab selection or directly showing the Simulator based on session state
if st.session_state.show_simulator:
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

    # Right column for output with header and buttons on the same row
    with col2:
        header_col, button_col1, button_col2 = st.columns([2, 1, 1])  # Adjust column widths as needed
        with header_col:
            st.header("Simulation Results")
        with button_col1:
            if st.button("Rerun Simulation"):
                st.session_state.run_simulation = True  # Trigger simulation rerun
        with button_col2:
            if st.button("Back to Introduction"):
                st.session_state.show_simulator = False  # Go back to Introduction tab

    # Run the simulation if "run_simulation" state is True or if the simulation hasn't run yet
    if "run_simulation" not in st.session_state or st.session_state.run_simulation:
        with col2:
            st.session_state.run_simulation = False  # Reset for next rerun

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

            # Convert results to DataFrame and display it with centered alignment
            df = pd.DataFrame(results)
            st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
            st.dataframe(df)  # Display with full width and scrolling for better visibility
            st.markdown('</div>', unsafe_allow_html=True)

            # New row for side-by-side plots
            plot_col1, plot_col2 = st.columns(2)

            # Plot Cumulative Repair Cost
            with plot_col1:
                fig1, ax1 = plt.subplots(figsize=(5, 4))
                ax1.plot(df["Year"], df["Cumulative Repair Cost ($)"], label="Cumulative Repair Cost", color='blue', marker='o')
                ax1.axhline(y=replacement_cost * replacement_threshold, color='red', linestyle='--', label="Replacement Threshold")
                ax1.set_xlabel("Year")
                ax1.set_ylabel("Cumulative Repair Cost ($)")
                ax1.legend()
                st.pyplot(fig1)

            # Plot Insurance Pool Balance
            with plot_col2:
                fig2, ax2 = plt.subplots(figsize=(5, 4))
                ax2.plot(df["Year"], df["Pool Balance ($)"], label="Insurance Pool Balance", color='green', marker='o')
                ax2.set_xlabel("Year")
                ax2.set_ylabel("Insurance Pool Balance ($)")
                ax2.legend()
                st.pyplot(fig2)

else:
    st.title("Wheelchair Funding Model Simulator")
    st.header("Introduction")
    
    # Description of the model
    st.markdown("""
    This simulator models the long-term costs of maintaining and potentially replacing a wheelchair, based on various factors that affect repairs, maintenance, and replacement decisions. It’s designed to provide insights into whether an insurance-like contribution strategy can sustain the costs associated with the lifecycle of a wheelchair or similar assistive device.
    """)

    st.subheader("Parameter Explanations")
    
    # Explanations for each parameter
    st.markdown("""
    - **Wheelchair Lifespan (years)**: The expected functional lifespan of the wheelchair.
    - **Initial Purchase Cost ($)**: The initial cost of purchasing the wheelchair.
    - **Annual Maintenance Budget ($)**: The estimated yearly cost of routine upkeep.
    - **Major Repair Cost ($)**: Cost of a significant repair event.
    - **Probability of Major Repair**: Likelihood of a major repair occurring each year.
    - **Replacement Cost ($)**: Cost to replace the wheelchair with a new one.
    - **Replacement Threshold (%)**: Percentage of the replacement cost at which replacement becomes a consideration.
    - **Annual Insurance Contribution ($)**: Yearly contribution to a fund intended to cover repair and replacement costs.
    - **User Intensity (1 = Light, >1 = Heavy)**: Level of use intensity, affecting repair frequency and cost.
    - **Decision Margin (%)**: Margin applied to the replacement threshold for early replacement reviews.
    - **Depreciation Rate (%)**: Rate reflecting the diminishing value of the wheelchair over time.
    """)

    st.subheader("Model Reasoning")
    st.markdown("""
    - **Insurance-Like Contributions**: By contributing a steady amount to an insurance pool each year, the model examines financial sustainability.
    - **Repair vs. Replacement Decisions**: This model factors in cumulative repair costs, asset value depreciation, and replacement thresholds to decide on repairs vs. replacement.
    - **Real-World Risk Management**: Parameters like user intensity and repair probability incorporate variability, allowing users to explore different maintenance and financial scenarios.
    """)

    # Button to switch to the Simulator tab
    if st.button("Proceed to Simulator"):
        st.session_state.show_simulator = True  # Update session state to show simulator

