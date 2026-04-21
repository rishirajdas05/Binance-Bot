"""
strategies.py — REST API routes for TWAP and Grid strategies.
Credentials loaded from .env automatically.
"""

import os
import sys
import threading
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

router = APIRouter()

running_strategies = {}


class TWAPRequest(BaseModel):
    symbol:           str
    side:             str
    total_quantity:   float
    intervals:        int
    interval_seconds: int


class GridRequest(BaseModel):
    symbol:            str
    lower_price:       float
    upper_price:       float
    grids:             int
    quantity_per_grid: float


@router.post("/strategies/twap")
def run_twap(req: TWAPRequest):
    try:
        from src.advanced.twap import TWAPExecutor
        executor = TWAPExecutor(
            req.symbol, req.side, req.total_quantity,
            req.intervals, req.interval_seconds,
        )

        def run():
            result = executor.run()
            running_strategies["twap_result"] = result

        t = threading.Thread(target=run, daemon=True)
        t.start()
        running_strategies["twap"] = executor

        return {
            "success": True,
            "message": f"TWAP started | {req.intervals} orders of "
                       f"{round(req.total_quantity / req.intervals, 8)} "
                       f"{req.symbol} every {req.interval_seconds}s"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/strategies/twap/stop")
def stop_twap():
    executor = running_strategies.get("twap")
    if executor:
        executor.stop()
        return {"success": True, "message": "TWAP stopped."}
    return {"success": False, "message": "No TWAP running."}


@router.get("/strategies/twap/result")
def twap_result():
    result = running_strategies.get("twap_result")
    if result:
        return {"success": True, "result": result}
    return {"success": False, "message": "No TWAP result yet."}


@router.post("/strategies/grid")
def run_grid(req: GridRequest):
    try:
        from src.advanced.grid_strategy import GridStrategy
        grid = GridStrategy(
            req.symbol, req.lower_price, req.upper_price,
            req.grids, req.quantity_per_grid,
        )

        def run():
            result = grid.run()
            running_strategies["grid_result"] = result

        t = threading.Thread(target=run, daemon=True)
        t.start()
        running_strategies["grid"] = grid

        return {
            "success": True,
            "message": f"Grid started | {req.grids} levels | "
                       f"{req.lower_price}–{req.upper_price}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/strategies/grid/stop")
def stop_grid():
    grid = running_strategies.get("grid")
    if grid:
        grid.stop()
        return {"success": True, "message": "Grid stopped and orders cancelled."}
    return {"success": False, "message": "No Grid running."}


@router.get("/strategies/grid/result")
def grid_result():
    result = running_strategies.get("grid_result")
    if result:
        return {"success": True, "result": result}
    return {"success": False, "message": "No Grid result yet."}