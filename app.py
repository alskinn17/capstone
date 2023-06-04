import requests
import json
from flask import Flask, render_template, request
import csv
import pandas as pd

app = Flask(__name__, static_folder='static')

#currently using predict_epl_boost_over model which is a boosted regression model that has oversampled data 
url = 'https://us-central1-aiplatform.googleapis.com/v1/projects/skinner-capstone/locations/us-central1/endpoints/947985731328933888:predict'


headers = {
    'Authorization': 'Bearer ya29.a0AWY7CkmUWkQAEBFWLQGz-TsU32PCwwQ9h_gWWAFOSwwfrr_H2mDXARiVPTRXeATMHaNo22jrNpF_KMFSgjO_0YT_H9eNeB6bsImMoG7TPyLStVN3glGPMhA64LEcJzp8XlKTfzYGadZErkk8Gglb7Qn4i1v-RDqfCcpnyNL8mABbI3V5Q_Px3Jdbaqnt8it8PfW32fKuWZDX8onwRnT6fCaw-9cnNm2W0WymuxcaCgYKAYcSARASFQG1tDrpKrIAOG0Ub8Cipm9Be3Di0g0238',
    'Content-Type': 'application/json'
}

def get_statistics(home_team, away_team):

    with open('last3_actual.csv', 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    home_team_row = next(row for row in rows if row['Team'] == home_team)
    away_team_row = next(row for row in rows if row['Team'] == away_team)

    if home_team_row is None:
        print(f"No data found for home team: {home_team}")
        return None

    if away_team_row is None:
        print(f"No data found for away team: {away_team}")
        return None

    total_goals_per_match_diff = float(home_team_row['total_goals_per_match']) - float(away_team_row['total_goals_per_match'])
    half_time_goals_per_match_diff = float(home_team_row['half_time_goals_per_match']) - float(away_team_row['half_time_goals_per_match'])
    shots_per_match_diff = float(home_team_row['shots_per_match']) - float(away_team_row['shots_per_match'])
    shots_on_target_per_match_diff = float(home_team_row['shots_on_target_per_match']) - float(away_team_row['shots_on_target_per_match'])
    fouls_per_match_diff = float(home_team_row['fouls_per_match']) - float(away_team_row['fouls_per_match'])
    corners_per_match_diff = float(home_team_row['corners_per_match']) - float(away_team_row['corners_per_match'])
    yellows_per_match_diff = float(home_team_row['yellows_per_match']) - float(away_team_row['yellows_per_match'])
    reds_per_match_diff = float(home_team_row['reds_per_match']) - float(away_team_row['reds_per_match'])
   

    statistics = {
        'total_goals_per_match_diff': total_goals_per_match_diff,
        'half_time_goals_per_match_diff': half_time_goals_per_match_diff,
        'shots_per_match_diff': shots_per_match_diff,
        'shots_on_target_per_match_diff': shots_on_target_per_match_diff,
        'fouls_per_match_diff': fouls_per_match_diff,
        'corners_per_match_diff': corners_per_match_diff,
        'yellows_per_match_diff': yellows_per_match_diff,
        'reds_per_match_diff': reds_per_match_diff
    }

    return statistics

@app.route('/', methods=['GET', 'POST'])
def home_page():
    flag = 0 #end of season flag

    champions = pd.read_csv('champions.csv')
    relegation = pd.read_csv('relegation.csv')
    prev_week = pd.read_csv('prev_week.csv')

    if flag == 1:
        next_week = pd.read_csv('end_of_season.csv')
    else:
        next_week = pd.read_csv('next_week.csv')

    return render_template('home.html', top4=champions.to_dict('records'), 
                           bot3=relegation.to_dict('records'),
                           prev_fixtures=prev_week.to_dict('records'),
                           next_fixtures=next_week.to_dict('records'),
                           active_page="home")

@app.route('/predict', methods=['GET', 'POST'])
def predict_result():
    if request.method == 'POST':
        # Get the selected teams from the form
        home_team = request.form['home_team']
        away_team = request.form['away_team']
        
        home_logo = home_team + '.png'
        away_logo = away_team + '.png'
        #home_logo = request.form['home_team']
        #away_logo = request.form['away_team']

        #team_logos = {
        #    'home': '/static/Images/home_team.png',
         #   'away': '/static/Images/away_team.png'
        #}

        # Get the statistics for the selected teams
        statistics = get_statistics(home_team, away_team)
        
        # Format the statistics as a JSON object
        data = {
            "instances": [{
                "total_goals_per_match_diff": statistics['total_goals_per_match_diff'],
                "half_time_goals_per_match_diff": statistics['half_time_goals_per_match_diff'],
                "shots_per_match_diff": statistics['shots_per_match_diff'],
                "shots_on_target_per_match_diff": statistics['shots_on_target_per_match_diff'],
                "fouls_per_match_diff": statistics['fouls_per_match_diff'],
                "corners_per_match_diff": statistics['corners_per_match_diff'],
                "yellows_per_match_diff": statistics['yellows_per_match_diff'],
                "reds_per_match_diff": statistics['reds_per_match_diff']
            }]
        }
        
        # Send the JSON object to the model's REST API endpoint
        response = requests.post(url, headers=headers, json=data)
        
        # Retrieve the predicted result from the response
        print(response.text)
        # Variable to save response
        response_data = json.loads(response.text)
        predictions = response_data['predictions']

        # Get predicted result
        result = predictions[0]['predicted_team_1_home_result']

        # Get probabilities of each result
        result_probs = predictions[0]['team_1_home_result_probs']
        #print(result_probs)
        draw = result_probs[0]
        home_team_win = result_probs[2]
        home_team_loss = result_probs[1]

        result_string = ""
        if result == ['0']:
            result_string = f'{home_team} is predicted to win'
        elif result == ['1']:
            result_string = f'{home_team} is predicted to lose'
        else:
            result_string = 'The match is predicted to be a draw'

        probs_string = f'{home_team} predicted probabilities: Win = {home_team_win*100:.2f}%, Lose = {home_team_loss*100:.2f}%, Draw = {draw*100:.2f}%'

        # Update the web interface with the predicted result
        return render_template('result.html', active_page='prediction', result_string=result_string, probs_string=probs_string, home_team=home_team, away_team=away_team, home_logo=home_logo, away_logo=away_logo)
    else:
        # Render the form for selecting the teams
        return render_template('form.html', active_page='prediction')

@app.route('/table')
def curren_table():

    csv_file_path = './table.csv'

    with open(csv_file_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        data = list(reader)

    return render_template('current_table.html', header=header, data=data, active_page='table')

@app.route('/standard')
def standard():
    data = pd.read_csv('standard.csv')
    headers = data.columns.tolist()
    return render_template('table.html', data=data.values.tolist(), headers=headers, active_page='team_stats')

@app.route('/defense')
def defense():
    data = pd.read_csv('defense.csv')
    headers = data.columns.tolist()
    return render_template('table.html', data=data.values.tolist(), headers=headers, active_page='team_stats')

@app.route('/gca')
def gca():
    data = pd.read_csv('goal_creation.csv')
    headers = data.columns.tolist()
    return render_template('table.html', data=data.values.tolist(), headers=headers, active_page='team_stats')

@app.route('/passing')
def passing():
    data = pd.read_csv('passing.csv')
    headers = data.columns.tolist()
    return render_template('table.html', data=data.values.tolist(), headers=headers, active_page='team_stats')

@app.route('/shooting')
def shooting():
    data = pd.read_csv('shooting.csv')
    headers = data.columns.tolist()
    return render_template('table.html', data=data.values.tolist(), headers=headers, active_page='team_stats')

@app.route('/standard-against')
def standard_against():
    data = pd.read_csv('standard_against.csv')
    headers = data.columns.tolist()
    return render_template('table.html', data=data.values.tolist(), headers=headers, active_page='team_stats')

@app.route('/defense-against')
def defense_against():
    data = pd.read_csv('defense_against.csv')
    headers = data.columns.tolist()
    return render_template('table.html', data=data.values.tolist(), headers=headers, active_page='team_stats')

@app.route('/gca-against')
def gca_against():
    data = pd.read_csv('goal_creation_against.csv')
    headers = data.columns.tolist()
    return render_template('table.html', data=data.values.tolist(), headers=headers, active_page='team_stats')

@app.route('/passing-against')
def passing_against():
    data = pd.read_csv('passing_against.csv')
    headers = data.columns.tolist()
    return render_template('table.html', data=data.values.tolist(), headers=headers, active_page='team_stats')

@app.route('/shooting-against')
def shooting_against():
    data = pd.read_csv('shooting_against.csv')
    headers = data.columns.tolist()
    return render_template('table.html', data=data.values.tolist(), headers=headers, active_page='team_stats')

if __name__ == '__main__':
    app.run(debug=True)