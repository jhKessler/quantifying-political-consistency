from src import config


import pandas as pd

def calc_future_polling_shift(polls: pd.DataFrame) -> pd.Series:
    k = 3
    polls['future_avg'] = polls['polling_percentage'].shift(-3).rolling(window=k).mean()
    polls['future_polling_shift_perc'] = (polls['future_avg'] - polls['polling_percentage']) / polls['polling_percentage'] * 100
    return polls.drop(columns=['future_avg'])    

def load_polls() -> pd.DataFrame:
    polls = pd.read_excel("input/sonntagsfragen.xlsx")[["date"] + [party for party in config.PARTIES]]
    polls["date"] = pd.to_datetime(polls["date"], format="%d.%m.%y")
    polls["month"] = polls["date"].dt.to_period('M')
    polls = polls.groupby("month").mean().reset_index().drop(columns="date").melt(
        id_vars=['month'],
        var_name='party',
        value_name='polling_percentage'
    )
    result = polls.groupby("party", group_keys=False).apply(calc_future_polling_shift)
    polls = polls.merge(result[['future_polling_shift_perc']], left_index=True, right_index=True)
    return polls
