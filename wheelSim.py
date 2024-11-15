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
        .dataframe-container table thead th {
            white-space: normal !important;
            text-align: center !important;
            word-wrap: break-word;
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
        # User Type Selection
        user_type = st.selectbox("Select User Type:", options=["Light User", "Heavy User"])

        lifespan = st.number_input("Wheelchair Lifespan (years):", min_value=1, max_value=50, value=7)
        initial_cost = st.number_input("Initial Purchase Cost ($):", min_value=0.0, value=5000.0)
        annual_rm_budget = st.number_input("Annual R&M Budget ($):", min_value=0.0, value=500.0)
        major_repair_cost = st.number_input("Base Major Repair Cost ($):", min_value=0.0, value=1000.0)
        base_repair_prob = st.slider("Base Probability of Major Repair:", min_value=0.0, max_value=1.0, value=0.15)
        replacement_cost = st.number_input("Replacement Cost ($):", min_value=0.0, value=5000.0)
        replacement_threshold = st.slider("Replacement Threshold (%):", min_value=0, max_value=100, value=80) / 100
        min_pool_balance_threshold = st.number_input("Minimum R&M Pool Balance Threshold ($):", min_value=-10000.0, value=100.0)
        depreciation_rate = st.slider("Depreciation Rate (%):", min_value=0, max_value=100, value=20) / 100

        # Maintenance Adherence Parameter
        maintenance_adherence = st.slider("Maintenance Adherence Probability:", min_value=0.0, max_value=1.0, value=1.0)

    # Right column for output with header and buttons on the same row
    with col2:
        header_col, button_col1, button_col2 = st.columns([2, 1, 1])  # Adjust column widths as needed
        with header_col:
            st.header("Simulation Results")
        with button_col1:
            if st.button("Rerun Simulation"):
                st.session_state.run_simulation = True  # Trigger simulation rerun
        with button_col2:
            if st.button("Back to Information"):
                st.session_state.show_simulator = False  # Go back to Information tab

    # Run the simulation if "run_simulation" state is True or if the simulation hasn't run yet
    if "run_simulation" not in st.session_state or st.session_state.run_simulation:
        with col2:
            st.session_state.run_simulation = False  # Reset for next rerun

            # Adjust repair probabilities and costs based on user type
            if user_type == "Light User":
                user_intensity = 1.0
                adjusted_repair_prob = base_repair_prob
            else:  # Heavy User
                user_intensity = 1.5  # Increased repair costs
                adjusted_repair_prob = min(1.0, base_repair_prob * 1.25)  # Increased probability of major repair

            minor_repair_cost_range = (200 * user_intensity, 400 * user_intensity)
            cumulative_repairs = []
            pool_balance = annual_rm_budget
            current_value = initial_cost
            results = {
                "Year": [], "Minor Repairs ($)": [], "Major Repairs ($)": [],
                "Total Repairs ($)": [], "Cumulative Repair Cost ($)": [],
                "Pool Balance ($)": [], "Current Value ($)": [], "Decision": []
            }

            year = 1
            while True:
                # Determine if the user adheres to maintenance schedule
                if np.random.rand() < maintenance_adherence:
                    minor_repair = np.random.randint(int(minor_repair_cost_range[0]), int(minor_repair_cost_range[1]))
                else:
                    minor_repair = 0  # No minor repair if not adhering to maintenance

                major_repair = major_repair_cost if np.random.rand() < adjusted_repair_prob else 0
                total_repair = minor_repair + major_repair
                cumulative_cost = total_repair + (cumulative_repairs[-1] if cumulative_repairs else 0)
                cumulative_repairs.append(cumulative_cost)

                # Update pool balance and apply depreciation
                pool_balance += annual_rm_budget - total_repair
                current_value *= (1 - depreciation_rate)
                current_value = max(0, current_value)

                # Decision Logic
                if cumulative_cost >= replacement_cost * replacement_threshold:
                    decision = "Replace"
                elif cumulative_cost >= (replacement_cost * replacement_threshold * 0.95):
                    decision = "Consider Replacement"
                elif pool_balance < min_pool_balance_threshold:
                    decision = "Review Required"
                else:
                    decision = "Continue Using"

                # Collect results for display
                results["Year"].append(year)
                results["Minor Repairs ($)"].append(minor_repair)
                results["Major Repairs ($)"].append(major_repair)
                results["Total Repairs ($)"].append(total_repair)
                results["Cumulative Repair Cost ($)"].append(cumulative_cost)
                results["Pool Balance ($)"].append(pool_balance)
                results["Current Value ($)"].append(current_value)
                results["Decision"].append(decision)

                # Modify termination condition
                # Continue until both conditions are met: lifespan is reached and cumulative cost exceeds threshold
                if year >= lifespan and (cumulative_cost >= replacement_cost * replacement_threshold or pool_balance < min_pool_balance_threshold):
                    break
                year += 1

            # Convert to DataFrame and display
            df = pd.DataFrame(results)
            st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
            st.dataframe(df)  # Display with full width and scrolling for better visibility
            st.markdown('</div>', unsafe_allow_html=True)

            # Initial Plots for Single Simulation
            plot_col1, plot_col2 = st.columns(2)

            # Plot Cumulative Repair Cost with extended portion
            with plot_col1:
                fig1, ax1 = plt.subplots(figsize=(5, 4))
                # Plot up to lifespan
                ax1.plot(df["Year"][:lifespan], df["Cumulative Repair Cost ($)"][:lifespan], label="Cumulative Repair Cost", color='blue', marker='o')
                # Plot beyond lifespan
                if len(df["Year"]) > lifespan:
                    ax1.plot(df["Year"][lifespan:], df["Cumulative Repair Cost ($)"][lifespan:], linestyle='--', color='blue')
                ax1.axhline(y=replacement_cost * replacement_threshold, color='red', linestyle='--', label="Replacement Threshold")
                ax1.set_xlabel("Year")
                ax1.set_ylabel("Cumulative Repair Cost ($)")
                ax1.legend()
                st.pyplot(fig1)

            # Plot Pool Balance with extended portion
            with plot_col2:
                fig2, ax2 = plt.subplots(figsize=(5, 4))
                # Plot up to lifespan
                ax2.plot(df["Year"][:lifespan], df["Pool Balance ($)"][:lifespan], label="R&M Pool Balance", color='green', marker='o')
                # Plot beyond lifespan
                if len(df["Year"]) > lifespan:
                    ax2.plot(df["Year"][lifespan:], df["Pool Balance ($)"][lifespan:], linestyle=':', color='green')
                ax2.axhline(y=min_pool_balance_threshold, color='orange', linestyle='--', label="Minimum Pool Threshold")
                ax2.set_xlabel("Year")
                ax2.set_ylabel("R&M Pool Balance ($)")
                ax2.legend()
                st.pyplot(fig2)

            # Updated Average Trajectory Simulation Function
            def simulate_avg_trajectory(user_type, n_simulations=1000):
                if user_type == "Light User":
                    user_intensity = 1.0
                    adjusted_repair_prob = base_repair_prob
                    max_years = 20  # Extend to 20 years for light users
                else:  # Heavy User
                    user_intensity = 1.5
                    adjusted_repair_prob = min(1.0, base_repair_prob * 1.25)
                    max_years = 12  # Keep 12 years for heavy users

                minor_repair_cost_range = (200 * user_intensity, 400 * user_intensity)

                # Initialize arrays to store cumulative costs
                avg_cumulative_repair = np.zeros(max_years)
                counts = np.zeros(max_years)

                for _ in range(n_simulations):
                    cumulative_cost = 0
                    cumulative_costs = []
                    pool_balance = annual_rm_budget
                    for year in range(max_years):
                        # Determine if the user adheres to maintenance schedule
                        if np.random.rand() < maintenance_adherence:
                            minor_repair = np.random.randint(int(minor_repair_cost_range[0]), int(minor_repair_cost_range[1]))
                        else:
                            minor_repair = 0  # No minor repair if not adhering to maintenance

                        major_repair = major_repair_cost if np.random.rand() < adjusted_repair_prob else 0
                        total_repair = minor_repair + major_repair
                        cumulative_cost += total_repair
                        pool_balance += annual_rm_budget - total_repair

                        # Append the cumulative cost
                        cumulative_costs.append(cumulative_cost)

                    # Convert to numpy array
                    cumulative_costs = np.array(cumulative_costs)

                    # For simulations where the cumulative cost exceeds the threshold, hold the value constant thereafter
                    threshold_mask = cumulative_costs >= (replacement_cost * replacement_threshold)
                    if np.any(threshold_mask):
                        first_exceed_index = np.argmax(threshold_mask)
                        cumulative_costs[first_exceed_index + 1:] = cumulative_costs[first_exceed_index]

                    # Accumulate the cumulative costs for averaging
                    avg_cumulative_repair += cumulative_costs
                    counts += 1

                # Calculate the average
                avg_cumulative_repair /= counts

                return avg_cumulative_repair, max_years

            # Run simulations for averages for Light and Heavy Users
            avg_cumulative_light, max_years_light = simulate_avg_trajectory("Light User")
            avg_cumulative_heavy, max_years_heavy = simulate_avg_trajectory("Heavy User")

            # Identify the year when the average cumulative repair cost intersects the replacement threshold
            def find_intersection_year(avg_cumulative_repair):
                threshold = replacement_cost * replacement_threshold
                for i, cost in enumerate(avg_cumulative_repair):
                    if cost >= threshold:
                        return i + 1  # Years are 1-indexed
                return None  # Intersection does not occur within max_years

            intersection_year_light = find_intersection_year(avg_cumulative_light)
            intersection_year_heavy = find_intersection_year(avg_cumulative_heavy)

            # New row for average trajectory plots
            st.markdown("### Average Trajectories for Light and Heavy Users")
            avg_plot_col1, avg_plot_col2 = st.columns(2)

            # Plot Average Cumulative Repair Costs for Light and Heavy Users
            with avg_plot_col1:
                fig3, ax3 = plt.subplots(figsize=(6, 4))
                years_light = np.arange(1, max_years_light + 1)
                years_heavy = np.arange(1, max_years_heavy + 1)

                ax3.plot(years_light, avg_cumulative_light, label="Light User", color='blue')
                ax3.plot(years_heavy, avg_cumulative_heavy, label="Heavy User", color='orange')
                ax3.axhline(y=replacement_cost * replacement_threshold, color='red', linestyle='--', label="Replacement Threshold")
                ax3.set_xlabel("Year")
                ax3.set_ylabel("Average Cumulative Repair Cost ($)")
                ax3.set_xlim(left=1)
                ax3.set_ylim(bottom=0)

                # Mark the intersection points if they occur within max_years
                if intersection_year_light is not None:
                    ax3.axvline(x=intersection_year_light, color='blue', linestyle=':')
                if intersection_year_heavy is not None:
                    ax3.axvline(x=intersection_year_heavy, color='orange', linestyle=':')
                ax3.legend()
                st.pyplot(fig3)

            # Inform the user if intersection does not occur within max_years
            info_message = ""
            if intersection_year_light is None:
                info_message += "Note: The average cumulative repair cost for light users does not intersect the replacement threshold within 20 years.\n"
            if intersection_year_heavy is None:
                info_message += "Note: The average cumulative repair cost for heavy users does not intersect the replacement threshold within 12 years."
            if info_message:
                st.info(info_message)

else:
    st.title("Wheelchair Funding Model Simulator")
    st.header("Information")

    st.markdown("""
    ### Purpose of the Simulator
    This simulator models the long-term costs of wheelchair maintenance and helps explore how cumulative repair costs and available R&M budget affect the decision to replace or repair a wheelchair.

    ### Parameters
    - **User Type**: Choose between a Light User or Heavy User. Heavy Users have higher repair costs and a higher probability of major repairs.
    - **Wheelchair Lifespan**: The expected number of years a wheelchair is anticipated to last under normal usage.
    - **Initial Purchase Cost**: The initial cost of purchasing the wheelchair.
    - **Annual R&M Budget**: The annual budget allocated for repairs and maintenance.
    - **Major Repair Cost**: The cost incurred for major repairs in a given year.
    - **Base Probability of Major Repair**: The base likelihood that a major repair will be required in any given year.
    - **Replacement Cost**: The cost of replacing the wheelchair entirely.
    - **Replacement Threshold**: The percentage of the replacement cost that triggers the need to consider replacing the wheelchair.
    - **Minimum R&M Pool Balance Threshold**: The minimum acceptable balance in the repair and maintenance budget. If the pool balance drops below this value, a review is triggered.
    - **Depreciation Rate**: The annual depreciation rate applied to the wheelchair’s value over time.
    - **Maintenance Adherence Probability**: The probability that the user adheres to the maintenance schedule. A value of 0 means they do not perform minor repairs; a value of 1 means they always perform minor repairs.

    ### Decision-Making Logic
    1. **Replacement Decision**:
       - Triggered when cumulative repair costs exceed a specified percentage of the replacement cost (e.g., 80%).
       - The decision is marked as **"Replace"**.
    2. **Consider Replacement**:
       - Triggered if cumulative repair costs are close to the replacement threshold (within a 5% margin).
       - The decision is marked as **"Consider Replacement"**.
    3. **Review Required**:
       - Triggered if the R&M pool balance falls below the minimum threshold.
       - The decision is marked as **"Review Required"**.
    4. **Continue Using**:
       - If none of the above conditions are met, the wheelchair continues to be used.
       - The decision is marked as **"Continue Using"**.

    ### Key Insights
    - **Light Users**:
       - Tend to have fewer repairs and longer wheelchair lifespans.
       - Their repair costs grow slowly, allowing extended use before replacement is required.
    - **Heavy Users**:
       - Experience frequent and costly repairs, leading to shorter effective lifespans for their wheelchairs.
       - Their cumulative repair costs often exceed thresholds earlier than for light users.

    ### Maintenance Adherence
    - Users who adhere to their maintenance schedule (higher maintenance adherence probability) are more likely to incur minor repair costs regularly, which may prevent larger issues and major repairs.
    - Users who do not adhere to their maintenance schedule may have lower minor repair costs but could face more frequent major repairs and higher cumulative costs over time.

    ### Average Trajectories
    - **Light Users vs Heavy Users**: The bottom plots showcase average trajectories, comparing cumulative repair costs for the two user types.
    - The light user trajectory typically intersects the replacement threshold later than that of heavy users, highlighting their longer effective wheelchair lifespan.
    """)

    if st.button("Proceed to Simulator"):
        st.session_state.show_simulator = True

