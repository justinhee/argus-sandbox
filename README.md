hello world
metacode api key test

## shop

A small order-processing service: catalog, inventory reservations, pricing
(volume tiers and coupons), sales tax, an order lifecycle, a payment gateway
client, signed API tokens, rate limiting, emails, CSV import and reports.

```
pip install pytest
python -m pytest
```

Configuration comes from `SHOP_*` environment variables (see `shop/config.py`).
