from __future__ import annotations

import hashlib, json
from .schemas import AgentCard, ToolContract


REQUESTER_CARD=AgentCard(name="procurement-requester",version="1.0",capabilities=["policy_search","submit_request"],scopes=["policy:read"])
REVIEWER_CARD=AgentCard(name="compliance-reviewer",version="1.0",capabilities=["policy_search","review","approve"],scopes=["policy:read","procurement:approve"])

POLICY_SEARCH=ToolContract(name="policy_search",description="Search local procurement policy",input_schema={"type":"object","properties":{"query":{"type":"string"}},"required":["query"],"additionalProperties":False},output_schema={"type":"object","properties":{"matches":{"type":"array"}},"required":["matches"]},side_effect=False,required_scope="policy:read")
APPROVE=ToolContract(name="approve_procurement",description="Record an approved synthetic procurement request",input_schema={"type":"object","properties":{"request_id":{"type":"string"},"amount":{"type":"number","minimum":0}},"required":["request_id","amount"],"additionalProperties":False},output_schema={"type":"object","properties":{"approval_id":{"type":"string"}},"required":["approval_id"]},side_effect=True,required_scope="procurement:approve")
CONTRACTS={item.name:item for item in [POLICY_SEARCH,APPROVE]}


def contract_digest(contract: ToolContract) -> str:
    payload=json.dumps(contract.model_dump(mode="json"),sort_keys=True,separators=(",",":"))
    return hashlib.sha256(payload.encode()).hexdigest()


PINNED_DIGESTS={name:contract_digest(contract) for name,contract in CONTRACTS.items()}
