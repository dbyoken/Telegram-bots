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
    """
    Mijozni Click to'lov sahifasiga yo'naltiruvchi havola yaratadi.
    order_id — sizning tizimingizdagi buyurtma/bandlov/kurs identifikatori (transaction_param).
    """
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
    """
    Click serverdan keladigan Prepare/Complete so'rovi imzosini tekshiradi.
    Click hujjatiga ko'ra sign_string quyidagicha tuziladi:
      Prepare: click_trans_id + service_id + SECRET_KEY + merchant_trans_id + amount + action + sign_time
      Complete: click_trans_id + service_id + SECRET_KEY + merchant_trans_id + merchant_prepare_id + amount + action + sign_time
    To'liq maydonlar ro'yxati Click hujjatida ko'rsatilgan; quyida eng ko'p ishlatiladigan tartib berilgan.
    """
    action = str(params.get("action", ""))
    raw = params.get("click_trans_id", "") + CLICK_SERVICE_ID + CLICK_SECRET_KEY + params.get("merchant_trans_id", "")
    if action == "1":  # Complete
        raw += params.get("merchant_prepare_id", "")
    raw += str(params.get("amount", "")) + action + params.get("sign_time", "")
    computed = hashlib.md5(raw.encode()).hexdigest()
    return computed == params.get("sign_string", "")
