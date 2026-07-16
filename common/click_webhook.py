# IXTIYORIY: Click'dan avtomatik to'lov tasdiqlash uchun webhook server.
# Bu faylni alohida serverga (domen + SSL bilan) joylashtirib, Click Merchant
# kabinetida "Webhook URL" sifatida ko'rsatasiz: https://sizningdomen.uz/click/webhook
#
# O'rnatish: pip install aiohttp
# Ishga tushirish: python click_webhook.py

import os
from aiohttp import web

from common.click_pay import verify_click_signature


async def on_payment_confirmed(order_id: str, amount: str):
    print(f"[CLICK] To'lov tasdiqlandi: order_id={order_id}, amount={amount}")
    # TODO: shu yerda botning send_message chaqiruvini yozing


async def click_webhook(request: web.Request) -> web.Response:
    data = await request.post()
    params = dict(data)

    if not verify_click_signature(params):
        return web.json_response({"error": -1, "error_note": "SIGN CHECK FAILED"})

    action = params.get("action")
    order_id = params.get("merchant_trans_id", "")
    amount = params.get("amount", "")

    if action == "0":
        return web.json_response({
            "click_trans_id": params.get("click_trans_id"),
            "merchant_trans_id": order_id,
            "merchant_prepare_id": order_id,
            "error": 0,
            "error_note": "Success",
        })

    if action == "1":
        await on_payment_confirmed(order_id, amount)
        return web.json_response({
            "click_trans_id": params.get("click_trans_id"),
            "merchant_trans_id": order_id,
            "merchant_confirm_id": order_id,
            "error": 0,
            "error_note": "Success",
        })

    return web.json_response({"error": -8, "error_note": "Unknown action"})


def main():
    app = web.Application()
    app.router.add_post("/click/webhook", click_webhook)
    port = int(os.getenv("PORT", "8080"))
    web.run_app(app, port=port)


if __name__ == "__main__":
    main()
