import os

api_key = os.environ['api_key']
api_secret = os.environ['api_secret']
#from config.py import *
import requests
import json
import numpy as np

from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

import pandas as pd
import datetime as dt
import time
import pandas_ta as ta
import warnings
import datetime
from colorama import init, Fore
import array as t  #für 60sec array

warnings.simplefilter(action='ignore',category=FutureWarning)  # das blendet Pandas append fehler aus

#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
scharf = True  #Client orders sind scharf geschalten. Für nur gucken auf False setzen!
bought = None  #wird nun berechnet
interval = "1m"
Coin = "MLN"
coinlenght=len(Coin)
Stablecoin = "USDT"
SYMBOL0 = Coin + Stablecoin
SYMBOL1 = "BTC" + Stablecoin
SYMBOL2 = Coin + "BTC"
LIMIT = "1000"  # taking xxx candles as limit
OFFCUT = 800  #kerzen Abschnitt
Wiedereinstiegsfaktor = 0.996
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------

sell_level_xxl = 0 #wird alles berechnet
sell_level_slow = 0
sell_level_fast = 0
buy_level_xxl = 0
buy_level_slow = 0
buy_level_fast = 0
last_buy_sy0 = 0 #wird nun automatisch aus letzem Trade extrahiert
last_sell_sy0 = 0 #wird nun automatisch aus letzem Trade extrahiert
Wiedereinstiegskurs = 0 #wird nun berechnet mit last_sell_sy0 * Wiedereinstiegsfaktor

last_calc = 0


if interval == "1s":
    fast_sma = round(int(LIMIT) * 0.04)  #0,8min
    slow_sma = round(int(LIMIT) * 0.25)  #4,15 min
    xxl_sma = round(int(LIMIT) * 0.5)  #8,3min
else:
    
    fast_sma = round(int(LIMIT) * 0.04)  #0,8min
    slow_sma = round(int(LIMIT) * 0.25)  #4,15 min
    xxl_sma = round(int(LIMIT) * 0.5)  #8,3min

symbol0_price = 0
symbol1_price = 0
symbol2_price = 0

startzeit = None
gewinn = None
QNTY = None

Coin_price = None
Coin_free = None
Coin_locked = None

Stablecoin_price = None
Stablecoin_free = None
Stablecoin_locked = None

last_ema_fast = None
last_ema_slow = None
ema_diff = None

margin_min = 0
margin_max = 0
margin_diff = 0
margin_aktuell_zu_slow = None
margin_aktuell_zu_fast = None
margin_aktuell_zu_xxl = None
profit_since_buy_sy0 = None
drop_since_sell_sy0 = None

m_fast_min = None
m_fast_max = None
m_slow_min = None
m_slow_max = None
m_xxl_min = None
m_xxl_max = None

SecondsSinceBuy = 0
SecondsSinceSell = 0

client = Client(api_key, api_secret)


def get_wallet_info():
    global bought
    global Coin_free
    global Coin_locked
    global Stablecoin_free
    global Stablecoin_locked

    get_my_last_trades()
    try:

        client = Client(api_key, api_secret)

        Coin_record = (client.get_asset_balance(asset=Coin))
        Coin_free = int(float(Coin_record['free']) *
                        1000) / 1000.0  #begrenzung auf 3 Kommastellen
        Coin_locked = int(float(Coin_record['locked']) *
                          1000) / 1000.0  #begrenzung auf 3 Kommastellen

        Stablecoin_record = (client.get_asset_balance(asset=Stablecoin))
        Stablecoin_free = int(float(Stablecoin_record['free']) *
                              1000) / 1000.0  #begrenzung auf 3 Kommastellen
        Stablecoin_locked = int(float(Stablecoin_record['locked']) *
                                1000) / 0100.0  #begrenzung auf 3 Kommastellen

    except:
        pass

    with open(('protocols/' + SYMBOL0 + str(filezeit) + '.txt'), 'a+') as file:
        file.write
        (Coin + "-free " + str(Coin_free) + Coin + "-locked" +
         str(Coin_locked) + Stablecoin + "-free " + str(Stablecoin_free) +
         Stablecoin + "-locked" + str(Stablecoin_locked) + '\n')

    if (Stablecoin_free > 10) and (Coin_free < 1): bought = False
    elif (Stablecoin_free < 1) and (Coin_free > 1): bought = True


def get_my_last_trades():
    global last_buy_sy0
    global last_sell_sy0
    global bought
    global SecondsSinceBuy
    global SecondsSinceSell
    global Wiedereinstiegskurs

    trade_record = []
    try:
        trade_record = client.get_my_trades(symbol=SYMBOL0, limit=1)
        #print(trade_record)
    except:
        pass

    if str(trade_record[0]['isBuyer']) == "True":
        last_buy_sy0 =float(trade_record[0]['price'])
        Kaufzeit = trade_record[0]['time']
        Sellzeit = 0
        bought = True
        
    else:
        last_sell_sy0 = float(trade_record[0]['price'])
        Sellzeit = trade_record[0]['time']
        bought = False
        Kaufzeit =0
        Wiedereinstiegskurs = last_sell_sy0 * Wiedereinstiegsfaktor
        
    #print(bought)
    SecondsSinceBuy = (int(time.time()) - int(Kaufzeit/1000))
    SecondsSinceSell = (int(time.time()) - int(Sellzeit/1000))

    if SecondsSinceBuy > 100000000:
        SecondsSinceBuy = SecondsSinceSell
    else:
        SecondsSinceSell = SecondsSinceBuy
           
    #print(last_buy_sy0)
    #print(SeccondsSinceBuy)
    #print(last_sell_sy0)
    #print(SecondsSinceSell)
    #breakpoint()
    

