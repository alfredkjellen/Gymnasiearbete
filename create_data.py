import pandas as pd
import math, random, chart_studio
from datetime import timedelta
import plotly.graph_objects as go
from load_competitions import all_competitions
import chart_studio.plotly as py

chart_studio.tools.set_credentials_file(username='alkj', api_key='')


# Metoder för att jämföra två listor
compiled_results_APD = pd.DataFrame() # APD, Average position difference, genomsnittlig positionsdifferens
compiled_results_RBO = pd.DataFrame() # Rank-Biased Overlap 
compiled_results_PPD = pd.DataFrame() # PPD, Percentage position difference, procentuell positionsdifferens

# region A (Kör igenom tävlingar och alla rankingkombinationer)
def run_GA():
 

    for comp in all_competitions:
        # Kör igenom alla klasser från tävlingen. 
        # Input är tävlingsdatan (comp), klassens resultat (ex. comp.h18result) och tillhörande rankingfil på befintliga löpare i respektive klass

        run_all_combinations(comp, comp.h18result, "app/Kopia av ranking_h18.xlsx", "H18")
        run_all_combinations(comp, comp.h20result, "app/Kopia av ranking_h20.xlsx", "H20")
        run_all_combinations(comp, comp.h21result, "app/Kopia av ranking_h21.xlsx", "H21")
        run_all_combinations(comp, comp.d18result, "app/Kopia av ranking_d18-1.xlsx", "D18")
        run_all_combinations(comp, comp.d21result, "app/Kopia av ranking_d21.xlsx", "D21")
        run_all_combinations(comp, comp.d20result, "app/Kopia av ranking_d20.xlsx", "D20")
        print("comp is done")


    # Hantera data ochs skapa figurer
    process_and_create_figure(compiled_results_APD, 'mean_APD', 'mean_APD.xlsx', 'Genomsnittlig positionsdifferens')
    process_and_create_figure(compiled_results_RBO, 'mean_RBO', 'mean_RBO.xlsx', 'Rank-Biased Overlap')
    process_and_create_figure(compiled_results_PPD, 'mean_PPD', 'mean_PPD.xlsx', 'Procentuell positionsdifferens')


def run_all_combinations(comp, comp_result, ranking_file, comp_category):
    
    row = 0
    column_name = comp_category + comp.name
         
    # Loopar igenom alla kombinationer av antal tävlingar räknade en viss period tillbaka i tiden
    for days in range(30,721,30):

        for competitions in range(1,11):

            
            #Baserat på antal "days" och "competitions" skapas en ranking
            predicted_ranking_with_scores = rank_runners_by_average(ranking_file, competitions, days, comp.date, comp_result)
            
            predicted_ranking = list(predicted_ranking_with_scores.keys())

            # Jämför de två listorna med genomsnittlig positionsdifferens
            average_position_difference = calculate_average_position_difference(predicted_ranking, comp_result)    
            
            # Jämför de två listorna med RBO
            rbo_value = rbo(predicted_ranking, comp_result)

            # Jämför de två listorna med procentuell positionsdifferens
            percentage_position_difference = percentage_shifts(predicted_ranking, comp_result)


            # Nästa rad i DataFrame
            row += 1
            
            
            compiled_results_APD.loc[row,'competition'] = competitions
            compiled_results_APD.loc[row,'days'] = days
            compiled_results_APD.loc[row,column_name] = average_position_difference

            compiled_results_RBO.loc[row,'competition'] = competitions
            compiled_results_RBO.loc[row,'days'] = days
            compiled_results_RBO.loc[row,column_name] = rbo_value

            compiled_results_PPD.loc[row,'competition'] = competitions
            compiled_results_PPD.loc[row,'days'] = days
            compiled_results_PPD.loc[row,column_name] = percentage_position_difference

            


# endregion



# region B (Skapa rankinglistor)

# Läser in data, beräknar snittpoäng och rangordnar löparna
def rank_runners_by_average(file_path, x, y, event_date, comp_result):
    all_data = read_excel_sheets(file_path)
    average_scores = calculate_average_ranking(x, y, all_data, event_date, comp_result)
    sorted_scores = dict(sorted(average_scores.items(), key=lambda item: item[1]))    
    return sorted_scores



