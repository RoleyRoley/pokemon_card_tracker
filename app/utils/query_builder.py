# Method to build the eBay search query based on the request data
def build_ebay_query(card_name: str, condition_type: str, grader=None, grade=None) -> str:
    query = f"{card_name} Pokemon".strip()

    if condition_type == "graded" and grader and grade is not None:
        query += f" {grader} {grade}"

    return query