# ═══════════════════════════════════════════════════════════════════════════════
#  🃏  Chinchón — Spanish Card Game  (BAT 3301 · Colazo)
#  Player vs Computer · Baraja Española · 40 cards
# ═══════════════════════════════════════════════════════════════════════════════

import streamlit as st
import random
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
        ss.player_score   = 0
        ss.computer_score = 0
        ss.round_num      = 1
    else:
        ss.round_num = ss.get('round_num', 1) + 1


# Bootstrap
if 'phase' not in st.session_state:
    st.session_state.phase         = 'menu'
    st.session_state.player_score  = 0
    st.session_state.computer_score = 0
    st.session_state.round_num     = 1

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
            f'First to 5 points wins the match</div>',
            unsafe_allow_html=True,
        )
with h3:
    if ss.phase not in ('menu',):
        p_col = '#86efac' if ss.player_score >= ss.computer_score else '#fca5a5'
        c_col = '#fca5a5' if ss.player_score >= ss.computer_score else '#86efac'
        st.markdown(
            f'<div class="score-panel">'
            f'<span style="color:{p_col};font-weight:700;font-size:17px;">{ss.player_score}</span>'
            f'<span style="color:rgba(255,255,255,0.3);margin:0 8px;">·</span>'
            f'<span style="color:{c_col};font-weight:700;font-size:17px;">{ss.computer_score}</span>'
            f'<div style="color:rgba(255,255,255,0.35);font-size:10px;letter-spacing:1px;">YOU · CPU</div>'
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

**Scoring:**
- Win normally → **+1 point**
- Chinchón → **+3 points**
- First to **5 points** wins the match!

**Tip:** Cards marked 🏆 in your hand can be discarded  
to win immediately — watch for the golden highlight!
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
    st.markdown('<div class="sec-lbl">🧑 Your hand</div>', unsafe_allow_html=True)

    if ss.message:
        msg_cls = ""
        if ss.phase == 'game_over':
            if ss.game_result in ('player_wins', 'player_cc'):
                msg_cls = "msg-win" if ss.game_result == 'player_wins' else "msg-cc"
            else:
                msg_cls = "msg-lose"
        st.markdown(f'<div class="msg {msg_cls}">{ss.message}</div>',
                    unsafe_allow_html=True)

    n_cards   = len(ss.player_hand)
    win_set   = {i for i, _ in ss.win_idx_list}
    win_cc    = {i for i, cc in ss.win_idx_list if cc}
    hand_cols = st.columns(n_cards)

    for i, card in enumerate(ss.player_hand):
        with hand_cols[i]:
            is_new = (i == ss.drawn_idx) and ss.phase == 'discard'
            is_win = (i in win_set)       and ss.phase == 'discard'
            st.markdown(card_html(card, new=is_new, win=is_win),
                        unsafe_allow_html=True)

            # ── Discard button ─────────────────────────────────────────────
            if ss.phase == 'discard':
                if i in win_cc:
                    btn_label = "🏅 CC!"
                elif i in win_set:
                    btn_label = "✋ Stop!"
                else:
                    btn_label = "↓"

                if st.button(btn_label,
                             key=f"d_{i}_{card['id']}",
                             use_container_width=True):
                    # ── Player discards card i ─────────────────────────────
                    discarded_card = ss.player_hand[i]
                    remaining      = [ss.player_hand[j]
                                      for j in range(n_cards) if j != i]
                    ss.discard_pile.append(discarded_card)

                    can, is_cc_result, melds = find_win(remaining)

                    if can:
                        # Player wins!
                        ss.player_hand = remaining
                        ss.melds       = melds
                        ss.phase       = 'game_over'
                        ss.computer_msg = ""
                        if is_cc_result:
                            ss.game_result   = 'player_cc'
                            ss.player_score += 3
                            ss.message = ("🏅 ¡CHINCHÓN! Perfect hand — "
                                          "you win this round!  +3 points")
                        else:
                            ss.game_result   = 'player_wins'
                            ss.player_score += 1
                            ss.message = ("✋ You stopped the game and win "
                                          "this round!  +1 point")
                    else:
                        # Normal discard → computer's turn (runs immediately)
                        ss.player_hand  = remaining
                        ss.phase        = 'draw'
                        ss.drawn_idx    = None
                        ss.win_idx_list = []

                        new_ch, disc_c, src, comp_can, comp_cc = computer_play(
                            ss.computer_hand, ss.discard_pile, ss.deck
                        )
                        if disc_c is not None:
                            ss.discard_pile.append(disc_c)
                        ss.computer_hand = new_ch

                        src_txt = "the discard pile" if src == 'discard' else "the deck"
                        disc_txt = cstr(disc_c) if disc_c else "?"
                        ss.computer_msg = (
                            f"🤖 Computer drew from {src_txt} · "
                            f"discarded {disc_txt}"
                        )

                        if comp_can:
                            ss.phase = 'game_over'
                            if comp_cc:
                                ss.game_result    = 'comp_cc'
                                ss.computer_score += 3
                                ss.computer_msg  += (
                                    " · 🏅 COMPUTER CHINCHÓN!  +3 pts"
                                )
                                ss.message = ("💀 Computer got Chinchón! "
                                              "You lose this round.")
                            else:
                                ss.game_result    = 'comp_wins'
                                ss.computer_score += 1
                                ss.computer_msg  += " · ✋ Computer stops!  +1 pt"
                                ss.message = ("😔 Computer stopped the game. "
                                              "You lose this round.")
                        else:
                            ss.message = "Your turn — draw a card."

                    st.rerun()

    # ── Game-over reveal ──────────────────────────────────────────────────────
    if ss.phase == 'game_over':
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Result banner
        is_player_win = ss.game_result in ('player_wins', 'player_cc')
        color  = "#fbbf24" if ss.game_result == 'player_cc' else \
                 "#86efac" if is_player_win else "#fca5a5"
        emoji  = "🏅" if ss.game_result == 'player_cc' else \
                 "🎉" if is_player_win else "😔"
        result_label = {
            'player_cc':   "¡CHINCHÓN! Perfect hand!",
            'player_wins': "You stopped — you win!",
            'comp_cc':     "Computer Chinchón — you lose!",
            'comp_wins':   "Computer stopped — you lose!",
        }.get(ss.game_result, "Round over")

        st.markdown(
            f'<div style="text-align:center;padding:18px;margin:10px 0;'
            f'background:rgba(0,0,0,0.45);border-radius:14px;'
            f'border:2px solid {color};">'
            f'<div style="font-size:40px;margin-bottom:4px;">{emoji}</div>'
            f'<div style="font-size:22px;font-weight:800;color:{color};">'
            f'{result_label}</div>'
            f'<div style="color:rgba(255,255,255,0.5);font-size:13px;margin-top:6px;">'
            f'Score &nbsp;·&nbsp; '
            f'You: <b style="color:#86efac;">{ss.player_score}</b> &nbsp;'
            f'CPU: <b style="color:#fca5a5;">{ss.computer_score}</b>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        # Winning melds
        if is_player_win and ss.melds:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="sec-lbl">Your winning sets</div>',
                        unsafe_allow_html=True)
            for meld in ss.melds:
                meld_type = "Sequence (Escalera)" if is_sequence(meld) else "Group (Grupo)"
                if is_chinchon(meld):
                    meld_type = "🏅 Chinchón!"
                st.markdown(
                    f'<div style="color:rgba(255,255,255,0.5);font-size:11px;'
                    f'margin-bottom:4px;">{meld_type}</div>'
                    + hand_html_row(meld, gap=5),
                    unsafe_allow_html=True,
                )

        # Match over?
        match_over = ss.player_score >= 5 or ss.computer_score >= 5
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        if match_over:
            winner = "YOU" if ss.player_score >= 5 else "COMPUTER"
            w_col  = "#86efac" if ss.player_score >= 5 else "#fca5a5"
            st.markdown(
                f'<div style="text-align:center;font-size:26px;font-weight:800;'
                f'color:{w_col};padding:10px;">🏆 {winner} WIN THE MATCH!</div>',
                unsafe_allow_html=True,
            )
            _, c_btn, _ = st.columns([3, 2, 3])
            with c_btn:
                if st.button("🎮 New Match", use_container_width=True, type="primary"):
                    init_game(reset_scores=True)
                    st.rerun()
        else:
            _, c_btn, _ = st.columns([3, 2, 3])
            with c_btn:
                if st.button("▶ Next Round", use_container_width=True, type="primary"):
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
