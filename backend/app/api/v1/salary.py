from __future__ import annotations

from fastapi import APIRouter, status
from app.schemas.salary import SalaryPredictRequest, SalaryPredictResponse
from app.services.salary_predictor import SalaryPredictor


router = APIRouter()


@router.post("/predict", response_model=SalaryPredictResponse, status_code=status.HTTP_200_OK)
async def predict_salary(request: SalaryPredictRequest):
    predictor = SalaryPredictor()
    result = predictor.predict(
        job_slug=request.job_slug,
        difficulty=request.difficulty,
        experience_years=request.experience_years,
    )
    return SalaryPredictResponse(**result)

