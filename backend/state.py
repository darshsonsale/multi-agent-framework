from typing import TypedDict, List, Dict, Any, Optional

class FIRState(TypedDict):
    messages: List[Dict[str, str]]
    fir: Dict[str, Any]
    intent: Optional[str]
    errors: List[str]
    next_question: Optional[str]
    review: Optional[dict]
    last_question: Optional[str]  # 🔥 NEW FIELD