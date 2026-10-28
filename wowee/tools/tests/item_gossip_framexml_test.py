"""Guard the remote-realm item-gossip presentation and selection contract."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUEST = (ROOT / "src/game/quest_handler.cpp").read_text()
SOCIAL = (ROOT / "src/addons/lua_social_api.cpp").read_text()


def function_body(source: str, signature: str) -> str:
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


handler = function_body(QUEST, "void QuestHandler::handleGossipMessage")
select = function_body(SOCIAL, '{"SelectGossipOption"')

assert "parseGossipMessage(packet, currentGossip_)" in handler
assert "gossipOwner->getType() == ObjectType::UNIT" in handler
assert "if (creatureOwned) return;" in handler
assert "dismissQuestDetails();" in handler
assert handler.index('("GOSSIP_SHOW", {})') < handler.index("if (!creatureOwned)")
assert "ShowUIPanel(GossipFrame)" in handler
assert "GossipFrame:Show()" in handler
assert "GossipFrameUpdate()" in handler
assert "[WOWEE_GOSSIP] virtual owner=" in handler

# The forced panel must retain the server's option path, not invent a local
# menu that cannot send the Book of Powers choice back to Warstorm.
assert "getCurrentGossip().options" in select
assert "gh->selectGossipOption(opt.id" in select

print(
    "PASS item gossip: non-NPC menus supersede stale quest details, force the "
    "standard GossipFrame visible, and preserve server option selection"
)
