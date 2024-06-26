import pandas as pd
import matplotlib.pyplot as plt


def plot_performance_graph(df, ax, title, plot_wait_time=False):
    # plt.figure(figsize=(10, 6))
    
    # Plot the lines
    ax.plot(df['num_parties'], df['reported_execution_time_avg'], label='Reported Execution Time (Avg)', linestyle='-', color='blue')
    ax.plot(df['num_parties'], df['total_execution_time_avg'], label='Total Execution Time (Avg)', linestyle='-', color='red')
    
    ax.plot(df['num_parties'], df['reported_CPU_time_avg'], label='Reported CPU Time (Avg)', linestyle='-', color='purple')
    ax.plot(df['num_parties'], df['total_CPU_time_avg'], label='Total CPU Time (Avg)', linestyle='-', color='orange')

    ax.xlabel('Number of Parties')
    ax.ylabel('Execution Time (s)')
    
    if plot_wait_time:
        ax.plot(df['num_parties'], df['reported_wait_time_avg'], label="Reported Wait time (Avg)", color='green', linestyle='--')


def plot_sum_overhead(df_sim, df_dist):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))  # Creating a figure with two subplots side by side

    # Plot for df_sim dataframe
    ax1.plot(df_sim['num_parties'], df_sim['reported_execution_time_avg'], label='Reported Execution Time (Avg)', linestyle='-', color='blue')
    ax1.plot(df_sim['num_parties'], df_sim['total_execution_time_avg'], label='Total Execution Time (Avg)', linestyle='-', color='red')
    ax1.plot(df_sim['num_parties'], df_sim['reported_CPU_time_avg'], label='Reported CPU Time (Avg)', linestyle='-', color='purple')
    ax1.plot(df_sim['num_parties'], df_sim['total_CPU_time_avg'], label='Total CPU Time (Avg)', linestyle='-', color='orange')
    ax1.set_xlabel('Number of Parties', fontsize=15)
    ax1.set_ylabel('Execution Time (s)', fontsize=15)
    ax1.set_title('Simulated execution', fontsize=18)
    ax1.legend(fontsize=16)
    ax1.grid(True)

    # Plot for df_dist dataframe
    ax2.plot(df_dist['num_parties'], df_dist['reported_execution_time_avg'], label='Reported Execution Time (Avg)', linestyle='-', color='blue')
    ax2.plot(df_dist['num_parties'], df_dist['total_execution_time_avg'], label='Total Execution Time (Avg)', linestyle='-', color='red')
    ax2.plot(df_dist['num_parties'], df_dist['reported_CPU_time_avg'], label='Reported CPU Time (Avg)', linestyle='-', color='purple')
    ax2.plot(df_dist['num_parties'], df_dist['total_CPU_time_avg'], label='Total CPU Time (Avg)', linestyle='-', color='orange')
    ax2.plot(df_dist['num_parties'], df_dist['reported_wait_time_avg'], label="Reported Wait time (Avg)", color='lime', linestyle='--', dashes=(10, 10))

    ax2.set_xlabel('Number of Parties', fontsize=15)
    ax2.set_ylabel('Execution Time (s)', fontsize=15)
    ax2.set_title('Distributed execution', fontsize=18)
    ax2.legend(fontsize=16)
    ax2.grid(True)

    fig.suptitle("Execution time vs the Number of parties in the summation protocol", fontsize=22)
    plt.tight_layout()  # Ensures labels and titles do not overlap
    plt.show()

def plot_wait_time(df):
    plt.figure(figsize=(10, 6))
    # Add error bars
    plt.plot(df['num_parties'], df['reported_wait_time_avg'], label="Reported Wait time (Avg)", color='purple')
    plt.errorbar(df['num_parties'], df['reported_wait_time_avg'], yerr=df['reported_wait_time_std'], alpha=0.5, color='blue')

    plt.xlabel('Number of Parties')
    plt.ylabel('Wait time (s)')
    plt.title('Wait time vs Number of Parties')
    plt.legend()
    plt.grid(True)
    plt.show()

def sum_stats_plot(df):
    # Create a figure and axis
   fig, ax1 = plt.subplots(figsize=(16,9))
   fig.subplots_adjust(top=0.92)

   font_s = 18
   
   # Plotting latency on the primary y-axis
   ax1.set_xlabel('Number of parties', fontsize=font_s)
   ax1.set_ylim(bottom=0, top=df["reported_execution_time_avg"].max()*1.05)
   ax1.set_ylabel('Reported execution time (s)', color='tab:red', fontsize=font_s)
   ax1.plot(df['num_parties'], df["reported_execution_time_avg"], color='tab:red', label='Exectution time')
   ax1.tick_params(axis='y', labelcolor='tab:red')
   
   ax2 = ax1.twinx()
   ax2.set_ylim(top=int(df["num_send_msgs"].max() * 1.1))
   ax2.set_ylabel('Number of messages', color='tab:blue', fontsize=font_s)
   ax2.plot(df['num_parties'], df["num_send_msgs"], color='tab:blue', label='Number of messages')
   ax2.tick_params(axis='y', labelcolor='tab:blue')
   
   ax3 = ax1.twinx()

   ax3.set_ylim(top=df["num_send_bytes"].max() * 1.2)
   ax3.spines['right'].set_position(('outward', 55))  # Adjust the position of the third y-axis
   ax3.set_ylabel('Number of sent bytes', color='tab:green', fontsize=font_s)
   ax3.plot(df["num_parties"], df['num_send_bytes'], color='tab:green', label='Number of bytes')
   ax3.tick_params(axis='y', labelcolor='tab:green')
   fig.legend(loc='upper left', bbox_to_anchor=(0.15, 0.85), fontsize=16)

   # Set title for the figure
   plt.title('Execution Time, Messages, and Bytes vs Number of Parties', fontsize=24)


   plt.show()


df = pd.read_csv("simulatedSumTest.csv")
sum_stats_plot(df)

# plot_sum_overhead(pd.read_csv("simulatedSumTest.csv"), pd.read_csv("distributedSumTest.csv"))
# plot_performance_graph(pd.read_csv("simulatedSumTest.csv"), "Execution time vs Number of Parties for the simulated sum protocol")
# plot_performance_graph(pd.read_csv("distributedSumTest.csv"), "Execution time vs Number of Parties for the distributed sum protocol", plot_wait_time=True)
# plot_wait_time(pd.read_csv("distributedSumTest.csv"))