def get_avg_price():
    global symbol0_price
    global symbol1_price
    global symbol2_price
    symbole = '["' + SYMBOL0 + '","' + SYMBOL1 + '","' + SYMBOL2 + '"]'
    try:
        ticker_info_dict = client.get_ticker(symbols=symbole)
    except:
        pass
    prices = {item['symbol']: item['lastPrice'] for item in ticker_info_dict}
    symbol0_price = float(prices[SYMBOL0])
    symbol1_price = float(prices[SYMBOL1])
    symbol2_price = float(prices[SYMBOL2])
    #print(symbol0_price)
    #print(symbol1_price)
    #print(symbol2_price)
    #breakpoint()

def get_actual_price():
    global symbol0_price
    global data
    global last_ema_fast
    global last_ema_slow
    global last_ema_xxl
    global margin_min
    global margin_max
    global margin_diff
    global ema_diff
    global last_signal
    global last_trade
    global margin_aktuell_zu_slow
    global margin_aktuell_zu_fast
    global margin_aktuell_zu_xxl
    global profit_since_buy_sy0
    global drop_since_sell_sy0

    try:  #lese nur letzte Kerze
        letzte_kerze = pd.DataFrame(
            client.get_klines(symbol=SYMBOL0, interval=interval, limit=2))
    except:
        plt.pause(5)
        letzte_kerze = pd.DataFrame(
            client.get_klines(symbol=SYMBOL0, interval=interval, limit=2))
        pass

    letzte_kerze.columns = [
        'datetime', 'open', 'high', 'low', 'close', 'volume', 'close_time',
        'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'trade'
    ]

    letzte_kerze = letzte_kerze.astype(float)

    #print (data)
    #print (letzte_kerze)
    data = data.astype(float)

    a = int((data.iloc[-1]['datetime']))  #Zeitstempel der letzen Kerze
    b = int((letzte_kerze.iloc[-2]['datetime']))  #vorletzter Zeitstempel
    c = int((letzte_kerze.iloc[-1]['datetime']))  #aktueller Zeitstempel

    if interval == "1s":
        zaehler = 1_000
    elif interval == "1m":
        zaehler = 60_000
    elif interval == "3m":
        zaehler = 1_800_000
    elif interval == "5m":
        zaehler = 3_000_000
    elif interval == "15m":
        zaehler = 15_000_000
    elif interval == "30m":
        zaehler = 30_000_000
    elif interval == "1h":
        zaehler = 60_000_000
    elif interval == "2h":
        zaehler = 120_000_000
    elif interval == "4h":
        zaehler = 240_000_000
    elif interval == "6h":
        zaehler = 360_000_000
    elif interval == "8h":
        zaehler = 480_000_000
    elif interval == "12h":
        zaehler = 720_000_000
    elif interval == "1D":
        zaehler = 1_440_000_000
    elif interval == "2D":
        zaehler = 2_880_000_000
    elif interval == "3D":
        zaehler = 4_320_000_000
    elif interval == "1w":
        zaehler = 10_080_000_000
    elif interval == "1M":
        zaehler = 40_320_000_000

    if (a - c) == 0:  #Kerzenwechsel nicht erkannt
        data = data[:-1]  #lösche letzte 1 Zeile
        data = data.append(letzte_kerze.iloc[-1],
                           ignore_index=True)  #appende letzte Kerze

    else:  #Kerzenwechsel erkannt, 2 Zeilen austauschen
        data.drop([0], inplace=True)  #lösche aber die erste Zeile
        data = data[:-1]  #lösche die letzte raus
        data = data.append(letzte_kerze, ignore_index=True)  #appende 2 Kerzen
        get_wallet_info()

    data.ta.ema(length=fast_sma, append=True)
    data.ta.ema(length=slow_sma, append=True)
    data.ta.ema(length=xxl_sma, append=True)
    data.ta.kdj(append=True, length=int(LIMIT) - 200)
    data.ta.bbands(ddof=0,append=True)  #using pandas_ta to calculate Bollinger bands
    data.ta.macd(append=True) #using pandas_ta to calculate Bollinger bands
    data["jk_diff"] = data['J_800_3'] - data['K_800_3']
    data['signal_jk']   = np.where((data['K_800_3']+0)      < (data['J_800_3']+0),        -1.0, -1.5)
    data['signal_MACDs'] = np.where((data['MACD_12_26_9']+0) > (data['MACDs_12_26_9']+0),  -2.0, -2.5)
    #data['signal_MACDh'] = np.where((data['MACD_12_26_9']+0) > (data['MACDh_12_26_9']+0),  -3.0, -3.5)
    data['signal_BBlow'] = np.where((data['low']+0) < (data['BBL_5_2.0']+0.01),  -4.0, -4.5)
    data['signal_BBhigh'] = np.where((data['high']+0) > (data['BBU_5_2.0']-0.02),  -5.0, -5.5)
    #data['signal_BB']   = np.where(((data['BBU_5_2.0']+0) - (data['BBL_5_2.0']+0)) < 0,   -3.0, -3.5)
    
    data['Kaufssignal'] = 0
    data['Verkaufssignal'] = 0
    data.loc[(data['signal_BBlow'].shift(1) == -4.5) & (data['signal_BBlow'] == -4), 'Kaufssignal'] = 1
    data.loc[(data['signal_BBhigh'].shift(1) == -5.5) & (data['signal_BBhigh'] == -5), 'Verkaufssignal'] = -1
    data['Tradesignal'] = (data['Kaufssignal'] + data['Verkaufssignal'])
    
    #data['trade'] = data["signal"].diff()

    data['margin_fast'] = (((data['close'] / data['EMA_' + str(fast_sma)]) * 100) - 100)
    data['margin_slow'] = (((data['close'] / data['EMA_' + str(slow_sma)]) * 100) - 100)
    data['margin_xxl'] = (((data['close'] / data['EMA_' + str(xxl_sma)]) * 100) - 100)
    

    last_ema_fast = float(data.iloc[-1]['EMA_' + str(fast_sma)])
    last_ema_slow = float(data.iloc[-1]['EMA_' + str(slow_sma)])
    last_ema_xxl = float(data.iloc[-1]['EMA_' + str(xxl_sma)])

    ema_diff = data.iloc[-1]['jk_diff']
    #symbol0_price = data.iloc[-1]['close']

    margin_aktuell_zu_slow = (((symbol0_price) / last_ema_slow) * 100) - 100
    margin_aktuell_zu_fast = (((symbol0_price) / last_ema_fast) * 100) - 100
    margin_aktuell_zu_xxl = (((symbol0_price) / last_ema_xxl) * 100) - 100

    if last_buy_sy0 > 0:
        profit_since_buy_sy0 = ((symbol0_price / last_buy_sy0) * 100) - 100
    else:
        profit_since_buy_sy0 = ((symbol0_price / last_sell_sy0) * 100) - 100
        
    if last_sell_sy0 > 0:
        drop_since_sell_sy0 = -((last_sell_sy0 / symbol0_price) - 1) * 100
    else:
        drop_since_sell_sy0 = 0
        profit_since_buy_sy0 = ((symbol0_price / last_buy_sy0) * 100) - 100

    #print (last_signal)
    #print (last_ema10)
    #print (last_ema50)
    #print (ema_diff)


