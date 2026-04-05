# ═══════════════════════════════════════════════════════════════════════════════
#  🃏  Chinchón — Spanish Card Game  (BAT 3301 · Colazo)
#  Player vs Computer · Baraja Española · 40 cards
# ═══════════════════════════════════════════════════════════════════════════════

import streamlit as st
import random
import math
from itertools import combinations

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Chinchón",
    page_icon="🃏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Green felt table */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    background: radial-gradient(ellipse at 50% 20%,#1d6b35 0%,#145228 55%,#0c3a1c 100%) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
.block-container { padding-top: 0.8rem !important; max-width: 1100px; }

/* Title */
.game-title {
    font-size: 30px; font-weight: 800; color: #fbbf24;
    text-shadow: 0 2px 8px rgba(0,0,0,0.6);
    letter-spacing: -1px; line-height: 1.1;
}
.game-sub { font-size: 12px; color: rgba(255,255,255,0.45); letter-spacing: 1.5px; }

/* Score display */
.score-panel {
    background: rgba(0,0,0,0.35);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px; padding: 8px 16px; text-align: center;
}

/* Section label */
.sec-lbl {
    font-size: 10px; font-weight: 700; letter-spacing: 2px;
    color: rgba(255,255,255,0.45); text-transform: uppercase; margin-bottom: 6px;
}

