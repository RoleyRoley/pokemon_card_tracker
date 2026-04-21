from app.utils.query_builder import build_ebay_query


def test_build_ebay_query_for_raw_card_adds_base_terms_and_exclusions():
    query = build_ebay_query(card_name="Charizard Base Set", condition_type="raw")

    assert query == "Charizard Base Set Pokemon -proxy -custom -art -digital"


def test_build_ebay_query_for_graded_card_includes_grader_and_grade():
    query = build_ebay_query(
        card_name="Pikachu EX",
        condition_type="graded",
        grader="PSA",
        grade=10,
    )

    assert query == "Pikachu EX Pokemon PSA 10 -proxy -custom -art -digital"