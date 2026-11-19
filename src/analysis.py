from data_loader import load_race

race = load_race(2026, 'Kuala Lumpur')
rc= race["race_control"]

sc=rc[rc["category"]=="SafetyCar"]
print(sc[["lap_number", "message"]])