"""
Project Models
Pydantic models for data validation.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ProjectBase(BaseModel):
    """Base project model with common fields."""
    
    # Identitas & Organisasi
    klaster_regional: str = Field(default="Regional 2", max_length=100)
    entitas_terminal: Optional[str] = Field(default=None, max_length=200)
    id_investasi: Optional[str] = Field(default=None, max_length=100)
    project_definition: Optional[str] = None
    
    # Klasifikasi & Status
    asset_categories: Optional[str] = Field(default=None, max_length=200)
    type_investasi: Optional[Literal['Murni', 'Multi Year', 'Carry Forward']] = None
    tahun_usulan: Optional[int] = None
    tahun_rkap: int = Field(default=2025)
    status_investasi: Optional[str] = Field(default=None, max_length=100)
    
    # Progres & Issue
    progres_description: Optional[str] = None
    issue_categories: Optional[str] = Field(default=None, max_length=200)
    issue_description: Optional[str] = None
    action_target: Optional[str] = None
    head_office_support_desc: Optional[str] = None
    pic: Optional[str] = Field(default=None, max_length=200)
    status_issue: Optional[Literal['Open', 'Closed']] = None
    
    # Lokasi
    latitude: Optional[Decimal] = Field(default=None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(default=None, ge=-180, le=180)
    
    class Config:
        str_strip_whitespace = True


class ProjectCreate(ProjectBase):
    """Model for creating a new project."""
    id_root: str = Field(..., max_length=50)


class ProjectFinance(BaseModel):
    """Financial data model for a project."""
    
    # RKAP
    kebutuhan_dana: Decimal = Field(default=Decimal('0'))
    rkap: Decimal = Field(default=Decimal('0'))
    rkap_januari: Decimal = Field(default=Decimal('0'))
    rkap_februari: Decimal = Field(default=Decimal('0'))
    rkap_maret: Decimal = Field(default=Decimal('0'))
    rkap_april: Decimal = Field(default=Decimal('0'))
    rkap_mei: Decimal = Field(default=Decimal('0'))
    rkap_juni: Decimal = Field(default=Decimal('0'))
    rkap_juli: Decimal = Field(default=Decimal('0'))
    rkap_agustus: Decimal = Field(default=Decimal('0'))
    rkap_september: Decimal = Field(default=Decimal('0'))
    rkap_oktober: Decimal = Field(default=Decimal('0'))
    rkap_november: Decimal = Field(default=Decimal('0'))
    rkap_desember: Decimal = Field(default=Decimal('0'))
    
    @field_validator('*', mode='before')
    @classmethod
    def validate_decimal(cls, v):
        if v is None:
            return Decimal('0')
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class ProjectContract(BaseModel):
    """Contract data model."""
    
    judul_kontrak: Optional[str] = None
    nilai_kontrak: Decimal = Field(default=Decimal('0'))
    penyerapan_sd_tahun_lalu: Decimal = Field(default=Decimal('0'))
    penyedia_jasa: Optional[str] = Field(default=None, max_length=300)
    no_kontrak: Optional[str] = Field(default=None, max_length=200)
    tanggal_kontrak: Optional[date] = None
    tgl_mulai_kontrak: Optional[date] = None
    jangka_waktu: Optional[int] = Field(default=None, ge=0)
    satuan_hari: str = Field(default='Hari', max_length=20)
    tanggal_selesai: Optional[date] = None


class ProjectRealisasi(BaseModel):
    """Monthly realization data model."""
    
    realisasi_januari: Decimal = Field(default=Decimal('0'))
    realisasi_februari: Decimal = Field(default=Decimal('0'))
    realisasi_maret: Decimal = Field(default=Decimal('0'))
    realisasi_april: Decimal = Field(default=Decimal('0'))
    realisasi_mei: Decimal = Field(default=Decimal('0'))
    realisasi_juni: Decimal = Field(default=Decimal('0'))
    realisasi_juli: Decimal = Field(default=Decimal('0'))
    realisasi_agustus: Decimal = Field(default=Decimal('0'))
    realisasi_september: Decimal = Field(default=Decimal('0'))
    realisasi_oktober: Decimal = Field(default=Decimal('0'))
    realisasi_november: Decimal = Field(default=Decimal('0'))
    realisasi_desember: Decimal = Field(default=Decimal('0'))
    
    @property
    def total(self) -> Decimal:
        return (
            self.realisasi_januari + self.realisasi_februari + self.realisasi_maret +
            self.realisasi_april + self.realisasi_mei + self.realisasi_juni +
            self.realisasi_juli + self.realisasi_agustus + self.realisasi_september +
            self.realisasi_oktober + self.realisasi_november + self.realisasi_desember
        )


class ProjectPrognosa(BaseModel):
    """Monthly prognosis data model."""
    
    prognosa_januari: Decimal = Field(default=Decimal('0'))
    prognosa_februari: Decimal = Field(default=Decimal('0'))
    prognosa_maret: Decimal = Field(default=Decimal('0'))
    prognosa_april: Decimal = Field(default=Decimal('0'))
    prognosa_mei: Decimal = Field(default=Decimal('0'))
    prognosa_juni: Decimal = Field(default=Decimal('0'))
    prognosa_juli: Decimal = Field(default=Decimal('0'))
    prognosa_agustus: Decimal = Field(default=Decimal('0'))
    prognosa_september: Decimal = Field(default=Decimal('0'))
    prognosa_oktober: Decimal = Field(default=Decimal('0'))
    prognosa_november: Decimal = Field(default=Decimal('0'))
    prognosa_sd_desember: Decimal = Field(default=Decimal('0'))
    
    @property
    def total(self) -> Decimal:
        return (
            self.prognosa_januari + self.prognosa_februari + self.prognosa_maret +
            self.prognosa_april + self.prognosa_mei + self.prognosa_juni +
            self.prognosa_juli + self.prognosa_agustus + self.prognosa_september +
            self.prognosa_oktober + self.prognosa_november + self.prognosa_sd_desember
        )


class ProjectFull(ProjectBase, ProjectFinance, ProjectContract, ProjectRealisasi, ProjectPrognosa):
    """Full project model with all fields."""
    id_root: str = Field(..., max_length=50)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)


class ProjectSummary(BaseModel):
    """Summary model for project listings."""
    id_root: str
    klaster_regional: str
    entitas_terminal: Optional[str]
    project_definition: Optional[str]
    type_investasi: Optional[str]
    tahun_rkap: int
    status_investasi: Optional[str]
    status_issue: Optional[str]
    rkap: Optional[Decimal]
    nilai_kontrak: Optional[Decimal]
    updated_at: Optional[datetime]
