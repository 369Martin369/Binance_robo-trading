# programmed by Martin Soos with the help of github examples and documentation of binance libraries

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
import pandas_ta as ta0000
import warnings

import array as t #für 60sec array

warnings.simplefilter(
    action='ignore',
    category=FutureWarning)  # das blendes Pandas append fehler aus

startzeit = None
gewinn = None
gewinnfaktor = 1.15  #bei 15%  über last kauf immer abstossen


QNTY = None
SYMBOL0 =  "MLNBUSD"
SYMBOL1 = "MLNBTC"
SYMBOL2 = "BTCBUSD"

#last_sell_sy0 = 0.001188
#last_buy_sy0 = 0.001188
last_buy_sy0 = 24.64
last_sell_sy0 = 25.04

scharf = False #Client orders sind schafr geschalten. Für nur gucken auf false setzen!
interval = "1m"
LIMIT = "1000"  # taking 120 candles as limit
OFFCUT= 100 #kerzen Abschnitt 
fast_sma = round(int(LIMIT) * 0.048)
slow_sma = round(int(LIMIT) * 0.196)
xxl_sma = round(int(LIMIT) * 0.55)
sell_level_slow = 5.8 # % über sell_buy_level_longterm_ema100
sell_level_fast =  1.5  # % über sell_buy_level_longterm_ema100
buy_level_slow = -5.8  # % über sell_buy_level_longterm_ema100
buy_level_fast =  -1.5 # % über sell_buy_level_longterm_ema100
bought = True #true, wenn 1.Währung im Paar gekauft, BTC false

symbol0_price = 0
lunc_price = None
lunc_free = None
lunc_locked = None

btc_price = None
btc_free = None
btc_locked = None

busd_price = None
busd_free = None
busd_locked = None

bnb_locked = None
bnb_free = None
bnb_price = None

mln_locked = None
mln_free = None
mln_price = None

last_ema_fast = None
last_ema_slow = None
ema_diff = None

abstand_aktuell_zu_slow = None
abstand_aktuell_zu_fast = None
abstand_aktuell_zu_xxl = None
profit_since_buy_sy0 = None
drop_since_sell_sy0 = None

last_k = None
last_d = None
last_j = None

client = Client(api_key, api_secret)


def get_wallet_info():
    global lunc_free
    global lunc_locked
    global btc_free
    global btc_locked
    global busd_free
    global busd_locked
    global bnb_free
    global bnb_locked
    global mln_free
    global mln_locked

    try:
        
        client = Client(api_key, api_secret)
               
        lunc_record = (client.get_asset_balance(asset='LUNC'))
        lunc_free = round(float(lunc_record['free']))
        lunc_locked = round(float(lunc_record['locked']))

        btc_record = (client.get_asset_balance(asset='BTC'))
        btc_free = float(btc_record['free'])
        btc_locked = float(btc_record['locked'])

        busd_record = (client.get_asset_balance(asset='BUSD'))
        busd_free = float(busd_record['free'])
        busd_locked = float(busd_record['locked'])

        bnb_record = (client.get_asset_balance(asset='BNB'))
        bnb_free = float(bnb_record['free'])
        bnb_locked = float(bnb_record['locked'])

        mln_record = (client.get_asset_balance(asset='MLN'))
        mln_free = float(mln_record['free'])
        mln_locked = float(mln_record['locked'])

    except BinanceAPIException as e:
        # error handling goes here
        print(e)
        pass
    except BinanceOrderException as e:
        # error handling goes here
        print(e)
        pass
       

    with open(('protocols/' + SYMBOL0 + str(filezeit) + '.txt'), 'a+') as file:
        file.write (" BTC-free " + str(btc_free)  +
                    " BTC-locked " + str(btc_locked) + 
                    " BNB-free " + str(bnb_free) + 
                    " BNB-locked " + str(bnb_locked) + 
                    " BUSD-free " + str(busd_free) + 
                    " BUSD-locked " + str(busd_locked) + 
                    " MLN-free " + str(mln_free) + 
                    " MLN-locked " + str(mln_locked) + 
                    " LUNC-free " + str(lunc_free) + 
                    " LUNC-locked " + str(lunc_locked) + 
                    "\n")


