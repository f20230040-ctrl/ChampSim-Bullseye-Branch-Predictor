import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def main():
    if not os.path.exists("summary_stats.csv"):
        print("summary_stats.csv not found")
        return
        
    df = pd.read_csv("summary_stats.csv")
    
    # We want to compare policies for every LLC size
    # Let's create a bar chart for average IPC across traces for single-core (16-way)
    
    df_1c = df[(df['Cores'] == 1) & (df['Ways'] == 16)]
    if not df_1c.empty:
        avg_ipc_1c = df_1c.groupby(['Size', 'Policy'])['IPC'].mean().reset_index()
        plt.figure(figsize=(10, 6))
        sns.barplot(data=avg_ipc_1c, x='Size', y='IPC', hue='Policy')
        plt.title('Average IPC vs LLC Size (Single-Core, 16-Way)')
        plt.xlabel('LLC Size (MB)')
        plt.ylabel('Average IPC')
        plt.legend(title='Policy')
        plt.savefig('ipc_single_core.png')
        plt.close()

    # Same for 4-core
    df_4c = df[(df['Cores'] == 4) & (df['Ways'] == 16)]
    if not df_4c.empty:
        avg_ipc_4c = df_4c.groupby(['Size', 'Policy'])['IPC'].mean().reset_index()
        plt.figure(figsize=(10, 6))
        sns.barplot(data=avg_ipc_4c, x='Size', y='IPC', hue='Policy')
        plt.title('Average IPC vs LLC Size (4-Core, 16-Way)')
        plt.xlabel('LLC Size (MB)')
        plt.ylabel('Average IPC')
        plt.legend(title='Policy')
        plt.savefig('ipc_4core.png')
        plt.close()
        
    # Compare 16-way vs 8-way for 2MB
    df_assoc = df[(df['Cores'] == 1) & (df['Size'] == 2)]
    if not df_assoc.empty:
        avg_ipc_assoc = df_assoc.groupby(['Ways', 'Policy'])['IPC'].mean().reset_index()
        plt.figure(figsize=(10, 6))
        sns.barplot(data=avg_ipc_assoc, x='Ways', y='IPC', hue='Policy')
        plt.title('Average IPC vs Associativity (Single-Core, 2MB)')
        plt.xlabel('Associativity (Ways)')
        plt.ylabel('Average IPC')
        plt.legend(title='Policy')
        plt.savefig('ipc_associativity.png')
        plt.close()
        
    print("Generated graphs successfully.")

if __name__ == "__main__":
    main()
