# Click (my.click.uz) to'lov tizimi bilan integratsiya moduli
# Barcha botlar shu modulni ishlatadi.
#
# Ishlashi uchun Click Merchant kabinetida (https://my.click.uz) ro'yxatdan o'ting va oling:
#   - CLICK_SERVICE_ID
#   - CLICK_MERCHANT_ID
#   - CLICK_MERCHANT_USER_ID  (webhook uchun)
#   - CLICK_SECRET_KEY        (webhook imzosini tekshirish uchun)

import hashlib
import os

CLICK_SERVICE_ID = os.getenv("CLICK_SERVICE_ID", "")
CLICK_MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID", "")
CLICK_MERCHANT_USER_ID = os.getenv("CLICK_MERCHANT_USER_ID", "")
CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY", "")


def generate_click_url(amount: int | float, order_id: str, return_url: str = "") -> str:
    url = (
        f"https://my.click.uz/services/pay"
        f"?service_id={CLICK_SERVICE_ID}"
        f"&merchant_id={CLICK_MERCHANT_ID}"
        f"&amount={amount}"
        f"&transaction_param={order_id}"
    )
    if return_url:
        url += f"&return_url={return_url}"
    return url


def verify_click_signature(params: dict) -> bool:
    action = str(params.get("action", ""))
    raw = params.get("click_trans_id", "") + CLICK_SERVICE_ID + CLICK_SECRET_KEY + params.get("merchant_trans_id", "")
    if action == "1":
        raw += params.get("merchant_prepare_id", "")
    raw += str(params.get("amount", "")) + action + params.get("sign_time", "")
    computed = hashlib.md5(raw.encode()).hexdigest()
    return computed == params.get("sign_string", "")
