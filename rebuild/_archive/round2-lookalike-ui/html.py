"""Small HTML snippets for the pages: panels, cards, chips, score rings, the stepper and notes.

Pure functions with no Streamlit import, so they are unit-tested directly. They only build
markup for display: every decision (scores, bands, validation, what is met) is made in the
pawmatch package and passed in. Text that could come from a user or the database goes
through esc(), because these strings are rendered as HTML (an animal called "<b>Rex</b>"
must show those characters, not bold text). The class names match webui/styles.css.
"""

from __future__ import annotations

from collections.abc import Sequence
from html import escape
from math import pi

BANDS = ("Strong", "Good", "Possible", "Low")
SPECIES_EMOJI = {"Dog": "🐶", "Cat": "🐱", "Rabbit": "🐰"}
BADGE = "app/static/paw-badge.png"  # served from static/ (server.enableStaticServing)
HERO = "app/static/hero.png"
RING_RADIUS = 34
RING_LENGTH = 2 * pi * RING_RADIUS  # circumference of the ring, about 213.6


def esc(value: object) -> str:
    return escape(str(value), quote=True)


def chip(text: str, kind: str = "soft") -> str:
    """A rounded label. kind: dog, cat, rabbit, soft, ok, no, warn, or a band in lower case."""
    return f'<span class="pm-chip pm-chip--{esc(kind)}">{esc(text)}</span>'


def species_chip(species: str) -> str:
    return chip(f"{SPECIES_EMOJI.get(species, '🐾')} {species}", species.lower())


def chips(*parts: str) -> str:
    return f'<div class="pm-chips">{"".join(parts)}</div>'


def ring(score: float, band: str, size: str = "md") -> str:
    """A circular score: the arc's length is the percentage and its shade is the band."""
    percent = max(0, min(100, round(score)))
    band = band if band in BANDS else "Low"
    gap = RING_LENGTH * (1 - percent / 100)
    return (f'<div class="pm-ring pm-ring--{band.lower()} pm-ring--{esc(size)}" role="img" '
            f'aria-label="{percent}% compatibility, {band.lower()} match">'
            f'<svg viewBox="0 0 80 80" aria-hidden="true">'
            f'<circle class="pm-ring__track" cx="40" cy="40" r="{RING_RADIUS}"/>'
            f'<circle class="pm-ring__arc" cx="40" cy="40" r="{RING_RADIUS}" transform="rotate(-90 40 40)" '
            f'style="stroke-dasharray:{RING_LENGTH:.1f};stroke-dashoffset:{gap:.1f};--pm-ring-from:{RING_LENGTH:.1f}"/>'
            f'</svg><div class="pm-ring__label"><b>{percent}%</b></div></div>')


def score(compatibility: float, band: str) -> str:
    """The band in words above its ring, as on the original results page."""
    band = band if band in BANDS else "Low"
    return f'<div class="pm-score"><p class="pm-score__band">{band} match</p>{ring(compatibility, band, "lg")}</div>'


def stepper(steps: Sequence[str], current: int) -> str:
    """The questionnaire's sections in a row: done ones ticked, the current one ringed.

    current is 0-based; current == len(steps) means every section is done.
    """
    items = []
    for i, label in enumerate(steps):
        state = "done" if i < current else "current" if i == current else "todo"
        mark = "✓" if state == "done" else str(i + 1)
        aria = ' aria-current="step"' if state == "current" else ""
        items.append(f'<li class="pm-step pm-step--{state}"{aria}><span class="pm-step__dot" aria-hidden="true">'
                     f'{mark}</span><span class="pm-step__label">{esc(label)}</span></li>')
    return f'<ol class="pm-stepper" aria-label="Questionnaire sections">{"".join(items)}</ol>'


def question_head(number: int, total: int) -> str:
    """'Question N of M', how far through as a percentage, and a progress bar."""
    percent = round(100 * number / total) if total else 0
    return (f'<div class="pm-qhead"><div><h1>Question {int(number)} of {int(total)}</h1>'
            f'<p class="pm-lead">Choose one answer, then continue.</p></div>'
            f'<span class="pm-qhead__pct">{percent}% through</span></div>'
            f'<div class="pm-progress" role="progressbar" aria-label="Questionnaire progress" aria-valuemin="0" '
            f'aria-valuemax="100" aria-valuenow="{percent}"><span style="width:{percent}%"></span></div>')


def question(section: str, prompt: str, hint: str = "") -> str:
    tip = f'<p class="pm-question__hint">{esc(hint)}</p>' if hint else ""
    return f'<p class="pm-eyebrow">{esc(section)}</p><h2 class="pm-question">{esc(prompt)}</h2>{tip}'


def note(body: str, kind: str = "info", title: str = "", icon: str = "") -> str:
    """A soft callout. body is trusted HTML from this module; title is escaped."""
    head = f'<p class="pm-note__title">{esc(icon + " " if icon else "")}{esc(title)}</p>' if title else ""
    return f'<div class="pm-note pm-note--{esc(kind)}" role="note">{head}<div class="pm-note__body">{body}</div></div>'


