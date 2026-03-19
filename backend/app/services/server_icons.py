from __future__ import annotations

ALLOWED_SERVER_ICON_ASSETS = (
    "Общая.png",
    "Ан-Зайлиль.png",
    "Валенвуд.png",
    "Венценосные.png",
    "Дом Даггерфорльский.png",
    "Дом Каменный кулак.png",
    "Дом Меркатто.png",
    "Дом Редоран.png",
    "Дом Тельванни.png",
    "Дом Титус.png",
    "Дом Фроуд.png",
    "Дракон.png",
    "Империя.png",
    "Клан Диренни.png",
    "Матиссен.png",
    "Некроманты.png",
    "Орден Араксии.png",
    "Орден Вирвека.png",
    "Орден Красной горы.png",
    "Орден Мелора.png",
    "Орден Талора.png",
    "Предшественники.png",
    "Разбойники.png",
    "Саммерсет.png",
    "Северное племя.png",
    "Скайрим.png",
    "Хай Рок.png",
    "Хаммерфелл.png",
    "Хист.png",
    "Чернотопье.png",
    "Эльсвеер.png",
    "Южное племя.png",
)

DEFAULT_SERVER_ICON_ASSET_BY_NAME = {
    "Общая": "Общая.png",
    "Империя": "Империя.png",
    "Саммерсет": "Саммерсет.png",
    "Хай Рок": "Хай Рок.png",
    "Валенвуд": "Валенвуд.png",
    "Хаммерфелл": "Хаммерфелл.png",
    "Скайрим": "Скайрим.png",
    "Тельваннис": "Дом Тельванни.png",
    "Солтсхейм": "Дракон.png",
    "Эльсвеер": "Эльсвеер.png",
}


def get_default_server_icon_asset(server_name: str) -> str | None:
    return DEFAULT_SERVER_ICON_ASSET_BY_NAME.get(server_name)


def normalize_server_icon_asset(icon_asset: str | None) -> str | None:
    if icon_asset is None:
        return None

    normalized = icon_asset.strip()
    if not normalized:
        return None

    if normalized not in ALLOWED_SERVER_ICON_ASSETS:
        raise ValueError("Недопустимая иконка группы")

    return normalized
