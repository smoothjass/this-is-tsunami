import pandas
import pandas as pd

df = pd.read_csv("mapReduceTemp.csv")

# Create a complete grid of 'x' and 'y' values
complete_grid = pd.DataFrame([(i, j) for i in range(19) for j in range(19)], columns=['x', 'y'])

# Merge the complete grid with the original DataFrame to fill missing values
merged_df = pd.merge(complete_grid, df, on=['x', 'y'], how='left')

# Fill NaN values with 0 for 'quakes' and 'tsunamis'
merged_df[['quakes', 'tsunamis']] = merged_df[['quakes', 'tsunamis']].fillna(0)

merged_df['quakes'] = merged_df['quakes'].astype(int)
merged_df['tsunamis'] = merged_df['tsunamis'].astype(int)

merged_df.to_csv("mapReduce.csv", index=False)