def get_avg_price():
    global symbol0_price
    global symbol1_price
    global symbol2_price
    

    try:
        symbol0_price = client.get_ticker(symbol=SYMBOL0)
        symbol0_price = float(symbol0_price['lastPrice'])
        symbol1_price = client.get_ticker(symbol=SYMBOL1)
        symbol1_price = float(symbol1_price['lastPrice'])
        symbol2_price = client.get_ticker(symbol=SYMBOL2)
        symbol2_price = float(symbol2_price['lastPrice'])
    except:
        pass


def get_actual_price():
    global symbol0_price
    global data
    global last_ema_fast
    global last_ema_slow
    global last_ema_xxl  
    global ema_diff
    global last_signal
    global last_trade
    global abstand_aktuell_zu_slow
    global abstand_aktuell_zu_fast
    global abstand_aktuell_zu_xxl
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
    data.ta.bbands(append=True) #using pandas_ta to calculate Bollinger bands
    #data.ta.macd(append=True) #using pandas_ta to calculate Bollinger bands
    data["kdj_diff"] = data['J_800_3'] - data['K_800_3']
    #print (data)
    #data['signal'] = np.where((data['K_800_3']+0) > (data['J_800_3']+0), -3.0, -5.0) 
    #data['trade'] = data["signal"].diff()

    data['margin_fast'] = (((data['close'] / data['EMA_' + str(fast_sma)]) * 100) - 100)
    data['margin_slow'] = (((data['close'] / data['EMA_' + str(slow_sma)]) * 100) - 100)
    data['margin_xxl'] = (((data['close'] / data['EMA_' + str(xxl_sma)]) * 100) - 100)
    #print(data.max(axis='index'))

    last_ema_fast = float(data.iloc[-1]['EMA_' + str(fast_sma)])
    last_ema_slow = float(data.iloc[-1]['EMA_' + str(slow_sma)])
    last_ema_xxl  = float(data.iloc[-1]['EMA_' + str(xxl_sma)])
    
    ema_diff = data.iloc[-1]['kdj_diff']
    symbol0_price = data.iloc[-1]['close']
    
    abstand_aktuell_zu_slow = (((symbol0_price) / last_ema_slow) * 100) - 100
    abstand_aktuell_zu_fast = (((symbol0_price) / last_ema_fast) * 100) - 100
    abstand_aktuell_zu_xxl = (((symbol0_price) / last_ema_xxl) * 100) - 100

    

    if last_buy_sy0 > 0:
        profit_since_buy_sy0 = ((symbol0_price / last_buy_sy0) * 100) - 100
    else:
        profit_since_buy_sy0 = 0
    
    if last_sell_sy0 > 0:
        drop_since_sell_sy0 = -((last_sell_sy0 / symbol0_price) -1) * 100
    else:
        drop_since_sell_sy0 = 0


        
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
    #data.ta.bbands(timeperiod=5, nbdevup=2, nbdevdn=2, matype=0, append=True) #using pandas_ta to calculate Bollinger bands
    
    data['kdj_diff'] = data['K_800_3'] - data['J_800_3']
    #data['signal'] = np.where(data['K_800_3'] > data['J_800_3'], -5.0, -6.0) 
    #data['trade'] = data["signal"].diff()

    data['margin_fast'] = (((data['close'] / data['EMA_' + str(fast_sma)]) * 100) - 100)
    data['margin_slow'] = (((data['close'] / data['EMA_' + str(slow_sma)]) * 100) - 100)
    data['margin_xxl'] = (((data['close'] / data['EMA_' + str(xxl_sma)]) * 100) - 100)
    
    #print (data)
    symbol0_price = (data.iloc[-1]['close'])
    last_ema_fast = float(data.iloc[-1]['EMA_' + str(fast_sma)])
    last_ema_slow = float(data.iloc[-1]['EMA_' + str(slow_sma)])
    last_ema_xxl  = float(data.iloc[-1]['EMA_' + str(xxl_sma)])

