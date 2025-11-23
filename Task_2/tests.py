import random
import re
import pytest
import requests

URL = "https://qa-internship.avito.com"


@pytest.fixture(scope="session", autouse=True)
def check_service_reachable():
    try:
        requests.get(URL)
    except Exception:
        pytest.skip(f"Нет доступа: {URL}")


@pytest.fixture(scope="module")
def seller_id():
    return random.randint(111111, 999999)


def test_create_item(seller_id):
    url = f"{URL}/api/1/item"
    payload = {
        "sellerID": seller_id,
        "name": "pytest item",
        "price": 123,
        "statistics": {
            "likes": 1,
            "viewCount": 10,
            "contacts": 2
        }
    }

    response = requests.post(url, json=payload, timeout=10)

    assert response.status_code == 200, \
        f"Ожидали 200, получили {response.status_code}: {response.text}"

    data = response.json()

    status_msg = data.get("status")
    assert status_msg, "В ответе нет поля status"

    m = re.search(r"[0-9a-fA-F-]{36}", status_msg)
    assert m, f"Не нашли id в ответе: {status_msg}"

    item_id = m.group(0)

    global CREATED_ITEM
    CREATED_ITEM = {
        "id": item_id,
        "sellerId": seller_id
    }


def test_get_item_by_id():
    item = globals().get("CREATED_ITEM")
    assert item, "Нет созданного объявления"

    item_id = item["id"]
    url = f"{URL}/api/1/item/{item_id}"

    response = requests.get(url, timeout=10)
    assert response.status_code == 200, \
        f"Ожидали 200, получили {response.status_code}"

    data = response.json()

    if isinstance(data, list):
        assert any(x.get("id") == item_id for x in data), \
            f"Объявление {item_id} не найдено"
    else:
        assert data.get("id") == item_id, \
            f"В ответе другой id: {data.get('id')}"


def test_get_items_by_seller(seller_id):
    url = f"{URL}/api/1/{seller_id}/item"

    response = requests.get(url, timeout=10)
    assert response.status_code == 200, \
        f"Ожидали 200, получили {response.status_code}"

    data = response.json()
    assert isinstance(data, list), "Ожидали список объявлений"

    if data:
        assert any(
            str(x.get("sellerId")) == str(seller_id)
            for x in data
        ), "Нет объявлений нужного продавца"


def test_get_statistic_by_item():
    item = globals().get("CREATED_ITEM")
    assert item, "Нет созданного объявления"

    item_id = item["id"]
    url = f"{URL}/api/1/statistic/{item_id}"

    response = requests.get(url, timeout=10)
    assert response.status_code == 200, \
        f"Ожидали 200, получили {response.status_code}"

    data = response.json()

    if isinstance(data, list) and data:
        entry = data[0]
    elif isinstance(data, dict):
        entry = data
    else:
        pytest.skip("Неизвестный формат статистики")

    for field in ("likes", "viewCount", "contacts"):
        assert field in entry, f"Нет поля {field} в статистике"

def test_negative_create_without_seller():

    url = f"{URL}/api/1/item"
    payload = {
        "name": "pytest missing seller",
        "price": 100,
        "statistics": {
            "likes": 1,
            "viewCount": 2,
            "contacts": 0
        }
    }

    response = requests.post(url, json=payload, timeout=10)

    assert response.status_code == 400, \
        f"Ожидали 400, получили {response.status_code} — {response.text}"


def test_negative_create_without_name(seller_id):

    url = f"{URL}/api/1/item"
    payload = {
        "sellerID": seller_id,
        "price": 100,
        "statistics": {
            "likes": 1,
            "viewCount": 2,
            "contacts": 0
        }
    }

    response = requests.post(url, json=payload, timeout=10)

    assert response.status_code == 400, \
        f"Ожидали 400, получили {response.status_code} — {response.text}"


def test_negative_get_item_invalid_id():

    fake_id = "00000000-0000-0000-0000-000000000000"
    url = f"{URL}/api/1/item/{fake_id}"

    response = requests.get(url, timeout=10)

    assert response.status_code == 404, \
        f"Ожидали 404, получили {response.status_code} — {response.text}"


def test_negative_get_stat_invalid_id():

    fake_id = "00000000-0000-0000-0000-000000000000"
    url = f"{URL}/api/1/statistic/{fake_id}"

    response = requests.get(url, timeout=10)

    assert response.status_code == 404, \
        f"Ожидали 404, получили {response.status_code} — {response.text}"


def test_negative_get_items_by_invalid_seller():

    bad_seller_id = "not_a_number"
    url = f"{URL}/api/1/{bad_seller_id}/item"

    response = requests.get(url, timeout=10)

    assert response.status_code == 400, \
        f"Ожидали 400, получили {response.status_code} — {response.text}"