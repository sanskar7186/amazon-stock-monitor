import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

PRODUCT_URL = "https://www.amazon.in/dp/B0FQFJ87HN"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(url, data=data, timeout=30)

        if response.status_code == 200:
            print("Telegram notification sent.")
            return True

        print("Telegram error:", response.text)

    except Exception as e:
        print("Telegram error:", e)

    return False


def check_amazon():

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-IN,en;q=0.9"
    }

    try:
        response = requests.get(
            PRODUCT_URL,
            headers=headers,
            timeout=30
        )

        print("HTTP Status:", response.status_code)

        if response.status_code != 200:
            return "UNKNOWN", None

        soup = BeautifulSoup(response.text, "html.parser")

        # -----------------------------
        # AVAILABILITY
        # -----------------------------

        availability = ""

        selectors = [
            "#availability",
            "#availability span",
            "#outOfStock"
        ]

        for selector in selectors:

            element = soup.select_one(selector)

            if element:
                text = element.get_text(" ", strip=True)

                if text:
                    availability = text
                    break

        page_text = soup.get_text(" ", strip=True).lower()

        if not availability:

            phrases = [
                "currently unavailable",
                "temporarily out of stock",
                "out of stock",
                "in stock",
                "available to ship"
            ]

            for phrase in phrases:

                if phrase in page_text:
                    availability = phrase
                    break

        # -----------------------------
        # PRICE
        # -----------------------------

        price = None

        price_selectors = [
            ".a-price .a-offscreen",
            "#corePriceDisplay_desktop_feature_div .a-price .a-offscreen",
            "#corePriceDisplay_mobile_feature_div .a-price .a-offscreen",
            "#corePrice_feature_div .a-price .a-offscreen",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "#priceblock_saleprice",
            "#apex_desktop .a-price .a-offscreen",
            ".priceToPay .a-offscreen"
        ]

        for selector in price_selectors:

            elements = soup.select(selector)

            for element in elements:

                text = element.get_text(" ", strip=True)

                match = re.search(
                    r"₹\s*[\d,]+(?:\.\d{1,2})?",
                    text
                )

                if match:
                    price = match.group(0)
                    break

            if price:
                break

        # -----------------------------
        # STOCK STATUS
        # -----------------------------

        availability_lower = availability.lower()

        if any(x in availability_lower for x in [
            "currently unavailable",
            "out of stock",
            "temporarily out of stock",
            "unavailable"
        ]):

            status = "OUT_OF_STOCK"

        elif any(x in availability_lower for x in [
            "in stock",
            "available to ship"
        ]):

            status = "IN_STOCK"

        else:

            add_to_cart = soup.select_one("#add-to-cart-button")
            buy_now = soup.select_one("#buy-now-button")

            if add_to_cart or buy_now:
                status = "IN_STOCK"
            else:
                status = "UNKNOWN"

        return status, price

    except Exception as e:

        print("Amazon error:", e)

        return "UNKNOWN", None


if __name__ == "__main__":

    print("=" * 60)
    print("AMAZON STOCK MONITOR")
    print("=" * 60)

    status, price = check_amazon()

    print("Checked:", datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"))
    print("Status :", status)
    print("Price  :", price or "Not found")

    if status == "IN_STOCK":

        message = (
            "🟢 PRODUCT AVAILABLE!\n\n"
            "Apple iPhone 17 256 GB White\n"
            f"💰 Price: {price or 'Not found'}\n\n"
            "🛒 Amazon India\n"
            f"{PRODUCT_URL}"
        )

        send_telegram(message)

    elif status == "OUT_OF_STOCK":

        print("🔴 Product is OUT OF STOCK.")

    else:

        print("⚠️ Stock status is UNKNOWN.")