def plot_klines():
    global abstand_aktuell_zu_slow
    global abstand_aktuell_zu_fast
    global abstand_aktuell_zu_xxl
    global symbol0_price
    global last_ema_xxl
    global symbol0_price
    global symbol1_price
    global symbol2_price

    df = data.copy()
    df['x'] = [dt.datetime.fromtimestamp(x / 1000.0) for x in df.datetime]
    df.drop(df.index[0:OFFCUT], inplace=True)
    
    plt.clf()
    plt.subplot(211)
    plt.rc('font', size=7)
    plt.grid(True)
    
    #plt.rcParams['legend.title_fontsize'] = 'x-small'
    #plt.style.use(['seaborn-v0_8-darkgrid'])
    #plt.title(str(symbol0_price)+'='+SYMBOL0 + ' ' + time.strftime('%H:%M:%S'))
    plt.title(str(symbol0_price)+'='+SYMBOL0 + ' ' + str(symbol1_price)[:8] +'='+SYMBOL1 + ' '+ str(symbol2_price)[:7] +'='+SYMBOL2)
    
    plt.xlabel(str(int(LIMIT)-OFFCUT) +" klines" + ' a ' + interval)
    #plt.ylabel('price', fontsize=10)

    plt.plot(df["x"], df['EMA_' + str(fast_sma)], linewidth=1, color='red', linestyle='--')
    plt.plot(df["x"], df['EMA_' + str(slow_sma)], linewidth=1, color='blue',linestyle='--')
    plt.plot(df["x"], df['EMA_' + str(xxl_sma)],  linewidth=1, color='black',linestyle='--')
    plt.plot(df["x"], df["high"], linewidth=1, color='green')
    plt.plot(df["x"], df["low"], linewidth=1, color='magenta')
    plt.legend(title=time.strftime('%H:%M:%S'), labels=
               ["EMA_" + str(fast_sma)+"="+ str(last_ema_fast)[:6],
               "EMA_" + str(slow_sma)+"="+ str(last_ema_slow)[:6],
               "xxl_" + str(xxl_sma) +"="+ str(last_ema_xxl)[:6],
               "high, actual=" + str(symbol0_price),
               "low"])
    #plt.plot(df["x"], df["close"], linewidth=0.5, color='green')
    #plt.plot(df["x"], df["BBU_5_2.0"], linewidth=0.5, color='blue')
    #plt.plot(df["x"], df["BBM_5_2.0"], linewidth=0.5, color='black')
    #plt.plot(df["x"], df["BBL_5_2.0"], linewidth=0.5, color='red')
    

    plt.subplot(212)
    plt.grid(True)
    plt.tight_layout()
    
    
    plt.plot(df["x"], df['margin_slow'], color='blue',linewidth=1, linestyle='-')
    plt.plot(df["x"], df['margin_fast'], color='red', linewidth=0.5, linestyle='--')
    plt.plot(df["x"], df['margin_xxl'], color='black',linewidth=0.5, linestyle='--')
    plt.plot(df["x"], (df['J_800_3']-df['K_800_3'])/30-0, color='green', linestyle='-',linewidth=1)
    
    plt.legend(labels=
               ['margin slow= ' + str(abstand_aktuell_zu_slow)[:6],
                'margin fast= ' + str(abstand_aktuell_zu_fast)[:6],
                'margin xxl= ' + str(abstand_aktuell_zu_xxl)[:6],
                'kj-diff, mfast= ' + str(abstand_aktuell_zu_fast)[:6]], 
               title = 'P&L $Pair: ' +str(profit_since_buy_sy0)[:6]+'%')
    #plt.ylabel("actual % margin over ema", fontsize=10)
    
    plt.show(block=False)


def write_file():
    global filezeit
    global bought
    global symbol0_price
    global last_buy_sy0
    global profit_since_buy_sy0
    global abstand_aktuell_zu_slow
    global abstand_aktuell_zu_fast
    global mln_free
    global mln_locked

    with open(('protocols/' + SYMBOL0 + str(filezeit) + '.txt'), 'a+') as file:
        file.write((str(time.strftime('%H:%M:%S')) + 
                    " bought " + str(bought) +
                    " " + SYMBOL0 + " " + str(symbol0_price) +
                    " lastbuy " + str(last_buy_sy0) +
                    " P&L " + str(round(profit_since_buy_sy0, 2)) + "%" +
                    " XEMA " +  str(round(last_ema_xxl,6)) +
                    " SEMA " +  str(round(last_ema_slow,6)) +
                    " " + SYMBOL1 + " " + str(symbol1_price) +
                    " " + SYMBOL2 + " " + str(symbol2_price) +
                    " Mxxl "+ str(round(abstand_aktuell_zu_xxl, 2)) + "%" +
                    " Mslow " + str(round(abstand_aktuell_zu_slow, 2)) + "%" +
                    " Mfast " + str(round(abstand_aktuell_zu_fast, 2))) + "%" +
                    "\n")


