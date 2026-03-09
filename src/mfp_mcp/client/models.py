"""Pydantic response models for MFP data serialisation."""

from pydantic import BaseModel


class FoodEntry(BaseModel):
    """A single food entry in a meal."""

    name: str
    nutrition: dict[str, float]


class MealData(BaseModel):
    """A meal containing food entries."""

    name: str
    entries: list[FoodEntry]
    totals: dict[str, float]


class DiaryDay(BaseModel):
    """A full day's food diary."""

    date: str
    meals: list[MealData]
    totals: dict[str, float]
    goals: dict[str, float]
    water: float | None = None
    notes: str | None = None


class NutritionDay(BaseModel):
    """Nutrition summary for a single day."""

    date: str
    totals: dict[str, float]
    complete: bool


class NutritionSummary(BaseModel):
    """Nutrition summary across a date range."""

    start_date: str
    end_date: str
    days: list[NutritionDay]
    averages: dict[str, float]


class MeasurementEntry(BaseModel):
    """A single measurement data point."""

    date: str
    value: float


class FoodSearchResult(BaseModel):
    """A food search result."""

    name: str
    brand: str | None = None
    mfp_id: int | None = None


class FoodDetail(BaseModel):
    """Detailed nutrition info for a food item."""

    name: str
    brand: str | None = None
    servings: list[dict] | None = None
    nutrition: dict[str, float]
