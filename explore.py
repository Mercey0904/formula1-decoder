import requests
import pandas as pd

BASE_URL = "https://api.openf1.org/v1"


def get_data(endpoint, **params):
    """Fetch data from an OpenF1 endpoint and return it as a DataFrame."""
    response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=30)
    response.raise_for_status()  # stop with a clear error if the request failed
    return pd.DataFrame(response.json())

pd.set_option('display.max_columns', None)   # show every column
pd.set_option('display.width', 200)          # allow wider lines before wrapping
pd.set_option('display.max_colwidth', None)  # don't cut off long text like 'message'



# 1. Find the 2024 Emilia Romagna Grand Prix race session (Imola)
# Italy hosted two races in 2024 (Imola and Monza), so pick Imola by name instead of by position
sessions = get_data("sessions", year=2024, country_name="Italy", session_name="Race")
print(sessions[["session_key", "location", "date_start"]])

session_key = sessions.loc[sessions['location']=='Imola', 'session_key'].iloc[0]

# 2. Get every lap and every tyre stint, pitting information, race conditions and the final result in that race
laps = get_data("laps", session_key=session_key)
stints = get_data("stints", session_key=session_key)
race_control = get_data("race_control", session_key=session_key)
pit= get_data("pit", session_key=session_key)
result = get_data("session_result", session_key=session_key)

print(laps[["driver_number", "lap_number", "lap_duration", "is_pit_out_lap"]].head(20))
print(stints[["driver_number", "stint_number", "compound", "lap_start", "lap_end"]].head(20))


#Practice
#1. Getting number of laps each driver complete
# a driver who retires gets a row for the lap they didn't finish (their last lap, with no time), so drop it before counting
# don't drop every lap with no time: lap 1 is sometimes missing a time even though it was completed
last_lap = laps.groupby('driver_number')['lap_number'].transform('max')
unfinished = (laps['lap_number']==last_lap) & laps['lap_duration'].isna()
laps_each_driver = laps[~unfinished].groupby('driver_number').size().reset_index(name="laps_completed")
print(laps_each_driver)


#2. Get what type of tyres did driver 16 use
tyre_type = stints.loc[stints['driver_number']==16, 'compound']
print (tyre_type)


#3. Which laps are usually slow and why
# We need to define what lap is considered as slow. Assuming the median lap duration exceeding 7% (107%) marked as slow
# But we need to drop laps with no time first (unfinished laps, sometimes lap 1)
laps = laps.dropna(subset=['lap_duration'])
driver_median= laps.groupby('driver_number')['lap_duration'].transform('median')
laps['slow']=laps['lap_duration']>driver_median *1.07

slow_laps= laps[laps['slow']]
print ('Slow Laps:')
print (slow_laps[['driver_number', 'lap_number', 'lap_duration']])

#Get the why. Later rules overwrite earlier ones, so the most specific rule goes last
#safety car
laps['reason']=''
sc_laps = race_control.loc[race_control['category']=='SafetyCar', 'lap_number']
laps.loc[laps['lap_number'].isin(sc_laps), 'reason'] = 'safety car'

#race start (standing start + first-lap traffic)
laps.loc[laps['lap_number']==1, 'reason'] = 'race start'

#pitting (the pit endpoint records the lap the driver came in)
pit_in = pit[['driver_number', 'lap_number']].assign(pit_in=True)
laps=laps.merge(pit_in, on=['driver_number', 'lap_number'], how='left')
laps.loc[laps['pit_in']==True, 'reason'] = 'pitting in lap'

#exiting pit
laps.loc[laps['is_pit_out_lap']==True, 'reason']='pitting out lap'

#retirement (official DNF from the race result, on the driver's last timed lap)
dnf_drivers = result.loc[result['dnf']==True, 'driver_number']
last_lap = laps.groupby('driver_number')['lap_number'].transform('max')
laps.loc[laps['driver_number'].isin(dnf_drivers) & (laps['lap_number']==last_lap), 'reason'] = 'retirement'

print ('Slow laps with reason:')
print(laps.loc[laps['slow'],['driver_number', 'lap_number', 'lap_duration', 'reason']])

#exception: slow laps none of the rules explain, check race control messages for these laps
unexplained = laps.loc[laps['slow'] & (laps['reason']==''), ['driver_number', 'lap_number', 'lap_duration']]
print ('Slow laps with no reason yet:')
print (unexplained)


print ("2022 Hungary Race:")
sessions = get_data("sessions", year=2024, country_name="Hungary", session_name="Race")
print(sessions[["session_key", "location", "date_start"]])