def calculate_average_ranking(x, y, ranking_data, event_date, comp_result):
    
    end_date = event_date - timedelta(days=y)

    average_rankings = {}

    for runner, data in ranking_data.items():

        if runner in comp_result:
            
            # Konvertera textdatum till datum-objekt
            data.iloc[:, 0] = pd.to_datetime(data.iloc[:, 0])
        
            # Konvertera textvärden i kolumnen till decimaltal
            data.iloc[:, 3] = data.iloc[:, 3].apply(convert_string_to_float)


            filtered_data = data[(data.iloc[:, 0] >= end_date) & (data.iloc[:, 0] < event_date)]

            best_results = filtered_data.sort_values(by=data.columns[3]).head(x)

            ## Om löparen saknar x antal tävlingar läggs n st 300-poängare till
            if len(best_results) < x: 
                missing_competitions = x - len(best_results) 
                extra_data = pd.DataFrame({filtered_data.columns[3]: [300] * missing_competitions})
                best_results = pd.concat([best_results, extra_data], ignore_index=True)
            ##

            avg_score = best_results.iloc[:, 3].mean()
            average_rankings[runner] = avg_score
        

    return average_rankings

# endregion



# region C (Evalueringsmetoder: RBO samt genomsnittlig och procentuell positionsdifferens)

#Beräknar den genomsnittliga positionsdifferensen
def calculate_average_position_difference(listA, listB):
    total_shifts = calculate_shifts(listA, listB)
    return total_shifts / len(listA)


# Beräknar den procentuella positionsidfferensen
def percentage_shifts(listA, listB):
    
    total_shifts = calculate_shifts(listA, listB)
    n = len(listA)

    max_shifts = n * (n-1) /2

    return 1 - total_shifts / max_shifts

# Beräknar positionsdifferensen
def calculate_shifts(listA, listB):
    total_shifts = 0
    for item in listA:
        shift = abs(listA.index(item) - listB.index(item))
        total_shifts += shift
    return total_shifts




# Beräknar RBO
def rbo(S,T, p= 0.9):
    
    k = max(len(S), len(T))
    x_k = len(set(S).intersection(set(T)))
    
    summation_term = 0

    for d in range (1, k+1): 
            set1 = set(S[:d]) if d < len(S) else set(S)
            set2 = set(T[:d]) if d < len(T) else set(T)
            
            x_d = len(set1.intersection(set2))

            a_d = x_d/d   
            
            summation_term = summation_term + math.pow(p, d) * a_d


    rbo_ext = (x_k/k) * math.pow(p, k) + ((1-p)/p * summation_term)

    return rbo_ext

# endregion



# region D (Skapa figur i plotly)
def process_and_create_figure(compiled_results, mean_column_name, excel_filename, plot_title):

    info_columns = compiled_results.iloc[:, :3]
    result_columns = compiled_results.iloc[:, 3:]

    # Beräkna medelvärden
    mean_values = result_columns.mean(axis=1)
    mean_results = info_columns.copy()
    mean_results[mean_column_name] = mean_values

    # Spara till en Excel-fil
    mean_results.to_excel(excel_filename)

    # Skapa en plotly-figur
    create_plotly_figure(mean_results, mean_column_name, plot_title)

 

def create_plotly_figure(results, value, plotly_name):
    fig = go.Figure()

    # Lägg till en linje för varje tävling
    for competition in results['competition'].unique():
        subset = results[results['competition'] == competition]
        fig.add_trace(go.Scatter(x=subset['days'], y=subset[value], mode='lines', name=f'Antal tävlingar räknade {competition}'))

    # Skapa layot
    fig.update_layout(xaxis_title="Tidsomfång (Antal dagar)",  yaxis_title= f"{plotly_name}-värde", title=plotly_name)

    # Spara ner till plotly chart studio
    py.plot(fig, filename=plotly_name, auto_open=True)

#endregion



# region E (Övriga funktioner)
def convert_string_to_float(s):
    if isinstance(s, str):
        return float(s.replace(',', '.'))
    return s

# Läser in alla flikar från en given Excel-fil
def read_excel_sheets(file_path):
    all_sheets = pd.read_excel(file_path, sheet_name=None, header=None)
    return all_sheets
# endregion




#Gymnasiearbetet körs
run_GA()



# region F (Slumpmässiga tester)
def run_random_tests(elements):

    listA = []

    for i in range(elements):
        listA.append(i)


    print(len(listA))

    random_RBO_value = 0
    random_AS_value = 0
    simulations = 10000

    for i in range(simulations):
        
        listB = list(listA)
        random.shuffle(listB)
    
        random_AS_value += calculate_average_position_difference(listA, listB)
        random_RBO_value += rbo(listA, listB)
        
    random_AS_value /= simulations
    random_RBO_value /= simulations

    print("Random AS:", random_AS_value)
    print("Random RBO:", random_RBO_value)


# endregion