def get_klines_erstbefuellung():
    global last_signal
    global last_trade
    global last_ema_fast
    global last_ema_slow
    global last_ema_xxl
    global ema_diff
    global data
    global symbol0_price

    try:
        data = pd.DataFrame(
            client.get_klines(symbol=SYMBOL0, interval=interval, limit=LIMIT))
    except:
        plt.pause(5)
        data = pd.DataFrame(
            client.get_klines(symbol=SYMBOL0, interval=interval, limit=LIMIT))
        pass

    data.columns = [
        'datetime', 'open', 'high', 'low', 'close', 'volume', 'close_time',
        'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'trade'
    ]

    data = data.astype(float)
    data.ta.ema(length=fast_sma, append=True)
    data.ta.ema(length=slow_sma, append=True)
    data.ta.ema(length=xxl_sma, append=True)
    data.ta.kdj(append=True, length=int(LIMIT) - 200)
    data.ta.bbands(ddof=0, append=True)  #using pandas_ta to calculate Bollinger bands
    data.ta.macd(append=True) #using pandas_ta to calculate Bollinger bands
    data["jk_diff"] = data['J_800_3'] - data['K_800_3']
    data['signal_jk'] = np.where((data['K_800_3']+0) < (data['J_800_3']+0), -1.0, -1.5)
    data['signal_MACDs'] = np.where((data['MACD_12_26_9']+0) > (data['MACDs_12_26_9']+0),  -2.0, -2.5)
    #data['signal_MACDh'] = np.where((data['MACD_12_26_9']+0) > (data['MACDh_12_26_9']+0),  -3.0, -3.5)
    data['signal_BBlow'] = np.where((data['low']+0) < (data['BBL_5_2.0']+0.01),  -4.0, -4.5)
    data['signal_BBhigh'] = np.where((data['high']+0) > (data['BBU_5_2.0']-0.02),  -5.0, -5.5)
    data['Kaufssignal'] = 0
    data['Verkaufssignal'] = 0
    
    data.loc[(data['signal_BBlow'].shift(1) == -4.5) & (data['signal_BBlow'] == -4), 'Kaufssignal'] = 1
    data.loc[(data['signal_BBhigh'].shift(1) == -5.5) & (data['signal_BBhigh'] == -5), 'Verkaufssignal'] = -1
    data['Tradesignal'] = data['Kaufssignal'] + data['Verkaufssignal']
    #data['trade'] = data["signal"].diff()

  
    data['margin_fast'] = (((data['close'] / data['EMA_' + str(fast_sma)]) * 100) - 100)
    data['margin_slow'] = (((data['close'] / data['EMA_' + str(slow_sma)]) * 100) - 100)
    data['margin_xxl'] = (((data['close'] / data['EMA_' + str(xxl_sma)]) * 100) - 100)

    #print (data)
    symbol0_price = (data.iloc[-1]['close'])
    last_ema_fast = float(data.iloc[-1]['EMA_' + str(fast_sma)])
    last_ema_slow = float(data.iloc[-1]['EMA_' + str(slow_sma)])
    last_ema_xxl = float(data.iloc[-1]['EMA_' + str(xxl_sma)])


