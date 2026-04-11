# Created by Gemini to fetch and process OECD education funding data for the US and other countries, then export to CSV for visualization.

import pandas as pd
import requests
import io
import pycountry

print("Initiating global API request to OECD SDMX servers...")

# 1. The Global API Endpoint
# Notice the 'all' keyword in the first slot. This requests every available country.
url = "https://sdmx.oecd.org/public/rest/data/OECD.EDU.IMEP,DSD_EAG_UOE_FIN@DF_UOE_FIN_INDIC_SOURCE_NATURE,3.1/.EXP.ISCED11_1T8.S1311+S1312+S1313.INST_EDU.DIR_EXP.V.XDC.SOURCE?startPeriod=2019&endPeriod=2022"
headers = {'Accept': 'application/vnd.sdmx.data+csv; charset=utf-8'}
response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(f"API Error: {response.status_code}")
    exit()

# 2. Load API response directly into Pandas
df = pd.read_csv(io.StringIO(response.text))
print(f"Successfully fetched {len(df)} rows from the API.")

# 3. Find the most recent reporting year for EACH country
idx = df.groupby('REF_AREA')['TIME_PERIOD'].idxmax()
latest_data = df.loc[idx][['REF_AREA', 'TIME_PERIOD']]
df = pd.merge(df, latest_data, on=['REF_AREA', 'TIME_PERIOD'])

# 4. Pivot the data
pivot_df = df.pivot_table(
    index='REF_AREA', 
    columns='EXP_SOURCE', 
    values='OBS_VALUE', 
    aggfunc='sum'
).fillna(0)

pivot_df['local_raw'] = pivot_df.get('S1312', 0) + pivot_df.get('S1313', 0)
pivot_df['central_raw'] = pivot_df.get('S1311', 0)

# 5. Calculate percentages
pivot_df['total'] = pivot_df['local_raw'] + pivot_df['central_raw']
pivot_df = pivot_df[pivot_df['total'] > 0] 

pivot_df['central'] = ((pivot_df['central_raw'] / pivot_df['total']) * 100).round(1)
pivot_df['local'] = ((pivot_df['local_raw'] / pivot_df['total']) * 100).round(1)

# 6. Map OECD 3-letter codes to full country names
def get_country_name(alpha_3):
    try:
        return pycountry.countries.get(alpha_3=alpha_3).name
    except AttributeError:
        # Returns None for non-country aggregates like "EU25" or "OECD Average"
        return None

final_df = pivot_df[['central', 'local']].reset_index()
final_df['country'] = final_df['REF_AREA'].apply(get_country_name)

# Drop any rows that were regional aggregates rather than real countries
final_df = final_df.dropna(subset=['country'])

# 7. Sort logically (US at the top to anchor the narrative, then by local funding)
final_df['sort_val'] = final_df.apply(lambda x: -1 if x['country'] == 'United States' else x['local'], axis=1)
final_df = final_df.sort_values('sort_val').drop('sort_val', axis=1)
final_df = final_df[['country', 'central', 'local']]

# 8. Export
export_path = 'static/data/school_funding.csv' 
final_df.to_csv(export_path, index=False)

print(f"\n--- Processed data for {len(final_df)} countries ---")
print(final_df.head(15))
print(f"\nSuccess! Global dataset saved to '{export_path}'.")