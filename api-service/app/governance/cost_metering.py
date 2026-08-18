PRICE_PER_1K_TOKENS = {
    "claude-sonnet-5": {"input": 0.003, "output": 0.015},
}

def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = PRICE_PER_1K_TOKENS.get(model)
    if not rates:
        return 0.0
    return (input_tokens / 1000) * rates["input"] + (output_tokens / 1000) * rates["output"]
