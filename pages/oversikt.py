"""Side 1 – Oversikt: banner, veiledning, kriterier, fem-fases tidslinje og
jury-matrise. Kriteriene og fasene er nå DATASTYRT (Kriterier-/Faser-fanen i
regnearket), ikke lenger hardkodet."""

import os

import streamlit as st

from components import kriterie_seksjon_html, rutenett
from data import er_tall
from jury import aktive_kriterier, aktiv_fase, kriterier_per_steg, mine_kriterier, read_criteria, read_faser, read_jury, read_veiledning
from sheets import read_fase1_scores, read_ratings, read_stores
from theme import KLASSE_IKON, KLASSE_TONE, STEG_FARGE


sh = st.session_state.get("_sh")
butikker, jury, alle_kriterier, faser = {}, {}, [], []
if sh:
    try:
        butikker, _ = read_stores(sh)
        jury = read_jury(sh)
        alle_kriterier = read_criteria(sh)
        faser = read_faser(sh)
    except Exception:
        pass

kriterier_fase3 = aktive_kriterier(alle_kriterier, fase="Fase 3")
KRITERIER_PER_STEG = kriterier_per_steg(kriterier_fase3)
STEG = list(KRITERIER_PER_STEG)
kriterium_info = {k["kriterium"]: k for k in kriterier_fase3}
gjeldende_fase = aktiv_fase(faser) if faser else None
fase_tekst = f"Fase {gjeldende_fase['Fase']} · {gjeldende_fase['Navn']}" if gjeldende_fase else "Fase 3 · Ekspertvurdering"

BANNER_HTML = (
    '<div class="banner">'
    f'<div class="fase">Bringprisen · {fase_tekst}</div>'
    "<h1>Bringprisen</h1>"
    "<p>Vurder butikkene på dine tildelte kriterier – gi score fra 1 til 5 og legg gjerne igjen en kommentar. "
    "Vurderingene lagres fortløpende i regnearket.</p>"
    "</div>"
)
if os.path.exists("assets/bring-logo.svg"):
    logo_kol, banner_kol = st.columns([1, 6])
    with logo_kol:
        st.image("assets/bring-logo.svg", width=64)
    with banner_kol:
        st.markdown(BANNER_HTML, unsafe_allow_html=True)
else:
    st.markdown(BANNER_HTML, unsafe_allow_html=True)
if st.button("Start vurdering →", type="primary", icon=":material/edit_note:"):
    st.switch_page("pages/vurdering.py")

# ── Hvordan bedømme ──
st.subheader("Hvordan bedømme", anchor=False)
veiledning = []
if sh:
    try:
        veiledning = read_veiledning(sh)
    except Exception:
        pass
if veiledning:
    for rad in veiledning:
        overskrift, tekst = rad.get("Overskrift", ""), rad.get("Tekst", "")
        if overskrift:
            with st.expander(overskrift):
                st.markdown(tekst)
else:
    st.caption("Veiledningsteksten lastes fra fanen «Veiledning» i regnearket.")

st.divider()

# ── Størrelsesklasser ──
st.subheader("Størrelsesklasser", anchor=False)
KLASSE_DEFINISJON = [("Liten", "Opp til 100 MNOK"), ("Stor", "Fra 100 MNOK")]
antall_per_klasse = {k: 0 for k, _ in KLASSE_DEFINISJON}
for info in butikker.values():
    if info.get("klasse") in antall_per_klasse:
        antall_per_klasse[info["klasse"]] += 1
deler = [
    f'<div class="rutenett-kort" style="background:{KLASSE_TONE.get(k, "")};border-top-color:transparent;">'
    f'<div class="kort-ikon">{KLASSE_IKON.get(k, "")}</div><div class="stor-tall">{antall_per_klasse[k]}</div>'
    f'<div style="font-weight:700;">{k}</div><div class="belop">{belop}</div></div>'
    for k, belop in KLASSE_DEFINISJON
]
st.markdown(f'<div class="rutenett to-per-rad">{"".join(deler)}</div>', unsafe_allow_html=True)

st.divider()

# ── Kriterier etter kundereisen ──
jurynavn = st.session_state.get("_jurynavn")
mine = mine_kriterier(jury, jurynavn) if jurynavn else set()

if STEG:
    # Viser hele Word-dokumentet: også Del 2 og Samlet vurdering, som ikke scores her.
    alle_aktive = aktive_kriterier(alle_kriterier)
    st.html(kriterie_seksjon_html(kriterier_per_steg(alle_aktive), {k["kriterium"]: k for k in alle_aktive}, mine))
else:
    st.caption("Ingen kriterier funnet – sjekk fanen «Kriterier» i regnearket.")

st.divider()

# ── Jury og ekspertområder ──
st.subheader("Jury og ekspertområder", anchor=False)
if not jury:
    st.caption("Ingen jurymedlemmer lagt til ennå.")
