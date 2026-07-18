Title: Configuration Management

Decision:

Use pydantic-settings for all application configuration.
Store environment-specific values in .env.
Commit only .env.example.
Expose a single cached settings instance throughout the application.

Why:

Type safety
Validation
Cleaner code
Easier deployment with Docker/Kubernetes
Centralized configuration