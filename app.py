import base64
from flask import Flask, request, render_template
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
app = Flask(__name__)
from lifelines import KaplanMeierFitter
import plotly.graph_objects as go
import plotly.io as pio


@app.route('/home')
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/get_patient_details')
def get_patient_details():
    return render_template('get_patient_details.html')


@app.route('/visualize', methods=['GET ', 'POST'])
def visualize():
    def plot_survival_by_user_input(data, column, user_value, event_column):
        # Function to add trace for a group with patient ID mapping
        def add_trace_for_group(group_data, label, id_column):
            kmf.fit(group_data['overall_survival_months'], event_observed=group_data[event_column], label=label)
            # Mapping time points to patient IDs
            time_to_patient_ids = group_data.groupby('overall_survival_months')[id_column].apply(list).to_dict()
            hover_texts = [
                f"Time: {time}<br>Survival Probability: {kmf.survival_function_.loc[time, kmf.survival_function_.columns[0]]:.2f}<br>Patient IDs: {', '.join(str(id) for id in time_to_patient_ids.get(time, []))}"
                for time in kmf.survival_function_.index]

            fig.add_trace(go.Scatter(
                x=kmf.survival_function_.index,
                y=kmf.survival_function_[kmf.survival_function_.columns[0]],
                mode='markers+lines',
                name=label,
                text=hover_texts,  # Use the generated hover texts
                hoverinfo="text"
            ))

        kmf = KaplanMeierFitter()
        id_column = data.columns[0]

        group = data[data[column] == user_value]
        if len(group) < 1:
            no_value = f"Warning: The group '{column} is {user_value}' has no data and will be skipped."
            return no_value
        other_group = data[data[column] != user_value]

        fig = go.Figure()

        if not group.empty:
            add_trace_for_group(group, f"{column} is {user_value}", id_column)
        else:
            print(f"Warning: The group '{column} is {user_value}' has no data and will be skipped.")

        if not other_group.empty:
            add_trace_for_group(other_group, f"{column} is not {user_value}", id_column)
        else:
            print(f"Warning: The group '{column} is not {user_value}' has no data and will be skipped.")

        fig.update_layout(
            title=f"Survival Analysis based on {column}",
            xaxis_title="Time in Months",
            yaxis_title="Survival Probability",
            legend_title=f"{column}"
        )
        #fig_html = pio.to_html(fig, full_html=False)
        #print("Figgggggg")
        return fig


   ## Main
    data = pd.read_csv("breast_cancer.csv")
    # Preprocess data: Convert event column to numeric and handle NaNs
    event_column = 'death_from_cancer'  # Replace with your actual event column name
    column = request.form.get('column_name')
    #plot_survial_by_all_unique_values(data, user_column, event_column_name)
    #def plot_survial_by_all_unique_values(data: pd.DataFrame, column: str, event_column: str):
    known_categories = {'Died of Disease': 1, 'Living': 0, 'Died of Other Causes': 0}

# Apply the mapping and handle unmapped categories
    data[event_column] = data[event_column].map(known_categories)
    data.dropna(subset=['overall_survival_months', event_column], inplace=True)
    kmf = KaplanMeierFitter()

    # This assumes the first column in your DataFrame is 'patient_id'
    id_column = data.columns[0]  # Adjust if your patient ID column is named differently

    # Determine if the column is numeric but effectively categorical
    if data[column].dtype != 'O' and data[column].nunique() <= 10:
        unique_values = data[column].unique()
    elif data[column].dtype == 'O':
        unique_values = data[column].dropna().unique()
    else:
        # this function will split the user selected value as one group and except other datas are another group
        # plot_survival_clean_user_input(data,column,event_column)
        user_value = float(request.form.get('column_value'))
        fig = plot_survival_by_user_input(data, column, user_value, event_column)
        if type(fig) == str:
            return fig
        else:
            fig_html = pio.to_html(fig, full_html=False)
            return render_template('graph.html', fig_html=fig_html)

    fig = go.Figure()

    for user_value in unique_values:
        group = data[data[column] == user_value]
        if len(group) < 1:
            continue

        # Fit the KaplanMeierFitter for this group
        kmf.fit(group['overall_survival_months'], event_observed=group[event_column])

        # Prepare the mapping from time points to patient IDs for this group
        time_to_patient_ids = group.groupby('overall_survival_months')[id_column].apply(list).to_dict()

        # Generate hover texts that include patient IDs for each time point
        hover_texts = [
            f"Time: {time}<br>Survival Probability: {kmf.survival_function_.loc[time, kmf.survival_function_.columns[0]]:.2f}<br>Patient IDs: {', '.join(str(id) for id in time_to_patient_ids.get(time, []))}"
            for time in kmf.survival_function_.index]

        fig.add_trace(go.Scatter(
            x=kmf.survival_function_.index,
            y=kmf.survival_function_[kmf.survival_function_.columns[0]],
            mode='lines+markers',
            name=str(user_value),
            text=hover_texts,  # Use the generated hover texts
            hoverinfo="text"
        ))

    # Update the layout of the figure
    fig.update_layout(
        title=f"Survival Analysis by {column}",
        xaxis_title="Time in Months",
        yaxis_title="Survival Probability",
        legend_title=f"{column}"
    )

    fig_html = pio.to_html(fig, full_html=False)
    print("fig 1")
    return render_template('graph.html', fig_html=fig_html)


if __name__ == '__main__':
    app.run(debug=True)