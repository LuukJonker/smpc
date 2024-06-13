import pandas as pd
import matplotlib.pyplot as plt


def plot_performance_graph(df):
    plt.figure(figsize=(10, 6))
    
    # Plot the lines
    plt.plot(df['num_parties'], df['reported_execution_time_avg'], label='Reported Execution Time (Avg)', linestyle='-', color='blue')
    plt.plot(df['num_parties'], df['total_execution_time_avg'], label='Total Execution Time (Avg)', linestyle='-', color='red')
    
    plt.plot(df['num_parties'], df['reported_CPU_time_avg'], label='Reported CPU Time (Avg)', linestyle='-', color='green')
    plt.plot(df['num_parties'], df['total_CPU_time_avg'], label='Total CPU Time (Avg)', linestyle='-', color='orange')
    
    
    plt.xlabel('Number of Parties')
    plt.ylabel('Execution Time (seconds)')
    plt.title('Execution Time vs Number of Parties')
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_wait_time(df):
    plt.figure(figsize=(10, 6))
    # Add error bars
    plt.plot(df['num_parties'], df['reported_wait_time_avg'], label="Reported Wait time (Avg)", color='purple')
    plt.errorbar(df['num_parties'], df['reported_wait_time_avg'], yerr=df['reported_wait_time_std'], alpha=0.5, color='blue')

    plt.xlabel('Number of Parties')
    plt.ylabel('Wait time (seconds)')
    plt.title('Wait time vs Number of Parties')
    plt.legend()
    plt.grid(True)
    plt.show()

# plot_performance_graph(pd.read_csv("simulatedSumTest.csv"))
plot_performance_graph(pd.read_csv("distributedSumTest.csv"))
plot_wait_time(pd.read_csv("distributedSumTest.csv"))