def plot_klines():
    global margin_aktuell_zu_slow
    global margin_aktuell_zu_fast
    global margin_aktuell_zu_xxl
    global symbol0_price
    global last_ema_xxl
    global symbol0_price
    global symbol1_price
    global symbol2_price
    global margin_max
    
        
    df = data.copy()
       
    df['x'] = [dt.datetime.fromtimestamp(x / 1000.0) for x in df.datetime]
    df.drop(df.index[0:OFFCUT], inplace=True)
    plt.clf()
    
    plt.subplot(211)
    plt.tight_layout()
    plt.rc('font', size=7)
    plt.grid(True)
    plt.title(str(symbol0_price) + '=' + SYMBOL0 + ' ' + str(symbol1_price)[:8] +'=' + SYMBOL1 + ' ' + str(symbol2_price)[:8] + '=' + SYMBOL2)
    plt.xlabel(str(int(LIMIT) - OFFCUT) + " klines" + ' a ' + interval)
    #plt.ylabel('price', fontsize=10)

    plt.plot(df["x"], df['EMA_' + str(fast_sma)], linewidth=1, color='red',    linestyle='-' )
    plt.plot(df["x"], df['EMA_' + str(slow_sma)], linewidth=1, color='blue',   linestyle='-' )
    plt.plot(df["x"], df['EMA_' + str(xxl_sma)],  linewidth=1, color='black',  linestyle='-' )
    plt.plot(df["x"], df["high"],                 linewidth=2, color='green',  linestyle='-' )
    plt.plot(df["x"], df["low"],                  linewidth=2, color='magenta',linestyle='-' )
    plt.plot(df["x"], df['BBU_5_2.0'],            linewidth=1, color='black',  linestyle='--')
    plt.plot(df["x"], df['BBL_5_2.0'],            linewidth=1, color='black',  linestyle='--')
    #plt.plot(df["x"], df['BBM_5_2.0'],           linewidth=1,color='black',linestyle='--')
    #plt.scatter(100, last_buy_sy0, s=100)
        
    plt.legend(title=time.strftime('%H:%M:%S'), labels=[
                   "EMA_"  + str(fast_sma) + "=" + str(last_ema_fast)[:7],
                   "EMA_"  + str(slow_sma) + "=" + str(last_ema_slow)[:7],
                   "xxl_"  + str(xxl_sma) + "=" + str(last_ema_xxl)[:7],
                   "high=" + str(float(df.iloc[-1]['high']))[:7],
                   "low="  + str(float(df.iloc[-1]['low']))[:7],
                   "BBH="  + str(float(df.iloc[-3]['BBU_5_2.0']))[:7],
                   "BBL="  + str(float(df.iloc[-3]['BBL_5_2.0']))[:7]])


    plt.subplot(212)
    plt.grid(True)
    plt.tight_layout()

    kj_diff_divisor = df['jk_diff'].max()      / df['margin_xxl'].max()
    MACD_div =        df['MACD_12_26_9'].max() / df['margin_xxl'].max() 
        
    plt.plot(df["x"], df['margin_slow'],            linewidth=1, color='blue',   linestyle='-')
    plt.plot(df["x"], df['margin_fast'],            linewidth=1, color='red',    linestyle='-')
    plt.plot(df["x"], df['margin_xxl'],             linewidth=1, color='black',  linestyle='-')
    plt.plot(df["x"], df['MACD_12_26_9']/MACD_div,  linewidth=1, color='red',    linestyle='--')
    plt.plot(df["x"], df['MACDh_12_26_9']/MACD_div, linewidth=1, color='black',  linestyle='--')
    plt.plot(df["x"], df['MACDs_12_26_9']/MACD_div, linewidth=1, color='blue',   linestyle='--')
    plt.plot(df["x"], df['jk_diff']/kj_diff_divisor,linewidth=1, color='magenta',linestyle='-')
    plt.plot(df["x"], df['signal_jk']              ,linewidth=1, color='blue',   linestyle='-')
    plt.plot(df["x"], df['signal_MACDs']           ,linewidth=1, color='blue',   linestyle='-')
    
    plt.plot(df["x"], df['signal_BBhigh']          ,linewidth=2, color='red',   linestyle='-')
    plt.plot(df["x"], df['signal_BBlow']           ,linewidth=2, color='green',   linestyle='-')
    #plt.plot(df["x"], df['Kaufssignal']             ,linewidth=2, color='red',   linestyle='-')
    #plt.plot(df["x"], df['Verkaufssignal']          ,linewidth=2, color='green',   linestyle='-')
    #plt.plot(df["x"], df['Tradesignal']             ,linewidth=3, color='black',   linestyle='-')

       
       
    
    plt.legend(title=('P&L='+ str(profit_since_buy_sy0)[:6] + '%'), labels=[
        'margin slow=   ' + str(margin_aktuell_zu_slow)[:6],
        'margin fast=   ' + str(margin_aktuell_zu_fast)[:6],
        'margin xxl=    ' + str(margin_aktuell_zu_xxl)[:6],
        'MACD_12_26_9=  ' + str(float(df.iloc[-1]['MACD_12_26_9']))[:6],
        'MACDh_12_26_9= ' + str(float(df.iloc[-1]['MACDh_12_26_9']))[:6],
        'MACDs_12_26_9= ' + str(float(df.iloc[-1]['MACDs_12_26_9']))[:6],
        'jk-diff=       ' + str(ema_diff)[:6]])

    #plt.plot(df["x"], df['J_800_3'],linewidth=1,color='black',linestyle='--')
    #plt.plot(df["x"], df['K_800_3'],linewidth=1,color='blue',linestyle='--')
    #plt.plot(df["x"], df['D_800_3'],linewidth=1,color='red',linestyle='--')

        
    plt.show(block=False)