else:
    from jury import beskriv_tildeling

    # Kompakt kort-variant (vises alltid øverst, og alene på mobil)
    kort = []
    for navn in sorted(jury.keys()):
        beskrivelse = beskriv_tildeling(navn, jury, KRITERIER_PER_STEG)
        merkelapper = "".join(
            f'<span class="klasse-badge" style="margin:2px 4px 2px 0;border-color:{STEG_FARGE.get(d.split(" – ")[0].strip(), "#888")};background:color-mix(in srgb, {STEG_FARGE.get(d.split(" – ")[0].strip(), "#888")} 20%, transparent);">{d.strip()}</span>'
            for d in beskrivelse.split("·")
        ) if beskrivelse else '<span style="color:var(--tekst-dempet);font-size:13px;">Ingen kriterier tildelt</span>'
        kort.append(f'<h4>{navn}</h4><div>{merkelapper}</div>')
    kort_html = "".join(f'<div class="rutenett-kort">{k}</div>' for k in kort)
    st.markdown(f'<div class="rutenett kun-mobil-vis">{kort_html}</div>', unsafe_allow_html=True)

    # Full matrise (skjules på mobil via CSS)
    if STEG:
        navn_rader = sorted(jury.keys())
        thead = "<tr><th style='text-align:left;padding:6px 10px;'>Jurymedlem</th>"
        for kat in STEG:
            for k in KRITERIER_PER_STEG[kat]:
                thead += f'<th style="background:{STEG_FARGE.get(kat, "#888")};color:white;font-size:11px;padding:6px 4px;writing-mode:vertical-rl;text-orientation:mixed;max-width:26px;">{kriterium_info[k]["visningsnavn"][:28]}</th>'
        thead += "</tr>"

        rader_html = ""
        dekning = {k: 0 for kat in STEG for k in KRITERIER_PER_STEG[kat]}
        for navn in navn_rader:
            rad = f"<tr><td style='padding:6px 10px;font-weight:600;white-space:nowrap;'>{navn}</td>"
            for kat in STEG:
                for k in KRITERIER_PER_STEG[kat]:
                    tildelt = k in mine_kriterier(jury, navn)
                    if tildelt:
                        dekning[k] += 1
                    rad += f"<td style='text-align:center;background:color-mix(in srgb, {STEG_FARGE.get(kat, '#888')} 22%, transparent);'>{'✅' if tildelt else ''}</td>"
            rad += "</tr>"
            rader_html += rad

        dekning_rad = "<tr><td style='padding:6px 10px;font-weight:700;'>Dekning</td>"
        for kat in STEG:
            for k in KRITERIER_PER_STEG[kat]:
                antall = dekning[k]
                farge = "color:var(--feil);font-weight:800;" if antall == 0 else "color:var(--tekst-dempet);"
                dekning_rad += f"<td style='text-align:center;{farge}'>{antall}</td>"
        dekning_rad += "</tr>"

        st.markdown(
            f'<div class="kun-desktop-vis" style="overflow-x:auto;"><table style="border-collapse:collapse;width:100%;">'
            f"<thead>{thead}</thead><tbody>{rader_html}{dekning_rad}</tbody></table></div>",
            unsafe_allow_html=True,
        )
        if any(v == 0 for v in dekning.values()):
            st.warning("Ett eller flere kriterier har ingen jurymedlem tildelt ennå (markert rødt i dekningsraden).", icon=":material/warning:")

st.divider()
st.subheader("Fasene i konkurransen", anchor=False)
if faser:
    faser_sortert = sorted(faser, key=lambda f: int(f.get("Fase", 0)))

    def _fase_fremdrift(navn_fase):
        """Henter fremdrift i prosent for faser vi faktisk har data for i
        appen – None for faser uten datakilde (vises da uten linje)."""
        if not sh:
            return None
        try:
            if navn_fase == "Ekspertvurdering":
                kriterier = [k["kriterium"] for k in aktive_kriterier(alle_kriterier, fase="Fase 3")]
                rating_data = read_ratings(sh)
                total = len(butikker) * len(kriterier)
                fylt = sum(1 for n in butikker for k in kriterier if rating_data.get(n, {}).get("scorer", {}).get(k))
            elif navn_fase == "Juryvurdering":
                kriterier = [k["kriterium"] for k in aktive_kriterier(alle_kriterier, fase="Fase 2")]
                fase1 = read_fase1_scores(sh)
                total = len(butikker) * len(kriterier)
                fylt = sum(1 for n in butikker for k in kriterier if fase1.get(n, {}).get(k))
            else:
                return None
            return round(fylt / total * 100) if total else None
        except Exception:
            return None

    deler = []
    for idx, f in enumerate(faser_sortert):
        status = str(f.get("Status", "")).strip() or "Kommende"
        css_klasse = {"Fullført": "fullfort", "Pågår": "pagar"}.get(status, "kommende")
        sirkel_innhold = "✓" if status == "Fullført" else str(f.get("Fase", idx + 1))
        beskrivelse = f.get("Beskrivelse", "").strip()
        beskrivelse_html = f'<div class="fase-beskrivelse">{beskrivelse}</div>' if beskrivelse else ""
        dato_start, dato_slutt = f.get("Startdato", "").strip(), f.get("Sluttdato", "").strip()
        dato_html = f'<div class="fase-dato">{dato_start}{" – " + dato_slutt if dato_slutt else ""}</div>' if (dato_start or dato_slutt) else ""
        fremdrift_html = ""
        if status == "Pågår":
            prosent = _fase_fremdrift(f.get("Navn", ""))
            if prosent is not None:
                fremdrift_html = (
                    f'<div class="fremdrift-bakgrunn" style="margin-top:8px;height:6px;">'
                    f'<div class="fremdrift-fyll" style="width:{prosent}%;"></div></div>'
                    f'<div class="fase-dato">{prosent}% vurdert</div>'
                )
        deler.append(
            f'<div class="fase-kort {css_klasse}"><div class="fase-sirkel">{sirkel_innhold}</div>'
            f'<div class="fase-badge {css_klasse}">{status}</div>'
            f'<div class="fase-navn">{f.get("Navn", "")}</div>'
            f'{beskrivelse_html}{dato_html}{fremdrift_html}</div>'
        )
        if idx < len(faser_sortert) - 1:
            linje_farge = "gronn" if status == "Fullført" else "gra"
            deler.append(f'<div class="fase-linje {linje_farge}"></div>')
    st.markdown(f'<div class="fase-rad">{"".join(deler)}</div>', unsafe_allow_html=True)
else:
    st.caption("Fasene lastes fra fanen «Faser» i regnearket.")
