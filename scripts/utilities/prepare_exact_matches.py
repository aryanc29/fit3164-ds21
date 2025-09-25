import pandas as pd
import os

in_path = r'd:\FIT3164\data\matches.csv'
out_dir = r'd:\FIT3164\data'
out_path = os.path.join(out_dir, 'matches_exact.csv')

os.makedirs(out_dir, exist_ok=True)

df = pd.read_csv(in_path)
# keep only exact matches
exact = df[df['match_type']=='exact'].copy()
# select/rename columns to match DB schema
# we'll include station_name (bom_name), site, latitude, longitude
exact_out = exact[['bom_name','site','lat','lon']].rename(columns={'bom_name':'station_name','lat':'latitude','lon':'longitude','site':'site_id'})
exact_out.to_csv(out_path, index=False)
print('Wrote', out_path)
print(exact_out.head(20).to_csv(index=False))