def write_record():
    global filezeit
    global bought
    global symbol0_price
    global last_buy_sy0
    global profit_since_buy_sy0
    global margin_aktuell_zu_slow
    global margin_aktuell_zu_fast

    with open(('protocols/' + SYMBOL0 + str(filezeit) + '.txt'), 'a+') as file:
        file.write((
            str(time.strftime('%H:%M:%S')) + " bought " + str(bought) + " " +
            SYMBOL0 + " " + str(symbol0_price) + " lastbuy " +
            str(last_buy_sy0) + " P&L " + str(round(profit_since_buy_sy0, 2)) +
            "%" + " XEMA " + str(round(last_ema_xxl, 6)) + " SEMA " +
            str(round(last_ema_slow, 6)) + " " + SYMBOL1 + " " +
            str(symbol1_price) + " " + SYMBOL2 + " " + str(symbol2_price) +
            " Mxxl " + str(round(margin_aktuell_zu_xxl, 2)) + "%" + " Mslow " +
            str(round(margin_aktuell_zu_slow, 2)) + "%" + " Mfast " +
            str(round(margin_aktuell_zu_fast, 2))) + "%" + "\n")


#def format_symbols(symbols):
#    formatted_symbols = ','.join(['"{}"'.format(symbol) for symbol in symbols])
#    return '[{}]'.format(formatted_symbols)


