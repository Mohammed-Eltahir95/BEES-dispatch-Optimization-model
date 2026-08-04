"""Forecast future market prices from the historical ``market_prices`` series.

The implementation intentionally depends only on NumPy and pandas, which are
already core project dependencies.  It fits a regularized autoregressive
regression with calendar-seasonality features and falls back to a seasonal
naive forecast when the available history is too short.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from bess_opt.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ForecastSettings:
    enabled: bool = True
    method: str = "ridge_regression"
    minimum_history_points: int = 12
    ridge_alpha: float = 10.0
    use_lag_1: bool = True
    use_daily_lag: bool = True
    use_weekly_lag: bool = True
    clip_forecasts: bool = True
    max_extrapolation_fraction: float = 0.25

    @classmethod
    def from_config(cls, config: dict | None) -> "ForecastSettings":
        cfg = config or {}
        return cls(
            enabled=bool(cfg.get("enabled", True)),
            method=str(cfg.get("method", "ridge_regression")),
            minimum_history_points=int(cfg.get("minimum_history_points", 12)),
            ridge_alpha=float(cfg.get("ridge_alpha", 10.0)),
            use_lag_1=bool(cfg.get("use_lag_1", True)),
            use_daily_lag=bool(cfg.get("use_daily_lag", True)),
            use_weekly_lag=bool(cfg.get("use_weekly_lag", True)),
            clip_forecasts=bool(cfg.get("clip_forecasts", True)),
            max_extrapolation_fraction=float(cfg.get("max_extrapolation_fraction", 0.25)),
        )


def prepare_price_series(
    historical: pd.Series,
    target_index: Iterable[pd.Timestamp],
    forecast_config: dict | None = None,
    market_name: str = "market",
) -> pd.Series:
    """Return a complete price series for the optimization horizon.

    Existing observations at target timestamps are retained. Missing timestamps
    after the last historical observation are forecast automatically. Missing
    timestamps inside the historical range are time-interpolated first.

    The returned Series contains ``attrs['forecasted_timestamps']`` so callers
    can distinguish forecast values from observed values in exported results.
    """
    settings = ForecastSettings.from_config(forecast_config)
    target = _normalise_target_index(target_index)
    history = _clean_history(historical, market_name)

    observed_on_target = history.reindex(target)
    missing_target = observed_on_target.isna()
    if not missing_target.any():
        result = observed_on_target.astype(float)
        result.name = historical.name or market_name
        result.attrs["forecasted_timestamps"] = []
        result.attrs["forecast_method"] = "observed"
        return result

    if not settings.enabled:
        missing = target[missing_target]
        raise ValueError(
            f"Forecasting is disabled, but '{market_name}' has {len(missing)} missing "
            f"price point(s) in the optimization horizon. First missing timestamp: {missing[0]}"
        )

    step = _infer_step(target, history.index)
    prepared_history = _fill_internal_history_gaps(history, step)
    max_target = target.max()

    if max_target > prepared_history.index.max():
        future_index = pd.date_range(
            start=prepared_history.index.max() + step,
            end=max_target,
            freq=step,
        )
        future = _forecast_future(prepared_history, future_index, settings, market_name)
        combined = pd.concat([prepared_history, future])
    else:
        combined = prepared_history

    result = combined.reindex(target)

    # Remaining gaps can occur when the requested horizon starts before the
    # first historical record. We do not silently extrapolate backwards.
    if result.isna().any():
        missing = result[result.isna()].index
        raise ValueError(
            f"Cannot prepare '{market_name}' prices for timestamps before the available "
            f"history. First unresolved timestamp: {missing[0]}; first history timestamp: "
            f"{prepared_history.index.min()}"
        )

    # Preserve exact observations from the workbook over generated values.
    result.loc[observed_on_target.dropna().index] = observed_on_target.dropna().astype(float)
    forecasted = target[observed_on_target.isna()]
    result = result.astype(float)
    result.name = historical.name or market_name
    result.attrs["forecasted_timestamps"] = [ts.isoformat() for ts in forecasted]
    result.attrs["forecast_method"] = settings.method

    logger.info(
        "Prepared '%s' horizon: %d observed, %d forecast price point(s)",
        market_name,
        int((~missing_target).sum()),
        int(missing_target.sum()),
    )
    return result


def _forecast_future(
    history: pd.Series,
    future_index: pd.DatetimeIndex,
    settings: ForecastSettings,
    market_name: str,
) -> pd.Series:
    if len(future_index) == 0:
        return pd.Series(dtype=float, index=future_index, name=history.name)

    method = settings.method.lower().strip()
    if method not in {"ridge_regression", "seasonal_naive"}:
        raise ValueError(
            f"Unsupported forecasting method '{settings.method}' for '{market_name}'. "
            "Use 'ridge_regression' or 'seasonal_naive'."
        )

    if method == "seasonal_naive" or len(history) < settings.minimum_history_points:
        logger.warning(
            "Using seasonal-naive forecast for '%s' (%d historical points)",
            market_name,
            len(history),
        )
        return _seasonal_naive(history, future_index)

    try:
        return _ridge_regression_forecast(history, future_index, settings)
    except (np.linalg.LinAlgError, ValueError, FloatingPointError) as exc:
        logger.warning(
            "Regression forecast failed for '%s' (%s); using seasonal-naive fallback",
            market_name,
            exc,
        )
        return _seasonal_naive(history, future_index)


def _ridge_regression_forecast(
    history: pd.Series,
    future_index: pd.DatetimeIndex,
    settings: ForecastSettings,
) -> pd.Series:
    step = _infer_step(future_index, history.index)
    daily_steps = max(1, int(round(pd.Timedelta(days=1) / step)))
    weekly_steps = 7 * daily_steps

    values = [float(v) for v in history.to_numpy(dtype=float)]
    timestamps = list(history.index)

    lags = []
    if settings.use_lag_1 and len(values) >= 3:
        lags.append(1)
    if settings.use_daily_lag and len(values) >= 2 * daily_steps:
        lags.append(daily_steps)
    if settings.use_weekly_lag and len(values) >= 2 * weekly_steps:
        lags.append(weekly_steps)

    max_lag = max(lags, default=0)
    x_rows: list[list[float]] = []
    y_rows: list[float] = []
    origin = timestamps[0]

    for i in range(max_lag, len(values)):
        x_rows.append(_feature_row(timestamps[i], i, origin, values, lags, daily_steps))
        y_rows.append(values[i])

    # A regression with too few rows is less reliable than the deterministic
    # seasonal fallback.
    feature_count = len(x_rows[0]) if x_rows else 0
    if len(x_rows) < max(6, feature_count + 1):
        return _seasonal_naive(history, future_index)

    x = np.asarray(x_rows, dtype=float)
    y = np.asarray(y_rows, dtype=float)

    # Standardise non-intercept columns to keep the ridge penalty comparable.
    means = x[:, 1:].mean(axis=0)
    scales = x[:, 1:].std(axis=0)
    scales[scales < 1e-9] = 1.0
    x_scaled = x.copy()
    x_scaled[:, 1:] = (x[:, 1:] - means) / scales

    penalty = np.eye(x_scaled.shape[1], dtype=float) * settings.ridge_alpha
    penalty[0, 0] = 0.0  # do not penalise the intercept
    coef = np.linalg.solve(x_scaled.T @ x_scaled + penalty, x_scaled.T @ y)

    lower, upper = _forecast_bounds(np.asarray(values), settings)
    predictions: list[float] = []

    for ts in future_index:
        i = len(values)
        raw = np.asarray(_feature_row(ts, i, origin, values, lags, daily_steps), dtype=float)
        scaled = raw.copy()
        scaled[1:] = (raw[1:] - means) / scales
        pred = float(scaled @ coef)
        if settings.clip_forecasts:
            pred = float(np.clip(pred, lower, upper))
        values.append(pred)
        timestamps.append(ts)
        predictions.append(pred)

    return pd.Series(predictions, index=future_index, name=history.name, dtype=float)


def _feature_row(
    timestamp: pd.Timestamp,
    position: int,
    origin: pd.Timestamp,
    values: list[float],
    lags: list[int],
    daily_steps: int,
) -> list[float]:
    elapsed_days = (timestamp - origin).total_seconds() / 86_400.0
    hour = timestamp.hour + timestamp.minute / 60.0
    weekday = timestamp.dayofweek + hour / 24.0

    row = [
        1.0,
        elapsed_days,
        np.sin(2.0 * np.pi * hour / 24.0),
        np.cos(2.0 * np.pi * hour / 24.0),
        np.sin(2.0 * np.pi * weekday / 7.0),
        np.cos(2.0 * np.pi * weekday / 7.0),
    ]
    for lag in lags:
        row.append(float(values[position - lag]))

    window = values[max(0, position - daily_steps):position]
    row.append(float(np.mean(window)) if window else float(values[-1]))
    return row


def _seasonal_naive(history: pd.Series, future_index: pd.DatetimeIndex) -> pd.Series:
    step = _infer_step(future_index, history.index)
    daily_steps = max(1, int(round(pd.Timedelta(days=1) / step)))
    weekly_steps = 7 * daily_steps

    values_by_time = {pd.Timestamp(ts): float(v) for ts, v in history.items()}
    ordered_values = [float(v) for v in history.to_numpy(dtype=float)]
    predictions: list[float] = []

    for ts in future_index:
        day_ago = ts - pd.Timedelta(days=1)
        week_ago = ts - pd.Timedelta(days=7)
        if day_ago in values_by_time:
            pred = values_by_time[day_ago]
        elif week_ago in values_by_time:
            pred = values_by_time[week_ago]
        elif len(ordered_values) >= daily_steps:
            pred = float(np.mean(ordered_values[-daily_steps:]))
        elif len(ordered_values) >= weekly_steps:
            pred = float(np.mean(ordered_values[-weekly_steps:]))
        else:
            pred = ordered_values[-1]
        values_by_time[ts] = pred
        ordered_values.append(pred)
        predictions.append(pred)

    return pd.Series(predictions, index=future_index, name=history.name, dtype=float)


def _clean_history(series: pd.Series, market_name: str) -> pd.Series:
    if series is None or len(series) == 0:
        raise ValueError(f"No historical prices supplied for '{market_name}'")

    cleaned = pd.Series(series.copy())
    cleaned.index = pd.to_datetime(cleaned.index)
    cleaned = pd.to_numeric(cleaned, errors="coerce").dropna()
    cleaned = cleaned.groupby(level=0).mean().sort_index().astype(float)

    if cleaned.empty:
        raise ValueError(f"Historical prices for '{market_name}' contain no numeric values")
    if not cleaned.index.is_monotonic_increasing:
        cleaned = cleaned.sort_index()
    return cleaned


def _fill_internal_history_gaps(history: pd.Series, step: pd.Timedelta) -> pd.Series:
    full_index = pd.date_range(history.index.min(), history.index.max(), freq=step)
    expanded = history.reindex(full_index)
    if expanded.isna().any():
        expanded = expanded.interpolate(method="time").ffill().bfill()
    expanded.name = history.name
    return expanded.astype(float)


def _normalise_target_index(target_index: Iterable[pd.Timestamp]) -> pd.DatetimeIndex:
    target = pd.DatetimeIndex(pd.to_datetime(list(target_index)))
    if target.empty:
        raise ValueError("Optimization horizon is empty")
    if target.has_duplicates:
        raise ValueError("Optimization horizon contains duplicate timestamps")
    if not target.is_monotonic_increasing:
        target = target.sort_values()
    return target


def _infer_step(*indexes: pd.Index) -> pd.Timedelta:
    for index in indexes:
        idx = pd.DatetimeIndex(index)
        if len(idx) >= 2:
            diffs = idx.to_series().diff().dropna()
            positive = diffs[diffs > pd.Timedelta(0)]
            if not positive.empty:
                return pd.Timedelta(positive.mode().iloc[0])
    return pd.Timedelta(hours=1)


def _forecast_bounds(values: np.ndarray, settings: ForecastSettings) -> tuple[float, float]:
    minimum = float(np.min(values))
    maximum = float(np.max(values))
    span = maximum - minimum
    reference = max(abs(float(np.mean(values))), 1.0)
    margin = max(span * settings.max_extrapolation_fraction, reference * 0.10, 1.0)
    return minimum - margin, maximum + margin
