# ═══════════════════════════════════════════════════════════════════════════════
#  🃏  Chinchón — Spanish Card Game  (BAT 3301 · Colazo)
#  Player vs Computer · Baraja Española · 40 cards
# ═══════════════════════════════════════════════════════════════════════════════

import streamlit as st
import streamlit.components.v1 as components
import random
import json
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

/* Hide relay input visually (still present in DOM for JS access) */
input[placeholder="__chinchon_relay__"] {
    position: absolute !important; width: 1px !important; height: 1px !important;
    top: -9999px !important; left: -9999px !important; opacity: 0 !important;
}
div[data-testid="stTextInput"]:has(input[placeholder="__chinchon_relay__"]) {
    position: absolute !important; width: 1px !important; height: 1px !important;
    top: -9999px !important; overflow: hidden !important;
}
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
    return {1: 'A', 10: 'S', 11: 'C', 12: 'R'}.get(v, str(v))

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
#  CARD HTML
# ═══════════════════════════════════════════════════════════════════════════════
_BACK = (
    '<div style="width:64px;height:96px;display:inline-flex;align-items:center;'
    'justify-content:center;background:linear-gradient(145deg,#1e3a8a,#3b82f6);'
    'border-radius:9px;border:2px solid #93c5fd;'
    'box-shadow:2px 4px 10px rgba(0,0,0,0.55);margin:2px;flex-shrink:0;">'
    '<span style="font-size:26px;color:rgba(255,255,255,0.35);">✦</span>'
    '</div>'
)

