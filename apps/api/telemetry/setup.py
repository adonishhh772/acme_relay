import logging

from config import Settings

logger = logging.getLogger("relay")


def configure_observability(settings: Settings) -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    if settings.enable_glitchtip and settings.glitchtip_dsn:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=settings.glitchtip_dsn,
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.2,
        )
        logger.info("GlitchTip/Sentry SDK initialised")

    if (
        settings.enable_langfuse
        and settings.langfuse_public_key
        and settings.langfuse_secret_key
    ):
        logger.info("Langfuse enabled host=%s", settings.langfuse_host)
        # Callbacks are attached per chat run in agent.graph.invoke_agent
