#!/usr/bin/env python3
"""Run a deterministic, long-only SMA-crossover backtest from OHLCV CSV data."""
from __future__ import annotations
import argparse, csv, json, math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
@dataclass
class Bar:
    timestamp: str; open: float; close: float
def parse_args():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",required=True,type=Path,help="CSV with timestamp,open,high,low,close,volume")
    p.add_argument("--output",type=Path,default=Path("data/reports/backtest-report.json")); p.add_argument("--initial-cash",type=float,default=100_000.0); p.add_argument("--fast",type=int,default=20); p.add_argument("--slow",type=int,default=50); p.add_argument("--fee-bps",type=float,default=10.0); p.add_argument("--slippage-bps",type=float,default=5.0)
    a=p.parse_args()
    if a.initial_cash<=0 or a.fast<=0 or a.slow<=a.fast: p.error("initial-cash must be positive and slow must exceed fast")
    if a.fee_bps<0 or a.slippage_bps<0: p.error("fee-bps and slippage-bps must be non-negative")
    return a
def load_bars(path):
    with path.open(newline="",encoding="utf-8") as h:
        r=csv.DictReader(h)
        if not r.fieldnames or not {"timestamp","open","close"}.issubset(r.fieldnames): raise ValueError("input CSV must contain timestamp,open,close columns")
        bars=[Bar(x["timestamp"],float(x["open"]),float(x["close"])) for x in r]
    if len(bars)<3: raise ValueError("input CSV requires at least three rows")
    if any(x.open<=0 or x.close<=0 for x in bars): raise ValueError("open and close prices must be positive")
    return bars
def sma(v,n): return sum(v[-n:])/n if len(v)>=n else None
def run(bars,initial_cash,fast,slow,fee_bps,slippage_bps):
    cash,units,trades=initial_cash,0.0,[]; closes=[]; prev=0; curve=[]; costs=(fee_bps+slippage_bps)/10_000
    for i,bar in enumerate(bars):
        if i:
            fs,ss=sma(closes,fast),sma(closes,slow); signal=0 if fs is None or ss is None else (1 if fs>ss else -1)
            if signal>0 and prev<=0 and units==0:
                fill=bar.open*(1+costs); units=cash/fill; cash=0.; trades.append({"timestamp":bar.timestamp,"side":"BUY","price":fill,"units":units})
            elif signal<0 and prev>=0 and units>0:
                fill=bar.open*(1-costs); cash=units*fill; trades.append({"timestamp":bar.timestamp,"side":"SELL","price":fill,"units":units}); units=0.
            if signal: prev=signal
        closes.append(bar.close); curve.append(cash+units*bar.close)
    peak=curve[0]; drawdown=0.
    for equity in curve: peak=max(peak,equity); drawdown=min(drawdown,equity/peak-1)
    returns=[curve[i]/curve[i-1]-1 for i in range(1,len(curve)) if curve[i-1]]; avg=sum(returns)/len(returns) if returns else 0.; vol=math.sqrt(sum((x-avg)**2 for x in returns)/len(returns)) if returns else 0.
    return {"generated_at":datetime.now(timezone.utc).isoformat(),"bars":len(bars),"parameters":{"initial_cash":initial_cash,"fast":fast,"slow":slow,"fee_bps":fee_bps,"slippage_bps":slippage_bps},"metrics":{"final_equity":curve[-1],"net_return":curve[-1]/initial_cash-1,"max_drawdown":drawdown,"return_volatility":vol,"trade_count":len(trades)},"trades":trades}
def main():
    a=parse_args(); report=run(load_bars(a.input),a.initial_cash,a.fast,a.slow,a.fee_bps,a.slippage_bps); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(report,indent=2),encoding="utf-8"); print(json.dumps(report["metrics"],indent=2))
if __name__=="__main__": main()
