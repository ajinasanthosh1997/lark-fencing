# Commerce API

All URLs below are relative to `/api/v1/`.

## Django app ownership

- `catalog`: products, pricing, inventory, and product APIs
- `orders`: checkout, order lines, fulfilment, and order APIs
- `payments`: cash-on-delivery/gateway transactions and refunds
- `core`: gallery images, categories, content, and contact forms

## Products

- `GET products/`
- `GET products/{slug}/`

Only active products are returned. A product includes its gallery images, current
server price and inventory availability.

## Create an order

`POST orders/`

```json
{
  "payment_method": "cash_on_delivery",
  "fulfilment_method": "delivery",
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "jane@example.com",
  "phone": "0890000000",
  "address_line_1": "1 Main Street",
  "address_line_2": "",
  "city": "Dublin",
  "county": "Dublin",
  "postal_code": "",
  "country_code": "IE",
  "customer_notes": "",
  "items": [
    {
      "product_id": 1,
      "quantity": 2,
      "customization": {}
    }
  ]
}
```

Cash-on-delivery orders are confirmed immediately with a pending payment record;
staff can record collection of cash through the dashboard. The storefront does
not expose card payment or product-return endpoints.

## Configuration

```env
DEFAULT_DELIVERY_FEE=0.00
```

Apply migrations with:

```powershell
python manage.py migrate --fake-initial
```
