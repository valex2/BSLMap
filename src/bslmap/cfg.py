from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    since_year: int = 2010
    max_per_institution: int = 1000
    email_for_ncbi: str = "your.email@example.org"
    europe_pmc_cc_by_only: bool = True
    chunk_target_tokens: int = 1200
    chunk_overlap_tokens: int = 150
    model_config = SettingsConfigDict(env_prefix="BSLMAP_", env_file="config/settings.toml")