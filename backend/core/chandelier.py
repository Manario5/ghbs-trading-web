from dataclasses import dataclass
from typing import Dict, Any

@dataclass(slots=True)
class ChandelierVerdict:
    kind: str
    stop_level: float
    current_price: float
    watermark: float
    atr_used: float
    message: str

class ChandelierEngine:
    @staticmethod
    def evaluate(pos_row: Dict[str, Any], data: Dict[str, Any]) -> ChandelierVerdict:
        if not data:
            return ChandelierVerdict("NO_DATA", 0, 0, 0, 0,
                                     "No market data available")
        close     = data["close"]
        low       = data["low"]
        atr22     = data["atr22"]
        watermark = max(pos_row["highest_close_since_entry"], close)
        stop      = watermark - pos_row["stop_atr_multiple"] * atr22

        if low <= stop:
            return ChandelierVerdict("STOP_TRIGGERED", stop, close,
                watermark, atr22,
                f"Low {low:.2f} breached Chandelier stop {stop:.2f} SAR.")
        if close > pos_row["highest_close_since_entry"]:
            return ChandelierVerdict("NEW_HIGH", stop, close, watermark, atr22,
                f"New watermark {close:.2f} SAR — stop raised to {stop:.2f}.")
        return ChandelierVerdict("HOLD", stop, close, watermark, atr22,
            f"Trend intact — stop at {stop:.2f} SAR.")
