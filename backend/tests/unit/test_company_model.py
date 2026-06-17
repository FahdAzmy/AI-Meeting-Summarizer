# tests/unit/test_company_model.py
"""T10.02 — Company Model tests."""
import pytest
from uuid import UUID


@pytest.mark.asyncio
async def test_create_company(db_session):
    """Should create a company with UUID primary key."""
    from src.models.company import Company
    company = Company(name="Acme Corp", subscription_plan="pro")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    assert isinstance(company.id, UUID)
    assert company.name == "Acme Corp"
    assert company.subscription_plan == "pro"


@pytest.mark.asyncio
async def test_company_name_unique(db_session):
    """Should reject duplicate company names."""
    from src.models.company import Company
    from sqlalchemy.exc import IntegrityError
    db_session.add(Company(name="Acme Corp"))
    await db_session.commit()
    db_session.add(Company(name="Acme Corp"))
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_company_default_plan(db_session):
    """Default subscription_plan should be 'free'."""
    from src.models.company import Company
    company = Company(name="NewCo")
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    assert company.subscription_plan == "free"
