def build_inverted_index(df):
    """
    Builds an inverted index from the tokenized dataset.
    Returns: dict {token: [row indices]}
    """
    inverted_index = {}

    for idx, token_lists in enumerate(df["tokens"]):
        # token_lists is a list of sublists (one per column)
        for token_list in token_lists:
            for token in token_list:
                if token not in inverted_index:
                    inverted_index[token] = []
                inverted_index[token].append(idx)

    return inverted_index
