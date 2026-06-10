select id as payment_id,
    orderid as order_id,
    paymentmethod as payment_method,
    status as payment_status,
    amount / 100 as payment_amount,
    created as payment_created,
    _batched_at
from {{ source('stripe', 'payment') }}