def printout_console():

    global bought
    global margin_min
    global margin_max
    global margin_diff
    global last_ema_fast
    global coinlenght
    global SecondsSinceBuy
    global SecondsSinceSell
    global Wiedereinstiegskurs
    global Wiedereinstiegsfaktor
    
    clear()  #clear console
    print(">>-----------", time.strftime('%Z %H:%M:%S'), "------------")
    print(Fore.CYAN + "--------------Walletstand--------------")
    print(" ", Coin, "  free:", Coin_free, Coin, "locked:", Coin_locked)
    print(" ", Stablecoin, " free:", Stablecoin_free, Stablecoin, "locked:",
          Stablecoin_locked)
    print("---------------------------------------", Fore.RESET)
    
    #--------------------------Kennzahlen Anzeige
    print("------------Kennzahlen-----------------")

    if bought:
        print(Fore.RED + "Verkauf von " + SYMBOL0[:coinlenght] + " zu Stablecoin " + Stablecoin + Fore.RESET)
    else:
        print(Fore.GREEN + "Kaufe mit " + SYMBOL0[coinlenght:8] + " nun " + SYMBOL0[:coinlenght] + Fore.RESET)

    print("Lastbuy", last_buy_sy0, "Lastsell", last_sell_sy0)
    print(SYMBOL0[:coinlenght], "=", symbol0_price, SYMBOL0[coinlenght:8], "~ ",float(int(float(Stablecoin_free / symbol0_price)*1000)/1000),SYMBOL0[:coinlenght] +" free")
    print("Profit/loss:{:>7.4f}".format(profit_since_buy_sy0), "%")
    print("---------------------------------------")
    
    #--------------------------Kaufsbedingungen Anzeige
    if not bought:
        print(Fore.GREEN + "--------- " + SYMBOL0[:coinlenght], "Kaufsbedingungen --------" + Fore.RESET)
    else:
        print(Fore.WHITE + "--------- " + SYMBOL0[:coinlenght], "Kaufsbedingungen --------" + Fore.RESET)
    ausdruck = "0.) Mxxl   {:>9.4f}  < {:>8.4f} {:<6}".format(
        round(margin_aktuell_zu_xxl, 2), buy_level_xxl, Fore.GREEN + "true" +
        Fore.RESET if margin_aktuell_zu_xxl < buy_level_xxl else Fore.RED +
        "false" + Fore.RESET)
    print(ausdruck)
    ausdruck = "1.) Mslow  {:>9.4f}  < {:>8.4f} {:<6}".format(
        round(margin_aktuell_zu_slow, 2), buy_level_slow, Fore.GREEN + "true" +
        Fore.RESET if margin_aktuell_zu_slow < buy_level_slow else Fore.RED +
        "false" + Fore.RESET)
    print(ausdruck)
    ausdruck = "2.) Mfast  {:>9.4f}  < {:>8.4f} {:<6}".format(
        round(margin_aktuell_zu_fast, 2), buy_level_fast, Fore.GREEN + "true" +
        Fore.RESET if margin_aktuell_zu_fast < buy_level_fast else Fore.RED +
        "false" + Fore.RESET)
    print(ausdruck)
    ausdruck = "3.) XXL-EMA{:>9.4f}  < {:>8.4f} {:<6}".format(
        round(symbol0_price, 2), round(last_ema_xxl, 2), Fore.GREEN + "true" +
        Fore.RESET if symbol0_price < last_ema_xxl else Fore.RED + "false" +
        Fore.RESET)
    print(ausdruck)
    ausdruck = "4.) reEntry {:>8.4f}  < {:>8.4f} {:<6}".format(
        symbol0_price, Wiedereinstiegskurs, Fore.GREEN + "true" +
        Fore.RESET if symbol0_price < Wiedereinstiegskurs else Fore.RED +
        "false" + Fore.RESET)
    print(ausdruck)

    is_true = (60 < SecondsSinceSell < 86400)
    status = Fore.GREEN + "true" + Fore.RESET if is_true else Fore.RED + "false" +  Fore.RESET
    ausdruck = "5.) TradeSec {:>7.0f}  {:>8} {:<6}".format(SecondsSinceSell, ">60 <86400", status)
    print(ausdruck)

    ausdruck = "6.) Stable_free{:>5.0f}  > {:>8.0f} {:<6}".format(Stablecoin_free, 10, Fore.GREEN + "true" + Fore.RESET if (Stablecoin_free > 10) else Fore.RED + "false" +  Fore.RESET)
    print(ausdruck)
    
    if bought:
        print(Fore.WHITE + "---------------------------------------" +
              Fore.RESET)
    else:
        print(Fore.GREEN + "---------------------------------------" +
              Fore.RESET)

    #--------------------------VerKaufsbedingungen Anzeige
    if bought:
        print(Fore.RED + "--------", SYMBOL0[:coinlenght], "Verkaufsbedingungen ------", Fore.RESET)
    else:
        print(Fore.WHITE + "--------", SYMBOL0[:coinlenght], "Verkaufsbedingungen ------", Fore.RESET)

    ausdruck = "0.) Mxxl   {:>9.4f}  > {:>8.4f} {:<6}".format(
        round(margin_aktuell_zu_xxl, 2), sell_level_xxl, Fore.GREEN + "true" +
        Fore.RESET if margin_aktuell_zu_xxl > sell_level_xxl else Fore.RED +
        "false" + Fore.RESET)
    print(ausdruck)
    ausdruck = "1.) Mslow  {:>9.4f}  > {:>8.4f} {:<6}".format(
        round(margin_aktuell_zu_slow,
              2), sell_level_slow, Fore.GREEN + "true" +
        Fore.RESET if margin_aktuell_zu_slow > sell_level_slow else Fore.RED +
        "false" + Fore.RESET)
    print(ausdruck)
    ausdruck = "2.) Mfast  {:>9.4f}  > {:>8.4f} {:<6}".format(
        round(margin_aktuell_zu_fast,
              2), sell_level_fast, Fore.GREEN + "true" +
        Fore.RESET if margin_aktuell_zu_fast > sell_level_fast else Fore.RED +
        "false" + Fore.RESET)
    print(ausdruck)
    ausdruck = "3.) XXL-EMA{:>9.4f}  > {:>8.4f} {:<6}".format(
        symbol0_price, last_ema_xxl, Fore.GREEN + "true" +
        Fore.RESET if symbol0_price > last_ema_xxl else Fore.RED + "false" +
        Fore.RESET)
    print(ausdruck)

    is_true = (60 < SecondsSinceBuy < 86400)
    status = Fore.GREEN + "true" + Fore.RESET if is_true else Fore.RED + "false" +  Fore.RESET
    ausdruck = "4.) TradeSec {:>7.0f}  {:>8} {:<6}".format(SecondsSinceBuy, ">60 <86400", status)
    print(ausdruck)
    
    ausdruck = "5.) P&L Slow{:>8.4f}  > {:>8.4f} {:<6}".format(profit_since_buy_sy0, sell_level_slow, Fore.GREEN + "true" + Fore.RESET if profit_since_buy_sy0 > sell_level_slow else Fore.RED + "false" + Fore.RESET)
    print(ausdruck)
   

    if bought:
        print(Fore.RED + "---------------------------------------" +       Fore.RESET)
    else:
        print(Fore.WHITE + "---------------------------------------" +     Fore.RESET)

    #--------------------------Stopploss Anzeige
    if bought:
        print(Fore.YELLOW + "------", SYMBOL0[:coinlenght], "Stopploss-Bedingungen ------", Fore.RESET)
        ausdruck = "1.) Loss?  {:>9.4f}  < {:>8.4f} {:<6}".format(profit_since_buy_sy0, -0.35, Fore.GREEN + "true" + Fore.RESET if profit_since_buy_sy0 < -0.35 else Fore.RED + "false" + Fore.RESET)
        print(ausdruck)
        ausdruck = "2.) XXL-EMA{:>9.4f}  < {:>8.4f} {:<6}".format(round(symbol0_price, 2), round(last_ema_xxl, 2), Fore.GREEN + "true" + Fore.RESET if symbol0_price < last_ema_xxl else Fore.RED + "false" +Fore.RESET)
        print(ausdruck)
        is_true = (60 < SecondsSinceBuy < 86400)
        status = Fore.GREEN + "true" + Fore.RESET if is_true else Fore.RED + "false" +  Fore.RESET
        ausdruck = "4.) TradeSec {:>7.0f}  {:>8} {:<6}".format(SecondsSinceBuy, ">60 <86400", status)
        print(ausdruck)
        print(Fore.YELLOW + "---------------------------------------" +       Fore.RESET)
    else:
        pass


    #----------------------Statistik Anzeige
    print("M-min:", round(margin_min, 2), "M-max:", round(margin_max, 2),
          "M-diff:", round(margin_diff, 2))

    if symbol0_price > last_ema_fast:
        print("EMA fast Trend:" + Fore.GREEN + " up" + Fore.RESET)
    else:
        print("EMA fast Trend:" + Fore.RED + " down" + Fore.RESET)
    if symbol0_price > last_ema_slow:
        print("EMA slow Trend:" + Fore.GREEN + " up" + Fore.RESET)
    else:
        print("EMA slow Trend:" + Fore.RED + " down" + Fore.RESET)
    if symbol0_price > last_ema_xxl:
        print("EMA xxl Trend:" + Fore.GREEN + " up" + Fore.RESET)
    else:
        print("EMA xxl Trend:" + Fore.RED + " down" + Fore.RESET)

    print("------------", time.strftime('%Z %H:%M:%S'), "-----------<<")
    


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def buy_sell_level_adoption():  # anpassung der startwerte wenn zyklus durchlaufen
    global margin_min
    global margin_max
    global margin_diff
    global buy_level_xxl
    global buy_level_slow
    global buy_level_fast
    global sell_level_xxl
    global sell_level_slow
    global sell_level_fast
    global margin_aktuell_zu_slow
    global margin_aktuell_zu_fast
    global margin_aktuell_zu_xxl
    global interval

    global m_fast_min
    global m_fast_max
    global m_slow_min
    global m_slow_max
    global m_xxl_min
    global m_xxl_max

    last_rows = data.tail((int(LIMIT)-int(OFFCUT+300)))

    m_fast_min = last_rows['margin_fast'].min()
    m_fast_max = last_rows['margin_fast'].max()
    m_slow_min = last_rows['margin_slow'].min()
    m_slow_max = last_rows['margin_slow'].max()
    m_xxl_min  = last_rows['margin_xxl'].min()
    m_xxl_max  = last_rows['margin_xxl'].max()
    #print(m_fast_min)
    #print(m_slow_min)
    #print(m_xxl_min)
    #print(m_fast_max)
    #print(m_slow_max)
    #print(m_xxl_max)

    margin_max = max(m_fast_max, m_slow_max, m_xxl_max)
    margin_min = min(m_fast_min,m_slow_min, m_xxl_min)
    margin_diff = margin_max - margin_min

    sell_factor=0.65
    sell_level_fast = m_fast_max * sell_factor * sell_factor* sell_factor
    sell_level_slow = m_slow_max * sell_factor * sell_factor
    sell_level_xxl  = m_xxl_max * sell_factor
    
    buy_factor=0.5
    buy_level_fast = m_fast_min * buy_factor * buy_factor * buy_factor
    buy_level_slow = m_slow_min * buy_factor * buy_factor
    buy_level_xxl  = m_xxl_min * buy_factor

