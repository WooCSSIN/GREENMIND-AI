

**Date:** 2026-02-23 11:24:47
**Model:** SARIMAX(2, 1, 2) with Discount as External Regressor
**Dataset:** Regime 2 only (post 2022-08-01)


- **Products Analyzed:** 5/10
- **Average MAE:** 119.73 units
- **Average RMSE:** 140.82 units
- **Best Product:** 5873954476.0 (MAE: 106.97)
- **Worst Product:** 10753341705.0 (MAE: 144.43)


- External regressor (discount) helps capture promotion effects
- Regime splitting reduces heteroskedasticity impact
- Confidence intervals now available for risk assessment


1. Deploy SARIMAX model for products with MAE < 108
2. Consider alternative models for high-MAE products
3. Monitor forecast accuracy weekly and retrain monthly
