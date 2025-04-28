"""
Streamlit UI for the my-poker-tutor Texas Hold'em simulator with EV coaching.

Usage:
    streamlit run ui_app.py
"""
import streamlit as st
import poker_tutor as pt
from typing import Tuple, Dict
import streamlit.components.v1 as components

# Page config and theme
st.set_page_config(page_title="Poker Tutor", page_icon="🂡", layout="wide")
st.markdown("""
<style>
  body { background:#0e0e0e; }
  .card { filter:drop-shadow(0 2px 4px rgba(0,0,0,.6)); }
  .stButton>button { color:white; border:none; }
  .stButton>button[aria-label="Fold"] { background-color:#3b76d4 !important; }
  .stButton>button[aria-label^="Call"] { background-color:#4a9859 !important; }
  .stButton>button[aria-label="Raise"] { background:linear-gradient(to right, #e14b4b, #851e1e) !important; }
  .stButton>button:hover { filter:brightness(0.95) !important; }

  /* poker table container */
  .felt {
    background:#1f3324;
    border-radius:50%/25%;
    width:95%; max-width:800px;
    height:70vh;
    margin:auto;
    position:relative;
    display:flex;
    flex-direction:column;
    justify-content:space-between;
    align-items:center;
  }
  .pots {
    position:absolute;
    top:10px;
    right:20px;
    font-size:1.2em;
    color:gold;
  }
  .board { display:flex; gap:10px; }
  .seat {
    background:#264d26;
    border:2px solid #444;
    border-radius:50%;
    width:120px;
    height:120px;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    color:#e6e6e6;
    font-size:0.9em;
  }
  .seat.hero { border-color:gold; }
  .seat.bot  { border-color:slategray; }
</style>
""", unsafe_allow_html=True)
components.html("""
<script>
  document.addEventListener('keydown', e => {
    if (['f','c','r'].includes(e.key)) {
      const url = new URL(window.location);
      url.searchParams.set('last_key', e.key);
      window.history.replaceState(null, '', url);
    }
  });
</script>
""", height=0)
# Blind sizes
SB: int = 1
BB: int = 2

def init_game() -> None:
    """Initialize a new GameState, BettingRound, and Coach in session state."""
    # fresh deck and players
    rng = pt.RNG(None)
    deck = pt.Deck(rng)
    # 3-hand game: Hero + two bots
    players = [pt.Player("Hero", 100)] + [pt.Player(f"Bot{i}", 100) for i in (1, 2)]  # type: ignore
    gs = pt.GameState(players, deck)
    gs.deal_hole_cards()
    # post pre-flop blinds
    br = pt.BettingRound(gs, SB, BB)
    br.post_blinds()
    # Monte-Carlo EV coach
    coach = pt.Coach([p for p in players if p.name != "Hero"], rollouts=200)
    # store in session state
    st.session_state['game'] = gs
    st.session_state['br'] = br
    st.session_state['coach'] = coach
    st.session_state['last_tip'] = ""
    st.session_state['game_over'] = False
    st.session_state['equity'] = None
    st.session_state['winner'] = None

BACK_URL = 'https://raw.githubusercontent.com/hayeah/playing-cards-assets/master/png/100px/back.png'
def card_img(card: pt.Card, hide: bool=False) -> str:
    """Return Liberty PNG URL for a card or back image when hidden."""
    # map rank characters to Liberty deck codes
    ranks = {'2':'02','3':'03','4':'04','5':'05','6':'06','7':'07','8':'08','9':'09',
             'T':'10','J':'J','Q':'Q','K':'K','A':'A'}
    suits = {'h':'H','d':'D','c':'C','s':'S'}
    if hide:
        return BACK_URL
    r = pt.RANK_STR[card.rank]
    s = pt.SUITS[card.suit]
    return f'https://raw.githubusercontent.com/hayeah/playing-cards-assets/master/png/100px/{ranks[r]}{suits[s]}.png'

