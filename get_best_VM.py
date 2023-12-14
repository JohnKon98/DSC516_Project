import json
import os
import pandas as pd
import optuna
import sys

def load_scout_dataset():
    osr_single_node_directory = 'osr_single_node'

    json_data = []
    csv_data = []

    for config_folder in os.listdir(osr_single_node_directory):
        config_folder_path = os.path.join(osr_single_node_directory, config_folder)
        

        if os.path.isdir(config_folder_path):
            json_files = [file for file in os.listdir(config_folder_path) if file.endswith('.json')]
            for file_name in json_files:
                file_path = os.path.join(config_folder_path, file_name)
                with open(file_path, 'r') as json_file:
                    data = json.load(json_file)
                    data['Configuration'] = config_folder # Adding in the json dataframe the name of the directory
                    json_data.append(data)
            
            
            csv_files = [file for file in os.listdir(config_folder_path) if file.endswith('.csv')]
            for file_name in csv_files:
                file_path = os.path.join(config_folder_path, file_name)
                df = pd.read_csv(file_path)
                df['Configuration'] = config_folder # Adding in the csv dataframe the name of the directory
                
                df = df.dropna(axis=1, how='all')
                csv_data.append(df)

    json_df = pd.DataFrame(json_data)
    csv_df = pd.concat(csv_data, ignore_index=True)

    #Here manually creating the VM prices in order to inject them in the dataframe
    vm_prices = {
    'c3.2xlarge' : 0.42,
    'c3.large' : 0.11,
    'c3.xlarge' : 0.21,
    'c4.2xlarge' : 0.40,
    'c4.large' : 0.10,
    'c4.xlarge' : 0.20,
    'm3.2xlarge' : 0.53,
    'm3.large' : 0.13,
    'm3.xlarge' : 0.27,
    'm4.2xlarge' : 0.40,
    'm4.large' : 0.10,
    'm4.xlarge' : 0.20,
    'r3.2xlarge' : 0.67,
    'r3.large' : 0.17,
    'r3.xlarge' : 0.33,
    'r4.2xlarge' : 0.53,
    'r4.large' : 0.13,
    'r4.xlarge' : 0.27
    }

    prices_df = pd.DataFrame(list(vm_prices.items()),columns=['VM_Type','Price'])


    merged_data = pd.merge(json_df, csv_df, on='Configuration') # Here we merge the two dataframes based on the Configuration

    merged_data[['VM_Type','Instance','Workload','Framework','Size','Iteration']] = merged_data['Configuration'].str.split('_',expand=True) # We split the Configuration Column to the different information it gives

    merged_data_with_prices = pd.merge(merged_data,prices_df,on='VM_Type') # Here we merge the dataframe with the prices of each VM Type

    return merged_data_with_prices


def objective(trial):

    vm_type = trial.suggest_categorical('vm_type', ['c3.2xlarge', 'c3.large', 'c3.xlarge', 'c4.2xlarge', 'c4.large', 'c4.xlarge', 'm3.2xlarge', 'm3.large', 'm3.xlarge', 'm4.2xlarge', 'm4.large', 'm4.xlarge', 'r3.2xlarge', 'r3.large', 'r3.xlarge', 'r4.2xlarge', 'r4.large', 'r4.xlarge'])  # Replace with actual VM types
    #vm_quantity = trial.suggest_int('vm_quantity', 1, 10)  # Adjust range based on your requirements
 
    def simulate_workload(vm_type, workload):

        filtered_data = scout_data[(scout_data['VM_Type'] == vm_type) & (scout_data['Workload'] == workload)] # Filter the data based on the VM Type and workload

        execution_time = filtered_data['elapsed_time'].max() 
        cost = filtered_data['Price'].max()
        execution_by_minute = execution_time / 60;
        execution_by_hour = execution_by_minute / 60;
        cost_by_execution_time = cost * execution_by_hour
        return execution_time, cost_by_execution_time
    
    current_execution_time, cost_by_execution_time = simulate_workload(vm_type,sys.argv[1])    


    direction = 'minimize'
    if direction == 'minimize':
       if sys.argv[2] == '1':
           return cost_by_execution_time
       elif sys.argv[2] == '2':
           return current_execution_time
    else:
       if sys.argv[2] == '1':
           return cost_by_execution_time
       elif sys.argv[2] == '2':
           return current_execution_time




scout_data = load_scout_dataset()
scout_data['elapsed_time'] = pd.to_numeric(scout_data['elapsed_time'])


study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=50)



best_params = study.best_params
best_values = study.best_value

print(f"for workload: {sys.argv[1]} Best parameters: {best_params} Best values: {best_values}")

