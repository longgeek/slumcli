MAX_TURNS = 2

def trim_messages(messages):
    user_indices = [i for i, msg in enumerate(messages) if msg["role"] == "user"]
    if len(user_indices) <= MAX_TURNS:
        return

    cut = user_indices[-MAX_TURNS]

    leading = 0
    while leading < len(messages) and messages[leading]["role"] == "system":
        leading += 1

    del messages[leading:cut]
