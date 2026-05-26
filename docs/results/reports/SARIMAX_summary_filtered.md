

**Date:** 2026-02-23 11:24:47
**Model:** SARIMAX(2, 1, 2) with Discount as External Regressor
**Dataset:** Regime 2 only (post 2022-08-01)


| Metric | Value |
|--------|-------|
| Original products | 5 |
| MAE = 0.0 (removed) | 2 |
| MAE > 500 (removed) | 0 |
| **Final products** | **3** |


| Metric | Before | After |
|--------|--------|-------|
| Average MAE  | 71.84 | 119.73 units |
| Median MAE   | 106.97 | 107.80 units |
| Average RMSE | 84.49 | 140.82 units |

- **Best Product :** 5873954476.0 (MAE: 106.97)
- **Worst Product:** 10753341705.0 (MAE: 144.43)


- V2 Average MAE  : ~351 units
- V3 Filtered MAE : 119.73 units
- **Improvement   : 65.9%**


1. Deploy SARIMAX for products with MAE < 126 units
2. Investigate outliers separately with alternative methods (Moving Average / Prophet)
3. Monitor weekly and retrain monthly
4. Add more features (price changes, holiday flags) for high-MAE products