def printout_console():

    print(">>----------", time.strftime('%Z %H:%M:%S'),"------------")
    print("------------Walletstand--------------")
    print("LUNCfree:", lunc_free, "LUNClock:", lunc_locked)
    print("BTCfree:", btc_free, "BTClock:", btc_locked)
    print("BUSDfree:", busd_free, "BUSDlock:", busd_locked)
    print("BNBfree:", bnb_free, "BNBlock:", bnb_locked)
    print("MLNfree:", mln_free, "MLNlock:", mln_locked)
    print("-----------Kennzahlen-----------------")
    print(SYMBOL0[:3], "gekauft?", bought)
    print("Lastbuy", last_buy_sy0,"Lastsell", last_sell_sy0)
    print(SYMBOL0,"=", symbol0_price)
    print("P&L:", round(profit_since_buy_sy0, 6), "%")
    print(SYMBOL1,"=", symbol1_price) 
    print(SYMBOL2,"=", round(symbol2_price,6))
       
    #print("KJ:", round(ema_diff,2),"\n")
    print("Mxxl", round(abstand_aktuell_zu_xxl, 6), "%")  
    print("Mslow", round(abstand_aktuell_zu_slow, 6), "%")
    print("Mfast", round(abstand_aktuell_zu_fast, 6), "%")
    
    print("----", SYMBOL0[:3],"True-Verkaufsbedingungen ---")
    print("1.) Mslow   ",round(abstand_aktuell_zu_slow,6), ">", sell_level_slow)
    print("2.) Mfast   ",round(abstand_aktuell_zu_fast,6) ,">", sell_level_fast)
    print("3.) price   ", symbol0_price, ">", "XEMA",round(last_ema_xxl,6))
    print("4.) Gain P&L",  round(profit_since_buy_sy0,6), ">", (sell_level_slow))
    
    print("-----", SYMBOL0[:3],"False-Kaufsbedingungen ----")
    print("1.) Mslow   ", round(abstand_aktuell_zu_slow,6),"<", buy_level_slow)
    print("2.) Mfast   ", round(abstand_aktuell_zu_fast,6) ,"<", buy_level_fast)
    print("3.) price   ", symbol0_price, "<", "XEMA",round(last_ema_xxl,6))
    print("4.) SellDrop", round(drop_since_sell_sy0,6), "<", round(-sell_level_slow,6)) #Wiedereinstieg nur tief
    print(">>----------",time.strftime('%Z %H:%M:%S'),"---------<<")

def kaufen(): #bought = false
    global bought
    global busd_free
    global btc_free
    global mln_free
    global last_buy_sy0
    global last_sell_sy0
    global last_ema_xxl
    global last_ema_slow
    global symbol0_price
    global buy_level_fast
    global buy_level_slow
    global scharf
    global abstand_aktuell_zu_fast
    global abstand_aktuell_zu_slow

    if not bought \
        and abstand_aktuell_zu_slow < buy_level_slow \
        and abstand_aktuell_zu_fast < buy_level_fast \
        and symbol0_price < last_ema_xxl \
        and drop_since_sell_sy0 < -sell_level_slow: #Verlust muss kleiner sein Summe Verkaufsprofite

        QNTY = round((btc_free / symbol0_price),3)
        print("Sofortkauf BNB für Budget BTC", btc_free, "zu Preis",
        symbol0_price, "Menge", QNTY)
        if scharf:
            client.order_market(symbol=SYMBOL0, side="buy", quantity=QNTY)
            
        #checke Ergebnis
        btc_record = (client.get_asset_balance(asset='BTC'))
        btc_free = float(btc_record['free'])
        bnb_record = (client.get_asset_balance(asset='BNB'))
        bnb_free = float(bnb_record['free'])
            
        if (bnb_free > 0.1) and (btc_free <
                                               0.001):  #wenn wahr, dann hat Kauf geklappt
            print("Wir haben gekauft. Am Konto sind jetzt:", bnb_free)
            bought = True
            last_buy_sy0 = symbol0_price
        else:
            bought = False
            #last_buy_sy0 = 0


