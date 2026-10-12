from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str
    environment: str
    log_level: str

    jira_url: str
    jira_email: str
    jira_api_token: str
    jira_project_key: str

    github_token: str
    github_owner: str
    github_repo: str

    gemini_api_key: str
    gemini_model: str

    groq_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()