def kaufen():  #bought = false
    global bought
    global Stablecoin_free
    global Coin_free
    global last_buy_sy0
    global last_sell_sy0
    global last_ema_xxl
    global last_ema_slow
    global symbol0_price
    global buy_level_fast
    global buy_level_slow
    global scharf
    global margin_aktuell_zu_fast
    global margin_aktuell_zu_slow
    global Wiedereinstiegskurs
    global Wiedereinstiegsfaktor
    global margin_max
    global margin_min
    global sell_level_slow
    global sell_level_xxl
    global SecondsSinceBuy
    global SecondsSinceSell
       
    #und Bedingungskette
    if not bought \
        and margin_aktuell_zu_xxl  < buy_level_xxl \
        and margin_aktuell_zu_slow < buy_level_slow \
        and margin_aktuell_zu_fast < buy_level_fast \
        and Stablecoin_free > 10.0 \
        and symbol0_price < last_ema_xxl \
        and 60 < SecondsSinceSell \
        and symbol0_price < Wiedereinstiegskurs:

        QNTY = (float(int(float(Stablecoin_free / symbol0_price)*1000)/1000))-0.001
        #print(QNTY)
        
        print("Sofortkauf", symbol0_price, "für Budget", Stablecoin,
              Stablecoin_free, "zu Preis", symbol0_price, "mit Menge", QNTY)

        if scharf:
            try:
                client.order_market(symbol=SYMBOL0, side="buy", quantity=QNTY)
                Coin_free = float(client.get_asset_balance(asset=Coin)['free'])
                Stablecoin_free = float(
                    client.get_asset_balance(asset=Stablecoin)['free'])
                print("Wir haben gekauft. Am Konto sind jetzt:", Coin_free,
                      " " + SYMBOL0[:3])
                bought = True
                last_buy_sy0 = symbol0_price  #stark vereinfacht
                sell_level_xxl = margin_max
                buy_level_slow = margin_min
                write_record()
                
            except:
                print("Wir haben nicht gekauft. Am Konto sind immer noch:",
                      Coin_free, " " + SYMBOL0[:3])
                bought = True
                last_buy_sy0 = symbol0_price  #stark vereinfacht
                sell_level_xxl = margin_max
                buy_level_slow = margin_min


