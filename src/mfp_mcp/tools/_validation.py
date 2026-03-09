"""Pydantic input validation models for tool arguments."""

from datetime import date

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


def format_validation_error(exc: ValidationError) -> str:
    """Convert ValidationError to a clean user-facing message."""
    parts = []
    for err in exc.errors():
        field_name = " -> ".join(str(loc) for loc in err["loc"]) if err["loc"] else "input"
        parts.append(f"{field_name}: {err['msg']}")
    return "; ".join(parts)


class DateInput(BaseModel):
    """Validates a single date input."""

    date: date

    @field_validator("date", mode="before")
    @classmethod
    def coerce_string(cls, v: object) -> object:
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v


class DateRangeInput(BaseModel):
    """Validates start/end date range."""

    start_date: date
    end_date: date

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def coerce_string(cls, v: object) -> object:
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v

    @model_validator(mode="after")
    def check_range(self) -> "DateRangeInput":
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before or equal to end_date")
        if (self.end_date - self.start_date).days > 31:
            raise ValueError("Date range too large. Maximum 31 days.")
        return self


class MeasurementInput(BaseModel):
    """Validates measurement query input."""

    measurement: str = Field(default="Weight")
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def coerce_string(cls, v: object) -> object:
        if v is None:
            return v
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v

    @model_validator(mode="after")
    def check_dates(self) -> "MeasurementInput":
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date must be before end_date")
        return self


class FoodSearchInput(BaseModel):
    """Validates food search input."""

    query: str = Field(min_length=1, max_length=200)