def render_board_imgs(gs: pt.GameState) -> None:
    """Display board cards (flop/turn/river) as images."""
    if not gs.board:
        return
    cols = st.columns(len(gs.board))
    for i, c in enumerate(gs.board):
        url = load_card_img(c)
        cols[i].markdown(f"<img src='{url}' class='card-img' width='100'/>", unsafe_allow_html=True)

def render_player_table(gs: pt.GameState) -> None:
    """Render each player's name, hole cards (or back), stack and bet."""
    for p in gs.players:
        status = '(F)' if p.has_folded else ''
        if p.name == 'Hero':
            urls = [load_card_img(c) for c in p.hole_cards]
        else:
            urls = [BACK_URL, BACK_URL]
        cards_html = ''.join(
            f"<img src='{u}' class='card-img' width='100' style='margin-right:4px;'/>" for u in urls
        )
        st.markdown(f"""
        <div style='display:flex; align-items:center; margin-bottom:8px;'>
          <div style='width:80px;'><strong>{p.name}</strong> {status}</div>
          <div>{cards_html}</div>
          <div style='margin-left:auto;'>Stack: {p.stack}  Bet: {p.bet}</div>
        </div>
        """, unsafe_allow_html=True)

def render_pots(gs: pt.GameState) -> None:
    """Display main and side-pot amounts in gold text."""
    labels = []
    for idx, pot in enumerate(gs.pots):  # type: ignore
        label = 'Main' if idx == 0 else f'Side-{idx}'
        labels.append(f"{label}: {pot.amount}")
    line = '   |   '.join(labels)
    st.markdown(f"<div style='color:gold; font-size:1.2em; margin-top:10px;'>{line}</div>", 
                unsafe_allow_html=True)
    
def draw_table(gs: pt.GameState) -> None:
    """Draw the poker table with felt, pots, board, and seats."""
    # build HTML for felt and content
    html = "<div class='felt'>"
    # side pots bar
    pots = []
    for idx, pot in enumerate(gs.pots):  # type: ignore
        label = 'Main' if idx == 0 else f'Side-{idx}'
        pots.append(f"{label} {pot.amount}")
    html += f"<div class='pots'>{' | '.join(pots)}</div>"
    # board cards
    html += "<div class='board'>"
    for c in gs.board:
        url = card_img(c)
        html += f"<img src='{url}' class='card' width='75'/>"
    html += "</div>"
    # player seats
    for i, p in enumerate(gs.players):
        role = 'hero' if p.name == 'Hero' else 'bot'
        css = f"seat {role}"
        if gs.to_act == i:
            css += " current"
        html += f"<div class='{css}'>"
        html += f"<div><strong>{p.name}</strong></div>"
        # hole cards
        for card in p.hole_cards:
            hide = (p.name != 'Hero')
            url = card_img(card, hide)
            html += f"<img src='{url}' class='card' width='50'/>"
        html += f"<div>{p.stack} bb | Bet {p.bet}</div>"
        html += "</div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
 
def draw_sidebar_stats(gs: pt.GameState) -> None:
    """Draw sidebar statistics and coach feedback."""
    tip = st.session_state.get('last_tip', '')
    if tip:
        if tip.startswith('✔'):
            st.success(tip)
        else:
            st.error(tip)

def draw_action_bar(gs: pt.GameState) -> Tuple[str, int] | None:
    """Render action buttons and return a decision tuple if clicked."""
    hero = gs.players[0]
    call_amt = gs.highest_bet - hero.bet
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Fold", key="btn_fold"):
            return 'fold', 0
    with c2:
        if st.button(f"Call {call_amt}", key="btn_call"):
            return 'call', 0
    with c3:
        raise_to = st.number_input("Raise to", min_value=BB * 2, step=BB, value=BB * 2, key="raise_to")
        if st.button("Raise", key="btn_raise"):
            return 'raise', raise_to
    return None