def verkaufen(): #bought = True
    global bought
    global busd_free
    global mln_free
    global bnb_free
    global last_buy_sy0
    global last_sell_sy0
    global symbol0_price
    global symbol1_price
    global symbol2_price
    global scharf

    
    if bought: #wenn wir erste währung des Parres besitzen
        if (abstand_aktuell_zu_slow > sell_level_slow):  #wenn es unter langsamen verkauflevel fällt
            if (abstand_aktuell_zu_fast > sell_level_fast):  #wenn es unter schnellen verkauflevel fällt
                if (symbol0_price > last_ema_xxl): # BUSD preis muss über ganz langsamen mittel liegen
                    if (profit_since_buy_sy0 > (sell_level_slow)): #profit muss über Summe der abs Margins liegen
                        
                        QNTY = round(bnb_free,3)
                        print("Sofortverkauf von BNB", bnb_free, "zu Preis", symbol0_price,
                              "Menge", QNTY)
                        if scharf:
                            client.order_market(symbol=SYMBOL0, side="sell", quantity=QNTY)
            
                        #checke Ergebnis
                        btc_record = (client.get_asset_balance(asset='BTC'))
                        btc_free = float(btc_record['free'])
                        bnb_record = (client.get_asset_balance(asset='BNB'))
                        bnb_free = float(bnb_record['free'])
            
                        if (bnb_free < 0.1) and (btc_free > 0.01):  #wenn wahr, dann hat Verkauf geklappt
                            print("Wir haben verkauft. Am Konto sind jetzt:", btc_free)
                            bought = False
                            last_sell_sy0 = symbol0_price
                        else:
                            bought = True
                            #last_sell_sy0 = 0

def gewinnverkauf():
    global habebesitz
    global bought
    global QNTY
    global mln_free
    global busd_free
    global last_sell_sy0
    global last_ema_xxl
    global symbol0_price
    global symbol1_price
    global symbol2_price
    global scharf

    if (symbol1_price > ((last_buy_sy0 * symbol2_price) * gewinnfaktor) and bought):  ##Gewinnverkauftry:
            QNTY = round(bnb_free,3)
            print("Gewinnverkauf von BNB", bnb_free, "zu Preis", symbol1_price,"Menge", QNTY)
            if scharf: 
                client.order_market(symbol=SYMBOL1, side="sell", quantity=QNTY)

            #checke Ergebnis
            bnb_record = (client.get_asset_balance(asset='BNB'))
            bnb_free = float(bnb_record['free'])
            busd_record = (client.get_asset_balance(asset='BUSD'))
            busd_free = float(busd_record['free'])


            if (bnb_free < 0.1) and (busd_free > 0.1):  #wenn wahr, dann hat Verkauf geklappt
                print("Wir haben verkauft. Am Konto sind jetzt:", busd_free)
                bought = False
                last_sell_sy0 = symbol0_price
            else:
                bought = True
                last_sell_sy0 = 0
def main():
    global last_buy_sy0
    global last_signal
    global last_trade
    global profit_since_buy_sy0
    global bought
    global gewinn
    global busd_free
    global lunc_free
    global lunc_price
    global mln_free
    global symbol0_price
    global QNTY
    global startzeit
    global refreshzeit
    global filezeit

    print("started running at ", time.strftime('%Y-%m-%d %H:%M:%S %Z'))
    startzeit = time.time()
    filezeit = int(time.time())
    refreshzeit = time.time()

    get_wallet_info()
    get_klines_erstbefuellung()
    get_avg_price()

    plot_klines()
    #breakpoint()
    plt.pause(1)
    client = Client(api_key, api_secret)

    while True:
        try:
            get_actual_price()
            if (time.time() > startzeit +2):
                plot_klines()
                plt.pause(0.1)
                get_avg_price()
                printout_console()
                startzeit = time.time()

            if (time.time() > refreshzeit + 3600): # jede Minute
                try:
                    client = Client(api_key, api_secret)
                    refreshzeit = time.time()
                    get_wallet_info()
                except:
                    pass
            
            get_avg_price()
            kaufen()  # prüfen ob gekauft werden soll
            verkaufen()  # prüfen ob verkauft werden soll
            #gewinnverkauf() #check ob BUSD Gewinn erreicht für Sofortverkauf
            #array_behandlung()
            write_file()

        except BinanceAPIException as e:
            # error handling goes here
            print(e)
            pass
        except BinanceOrderException as e:
            # error handling goes here
            print(e)
            pass


if __name__ == "__main__":
    main()