def eyebrow(text: str, light: bool = False) -> str:
    return f'<p class="pm-eyebrow{" pm-eyebrow--light" if light else ""}">{esc(text)}</p>'


def page_header(title: str, lead: str = "", kicker: str = "") -> str:
    top = eyebrow(kicker) if kicker else ""
    sub = f'<p class="pm-lead">{esc(lead)}</p>' if lead else ""
    return f'<header class="pm-page-header">{top}<h1>{esc(title)}</h1>{sub}</header>'


def section_header(title: str, lead: str = "", kicker: str = "") -> str:
    top = eyebrow(kicker) if kicker else ""
    sub = f'<p class="pm-section-lead">{esc(lead)}</p>' if lead else ""
    return f'<div class="pm-section-head">{top}<h2 class="pm-section-title">{esc(title)}</h2>{sub}</div>'


def label(text: str) -> str:
    """A small capitalised label above a group, such as MAIN ACTIONS."""
    return f'<p class="pm-label">{esc(text)}</p>'


def auth_panel(kicker: str, title: str, copy: str, benefits: Sequence[str], picture: bool = True) -> str:
    """The pink panel beside the log-in and registration forms."""
    ticks = "".join(f'<li><span class="pm-tick" aria-hidden="true">✓</span>{esc(b)}</li>' for b in benefits)
    art = (f'<img class="pm-hero__art" src="{HERO}" alt="A dog, a cat and a rabbit waiting for a home">'
           if picture else "")
    return (f'<section class="pm-hero"><img class="pm-hero__badge" src="{BADGE}" alt="" width="58" height="58">'
            f'{eyebrow(kicker, light=True)}<h1>{esc(title)}</h1><p class="pm-hero__copy">{esc(copy)}</p>'
            f'<ul class="pm-ticks">{ticks}</ul>{art}</section>')


def form_intro(kicker: str, title: str, copy: str) -> str:
    return f'<div class="pm-form-intro">{eyebrow(kicker)}<h2>{esc(title)}</h2><p>{esc(copy)}</p></div>'


def divider(text: str) -> str:
    return f'<div class="pm-divider" role="separator"><span>{esc(text)}</span></div>'


def field_error(message: str) -> str:
    """One validation message, shown directly under the field it belongs to."""
    return f'<p class="pm-field-error" role="alert"><span aria-hidden="true">!</span>{esc(message)}</p>'


def brand(subtitle: str) -> str:
    """The badge and name at the top of the menu."""
    return (f'<div class="pm-brand"><img src="{BADGE}" alt="" width="42" height="42">'
            f'<div><b>PawMatch</b><span>{esc(subtitle)}</span></div></div>')


def initials(name: str) -> str:
    return "".join(word[0] for word in name.split()[:2]).upper() or "?"


def person(name: str, detail: str) -> str:
    """Who is signed in: initials, name and their kind of account."""
    return (f'<div class="pm-person"><span class="pm-avatar" aria-hidden="true">{esc(initials(name))}</span>'
            f'<div><b>{esc(name)}</b><span>{esc(detail)}</span></div></div>')


def action_card(emoji: str, title: str, body: str) -> str:
    return (f'<div class="pm-action"><span class="pm-action__icon" aria-hidden="true">{esc(emoji)}</span>'
            f'<h3>{esc(title)}</h3><p>{esc(body)}</p></div>')


def how_it_works(steps: Sequence[tuple[str, str]]) -> str:
    """Numbered cards explaining the process, as on the original home page."""
    cards = "".join(f'<li><span class="pm-how__num" aria-hidden="true">{i}</span><b>{esc(t)}</b><p>{esc(d)}</p></li>'
                    for i, (t, d) in enumerate(steps, start=1))
    return f'<ol class="pm-how">{cards}</ol>'


def animal_blurb(name: str, line: str, details: str, description: str) -> str:
    """Name, 'Species · breed', 'age · sex · size' and the description on a browse card."""
    return (f'<h3 class="pm-card-title">{esc(name)}</h3><p class="pm-card-kicker">{esc(line)}</p>'
            f'<p class="pm-card-sub">{esc(details)}</p><p class="pm-card-text">{esc(description)}</p>')


def match_heading(rank: int, name: str, line: str) -> str:
    return (f'<div class="pm-match-head"><span class="pm-rank" aria-label="Rank {int(rank)}">{int(rank)}</span>'
            f'<div><h3 class="pm-match-name">{esc(name)}</h3><p class="pm-card-kicker">{esc(line)}</p></div></div>')