def handle_action(decision: Tuple[str, int]) -> None:
    """Apply Hero's decision, let bots respond, advance street or showdown."""
    gs: pt.GameState = st.session_state['game']  # type: ignore
    br: pt.BettingRound = st.session_state['br']  # type: ignore
    coach: pt.Coach = st.session_state['coach']  # type: ignore
    action, amt = decision
    hero = gs.players[0]
    # Hero action
    if action == 'fold':
        hero.has_folded = True
    elif action == 'call':
        to_call = gs.highest_bet - hero.bet
        gs.collect_bet(hero, to_call)
    elif action == 'raise':
        to_call = gs.highest_bet - hero.bet
        min_raise = max(BB, gs.highest_bet * 2 - hero.bet)
        extra = max(amt, min_raise)
        gs.collect_bet(hero, to_call + extra)
    # Coach feedback
    tip = coach.explain(decision, gs)
    st.session_state['last_tip'] = tip
    # advance to bots
    gs.to_act = (0 + 1) % len(gs.players)
    # bots act until round end
    br.run()
    # check for single winner
    active = gs.active_players
    if len(active) == 1:
        winner = active[0]
        gs.players[winner].stack += gs.pot
        st.session_state['winner'] = gs.players[winner].name
        st.session_state['equity'] = None
        st.session_state['game_over'] = True
        return
    # next street or showdown
    if gs.street != pt.Street.SHOWDOWN:
        gs.deal_next_street()
        st.session_state['br'] = pt.BettingRound(gs, SB, BB)
    else:
        # showdown: compute deltas and winners
        he = pt.HandEvaluator()
        active_idxs = [i for i, p in enumerate(gs.players) if not p.has_folded]
        evals: Dict[int, Tuple[int, list]] = {
            i: he.evaluate(gs.players[i].hole_cards + gs.board) for i in active_idxs  # type: ignore
        }
        deltas: Dict[int, int] = {}
        for pot in gs.pots:  # type: ignore
            eligible = [i for i in pot.eligible if i in active_idxs]
            if not eligible:
                continue
            best = max(evals[i] for i in eligible)
            winners = [i for i in eligible if evals[i] == best]
            share = pot.amount // len(winners)
            for i in winners:
                deltas[i] = deltas.get(i, 0) + share
        # apply chips
        for i, p in enumerate(gs.players):
            p.stack += deltas.get(i, 0)
        # record results
        main = gs.pots[0]  # type: ignore
        best_main = max(evals[i] for i in active_idxs)
        main_winners = [i for i in main.eligible if i in active_idxs and evals[i] == best_main]
        names = ", ".join(gs.players[i].name for i in main_winners)
        st.session_state['winner'] = names
        # equity: hero share / total pot
        total = sum(p.amount for p in gs.pots)  # type: ignore
        st.session_state['equity'] = deltas.get(0, 0) / total * 100  # type: ignore
        st.session_state['game_over'] = True

def main() -> None:
    """Main Streamlit app entrypoint."""
    if 'game' not in st.session_state:
        init_game()
    gs: pt.GameState = st.session_state['game']  # type: ignore
    # Hotkey handling via URL query params (f=fold, c=call)
    # use modern query_params API (Streamlit ≥1.30)
    params = st.query_params
    key = params.get('last_key', [None])[0]
    if key in ('f', 'c'):
        # apply hotkey action then clear the query state
        if key == 'f':
            handle_action(('fold', 0))
        else:
            handle_action(('call', 0))
        # clear keys so action isn't repeated
        st.query_params.clear()
    # Game over view
    if st.session_state.get('game_over', False):
        st.success(f"Winner: {st.session_state.get('winner')}")
        eq = st.session_state.get('equity')
        if eq is not None:
            st.write(f"Hero equity: {eq:.1f}%")
        if st.button("Deal Next Hand"):
            init_game()
        return
    # active game view: table and sidebar
    col1, col2 = st.columns([3, 1])
    with col1:
        draw_table(gs)
    with col2:
        draw_sidebar_stats(gs)
    # actions
    act = draw_action_bar(gs)
    if act:
        handle_action(act)

if __name__ == "__main__":
    main()