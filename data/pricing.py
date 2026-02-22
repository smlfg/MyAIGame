PRICING = {
    "opus": {"input": 15.00, "output": 75.00},
    "sonnet": {"input": 3.00, "output": 15.00},
    "haiku": {"input": 0.25, "output": 1.25},
    "flash": {"input": 0.075, "output": 0.30},
    "minimax": {"input": 0.10, "output": 0.30},
}


def calc_cost(agent: str, tokens_in: int, tokens_out: int) -> float:
    p = PRICING.get(agent, PRICING["sonnet"])
    return (tokens_in * p["input"] + tokens_out * p["output"]) / 1_000_000


def model_to_agent(model_str: str) -> str:
    model_str = (model_str or "").lower()
    if "opus" in model_str:
        return "opus"
    if "sonnet" in model_str:
        return "sonnet"
    if "haiku" in model_str:
        return "haiku"
    if "flash" in model_str or "gemini" in model_str:
        return "flash"
    if "minimax" in model_str:
        return "minimax"
    return "sonnet"  # default