def requirements(met: Sequence[str], unmet: Sequence[str], important: Sequence[str] = ()) -> str:
    """What fits (green) and what does not (amber); welfare-critical gaps are labelled Important."""
    ok = "".join(f'<li><span aria-hidden="true">✓</span>{esc(m)}</li>' for m in met)
    ok_box = (f'<div class="pm-req pm-req--met"><p class="pm-req__title">Requirements met</p>'
              f'<ul>{ok}</ul></div>') if met else ""
    rows = []
    for item in unmet:
        flag = (' class="pm-req__important"', '<span class="pm-chip pm-chip--warn">Important</span>') \
            if item in important else ("", "")
        rows.append(f'<li{flag[0]}><span aria-hidden="true">✕</span><span>{esc(item)}{flag[1]}</span></li>')
    gaps = f'<ul>{"".join(rows)}</ul>' if rows else '<p>No requirements are unmet for this animal.</p>'
    return f'{ok_box}<div class="pm-req pm-req--unmet"><p class="pm-req__title">Requirements not met</p>{gaps}</div>'


def fact_tiles(rows: Sequence[tuple[str, str]]) -> str:
    """Value-over-label tiles (age, sex, size) on the animal profile."""
    tiles = "".join(f'<div><b>{esc(value)}</b><span>{esc(name)}</span></div>' for value, name in rows)
    return f'<div class="pm-tiles">{tiles}</div>'


def facts(rows: Sequence[tuple[str, str, str]]) -> str:
    """Icon, label and value rows (an animal's needs at a glance)."""
    items = "".join(f'<li><span class="pm-fact__icon" aria-hidden="true">{esc(icon)}</span>'
                    f'<span class="pm-fact__label">{esc(name)}</span>'
                    f'<span class="pm-fact__value">{esc(value)}</span></li>' for icon, name, value in rows)
    return f'<ul class="pm-facts">{items}</ul>'


def answer_rows(rows: Sequence[tuple[str, str]]) -> str:
    """Question and answer pairs for the questionnaire's review step."""
    items = "".join(f'<div><dt>{esc(q)}</dt><dd>{esc(a)}</dd></div>' for q, a in rows)
    return f'<dl class="pm-answers">{items}</dl>'


def empty_state(title: str, body: str, emoji: str = "🐾") -> str:
    return (f'<div class="pm-empty"><div class="pm-empty__emoji" aria-hidden="true">{esc(emoji)}</div>'
            f'<h3>{esc(title)}</h3><p>{esc(body)}</p></div>')


def stat(name: str, value: int, emoji: str, tone: str = "pink", sub: str = "") -> str:
    """A dashboard count: icon badge, small capital label, big number and a line under it."""
    line = f'<span class="pm-stat__sub">{esc(sub)}</span>' if sub else ""
    return (f'<div class="pm-stat pm-stat--{esc(tone)}"><span class="pm-stat__icon" aria-hidden="true">{esc(emoji)}</span>'
            f'<div><span class="pm-stat__label">{esc(name)}</span><span class="pm-stat__value">{int(value)}</span>'
            f'{line}</div></div>')


def stats(cards: Sequence[str]) -> str:
    return f'<div class="pm-stats">{"".join(cards)}</div>'


def bars(rows: Sequence[tuple[str, int]], total: int) -> str:
    """Horizontal bars: each row's share of the total (the shelter's species mix)."""
    items = []
    for name, value in rows:
        share = round(100 * value / total) if total else 0
        items.append(f'<li><span class="pm-bars__name">{esc(name)}</span><b>{int(value)}</b>'
                     f'<span class="pm-bars__track" aria-hidden="true"><span style="width:{share}%"></span></span></li>')
    return f'<ul class="pm-bars">{"".join(items)}</ul>'


def access_card(level: str) -> str:
    return (f'<div class="pm-access"><span aria-hidden="true">🛡️</span><div><small>Access level</small>'
            f'<b>{esc(level)}</b></div></div>')


def profile_card(name: str, rows: Sequence[tuple[str, str]]) -> str:
    """The account summary: initials, name and label/value rows."""
    items = "".join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in rows)
    return (f'<div class="pm-profile"><span class="pm-avatar pm-avatar--lg" aria-hidden="true">{esc(initials(name))}</span>'
            f'<div><h2>{esc(name)}</h2><dl>{items}</dl></div></div>')


def welcome(kicker: str, title: str, copy: str, status: str = "") -> str:
    """The home page hero text (the original's "Welcome Back" header)."""
    line = f'<p class="pm-status">{esc(status)}</p>' if status else ""
    return (f'<div class="pm-welcome">{eyebrow(kicker)}<h1>{esc(title)}</h1>'
            f'<p class="pm-lead">{esc(copy)}</p>{line}</div>')


def art(alt: str) -> str:
    """The illustration of a dog, a cat and a rabbit (static/hero.png)."""
    return f'<img class="pm-art" src="{HERO}" alt="{esc(alt)}">'


def done_card(title: str, body: str) -> str:
    """The questionnaire's completion card."""
    return (f'<div class="pm-done"><span class="pm-done__tick" aria-hidden="true">✓</span>'
            f'<h2>{esc(title)}</h2><p>{esc(body)}</p></div>')
