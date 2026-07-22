"""
utils/safe_ui.py — WebSocket-Safe UI Update Wrappers
=====================================================
Provides helper functions that wrap Streamlit UI updates in try/except
blocks to gracefully handle disconnected clients.

When the browser tab is closed or the connection drops during a
long-running pipeline (embedding, FAISS build, etc.), Streamlit's
tornado backend raises WebSocketClosedError or StreamClosedError.
These helpers silently swallow those errors so the pipeline can
finish without crashing.
"""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


def safe_progress_update(
    progress_bar,
    status_label,
    pct: int,
    msg: str,
    pause: float = 0.05,
) -> None:
    """
    Update a Streamlit progress bar and status label, silently handling
    WebSocket/Stream closed errors that occur when the client disconnects.

    Args:
        progress_bar:  Streamlit progress bar placeholder (from st.progress or st.empty).
        status_label:  Streamlit empty placeholder for stage labels.
        pct:           Progress percentage (0-100).
        msg:           Status message to display.
        pause:         Seconds to sleep after update (for visual smoothness).
    """
    try:
        if progress_bar is not None:
            progress_bar.progress(pct)
    except Exception as exc:
        _log_suppressed(exc, "progress_bar.progress")

    try:
        if status_label is not None:
            status_label.markdown(
                f'<p class="stage-label">{msg}</p>',
                unsafe_allow_html=True,
            )
    except Exception as exc:
        _log_suppressed(exc, "status_label.markdown")

    if pause > 0:
        time.sleep(pause)


def safe_empty(placeholder) -> None:
    """Safely call .empty() on a Streamlit placeholder."""
    try:
        if placeholder is not None:
            placeholder.empty()
    except Exception as exc:
        _log_suppressed(exc, "placeholder.empty")


def _log_suppressed(exc: Exception, context: str) -> None:
    """Log a suppressed UI-update error at DEBUG level."""
    exc_name = type(exc).__name__
    if "closed" in exc_name.lower() or "closed" in str(exc).lower():
        logger.debug(
            "Suppressed %s in %s (client likely disconnected): %s",
            exc_name, context, exc,
        )
    else:
        logger.warning(
            "Unexpected error in %s: %s: %s",
            context, exc_name, exc,
        )
