import logging
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

mcp = FastMCP("meals")

API_BASE = "https://www.themealdb.com/api/json/v1/1"


async def get_json(path: str, params: dict[str, Any] | None = None) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{API_BASE}/{path}",
                params=params,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as error:
        logging.error("MealDB request failed: %s", error)
        raise RuntimeError("TheMealDB request failed.") from error
    except ValueError as error:
        logging.error("MealDB returned invalid JSON.")
        raise RuntimeError("TheMealDB returned invalid JSON.") from error


def meal_card(meal: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": meal.get("idMeal"),
        "name": meal.get("strMeal"),
        "area": meal.get("strArea"),
        "category": meal.get("strCategory"),
        "thumb": meal.get("strMealThumb"),
    }


def ingredient_list(meal: dict[str, Any]) -> list[dict[str, str]]:
    ingredients = []

    for number in range(1, 21):
        ingredient = meal.get(f"strIngredient{number}")
        measure = meal.get(f"strMeasure{number}")

        if ingredient and ingredient.strip():
            ingredients.append(
                {
                    "name": ingredient.strip(),
                    "measure": (measure or "").strip(),
                }
            )

    return ingredients


def meal_details_shape(meal: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": meal.get("idMeal"),
        "name": meal.get("strMeal"),
        "category": meal.get("strCategory"),
        "area": meal.get("strArea"),
        "instructions": meal.get("strInstructions"),
        "image": meal.get("strMealThumb"),
        "source": meal.get("strSource"),
        "youtube": meal.get("strYoutube"),
        "ingredients": ingredient_list(meal),
    }


@mcp.tool()
async def search_meals_by_name(
    query: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    if not query.strip():
        raise ValueError("query must not be empty")

    if limit < 1 or limit > 25:
        raise ValueError("limit must be between 1 and 25")

    payload = await get_json(
        "search.php",
        {"s": query.strip()},
    )

    meals = payload.get("meals") or []

    return [
        meal_card(meal)
        for meal in meals[:limit]
    ]


@mcp.tool()
async def meals_by_ingredient(
    ingredient: str,
    limit: int = 12,
) -> list[dict[str, Any]]:
    if not ingredient.strip():
        raise ValueError("ingredient must not be empty")

    if limit < 1 or limit > 25:
        raise ValueError("limit must be between 1 and 25")

    payload = await get_json(
        "filter.php",
        {"i": ingredient.strip()},
    )

    meals = payload.get("meals") or []

    return [
        {
            "id": meal.get("idMeal"),
            "name": meal.get("strMeal"),
            "thumb": meal.get("strMealThumb"),
        }
        for meal in meals[:limit]
    ]


@mcp.tool()
async def random_meal() -> dict[str, Any]:
    payload = await get_json("random.php")
    meals = payload.get("meals") or []

    if not meals:
        return {
            "message": "no matches",
            "meal": None,
        }

    return meal_details_shape(meals[0])


@mcp.tool()
async def meal_details(
    id: str | int,
) -> dict[str, Any]:
    payload = await get_json(
        "lookup.php",
        {"i": str(id)},
    )

    meals = payload.get("meals") or []

    if not meals:
        return {
            "message": "no matches",
            "meal": None,
        }

    return meal_details_shape(meals[0])


if __name__ == "__main__":
    mcp.run(transport="stdio")