/* Message */
.msg {
    background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px; padding: 8px 14px; color: rgba(255,255,255,0.85);
    font-size: 13px; text-align: center; margin: 6px 0;
}
.msg-win  { border-color:#86efac; color:#86efac; background:rgba(22,101,52,0.3); }
.msg-lose { border-color:#fca5a5; color:#fca5a5; background:rgba(153,27,27,0.3); }
.msg-cc   { border-color:#fbbf24; color:#fbbf24; background:rgba(120,53,15,0.3); }

/* Pile area */
.pile-zone {
    background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px; padding: 10px 14px; margin-bottom: 10px;
}

/* Card area backdrop */
.hand-zone {
    background: rgba(0,0,0,0.15);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 12px 16px; margin-bottom: 10px;
}

/* Divider */
hr.felt { border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 10px 0; }

/* Button tweaks */
.stButton button {
    border-radius: 6px !important; font-size: 12px !important;
    font-weight: 600 !important; padding: 4px 4px !important;
}

/* Menu centering */
.menu-wrap { text-align: center; padding: 30px 0 20px; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  CARD CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
SUITS  = ['Oros', 'Copas', 'Espadas', 'Bastos']
VALUES = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]      # 8 and 9 don't exist

SUIT_EMOJI = {'Oros': '🪙', 'Copas': '🍷', 'Espadas': '⚔️', 'Bastos': '🏑'}
SUIT_COLOR = {'Oros': '#92400e', 'Copas': '#991b1b', 'Espadas': '#1e3a8a', 'Bastos': '#14532d'}
SUIT_LIGHT = {'Oros': '#fef3c7', 'Copas': '#fee2e2', 'Espadas': '#dbeafe', 'Bastos': '#d1fae5'}

def vlabel(v):
    """Display label for a card value."""
    return {1: 'A'}.get(v, str(v))

def vpoints(v):
    """Point value of an unmatched card."""
    return {1:1,2:2,3:3,4:4,5:5,6:6,7:7,10:10,11:10,12:10}[v]

def cstr(c):
    """Short card string for messages."""
    return f"{vlabel(c['v'])}{SUIT_EMOJI[c['s']]}"

# ═══════════════════════════════════════════════════════════════════════════════
#  DECK
# ═══════════════════════════════════════════════════════════════════════════════
def make_deck():
    deck = [{'v': v, 's': s, 'id': si * 10 + vi}
            for si, s in enumerate(SUITS)
            for vi, v in enumerate(VALUES)]
    random.shuffle(deck)
    return deck

# ═══════════════════════════════════════════════════════════════════════════════
#  MELD LOGIC
# ═══════════════════════════════════════════════════════════════════════════════
def rank(v):
    return VALUES.index(v)

def is_group(cards):
    """3 or 4 cards of same value."""
    return len(cards) >= 3 and len(set(c['v'] for c in cards)) == 1

def is_sequence(cards):
    """3+ consecutive cards of the same suit.
    In the Spanish deck, 7 and 10 are consecutive (no 8 or 9)."""
    if len(cards) < 3:
        return False
    if len(set(c['s'] for c in cards)) != 1:
        return False
    rnks = sorted(rank(c['v']) for c in cards)
    return all(rnks[i+1] == rnks[i]+1 for i in range(len(rnks)-1))

def is_meld(cards):
    return bool(cards) and (is_group(cards) or is_sequence(cards))

def is_chinchon(hand):
    """All 7 cards: same suit, consecutive sequence."""
    return len(hand) == 7 and is_sequence(hand)

def find_win(hand):
    """
    Check if a 7-card hand can be declared.
    Returns (can_win, is_chinchon, list_of_melds).
    Winning = Chinchón OR two valid sets totalling 7 cards.
    """
    if len(hand) != 7:
        return False, False, []

    # Chinchón: all 7 same-suit sequence
    if is_chinchon(hand):
        return True, True, [hand[:]]

    # 7-card group (very rare)
    if is_group(hand):
        return True, False, [hand[:]]

    # Split into 3+4
    for idx3 in combinations(range(7), 3):
        m1 = [hand[i] for i in idx3]
        m2 = [hand[i] for i in range(7) if i not in idx3]
        if is_meld(m1) and is_meld(m2):
            return True, False, [m1, m2]

    return False, False, []


def winning_discards(hand8):
    """
    For an 8-card hand, return list of (index, is_chinchon) pairs
    where discarding that card produces a winning 7-card hand.
    """
    result = []
    if len(hand8) != 8:
        return result
    for i in range(8):
        rem = [hand8[j] for j in range(8) if j != i]
        can, cc, _ = find_win(rem)
        if can:
            result.append((i, cc))
    return result

# ═══════════════════════════════════════════════════════════════════════════════
#  DEADWOOD CALCULATOR
# ═══════════════════════════════════════════════════════════════════════════════
def deadwood(hand):
    """
    For a 7-card hand, return (min_penalty, unmatched_cards).
    Finds the subset of melds that minimises the sum of unmatched card values.
    """
    total_pts = sum(vpoints(c['v']) for c in hand)
    best_pen  = total_pts
    best_rem  = hand[:]

    # Try one meld of any size
    for sz in range(3, 8):
        for idx in combinations(range(len(hand)), sz):
            sub = [hand[i] for i in idx]
            if not is_meld(sub):
                continue
            rem  = [hand[i] for i in range(len(hand)) if i not in idx]
            pen  = sum(vpoints(c['v']) for c in rem)
            if pen < best_pen:
                best_pen = pen
                best_rem = rem

    # Try two melds
    for sz1 in range(3, 5):
        for idx1 in combinations(range(len(hand)), sz1):
            m1 = [hand[i] for i in idx1]
            if not is_meld(m1):
                continue
            rem1_idx = [i for i in range(len(hand)) if i not in idx1]
            for sz2 in range(3, len(rem1_idx) + 1):
                for sub2 in combinations(range(len(rem1_idx)), sz2):
                    m2 = [hand[rem1_idx[j]] for j in sub2]
                    if not is_meld(m2):
                        continue
                    used = set(idx1) | {rem1_idx[j] for j in sub2}
                    rem  = [hand[i] for i in range(len(hand)) if i not in used]
                    pen  = sum(vpoints(c['v']) for c in rem)
                    if pen < best_pen:
                        best_pen = pen
                        best_rem = rem

    return best_pen, best_rem


# ═══════════════════════════════════════════════════════════════════════════════
#  COMPUTER AI
# ═══════════════════════════════════════════════════════════════════════════════
def hand_quality(h7):
    """Score a 7-card hand. Higher = closer to winning."""
    can, cc, _ = find_win(h7)
    if can:
        return 2000 + (1000 if cc else 0)

    # Best subset that forms a meld
    best = 0
    for sz in range(6, 2, -1):
        for idx in combinations(range(len(h7)), sz):
            sub = [h7[i] for i in idx]
            if is_meld(sub):
                best = max(best, sz)
                break

    # Near-meld bonus (pairs of same value, or adjacent same-suit)
    bonus = 0.0
    for i, j in combinations(range(len(h7)), 2):
        a, b = h7[i], h7[j]
        if a['v'] == b['v']:
            bonus += 0.5
        elif a['s'] == b['s'] and abs(rank(a['v']) - rank(b['v'])) == 1:
            bonus += 0.5

    return best * 100 + bonus


def best_discard_idx(h8):
    """Return the index of the card to discard from an 8-card hand."""
    scores = [hand_quality([h8[j] for j in range(8) if j != i]) for i in range(8)]
    return scores.index(max(scores))


def computer_play(hand, discard_pile, deck):
    """
    Computer draws, chooses a card to discard, and optionally wins.
    Returns: (new_hand, discarded_card, source, won, is_chinchon)
    """
    draw_from_discard = False

    if discard_pile:
        top = discard_pile[-1]
        h8_d = hand + [top]
        di_d  = best_discard_idx(h8_d)
        h7_d  = [h8_d[j] for j in range(8) if j != di_d]
        q_d   = hand_quality(h7_d)
        q_now = hand_quality(hand)
        # Take discard if it clearly improves the hand or gives a win
        if q_d > q_now + 30 or q_d >= 2000:
            draw_from_discard = True

    if draw_from_discard and discard_pile:
        drawn  = discard_pile.pop()
        source = 'discard'
    else:
        # Reshuffle discard into deck if needed
        if not deck:
            if len(discard_pile) > 1:
                top = discard_pile.pop()
                random.shuffle(discard_pile)
                deck.extend(discard_pile)
                discard_pile.clear()
                discard_pile.append(top)
            else:
                return hand, None, 'none', False, False
        drawn  = deck.pop()
        source = 'deck'

    h8        = hand + [drawn]
    di        = best_discard_idx(h8)
    discarded = h8[di]
    new_hand  = [h8[j] for j in range(8) if j != di]
    can, cc, _ = find_win(new_hand)
    return new_hand, discarded, source, can, cc

# ═══════════════════════════════════════════════════════════════════════════════
#  CARD SVG  (Fournier-inspired design)
# ═══════════════════════════════════════════════════════════════════════════════
_CW, _CH = 72, 108   # card pixel dimensions

# Suit symbol positions (x, y) and sizes for values 1-7
_POS = {
    1: [(36, 54)],
    2: [(36, 30), (36, 78)],
    3: [(36, 24), (36, 54), (36, 84)],
    4: [(22, 32), (50, 32), (22, 76), (50, 76)],
    5: [(22, 24), (50, 24), (36, 54), (22, 84), (50, 84)],
    6: [(22, 24), (50, 24), (22, 54), (50, 54), (22, 84), (50, 84)],
    7: [(22, 20), (50, 20), (36, 38), (22, 54), (50, 54), (22, 76), (50, 76)],
}
_SZ = {1: 15, 2: 13, 3: 12, 4: 10, 5: 9, 6: 9, 7: 8}

_TEXT_COL = {
    'Oros':    '#8A6010',
    'Espadas': '#1A3A80',
    'Copas':   '#8A0000',
    'Bastos':  '#1E5A0E',
}


def _sym(suit, cx, cy, sz):
    """SVG markup for one suit symbol centred at (cx, cy) with half-size sz."""
    cx, cy = round(cx, 1), round(cy, 1)
    if suit == 'Oros':
        sw = max(1.1, sz * 0.12)
        return (
            f'<circle cx="{cx}" cy="{cy}" r="{sz:.1f}" fill="#F6C820" stroke="#A07818" stroke-width="{sw:.1f}"/>' 
            f'<circle cx="{cx}" cy="{cy}" r="{sz*0.62:.1f}" fill="none" stroke="#A07818" stroke-width="{sw*0.55:.1f}"/>' 
            f'<circle cx="{cx}" cy="{cy}" r="{sz*0.26:.1f}" fill="#A07818"/>' 
        )
    elif suit == 'Espadas':
        bw = max(1.4, sz * 0.17)
        gw = sz * 0.72
        return (
            f'<polygon points="{cx},{cy-sz:.1f} {cx-bw:.1f},{cy-sz*0.28:.1f} {cx+bw:.1f},{cy-sz*0.28:.1f}" fill="#4068B8"/>' 
            f'<rect x="{cx-bw:.1f}" y="{cy-sz*0.28:.1f}" width="{bw*2:.1f}" height="{sz*0.54:.1f}" fill="#4068B8"/>' 
            f'<rect x="{cx-gw:.1f}" y="{cy+sz*0.24:.1f}" width="{gw*2:.1f}" height="{sz*0.17:.1f}" fill="#9B6E22" rx="2"/>' 
            f'<rect x="{cx-bw*1.6:.1f}" y="{cy+sz*0.41:.1f}" width="{bw*3.2:.1f}" height="{sz*0.59:.1f}" fill="#7A4C18" rx="2"/>' 
        )
    elif suit == 'Copas':
        bw = sz * 0.86; bh = sz * 0.70
        y0 = cy - sz; ym = y0 + bh
        sw2 = sz * 0.15; sh = sz * 0.42; baw = sz * 0.58
        return (
            f'<path d="M{cx-bw:.1f},{y0:.1f} Q{cx-bw:.1f},{ym:.1f} {cx:.1f},{ym:.1f} Q{cx+bw:.1f},{ym:.1f} {cx+bw:.1f},{y0:.1f} Z" fill="#CC1800" stroke="#880000" stroke-width="0.9"/>' 
            f'<rect x="{cx-sw2:.1f}" y="{ym:.1f}" width="{sw2*2:.1f}" height="{sh:.1f}" fill="#AA1400"/>' 
            f'<ellipse cx="{cx:.1f}" cy="{ym+sh:.1f}" rx="{baw:.1f}" ry="{sz*0.17:.1f}" fill="#880000"/>' 
        )
    else:  # Bastos
        ang = 20 * 3.14159 / 180
        rx_ = max(3.5, sz * 0.30)
        kr  = max(4.0, sz * 0.40)
        tx  = cx - math.sin(ang) * sz; ty = cy - math.cos(ang) * sz
        bx  = cx + math.sin(ang) * sz; by_ = cy + math.cos(ang) * sz
        return (
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx_:.1f}" ry="{sz:.1f}" fill="#589030" stroke="#286010" stroke-width="0.8" transform="rotate(20,{cx:.1f},{cy:.1f})"/>' 
            f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="{kr:.1f}" fill="#487820"/>' 
            f'<circle cx="{bx:.1f}" cy="{by_:.1f}" r="{kr:.1f}" fill="#487820"/>' 
        )


def _face_body(suit, v):
    """SVG body elements for face cards (v=10 Sota, 11 Caballo, 12 Rey)."""
    cx, cy = _CW // 2, _CH // 2
    band = {'Oros':'#C89010','Espadas':'#2050A0','Copas':'#AA1400','Bastos':'#2E6818'}[suit]

    # Coloured bands top and bottom
    out = (
        f'<rect x="0" y="0" width="{_CW}" height="28" fill="{band}" opacity="0.35" rx="5"/>' 
        f'<rect x="0" y="{_CH-28}" width="{_CW}" height="28" fill="{band}" opacity="0.35"/>' 
    )

    if v == 10:   # Sota — standing page
        out += (
            f'<circle cx="{cx}" cy="{cy-24}" r="10" fill="#FDBF78" stroke="#8B5A28" stroke-width="1"/>' 
            f'<rect x="{cx-11}" y="{cy-14}" width="22" height="30" rx="4" fill="{band}"/>' 
            f'<rect x="{cx-8}" y="{cy+16}" width="7" height="18" rx="3" fill="{band}"/>' 
            f'<rect x="{cx+1}" y="{cy+16}" width="7" height="18" rx="3" fill="{band}"/>' 
            f'<rect x="{cx-18}" y="{cy-11}" width="8" height="14" rx="3" fill="{band}"/>' 
            f'<rect x="{cx+10}" y="{cy-11}" width="8" height="14" rx="3" fill="{band}"/>' 
        )
    elif v == 11:  # Caballo — knight on horse
        out += (
            f'<ellipse cx="{cx}" cy="{cy+16}" rx="19" ry="10" fill="#D0A070"/>' 
            f'<circle cx="{cx+16}" cy="{cy+6}" r="7" fill="#D0A070"/>' 
            f'<rect x="{cx-15}" y="{cy+24}" width="5" height="14" rx="2" fill="#B08050"/>' 
            f'<rect x="{cx-6}" y="{cy+24}" width="5" height="14" rx="2" fill="#B08050"/>' 
            f'<rect x="{cx+4}" y="{cy+24}" width="5" height="14" rx="2" fill="#B08050"/>' 
            f'<rect x="{cx+12}" y="{cy+24}" width="5" height="14" rx="2" fill="#B08050"/>' 
            f'<circle cx="{cx-2}" cy="{cy-16}" r="9" fill="#FDBF78" stroke="#8B5A28" stroke-width="1"/>' 
            f'<rect x="{cx-10}" y="{cy-7}" width="19" height="22" rx="3" fill="{band}"/>' 
        )
    else:  # Rey — king
        out += (
            f'<circle cx="{cx}" cy="{cy-22}" r="10" fill="#FDBF78" stroke="#8B5A28" stroke-width="1"/>' 
            f'<polygon points="{cx-10},{cy-31} {cx-10},{cy-40} {cx-4},{cy-33} {cx},{cy-42} {cx+4},{cy-33} {cx+10},{cy-40} {cx+10},{cy-31}" fill="#F8C820" stroke="#A07010" stroke-width="1.2"/>' 
            f'<circle cx="{cx}" cy="{cy-37}" r="3.5" fill="#CC2020"/>' 
            f'<polygon points="{cx-15},{cy-12} {cx+15},{cy-12} {cx+19},{cy+36} {cx-19},{cy+36}" fill="{band}"/>' 
            f'<rect x="{cx-14}" y="{cy+2}" width="28" height="6" fill="#F8C820"/>' 
            f'<rect x="{cx-22}" y="{cy-10}" width="9" height="16" rx="3" fill="{band}"/>' 
            f'<rect x="{cx+13}" y="{cy-10}" width="9" height="16" rx="3" fill="{band}"/>' 
        )

    # Small suit symbol watermark centre-bottom
    out += _sym(suit, cx, cy + 30, 9)
    return out


_BACK = (
    f'<div style="width:{_CW}px;height:{_CH}px;display:inline-flex;align-items:center;' 
    f'justify-content:center;' 
    f'background:linear-gradient(160deg,#1e40af 0%,#2563eb 60%,#1e3a8a 100%);' 
    f'border-radius:7px;border:2px solid #60a5fa;' 
    f'box-shadow:2px 5px 10px rgba(0,0,0,0.5);margin:2px;flex-shrink:0;">' 
    f'<span style="font-size:30px;color:rgba(255,255,255,0.22);">✦</span>' 
    f'</div>'
)


def card_html(card, new=False, win=False, facedown=False):
    if facedown or card is None:
        return _BACK
    v = card['v']; s = card['s']; lb = vlabel(v)
    tcol = _TEXT_COL[s]

    if win:
        border = '3px solid #fbbf24'
        shadow = '0 0 18px #fbbf2480, 2px 5px 10px rgba(0,0,0,0.4)'
    elif new:
        border = '3px solid #60a5fa'
        shadow = '0 0 14px rgba(96,165,250,0.65), 2px 5px 10px rgba(0,0,0,0.4)'
    else:
        border = '1.5px solid #b8b8b8'
        shadow = '2px 5px 10px rgba(0,0,0,0.35)'

    # Build centre SVG
    if v in (10, 11, 12):
        body = _face_body(s, v)
    else:
        body = ''.join(_sym(s, px, py, _SZ[v]) for px, py in _POS[v])

    return (
        f'<div style="width:{_CW}px;height:{_CH}px;background:#FFFEF0;border:{border};' 
        f'border-radius:7px;box-shadow:{shadow};margin:2px;flex-shrink:0;' 
        f'position:relative;overflow:hidden;display:inline-block;">' 
        f'<svg width="{_CW}" height="{_CH}" xmlns="http://www.w3.org/2000/svg" ' 
        f'style="position:absolute;top:0;left:0;">{body}</svg>' 
        f'<div style="position:absolute;top:3px;left:4px;font-size:13px;font-weight:900;' 
        f'color:{tcol};line-height:1;text-shadow:0 0 4px #fff8,0 1px 2px #fff;">{lb}</div>' 
        f'<div style="position:absolute;bottom:3px;right:4px;font-size:13px;font-weight:900;' 
        f'color:{tcol};line-height:1;transform:rotate(180deg);' 
        f'text-shadow:0 0 4px #fff8,0 1px 2px #fff;">{lb}</div>' 
        f'</div>'
    )


def hand_html_row(cards, highlights=None, win_set=None, facedown=False, gap=6):
    """Render a horizontal row of cards as one HTML block."""
    hl  = highlights or set()
    ws  = win_set   or set()
    out = f'<div style="display:flex;gap:{gap}px;flex-wrap:nowrap;align-items:flex-end;">'
    for i, c in enumerate(cards):
        out += card_html(c, new=(i in hl), win=(i in ws), facedown=facedown)
    out += '</div>'
    return out


# ═══════════════════════════════════════════════════════════════════════════════
#  GAME ACTIONS  (module-level so they are callable from the header)
# ═══════════════════════════════════════════════════════════════════════════════
def _run_computer_turn():
    """Execute computer's turn and update session state. Returns nothing."""
    ss = st.session_state
    new_ch, disc_c, src, comp_can, comp_cc = computer_play(
        ss.computer_hand, ss.discard_pile, ss.deck)
    if disc_c is not None:
        ss.discard_pile.append(disc_c)
    ss.computer_hand = new_ch
    src_txt  = "the discard pile" if src == 'discard' else "the deck"
    disc_txt = cstr(disc_c) if disc_c else "?"
    ss.computer_msg = f"\U0001f916 Computer drew from {src_txt} \u00b7 discarded {disc_txt}"
    if comp_can:
        ss.phase = 'game_over'
        ss.hand_penalty_computer = 0; ss.hand_unmatched_computer = []
        if comp_cc:
            ss.game_result = 'comp_cc'
            ss.hand_penalty_player = None; ss.hand_unmatched_player = []
            ss.computer_msg += " \u00b7 \U0001f3c5 COMPUTER CHINCH\u00d3N!"
            ss.message = "\U0001f480 Computer got Chinch\u00f3n and wins the game!"
        else:
            pen, unmatched       = deadwood(ss.player_hand)
            ss.player_score     += pen
            ss.hand_penalty_player   = pen
            ss.hand_unmatched_player = unmatched
            ss.game_result    = 'comp_wins'
            ss.computer_msg  += " \u00b7 \u270b Computer stops!"
            ss.message = f"\U0001f614 Computer stopped. You pay {pen} penalty points."
    else:
        ss.message = "Your turn \u2014 draw a card."


def do_discard(idx: int):
    """Discard player card at idx, run computer turn, update state."""
    ss = st.session_state
    n_h = len(ss.player_hand)
    if not (0 <= idx < n_h):
        return
    discarded_card = ss.player_hand[idx]
    remaining      = [ss.player_hand[j] for j in range(n_h) if j != idx]
    ss.discard_pile.append(discarded_card)
    can, is_cc_result, melds = find_win(remaining)
    if can:
        ss.player_hand = remaining; ss.melds = melds
        ss.phase = 'game_over'; ss.computer_msg = ""
        ss.hand_penalty_player = 0; ss.hand_unmatched_player = []
        if is_cc_result:
            ss.game_result             = 'player_cc'
            ss.hand_penalty_computer   = None
            ss.hand_unmatched_computer = []
            ss.message = "\U0001f3c5 \u00a1CHINCH\u00d3N! You win the entire game!"
        else:
            pen, unmatched         = deadwood(ss.computer_hand)
            ss.computer_score     += pen
            ss.hand_penalty_computer   = pen
            ss.hand_unmatched_computer = unmatched
            ss.game_result   = 'player_wins'
            ss.message = f"\u270b You stopped! Computer pays {pen} penalty points."
    else:
        ss.player_hand  = remaining; ss.phase = 'draw'
        ss.drawn_idx    = None; ss.win_idx_list = []
        _run_computer_turn()
    st.rerun()


def end_hand_with_scoring():
    """
    Player declares win — score the hand regardless of completeness.
    In discard phase: auto-picks best discard first.
    Complete hand → normal win.  Incomplete → both pay deadwood, hand ends.
    """
    ss = st.session_state
    # Determine the 7-card hand to score
    if ss.phase == 'discard' and len(ss.player_hand) == 8:
        # Pick the discard that minimises deadwood (or wins outright)
        best_i = 0; best_dw = float('inf')
        for i in range(8):
            rem = [ss.player_hand[j] for j in range(8) if j != i]
            can, is_cc, _ = find_win(rem)
            if can:
                best_i = i
                best_dw = -1  # flag: complete hand
                break
            dw, _ = deadwood(rem)
            if dw < best_dw:
                best_dw, best_i = dw, i
        discard_card = ss.player_hand[best_i]
        remaining    = [ss.player_hand[j] for j in range(8) if j != best_i]
        ss.discard_pile.append(discard_card)
        hand7 = remaining
    else:
        hand7 = list(ss.player_hand)

    can, is_cc_result, melds = find_win(hand7)

    if can:
        # Normal win path
        ss.player_hand = hand7; ss.melds = melds
        ss.phase = 'game_over'; ss.computer_msg = ""
        ss.hand_penalty_player = 0; ss.hand_unmatched_player = []
        if is_cc_result:
            ss.game_result             = 'player_cc'
            ss.hand_penalty_computer   = None
            ss.hand_unmatched_computer = []
            ss.message = "\U0001f3c5 \u00a1CHINCH\u00d3N! You win the entire game!"
        else:
            pen, unmatched         = deadwood(ss.computer_hand)
            ss.computer_score     += pen
            ss.hand_penalty_computer   = pen
            ss.hand_unmatched_computer = unmatched
            ss.game_result   = 'player_wins'
            ss.message = f"\u270b You stopped! Computer pays {pen} penalty points."
    else:
        # Incomplete hand — score both sides
        p_pen, p_unmatched = deadwood(hand7)
        c_pen, c_unmatched = deadwood(ss.computer_hand)
        ss.player_score   += p_pen
        ss.computer_score += c_pen
        ss.player_hand = hand7; ss.melds = []
        ss.phase = 'game_over'; ss.computer_msg = ""
        ss.hand_penalty_player     = p_pen
        ss.hand_unmatched_player   = p_unmatched
        ss.hand_penalty_computer   = c_pen
        ss.hand_unmatched_computer = c_unmatched
        ss.game_result = 'player_declare'
        ss.message = (f"\U0001f5d2 Declared! You pay +{p_pen} pts, "
                      f"Computer pays +{c_pen} pts.")
    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════
def init_game(reset_scores=False):
    ss = st.session_state
    deck = make_deck()
    ss.player_hand   = [deck.pop() for _ in range(7)]
    ss.computer_hand = [deck.pop() for _ in range(7)]
    ss.discard_pile  = [deck.pop()]
    ss.deck          = deck
    ss.phase         = 'draw'           # draw | discard | game_over
    ss.drawn_idx     = None             # index of new card in 8-card hand
    ss.win_idx_list  = []               # [(idx, is_cc)]
    ss.message       = "Your turn — draw a card."
    ss.computer_msg  = ""
    ss.game_result   = None             # player_wins | player_cc | comp_wins | comp_cc
    ss.melds         = []
    if reset_scores or 'player_score' not in ss:
        ss.player_score    = 0
        ss.computer_score  = 0
        ss.round_num       = 1
    else:
        ss.round_num = ss.get('round_num', 1) + 1
    ss.hand_penalty_player   = None   # penalty added this hand
    ss.hand_penalty_computer = None
    ss.hand_unmatched_player  = []
    ss.hand_unmatched_computer = []


# Bootstrap
if 'phase' not in st.session_state:
    st.session_state.phase                   = 'menu'
    st.session_state.player_score            = 0
    st.session_state.computer_score          = 0
    st.session_state.round_num               = 1
    st.session_state.hand_penalty_player     = None
    st.session_state.hand_penalty_computer   = None
    st.session_state.hand_unmatched_player   = []
    st.session_state.hand_unmatched_computer = []

ss = st.session_state

# ═══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════════════════════════
h1, h2, h3 = st.columns([2, 3, 2])
with h1:
    st.markdown(
        '<div class="game-title">🃏 Chinchón</div>'
        '<div class="game-sub">BARAJA ESPAÑOLA · BAT 3301</div>',
        unsafe_allow_html=True,
    )
with h2:
    if ss.phase not in ('menu',):
        st.markdown(
            f'<div style="text-align:center;color:rgba(255,255,255,0.5);'
            f'font-size:13px;padding-top:8px;">'
            f'Round {ss.round_num} &nbsp;·&nbsp; '
            f'Reach 100 points and you <b>lose</b></div>',
            unsafe_allow_html=True,
        )
with h3:
    if ss.phase not in ('menu',):
        def _score_color(pts):
            if pts >= 80: return '#f87171'   # danger red
            if pts >= 50: return '#fb923c'   # orange warning
            return '#86efac'                  # safe green
        p_col = _score_color(ss.player_score)
        c_col = _score_color(ss.computer_score)
        st.markdown(
            f'<div class="score-panel">'
            f'<span style="color:{p_col};font-weight:700;font-size:17px;">{ss.player_score}</span>'
            f'<span style="color:rgba(255,255,255,0.3);margin:0 8px;">·</span>'
            f'<span style="color:{c_col};font-weight:700;font-size:17px;">{ss.computer_score}</span>'
            f'<div style="color:rgba(255,255,255,0.35);font-size:10px;letter-spacing:1px;">'
            f'YOU · CPU &nbsp;(lower is better)</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("🔄 Reset Game", key="btn_reset",
                     use_container_width=True,
                     help="Discard this game and start a new one from zero"):
            init_game(reset_scores=True)
            st.rerun()
        if ss.phase in ('draw', 'discard'):
            st.markdown("<div style='height:3px'></div>", unsafe_allow_html=True)
            if st.button("✋ Declare Win", key="btn_hdr_declare",
                         use_container_width=True, type="primary",
                         help="Stop and score the hand now, even if not complete"):
                end_hand_with_scoring()

st.markdown("<hr class='felt'>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  MENU
# ═══════════════════════════════════════════════════════════════════════════════
if ss.phase == 'menu':
    st.markdown("""
    <div class="menu-wrap">
      <div style="font-size:80px;margin-bottom:10px;">🃏</div>
      <div style="font-size:40px;font-weight:800;color:#fbbf24;margin-bottom:8px;">Chinchón</div>
      <div style="color:rgba(255,255,255,0.65);font-size:15px;max-width:520px;
                  margin:0 auto 28px;line-height:1.75;">
        Classic Spanish card game with the 40-card Baraja Española.<br>
        Form <b style="color:#86efac;">2 sets</b> (sequences or groups) with your 7 cards.<br>
        Get <b style="color:#fbbf24;">Chinchón</b> — 7 consecutive same-suit cards — for glory!
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Rules expander
    with st.expander("📖 Rules & Scoring"):
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("""
**Deck:** 40-card Baraja Española
- 🪙 Oros (Gold) · 🍷 Copas (Cups)
- ⚔️ Espadas (Swords) · 🏑 Bastos (Clubs)
- Values: A 2 3 4 5 6 7 **S** C R  
  *(S=Sota, C=Caballo, R=Rey · no 8 or 9)*

**Turn:** Draw 1 card → Discard 1 card

**Valid sets:**
- **Sequence (Escalera):** 3+ consecutive cards, same suit  
  *(7 and S/10 are consecutive!)*
- **Group (Grupo):** 3 or 4 cards, same value
""")
        with col_r2:
            st.markdown("""
**Winning — you MUST cover all 7 cards:**
- **Stop (Corte):** 7 cards = 2 valid sets (3+4)
- **Chinchón:** All 7 = one sequence, same suit ✨

**Scoring (penalty points — lower is better):**
- Winner of the hand scores **0 points**
- Loser scores the **sum of their unmatched cards**
  *(A=1, 2–7=face, S/C/R=10 pts each)*
- **Chinchón = instant victory**, regardless of scores
- First player to reach **100 points loses**!

**Tip:** Cards marked 🏅 can be discarded to win now!
""")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([3, 2, 3])
    with btn_col:
        if st.button("🎮 Start Game", use_container_width=True, type="primary"):
            init_game(reset_scores=True)
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
#  GAME BOARD
# ═══════════════════════════════════════════════════════════════════════════════
elif ss.phase in ('draw', 'discard', 'game_over'):

    # ── Computer hand ─────────────────────────────────────────────────────────
    st.markdown('<div class="sec-lbl">🤖 Computer\'s hand</div>', unsafe_allow_html=True)

    show_comp_face_up = (ss.phase == 'game_over' and
                         ss.game_result in ('comp_wins', 'comp_cc'))

    if show_comp_face_up:
        # Reveal computer's winning hand
        st.markdown(hand_html_row(ss.computer_hand, facedown=False),
                    unsafe_allow_html=True)
    else:
        comp_row = (
            hand_html_row(ss.computer_hand, facedown=True) +
            f'<span style="color:rgba(255,255,255,0.35);font-size:12px;'
            f'vertical-align:middle;margin-left:10px;">'
            f'({len(ss.computer_hand)} cards)</span>'
        )
        st.markdown('<div style="display:flex;align-items:center;">' +
                    comp_row + '</div>', unsafe_allow_html=True)

    # Computer's last action
    if ss.computer_msg:
        st.markdown(f'<div class="msg">{ss.computer_msg}</div>',
                    unsafe_allow_html=True)

    st.markdown("<hr class='felt'>", unsafe_allow_html=True)

    # ── Piles ────────────────────────────────────────────────────────────────
    pile_c1, pile_c2, pile_c3 = st.columns([1.2, 1.2, 4])

    with pile_c1:
        st.markdown('<div class="sec-lbl">📦 Deck</div>', unsafe_allow_html=True)
        st.markdown(_BACK, unsafe_allow_html=True)
        st.markdown(
            f'<div style="color:rgba(255,255,255,0.4);font-size:11px;'
            f'text-align:center;margin-top:2px;">{len(ss.deck)} remaining</div>',
            unsafe_allow_html=True,
        )
        if ss.phase == 'draw':
            st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)
            if st.button("Draw\nfrom deck", key="btn_deck",
                         use_container_width=True):
                # Reshuffle discard if needed
                if not ss.deck:
                    if len(ss.discard_pile) > 1:
                        top = ss.discard_pile.pop()
                        random.shuffle(ss.discard_pile)
                        ss.deck = ss.discard_pile[:]
                        ss.discard_pile = [top]
                drawn = ss.deck.pop()
                ss.player_hand.append(drawn)
                ss.drawn_idx    = len(ss.player_hand) - 1
                ss.phase        = 'discard'
                ss.win_idx_list = winning_discards(ss.player_hand)
                ss.message      = ("Select a card to discard.  "
                                   "🏅 = Chinchón!  ✋ = Stop!")
                st.rerun()

    with pile_c2:
        st.markdown('<div class="sec-lbl">🗃️ Discard pile</div>',
                    unsafe_allow_html=True)
        if ss.discard_pile:
            st.markdown(card_html(ss.discard_pile[-1]), unsafe_allow_html=True)
        else:
            st.markdown(
                '<div style="color:rgba(255,255,255,0.3);font-size:12px;'
                'margin-top:20px;">Empty</div>',
                unsafe_allow_html=True,
            )
        if ss.phase == 'draw' and ss.discard_pile:
            st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)
            top_card = ss.discard_pile[-1]
            if st.button(f"Take  {cstr(top_card)}", key="btn_disc_take",
                         use_container_width=True):
                drawn = ss.discard_pile.pop()
                ss.player_hand.append(drawn)
                ss.drawn_idx    = len(ss.player_hand) - 1
                ss.phase        = 'discard'
                ss.win_idx_list = winning_discards(ss.player_hand)
                ss.message      = ("Select a card to discard.  "
                                   "🏅 = Chinchón!  ✋ = Stop!")
                st.rerun()

    st.markdown("<hr class='felt'>", unsafe_allow_html=True)

    # ── Player hand ───────────────────────────────────────────────────────────
    st.markdown('<div class="sec-lbl">🧑 Your hand &nbsp;·&nbsp; '
                '<span style="font-size:10px;opacity:0.5;">← → to reorder</span>'
                '</div>', unsafe_allow_html=True)

    if ss.message:
        msg_cls = ""
        if ss.phase == 'game_over':
            if ss.game_result in ('player_wins', 'player_cc'):
                msg_cls = "msg-win" if ss.game_result == 'player_wins' else "msg-cc"
            else:
                msg_cls = "msg-lose"
        st.markdown(f'<div class="msg {msg_cls}">{ss.message}</div>',
                    unsafe_allow_html=True)

    n_cards  = len(ss.player_hand)
    win_set  = {i for i, _ in ss.win_idx_list}
    win_cc   = {i for i, cc in ss.win_idx_list if cc}

    # ── Meld highlight for game-over ──────────────────────────────────────────
    meld_ids = set()
    if ss.phase == 'game_over' and ss.game_result in ('player_wins','player_cc') and ss.melds:
        for meld in ss.melds:
            meld_ids.update(c['id'] for c in meld)

    # ── Card images ────────────────────────────────────────────────────────────
    card_cols = st.columns(n_cards)
    for i, card in enumerate(ss.player_hand):
        with card_cols[i]:
            is_new      = (i == ss.drawn_idx) and ss.phase == 'discard'
            is_win      = (i in win_set) and ss.phase == 'discard'
            in_meld_set = card['id'] in meld_ids
            st.markdown(
                card_html(card, new=is_new, win=(is_win or in_meld_set)),
                unsafe_allow_html=True,
            )

    # ── Reorder row (← →) ─────────────────────────────────────────────────────
    if ss.phase in ('draw', 'discard'):
        swap_cols = st.columns(n_cards)
        for i in range(n_cards):
            with swap_cols[i]:
                btn_row = st.columns(2)

                # ← move left
                with btn_row[0]:
                    if i > 0:
                        if st.button("\u2190", key=f"ml_{i}_{ss.player_hand[i]['id']}",
                                     use_container_width=True, help="Move left"):
                            drawn_id = (ss.player_hand[ss.drawn_idx]['id']
                                        if ss.drawn_idx is not None else None)
                            # Build a new list — never mutate session state in place
                            new_hand = list(ss.player_hand)
                            new_hand[i], new_hand[i-1] = new_hand[i-1], new_hand[i]
                            ss.player_hand = new_hand
                            if drawn_id is not None:
                                ss.drawn_idx = next(
                                    (j for j, c in enumerate(ss.player_hand)
                                     if c['id'] == drawn_id), None)
                            if ss.phase == 'discard' and len(ss.player_hand) == 8:
                                ss.win_idx_list = winning_discards(ss.player_hand)
                            st.rerun()

                # → move right
                with btn_row[1]:
                    if i < n_cards - 1:
                        if st.button("\u2192", key=f"mr_{i}_{ss.player_hand[i]['id']}",
                                     use_container_width=True, help="Move right"):
                            drawn_id = (ss.player_hand[ss.drawn_idx]['id']
                                        if ss.drawn_idx is not None else None)
                            new_hand = list(ss.player_hand)
                            new_hand[i], new_hand[i+1] = new_hand[i+1], new_hand[i]
                            ss.player_hand = new_hand
                            if drawn_id is not None:
                                ss.drawn_idx = next(
                                    (j for j, c in enumerate(ss.player_hand)
                                     if c['id'] == drawn_id), None)
                            if ss.phase == 'discard' and len(ss.player_hand) == 8:
                                ss.win_idx_list = winning_discards(ss.player_hand)
                            st.rerun()

    # ── Discard buttons ────────────────────────────────────────────────────────
    if ss.phase == 'discard':
        disc_cols = st.columns(n_cards)
        for i, card in enumerate(ss.player_hand):
            with disc_cols[i]:
                if i in win_cc:
                    lbl = "\U0001f3c5 CC!"
                elif i in win_set:
                    lbl = "\u270b Stop!"
                else:
                    lbl = "\u2193 discard"
                if st.button(lbl, key=f"d_{i}_{card['id']}",
                             use_container_width=True):
                    do_discard(i)

    # ── Game-over reveal ──────────────────────────────────────────────────────
    if ss.phase == 'game_over':
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        is_player_win = ss.game_result in ('player_wins', 'player_cc')
        is_chinchon_end = ss.game_result in ('player_cc', 'comp_cc')
        is_declare = ss.game_result == 'player_declare'
        color  = ('#fbbf24' if is_chinchon_end else
                  '#fb923c' if is_declare else
                  '#86efac' if is_player_win else '#fca5a5')
        emoji  = ('🏅' if is_chinchon_end else
                  '🗒️' if is_declare else
                  '🎉' if is_player_win else '😔')
        result_label = {
            'player_cc':      '\u00a1CHINCH\u00d3N! You win the game!',
            'player_wins':    'You stopped — you win this hand!',
            'comp_cc':        'Computer Chinch\u00f3n — game over!',
            'comp_wins':      'Computer stopped — you lose this hand!',
            'player_declare': 'Declared — both hands scored.',
        }.get(ss.game_result, 'Round over')

        # Determine who is the loser of THIS hand for penalty display
        def _score_col(pts):
            if pts >= 80: return '#f87171'
            if pts >= 50: return '#fb923c'
            return '#86efac'

        pen_p = ss.get('hand_penalty_player',   0) or 0
        pen_c = ss.get('hand_penalty_computer', 0) or 0
        pen_line = ""
        if not is_chinchon_end:
            if is_declare:
                pen_line = (f'You +{pen_p} pts &nbsp;&middot;&nbsp; CPU +{pen_c} pts')
            elif is_player_win:
                pen_line = (f'Computer pays <b style="color:#fca5a5;">+{pen_c} pts</b>')
            else:
                pen_line = (f'You pay <b style="color:#fca5a5;">+{pen_p} pts</b>')

        st.markdown(
            f'<div style="text-align:center;padding:18px;margin:10px 0;'
            f'background:rgba(0,0,0,0.45);border-radius:14px;border:2px solid {color};">'
            f'<div style="font-size:40px;margin-bottom:4px;">{emoji}</div>'
            f'<div style="font-size:22px;font-weight:800;color:{color};">{result_label}</div>'
            + (f'<div style="color:rgba(255,255,255,0.6);font-size:13px;margin-top:6px;">{pen_line}</div>' if pen_line else "")
            + f'<div style="margin-top:10px;display:flex;gap:20px;justify-content:center;">'
            f'<div style="text-align:center;">'
            f'<div style="color:rgba(255,255,255,0.4);font-size:10px;letter-spacing:1px;">YOUR SCORE</div>'
            f'<div style="font-size:24px;font-weight:800;color:{_score_col(ss.player_score)};">{ss.player_score}</div>'
            f'</div>'
            f'<div style="text-align:center;">'
            f'<div style="color:rgba(255,255,255,0.4);font-size:10px;letter-spacing:1px;">CPU SCORE</div>'
            f'<div style="font-size:24px;font-weight:800;color:{_score_col(ss.computer_score)};">{ss.computer_score}</div>'
            f'</div></div>'
            f'<div style="color:rgba(255,255,255,0.3);font-size:11px;margin-top:6px;">First to 100 loses</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Winning melds (player)
        if is_player_win and ss.melds:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="sec-lbl">Your winning sets</div>',
                        unsafe_allow_html=True)
            for meld in ss.melds:
                meld_type = "Sequence (Escalera)" if is_sequence(meld) else "Group (Grupo)"
                if is_chinchon(meld):
                    meld_type = "🏅 Chinchón!"
                st.markdown(
                    f'<div style="color:rgba(255,255,255,0.45);font-size:11px;margin-bottom:3px;">{meld_type}</div>'
                    + hand_html_row(meld, gap=4),
                    unsafe_allow_html=True,
                )

        # Deadwood breakdown for the loser of the hand
        unmatched_p = ss.get('hand_unmatched_player',   [])
        unmatched_c = ss.get('hand_unmatched_computer', [])

        if (not is_player_win or is_declare) and unmatched_p and not is_chinchon_end:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            st.markdown(
                f'<div class="sec-lbl">Your unmatched cards &nbsp;&middot;&nbsp; '
                f'+{pen_p} penalty points</div>',
                unsafe_allow_html=True)
            st.markdown(hand_html_row(unmatched_p, gap=4), unsafe_allow_html=True)

        if (is_player_win or is_declare) and unmatched_c and not is_chinchon_end:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            st.markdown(
                f'<div class="sec-lbl">Computer unmatched cards &nbsp;&middot;&nbsp; '
                f'+{pen_c} penalty points</div>',
                unsafe_allow_html=True)
            st.markdown(hand_html_row(unmatched_c, gap=4), unsafe_allow_html=True)

        # Chinchón = game ends now
        # 100+ = game ends now
        game_over = is_chinchon_end or ss.player_score >= 100 or ss.computer_score >= 100
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        if game_over:
            if is_chinchon_end:
                winner_label = "YOU WIN THE GAME! 🏅" if is_player_win else "COMPUTER WINS 💀"
                w_col = "#fbbf24"
            elif ss.player_score >= 100 and ss.computer_score >= 100:
                winner_label = "BOTH BUST — CPU WINS (tied at 100+)"
                w_col = "#fb923c"
            elif ss.player_score >= 100:
                winner_label = "YOU REACHED 100 — COMPUTER WINS 💀"
                w_col = "#f87171"
            else:
                winner_label = "CPU REACHED 100 — YOU WIN! 🏆"
                w_col = "#86efac"
            st.markdown(
                f'<div style="text-align:center;font-size:22px;font-weight:800;'
                f'color:{w_col};padding:10px 0;">{winner_label}</div>',
                unsafe_allow_html=True,
            )
            _, c_btn, _ = st.columns([3, 2, 3])
            with c_btn:
                if st.button("🎮 New Game", use_container_width=True, type="primary"):
                    init_game(reset_scores=True)
                    st.rerun()
        else:
            _, c_btn, _ = st.columns([3, 2, 3])
            with c_btn:
                if st.button("▶ Next Hand", use_container_width=True, type="primary"):
                    init_game(reset_scores=False)
                    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
#  LEGEND  (always shown in game)
# ═══════════════════════════════════════════════════════════════════════════════
if ss.phase not in ('menu',):
    st.markdown("<hr class='felt'>", unsafe_allow_html=True)
    leg_cols = st.columns(4)
    legends = [
        ("🪙 Oros", "Gold coins"),
        ("🍷 Copas", "Cups"),
        ("⚔️ Espadas", "Swords"),
        ("🏑 Bastos", "Clubs"),
    ]
    for col, (sym, name) in zip(leg_cols, legends):
        with col:
            st.markdown(
                f'<div style="text-align:center;color:rgba(255,255,255,0.4);'
                f'font-size:12px;">{sym}&nbsp;<b>{name}</b></div>',
                unsafe_allow_html=True,
            )
    st.markdown(
        '<div style="text-align:center;color:rgba(255,255,255,0.25);'
        'font-size:11px;margin-top:6px;">'
        'A 2 3 4 5 6 7 <b>S</b>(Sota) <b>C</b>(Caballo) <b>R</b>(Rey) &nbsp;·&nbsp; '
        'White glow = just drawn &nbsp;·&nbsp; Gold glow = winning discard'
        '</div>',
        unsafe_allow_html=True,
    )
