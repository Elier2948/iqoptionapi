import time
import numpy as np
import pandas as pd
from iqoptionapi.stable_api import IQ_Option
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

# ================= CONFIG =================
EMAIL = "elier2948@gmail.com"
PASSWORD = "Joandree29"

PARES = ["EURUSD", "EURUSD-OTC"]
MONTO = 100

RSI_PERIOD = 14
EMA_FAST = 9
EMA_SLOW = 21

TF_ENTRADA = 60     # M1
TF_TENDENCIA = 300  # M5

RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

DELAY = 1.5
# =========================================


def conectar():
    print("🔌 Conectando a IQ Option...")
    api = IQ_Option(EMAIL, PASSWORD)
    api.connect()

    if not api.check_connect():
        raise Exception("❌ Error de conexión")

    api.change_balance("PRACTICE")
    print("✅ Conectado a IQ Option")
    return api


def iniciar_stream(api, par):
    api.start_candles_stream(par, TF_ENTRADA, 50)
    api.start_candles_stream(par, TF_TENDENCIA, 50)
    time.sleep(1)


def obtener_cierres(api, par, tf):
    velas = api.get_realtime_candles(par, tf)
    if not velas or len(velas) < EMA_SLOW:
        return None
    return [velas[t]["close"] for t in sorted(velas)]


def calcular_indicadores(closes):
    serie = pd.Series(closes)

    rsi = RSIIndicator(serie, RSI_PERIOD).rsi().iloc[-1]
    ema_fast = EMAIndicator(serie, EMA_FAST).ema_indicator().iloc[-1]
    ema_slow = EMAIndicator(serie, EMA_SLOW).ema_indicator().iloc[-1]

    return rsi, ema_fast, ema_slow


def esperar_cierre_m1():
    while True:
        if time.localtime().tm_sec >= 58:
            break
        time.sleep(0.2)


def ejecutar_trade(api, par, direccion):
    esperar_cierre_m1()
    ok, trade_id = api.buy(MONTO, par, direccion, 1)

    if ok:
        print(f"🟢 ENTRADA {par} {direccion.upper()}")
        resultado = api.check_win_v3(trade_id)
        print(f"📊 RESULTADO {par}: {resultado}")
    else:
        print(f"⛔ ORDEN FALLIDA {par}")


def main():
    api = conectar()

    for par in PARES:
        iniciar_stream(api, par)

    print("🤖 BOT EMA + RSI + MTF INICIADO\n")

    try:
        while True:
            for par in PARES:
                c_m1 = obtener_cierres(api, par, TF_ENTRADA)
                c_m5 = obtener_cierres(api, par, TF_TENDENCIA)

                if not c_m1 or not c_m5:
                    continue

                rsi1, emaf1, emas1 = calcular_indicadores(c_m1)
                rsi5, emaf5, emas5 = calcular_indicadores(c_m5)

                print(
                    f"📊 {par} | M1 RSI:{rsi1:.1f} EMA9:{emaf1:.5f} EMA21:{emas1:.5f} "
                    f"| M5 RSI:{rsi5:.1f}"
                )

                # ===== CALL =====
                if (
                    rsi1 <= RSI_OVERSOLD and
                    emaf1 > emas1 and
                    emaf5 > emas5 and
                    rsi5 > 50
                ):
                    ejecutar_trade(api, par, "call")

                # ===== PUT =====
                elif (
                    rsi1 >= RSI_OVERBOUGHT and
                    emaf1 < emas1 and
                    emaf5 < emas5 and
                    rsi5 < 50
                ):
                    ejecutar_trade(api, par, "put")

                time.sleep(DELAY)

    except KeyboardInterrupt:
        print("\n🛑 Bot detenido")
    finally:
        for par in PARES:
            api.stop_candles_stream(par, TF_ENTRADA)
            api.stop_candles_stream(par, TF_TENDENCIA)
        api.disconnect()


if __name__ == "__main__":
    main()
