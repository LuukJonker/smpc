import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("sumTest.csv")

plt.figure(figsize=(10, 6))

# Plot the lines
plt.plot(df['num_parties'], df['reported_execution_time_avg'], label='Reported Execution Time (Avg)', linestyle='-', color='blue')
plt.plot(df['num_parties'], df['total_execution_time_avg'], label='Total Execution Time (Avg)', linestyle='-', color='red')

plt.plot(df['num_parties'], df['reported_CPU_time_avg'], label='Reported CPU Time (Avg)', linestyle='-', color='green')
plt.plot(df['num_parties'], df['total_CPU_time_avg'], label='Total CPU Time (Avg)', linestyle='-', color='orange')

# Add error bars
# plt.errorbar(df['num_parties'], df['reported_execution_time_avg'], yerr=df['reported_execution_time_std'], alpha=0.5, color='blue')
# plt.errorbar(df['num_parties'], df['total_execution_time_avg'], yerr=df['total_execution_time_std'], alpha=0.5, color='red')

plt.xlabel('Number of Parties')
plt.ylabel('Execution Time (seconds)')
plt.title('Execution Time vs Number of Parties')
plt.legend()
plt.grid(True)
plt.show()