def Stopploss():
    global bought
    global Stablecoin_free
    global Coin_free
    global last_buy_sy0
    global last_sell_sy0
    global symbol0_price
    global symbol1_price
    global symbol2_price
    global scharf
    global Wiedereinstiegskurs
    global Wiedereinstiegsfaktor
    global margin_max
    global margin_min
    global sell_level_slow
    global sell_level_xxl
    global sell_level_fast
    global buy_level_xxl
    global SecondsSinceBuy
    global SecondsSinceSell

    if bought \
        and (-1.0 < profit_since_buy_sy0 < -0.35) \
        and symbol0_price < last_ema_xxl \
        and 60 < SecondsSinceBuy < 86400:  #wenn 1min und 1Tag


        symbol0_price < last_ema_xxl
        #profit und alle EMA zeigen nach unten und 40sec sind vergangen? Fire-sell!!

        QNTY = round(float(Coin_free),2)
        print("Stopploss von", SYMBOL0, "zu Preis", symbol0_price,
              "mit Menge:", QNTY)

        if scharf:
            try:
                client.order_market(symbol=SYMBOL0, side="sell", quantity=QNTY)
                Coin_free = float(client.get_asset_balance(asset=Coin)['free'])
                Stablecoin_free = float(
                    client.get_asset_balance(asset=Stablecoin)['free'])
                print("Wir haben notverkauft. Am Konto sind wieder:",
                      Stablecoin_free, " " + SYMBOL0[coinlenght:8])
                bought = False
                last_sell_sy0 = symbol0_price  #stark vereinfacht
                Wiedereinstiegskurs = last_sell_sy0 * Wiedereinstiegsfaktor
                write_record()

            except:
                print("Wir haben nicht verkauft. Am Konto sind immer noch:",
                      Stablecoin_free, " " + SYMBOL0[3:8])
                bought = False

            last_sell_sy0 = symbol0_price  #stark vereinfacht
            Wiedereinstiegskurs = last_sell_sy0 * Wiedereinstiegsfaktor


def verkaufen():  #bought = True
    global bought
    global Stablecoin_free
    global Coin_free
    global last_buy_sy0
    global last_sell_sy0
    global symbol0_price
    global symbol1_price
    global symbol2_price
    global scharf
    global Wiedereinstiegskurs
    global Wiedereinstiegsfaktor
    global margin_max
    global margin_min
    global sell_level_slow
    global sell_level_xxl
    global sell_level_fast
    global SecondsSinceBuy
    global SecondsSinceSell

    if bought \
        and margin_aktuell_zu_xxl  >= sell_level_xxl \
        and margin_aktuell_zu_slow >= sell_level_slow \
        and margin_aktuell_zu_fast >= sell_level_fast \
        and symbol0_price >= last_ema_xxl \
        and 60 < SecondsSinceBuy \
        and profit_since_buy_sy0 > sell_level_slow :

        QNTY = round(float(Coin_free),2)
        print("Sofortverkauf von ", SYMBOL0, " zu Preis", symbol0_price,
              "mit Menge:", QNTY)

        if scharf:
            try:
                client.order_market(symbol=SYMBOL0, side="sell", quantity=QNTY)
                Coin_free = float(client.get_asset_balance(asset=Coin)['free'])
                Stablecoin_free = float(
                    client.get_asset_balance(asset=Stablecoin)['free'])
                print("Wir verkauft. Am Konto sind jetzt:", Stablecoin_free,
                      " " + SYMBOL0[3:8])
                bought = False
                                
                last_sell_sy0 = symbol0_price  #stark vereinfacht
                Wiedereinstiegskurs = last_sell_sy0 * Wiedereinstiegsfaktor
                
                sell_level_xxl = margin_max
                buy_level_xxl = margin_min
                write_record()
            except:
                print("Wir haben nicht verkauft. Am Konto sind immer noch:",
                      Stablecoin_free, " " + SYMBOL0[3:8])
                bought = False
                
                last_sell_sy0 = symbol0_price  #stark vereinfacht
                Wiedereinstiegskurs = last_sell_sy0 * Wiedereinstiegsfaktor
                
                sell_level_xxl = margin_max
                buy_level_xxl = margin_min


def main():
    global last_buy_sy0
    global last_signal
    global last_trade
    global profit_since_buy_sy0
    global bought
    global gewinn
    global Stablecoin_free
    global Coin_price
    global symbol0_price
    global QNTY
    global startzeit
    global refreshzeit
    global filezeit

    #print("started running at", time.strftime('%Y-%m-%d %H:%M:%S %Z'))
    startzeit = time.time()
    filezeit = int(time.time())
    refreshzeit = time.time()

    get_wallet_info()
    get_klines_erstbefuellung()
    get_avg_price()

    plot_klines()
    get_my_last_trades()
    
    #breakpoint()
    plt.pause(1)
    client = Client(api_key, api_secret)

    while True:

        try:
            get_actual_price()
            get_my_last_trades()
            get_avg_price()
            Stopploss()  #loss prevention
            
            if (time.time() > startzeit + 3):
                plot_klines()
                plt.pause(0.01)
                startzeit = time.time()

            if (time.time() > refreshzeit + 30):  # jede Minute
                try:
                    client = Client(api_key, api_secret)
                    refreshzeit = time.time()
                    get_wallet_info()
                    
                except:
                    pass

            buy_sell_level_adoption()
            printout_console()
            kaufen()  # prüfen ob gekauft werden soll
            verkaufen()  # prüfen ob verkauft werden soll
            

        except:
            pass


if __name__ == "__main__":
    main()
