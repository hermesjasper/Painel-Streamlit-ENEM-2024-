
from __future__ import annotations

from pathlib import Path
from typing import Dict

import streamlit as st


def inject_theme_variables(theme: Dict[str, str]) -> None:
    css_vars = "; ".join(
        f"--{key.replace('_', '-')}: {value}" for key, value in theme.items()
    )
    style = f":root {{{css_vars};}}"
    st.markdown(f"<style>{style}</style>", unsafe_allow_html=True)


def inject_base_css() -> None:
    css_path = Path(__file__).resolve().parent.parent / "assets" / "theme.css"
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