def card_html(card, new=False, win=False, facedown=False):
    if facedown or card is None:
        return _BACK
    col = SUIT_COLOR[card['s']]
    bg  = SUIT_LIGHT[card['s']]
    em  = SUIT_EMOJI[card['s']]
    lb  = vlabel(card['v'])

    if win:
        border = '3px solid #fbbf24'
        shadow = '0 0 16px #fbbf2488, 2px 4px 8px rgba(0,0,0,0.3)'
    elif new:
        border = '3px solid #ffffff'
        shadow = '0 0 12px rgba(255,255,255,0.6), 2px 4px 8px rgba(0,0,0,0.3)'
    else:
        border = f'2px solid {col}70'
        shadow = '2px 4px 8px rgba(0,0,0,0.25)'

    return (
        f'<div style="width:64px;height:96px;background:{bg};border:{border};'
        f'border-radius:9px;box-shadow:{shadow};margin:2px;flex-shrink:0;'
        f'display:flex;flex-direction:column;align-items:center;'
        f'justify-content:space-between;padding:5px 4px;">'
        f'<div style="font-size:14px;font-weight:800;color:{col};'
        f'width:100%;text-align:left;padding-left:1px;line-height:1;">{lb}</div>'
        f'<div style="font-size:30px;line-height:1;text-align:center;">{em}</div>'
        f'<div style="font-size:14px;font-weight:800;color:{col};'
        f'width:100%;text-align:right;padding-right:1px;line-height:1;'
        f'transform:rotate(180deg);">{lb}</div>'
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
#  DRAGGABLE HAND COMPONENT  (HTML5 drag-and-drop + relay communication)
# ═══════════════════════════════════════════════════════════════════════════════
def build_hand_component(hand_data: list, phase: str) -> str:
    """
    Returns a full HTML page that renders the player's hand with HTML5
    drag-and-drop.  Communicates back to Streamlit by updating a hidden
    relay <input> in the parent document via React's native value setter.

    Messages sent to relay input:
      order:0,2,1,...   -> reorder hand to this permutation
      discard:3         -> player discards card at display-index 3
    """
    cards_json = json.dumps(hand_data)
    n          = len(hand_data)
    is_discard = (phase == "discard")
    card_w     = 68
    card_h     = 102

    # ── CSS block ────────────────────────────────────────────────────────────
    css = (
        '* { box-sizing: border-box; margin: 0; padding: 0; }\n'
        'body {\n'
        '  background: transparent;\n'
        "  font-family: 'Inter', -apple-system, sans-serif;\n"
        '  padding: 6px 4px 4px;\n'
        '  user-select: none;\n'
        '}\n'
        '.hand-row {\n'
        '  display: flex; gap: 6px; align-items: flex-end;\n'
        '  flex-wrap: nowrap; justify-content: center;\n'
        '}\n'
        '.card-slot { display: flex; flex-direction: column; align-items: center; gap: 4px; }\n'
        f'.card {{\n'
        f'  width: {card_w}px; height: {card_h}px;\n'
        '  border-radius: 9px; cursor: grab;\n'
        '  display: flex; flex-direction: column;\n'
        '  align-items: center; justify-content: space-between;\n'
        '  padding: 5px 4px;\n'
        '  transition: transform 0.12s ease, box-shadow 0.12s ease;\n'
        '  position: relative;\n'
        '}\n'
        '.card:hover { transform: translateY(-6px); }\n'
        '.card.dragging { opacity: 0.35; cursor: grabbing; transform: scale(0.95); }\n'
        '.card.drag-over { transform: translateY(-10px) scale(1.04); }\n'
        '.card .top-val, .card .bot-val {\n'
        '  font-size: 15px; font-weight: 800; width: 100%; line-height: 1;\n'
        '}\n'
        '.card .top-val { text-align: left; padding-left: 2px; }\n'
        '.card .bot-val { text-align: right; padding-right: 2px; transform: rotate(180deg); }\n'
        '.card .suit-icon { font-size: 34px; line-height: 1; text-align: center; }\n'
        '.card .badge {\n'
        '  position: absolute; top: -7px; right: -7px;\n'
        '  width: 20px; height: 20px; border-radius: 50%;\n'
        '  font-size: 11px; display: flex; align-items: center; justify-content: center;\n'
        '  font-weight: 800; border: 2px solid white;\n'
        '}\n'
        '.badge-new  { background: #3b82f6; color: white; }\n'
        '.badge-cc   { background: #fbbf24; color: #1c1917; }\n'
        '.badge-win  { background: #22c55e; color: white; }\n'
        '.discard-btn {\n'
        f'  width: {card_w}px; padding: 5px 0; border-radius: 6px; border: none;\n'
        '  font-size: 12px; font-weight: 700; cursor: pointer; letter-spacing: 0.5px;\n'
        '  transition: background 0.15s, transform 0.1s;\n'
        '}\n'
        '.discard-btn:hover { transform: scale(1.05); }\n'
        '.discard-btn.normal { background: rgba(0,0,0,0.35); color: rgba(255,255,255,0.7); }\n'
        '.discard-btn.normal:hover { background: rgba(0,0,0,0.55); }\n'
        '.discard-btn.stop { background: #16a34a; color: white; }\n'
        '.discard-btn.chinchon { background: #f59e0b; color: #1c1917; }\n'
        '.drag-hint {\n'
        '  text-align: center; font-size: 10px; color: rgba(255,255,255,0.3);\n'
        '  letter-spacing: 1px; text-transform: uppercase; margin-top: 6px;\n'
        '}\n'
    )

    # ── JavaScript block ─────────────────────────────────────────────────────
    js = (
        'const CARDS = ' + cards_json + ';\n'
        'const PHASE = ' + json.dumps(phase) + ';\n'
        'const IS_DISCARD = ' + ('true' if is_discard else 'false') + ';\n'
        '\n'
        'let dragSrcIdx = null;\n'
        'let order = CARDS.map((_, i) => i);\n'
        '\n'
        '// Relay communication to parent Streamlit app\n'
        'function sendRelay(msg) {\n'
        '  try {\n'
        '    const inputs = window.parent.document.querySelectorAll("input");\n'
        '    let relay = null;\n'
        '    for (const inp of inputs) {\n'
        '      if (inp.placeholder === "__chinchon_relay__") { relay = inp; break; }\n'
        '    }\n'
        '    if (!relay) return;\n'
        '    const setter = Object.getOwnPropertyDescriptor(\n'
        '      window.parent.HTMLInputElement.prototype, "value"\n'
        '    ).set;\n'
        '    setter.call(relay, msg);\n'
        '    relay.dispatchEvent(new Event("input", { bubbles: true }));\n'
        '  } catch(e) {}\n'
        '}\n'
        '\n'
        'function renderCard(ci, displayIdx) {\n'
        '  const c = CARDS[ci];\n'
        '  let border = "2px solid " + c.color + "70";\n'
        '  let shadow = "2px 4px 8px rgba(0,0,0,0.25)";\n'
        '  let badge  = "";\n'
        '  if (c.is_new) {\n'
        '    border = "3px solid #ffffff";\n'
        '    shadow = "0 0 14px rgba(255,255,255,0.55),2px 4px 8px rgba(0,0,0,0.3)";\n'
        '    badge  = \'<div class="badge badge-new">&#9733;</div>\';\n'
        '  }\n'
        '  if (c.is_cc) {\n'
        '    border = "3px solid #fbbf24";\n'
        '    shadow = "0 0 18px #fbbf2488,2px 4px 8px rgba(0,0,0,0.3)";\n'
        '    badge  = \'<div class="badge badge-cc">&#127885;</div>\';\n'
        '  } else if (c.is_win) {\n'
        '    border = "3px solid #22c55e";\n'
        '    shadow = "0 0 12px #22c55e66,2px 4px 8px rgba(0,0,0,0.3)";\n'
        '    badge  = \'<div class="badge badge-win">&#9995;</div>\';\n'
        '  }\n'
        '\n'
        '  let btnHtml = "";\n'
        '  if (IS_DISCARD) {\n'
        '    let cls = "normal", lbl = "&#8595; discard";\n'
        '    if (c.is_cc)       { cls = "chinchon"; lbl = "&#127885; Chinch\\u00f3n!"; }\n'
        '    else if (c.is_win) { cls = "stop";    lbl = "&#9995; Stop!"; }\n'
        '    btnHtml = \'<button class="discard-btn \' + cls + \'" onclick="discard(\' + displayIdx + \')">\'\n'
        '             + lbl + "</button>";\n'
        '  }\n'
        '\n'
        '  return \'<div class="card-slot" data-idx="\' + displayIdx + \'">\'\n'
        '       + \'<div class="card" id="card-\' + displayIdx + \'"\'\n'
        '       + \' draggable="true" data-idx="\' + displayIdx + \'"\'\n'
        '       + \' style="background:\' + c.bg + \';border:\' + border + \';box-shadow:\' + shadow + \';"\'\n'
        '       + \' ondragstart="onDragStart(event,\' + displayIdx + \')"\'\n'
        '       + \' ondragover="onDragOver(event)"\'\n'
        '       + \' ondrop="onDrop(event,\' + displayIdx + \')"\'\n'
        '       + \' ondragend="onDragEnd(event)"\'\n'
        '       + \' ondragenter="onDragEnter(event)"\'\n'
        '       + \' ondragleave="onDragLeave(event)">\'\n'
        '       + badge\n'
        '       + \'<div class="top-val" style="color:\' + c.color + \';">\' + c.label + "</div>"\n'
        '       + \'<div class="suit-icon">\' + c.emoji + "</div>"\n'
        '       + \'<div class="bot-val" style="color:\' + c.color + \';">\' + c.label + "</div>"\n'
        '       + "</div>"\n'
        '       + btnHtml\n'
        '       + "</div>";\n'
        '}\n'
        '\n'
        'function render() {\n'
        '  const row = document.getElementById("handRow");\n'
        '  row.innerHTML = order.map((ci, di) => renderCard(ci, di)).join("");\n'
        '}\n'
        '\n'
        'function onDragStart(e, idx) {\n'
        '  dragSrcIdx = idx;\n'
        '  e.dataTransfer.effectAllowed = "move";\n'
        '  setTimeout(function() {\n'
        '    const el = document.getElementById("card-" + idx);\n'
        '    if (el) el.classList.add("dragging");\n'
        '  }, 0);\n'
        '}\n'
        '\n'
        'function onDragOver(e) { e.preventDefault(); e.dataTransfer.dropEffect = "move"; }\n'
        '\n'
        'function onDragEnter(e) {\n'
        '  const card = e.currentTarget.closest ? e.currentTarget : e.target;\n'
        '  if (card && parseInt(card.dataset.idx) !== dragSrcIdx)\n'
        '    card.classList.add("drag-over");\n'
        '}\n'
        '\n'
        'function onDragLeave(e) {\n'
        '  if (e.currentTarget.classList)\n'
        '    e.currentTarget.classList.remove("drag-over");\n'
        '}\n'
        '\n'
        'function onDrop(e, destIdx) {\n'
        '  e.preventDefault();\n'
        '  if (dragSrcIdx === null || dragSrcIdx === destIdx) return;\n'
        '  const newOrder = order.slice();\n'
        '  const tmp = newOrder[dragSrcIdx];\n'
        '  newOrder[dragSrcIdx] = newOrder[destIdx];\n'
        '  newOrder[destIdx] = tmp;\n'
        '  order = newOrder;\n'
        '  render();\n'
        '  sendRelay("order:" + order.join(","));\n'
        '}\n'
        '\n'
        'function onDragEnd(e) {\n'
        '  dragSrcIdx = null;\n'
        '  document.querySelectorAll(".card").forEach(function(el) {\n'
        '    el.classList.remove("dragging");\n'
        '    el.classList.remove("drag-over");\n'
        '  });\n'
        '}\n'
        '\n'
        'function discard(displayIdx) { sendRelay("discard:" + displayIdx); }\n'
        '\n'
        'render();\n'
    )

    html = (
        '<!DOCTYPE html><html><head>'
        '<meta charset="UTF-8">'
        '<style>'
        + css +
        '</style></head><body>'
        '<div class="hand-row" id="handRow"></div>'
        '<div class="drag-hint">&#8596; drag cards to reorder</div>'
        '<script>'
        + js +
        '</script></body></html>'
    )
    return html





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

    # ── Relay: receive messages from the draggable card component ─────────────
    relay_val = st.text_input(
        "Relay", value="", key="_relay_input",
        placeholder="__chinchon_relay__",
        label_visibility="hidden",
    )

    if relay_val and ss.phase in ('draw', 'discard'):
        if relay_val.startswith('order:') and ss.phase == 'draw':
            # Reorder in draw phase (7 cards, no discard yet)
            try:
                new_idx = [int(x) for x in relay_val[6:].split(',')]
                if (len(new_idx) == len(ss.player_hand)
                        and sorted(new_idx) == list(range(len(ss.player_hand)))):
                    ss.player_hand = [ss.player_hand[i] for i in new_idx]
                    # drawn_idx is None in draw phase
            except Exception:
                pass
            st.session_state._relay_input = ""
            st.rerun()

        elif relay_val.startswith('order:') and ss.phase == 'discard':
            # Reorder in discard phase (8 cards); fix drawn_idx and win_idx_list
            try:
                new_idx = [int(x) for x in relay_val[6:].split(',')]
                if (len(new_idx) == len(ss.player_hand)
                        and sorted(new_idx) == list(range(len(ss.player_hand)))):
                    # Track drawn card by id before reorder
                    drawn_id = (ss.player_hand[ss.drawn_idx]['id']
                                if ss.drawn_idx is not None else None)
                    ss.player_hand = [ss.player_hand[i] for i in new_idx]
                    # Fix drawn_idx for new order
                    if drawn_id is not None:
                        ss.drawn_idx = next(
                            (j for j, c in enumerate(ss.player_hand)
                             if c['id'] == drawn_id), None)
                    # Recompute win list for new order
                    ss.win_idx_list = winning_discards(ss.player_hand)
            except Exception:
                pass
            st.session_state._relay_input = ""
            st.rerun()

        elif relay_val.startswith('discard:') and ss.phase == 'discard':
            try:
                discard_display_idx = int(relay_val[8:])
            except Exception:
                discard_display_idx = -1
            st.session_state._relay_input = ""
            if 0 <= discard_display_idx < len(ss.player_hand):
                # ── Trigger discard via session state flag ─────────────────
                ss._pending_discard = discard_display_idx
            st.rerun()

    # ── Process pending discard (set by relay) ────────────────────────────────
    if getattr(ss, '_pending_discard', None) is not None:
        _di = ss._pending_discard
        ss._pending_discard = None
        n_cards_pd  = len(ss.player_hand)
        if 0 <= _di < n_cards_pd and ss.phase == 'discard':
            discarded_card = ss.player_hand[_di]
            remaining      = [ss.player_hand[j] for j in range(n_cards_pd) if j != _di]
            ss.discard_pile.append(discarded_card)
            can, is_cc_result, melds = find_win(remaining)
            if can:
                ss.player_hand  = remaining; ss.melds = melds
                ss.phase        = 'game_over'; ss.computer_msg = ""
                ss.hand_penalty_player = 0; ss.hand_unmatched_player = []
                if is_cc_result:
                    ss.game_result             = 'player_cc'
                    ss.hand_penalty_computer   = None
                    ss.hand_unmatched_computer = []
                    ss.message = "🏅 ¡CHINCHÓN! You win the entire game!"
                else:
                    pen, unmatched          = deadwood(ss.computer_hand)
                    ss.computer_score      += pen
                    ss.hand_penalty_computer   = pen
                    ss.hand_unmatched_computer = unmatched
                    ss.game_result   = 'player_wins'
                    ss.message = (f"✋ You stopped! Computer pays "
                                  f"{pen} penalty points.")
            else:
                ss.player_hand = remaining; ss.phase = 'draw'
                ss.drawn_idx = None; ss.win_idx_list = []
                new_ch, disc_c, src, comp_can, comp_cc = computer_play(
                    ss.computer_hand, ss.discard_pile, ss.deck)
                if disc_c is not None: ss.discard_pile.append(disc_c)
                ss.computer_hand = new_ch
                src_txt  = "the discard pile" if src == 'discard' else "the deck"
                disc_txt = cstr(disc_c) if disc_c else "?"
                ss.computer_msg = (f"🤖 Computer drew from {src_txt} · discarded {disc_txt}")
                if comp_can:
                    ss.phase = 'game_over'
                    ss.hand_penalty_computer = 0; ss.hand_unmatched_computer = []
                    if comp_cc:
                        ss.game_result = 'comp_cc'
                        ss.hand_penalty_player = None; ss.hand_unmatched_player = []
                        ss.computer_msg += " · 🏅 COMPUTER CHINCHÓN!"
                        ss.message = "💀 Computer got Chinchón and wins the game!"
                    else:
                        pen, unmatched       = deadwood(ss.player_hand)
                        ss.player_score     += pen
                        ss.hand_penalty_player   = pen
                        ss.hand_unmatched_player = unmatched
                        ss.game_result    = 'comp_wins'
                        ss.computer_msg  += " · ✋ Computer stops!"
                        ss.message = (f"😔 Computer stopped. You pay {pen} penalty points.")
                else:
                    ss.message = "Your turn — draw a card."
            st.rerun()

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
                '<span style="font-size:10px;opacity:0.5;">drag cards to reorder</span>'
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

    win_set = {i for i, _ in ss.win_idx_list}
    win_cc  = {i for i, cc in ss.win_idx_list if cc}

    # ── Build hand data for the JS component ──────────────────────────────────
    hand_data = [
        {
            "id":     c['id'],
            "v":      c['v'],
            "s":      c['s'],
            "label":  vlabel(c['v']),
            "emoji":  SUIT_EMOJI[c['s']],
            "color":  SUIT_COLOR[c['s']],
            "bg":     SUIT_LIGHT[c['s']],
            "is_new": (i == ss.drawn_idx) and ss.phase == 'discard',
            "is_cc":  (i in win_cc)        and ss.phase == 'discard',
            "is_win": (i in win_set)        and ss.phase == 'discard',
        }
        for i, c in enumerate(ss.player_hand)
    ]

    if ss.phase == 'game_over':
        # Static display only — no drag, no discard buttons
        # Highlight meld cards in gold if player won
        meld_ids = set()
        if ss.game_result in ('player_wins', 'player_cc') and ss.melds:
            for meld in ss.melds:
                meld_ids.update(c['id'] for c in meld)
        for d in hand_data:
            d['is_win']  = d['id'] in meld_ids
            d['is_new']  = False
            d['is_cc']   = False
        st.markdown(
            hand_html_row(ss.player_hand,
                          win_set={i for i, d in enumerate(hand_data) if d['is_win']}),
            unsafe_allow_html=True,
        )
    else:
        # Live interactive component with drag-and-drop + discard buttons
        n_cards   = len(ss.player_hand)
        card_h_px = 115 if ss.phase == 'discard' else 130
        components.html(
            build_hand_component(hand_data, ss.phase),
            height=card_h_px + (36 if ss.phase == 'discard' else 0) + 30,
            scrolling=False,
        )

    # ── Game-over reveal ──────────────────────────────────────────────────────
    if ss.phase == 'game_over':
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        is_player_win = ss.game_result in ('player_wins', 'player_cc')
        is_chinchon_end = ss.game_result in ('player_cc', 'comp_cc')
        color  = "#fbbf24" if is_chinchon_end else                  "#86efac" if is_player_win else "#fca5a5"
        emoji  = "🏅" if is_chinchon_end else                  "🎉" if is_player_win else "😔"
        result_label = {
            'player_cc':   "¡CHINCHÓN! You win the game!",
            'player_wins': "You stopped — you win this hand!",
            'comp_cc':     "Computer Chinchón — game over!",
            'comp_wins':   "Computer stopped — you lose this hand!",
        }.get(ss.game_result, "Round over")

        # Determine who is the loser of THIS hand for penalty display
        def _score_col(pts):
            if pts >= 80: return '#f87171'
            if pts >= 50: return '#fb923c'
            return '#86efac'

        pen_p = ss.get('hand_penalty_player',   0) or 0
        pen_c = ss.get('hand_penalty_computer', 0) or 0
        pen_line = ""
        if not is_chinchon_end:
            if is_player_win:
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

        if not is_player_win and unmatched_p and not is_chinchon_end:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            st.markdown(
                f'<div class="sec-lbl">Your unmatched cards &nbsp;·&nbsp; ' +
                f'+{pen_p} penalty points</div>',
                unsafe_allow_html=True)
            st.markdown(hand_html_row(unmatched_p, gap=4), unsafe_allow_html=True)

        if is_player_win and unmatched_c and not is_chinchon_end:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            st.markdown(
                f'<div class="sec-lbl">Computer unmatched cards &nbsp;&middot;&nbsp; ' +
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
