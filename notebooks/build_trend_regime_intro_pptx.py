"""Build trend_regime_intro.pptx — matches LTCM_Presentation navy theme."""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

REPO = Path(__file__).resolve().parents[1]
SLIDES_DIR = REPO / "Notebooks" / "output" / "trend_regime_slides"
OUT_PPT = REPO / "trend_regime_intro.pptx"
TEMPLATE = REPO / "LTCM_Presentation.pptx"

BG_NAVY = RGBColor(0x0F, 0x1B, 0x2D)
TITLE_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SUBTITLE_CYAN = RGBColor(0x22, 0xD3, 0xEE)
BODY_MUTED = RGBColor(0xCB, 0xD5, 0xE1)
ACCENT_CYAN = RGBColor(0x22, 0xD3, 0xEE)
BODY_WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def _set_slide_background(slide, color: RGBColor = BG_NAVY) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def _style_para(p, text: str, *, size: int, bold: bool = False, color: RGBColor = BODY_WHITE) -> None:
    p.clear()
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color


def _blank_slide(prs: Presentation):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_slide_background(slide)
    return slide


def _add_title(slide, title: str, subtitle: str = "") -> None:
    box = slide.shapes.add_textbox(Inches(0.5), Inches(0.28), Inches(12.3), Inches(0.75))
    tf = box.text_frame
    tf.word_wrap = True
    _style_para(tf.paragraphs[0], title, size=24, bold=True, color=TITLE_WHITE)
    if subtitle:
        _style_para(tf.add_paragraph(), subtitle, size=11, color=SUBTITLE_CYAN)


def _add_bullets(slide, items: list[str], left=0.5, top=1.0, width=5.75, height=4.35, size=10) -> None:
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        _style_para(p, item, size=size, color=BODY_MUTED)
        p.space_after = Pt(5)


def _add_callout(slide, text: str, top=5.55) -> None:
    box = slide.shapes.add_textbox(Inches(0.5), Inches(top), Inches(12.3), Inches(0.5))
    p = box.text_frame.paragraphs[0]
    p.clear()
    r0 = p.add_run()
    r0.text = "Takeaway: "
    r0.font.size = Pt(9.5)
    r0.font.bold = True
    r0.font.color.rgb = ACCENT_CYAN
    r1 = p.add_run()
    r1.text = text
    r1.font.size = Pt(9.5)
    r1.font.color.rgb = BODY_WHITE


def _add_image(slide, name: str, left, top, width, height) -> None:
    path = SLIDES_DIR / name
    if path.exists():
        slide.shapes.add_picture(str(path), Inches(left), Inches(top),
                                 width=Inches(width), height=Inches(height))


def main() -> None:
    import runpy
    runpy.run_path(str(Path(__file__).with_name("build_trend_regime_slide_assets.py")), run_name="__main__")

    prs = Presentation()
    if TEMPLATE.exists():
        t = Presentation(str(TEMPLATE))
        prs.slide_width, prs.slide_height = t.slide_width, t.slide_height

    s1 = _blank_slide(prs)
    _add_title(s1, "Commodity-Trend Across Yield-Curve Regimes",
               "Method 1 vs 60/40 · 2001–May 2026 · named regimes (~48% of days)")
    _add_bullets(s1, [
        "Commodity-Trend does best when the yield curve steepens or twists — i.e. when 2Y and 10Y "
        "are not moving in lockstep. In those regimes it beats 60/40 on return and Sharpe; in "
        "flatteners (Bull Flattener, Bear Steepener), 60/40 wins because stocks and bonds both "
        "contribute.",
        "Even when it lags on return, it still helps a 60/40 book: correlation stays below 0.24 "
        "in every named regime, and max drawdown is smaller in five of six cases — Bull Steepener "
        "−6.6% vs −18.3% for 60/40.",
        "Most of the sample’s edge sits in two labels: Bull Steepener (14.5% ann., Sharpe 1.73) "
        "and Flattener Twist (10.9%, Sharpe 2.12). In flatteners, expect diversification and "
        "shallower drawdowns — not headline outperformance vs 60/40.",
    ], top=0.95, height=4.0, size=9.5)
    _add_image(s1, "slide1_regime_performance.png", 6.2, 0.92, 6.5, 4.55)
    _add_callout(s1, "Steepening/twist → Commodity-Trend adds return; flatteners → it adds "
                 "diversification, not a return substitute.")

    s2 = _blank_slide(prs)
    _add_title(s2, "Why Curve Shape Maps to Commodity-Trend Performance",
               "Bull / Bear / Twist buckets · first 21 days vs later (project data)")
    _add_bullets(s2, [
        "Bull and Bear buckets = yields moving together. Both stocks and bonds tend to work, so "
        "60/40 beats Commodity-Trend on average days (−1.4 to −1.5 bps/day) even though Bull "
        "Sharpe is higher (1.24 vs 0.95). Here Commodity-Trend smooths the path — it does not "
        "replace 60/40 on return.",
        "Twist bucket = 2Y and 10Y move opposite ways (e.g. Fed hiking short rates while long "
        "rates fall). 60/40 earns only 1.6% ann.; Commodity-Trend earns 7.6% and beats 60/40 "
        "every day on average (+2.3 bps/day). This is the clearest case for adding the sleeve.",
        "How long you stay in the label matters: Bear Flattener pays +10% ann. in the first 21 "
        "days after entry, then −1.3% after — good for the hiking *transition*, not for holding "
        "through the cycle. Bull Steepener builds from +5.6% early to +18.2% if easing persists.",
    ], top=0.95, height=4.35, size=9.5)
    _add_image(s2, "slide2_bull_bear_twist_rollup.png", 6.2, 0.95, 6.5, 2.05)
    _add_image(s2, "slide2_onset_vs_steady.png", 6.2, 3.08, 6.5, 1.75)
    _add_callout(s2, "Rates move together → diversify; 2Y vs 10Y diverge → Commodity-Trend can "
                 "outperform.")

    s3 = _blank_slide(prs)
    _add_title(s3, "What Happens When the Curve Regime Changes?",
               "Event study · Commodity-Trend return after a filtered label change")
    _add_bullets(s3, [
        "Chart: all six named regime entries since 2001 (65 label changes total) — descriptive, "
        "not a trading rule. Top panel = median return at day +63 for each entry; two path charts "
        "below split the macro pair from the other four.",
        "Main macro story — Bull Steepener (Fed easing after a growth scare): median +0.9%, "
        "positive in 71% of 14 events; path drifts up after day 0. Best follow-through in the sample.",
        "Main macro story — Bear Flattener (hiking entry): median −0.5%, only 40% positive in "
        "10 events; path flat-to-down by day 63 (front-loaded gain is in slide 2). Other entries "
        "are mixed — e.g. Steepener Twist +2.6% but only 7 events; Bull Flt −0.7%.",
    ], top=0.95, height=4.35, size=9.5)
    _add_image(s3, "slide3_regime_entry_bars.png", 6.2, 0.92, 6.5, 2.05)
    _add_image(s3, "slide3_regime_paths_macro.png", 6.2, 3.02, 6.5, 1.25)
    _add_image(s3, "slide3_regime_paths_other.png", 6.2, 4.32, 6.5, 1.2)
    _add_callout(s3, "Fed easing after a growth scare = best follow-through; hiking entry = "
                 "short-lived, not a long hold.")

    prs.save(str(OUT_PPT))
    print("Wrote", OUT_PPT)


if __name__ == "__main__":
    main()
