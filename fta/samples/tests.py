from bs4 import BeautifulSoup

from .utils import convert_fathom_sample_to_labeled_sample

PAGE_BEGIN = (
    '<html lang="en-us">'
    '<head><meta charset="utf-8"/>'
    "<title>Title</title>"
    '<body class="app-polls model-question change-list">'
)
PAGE_END = "</body></html>"
SEARCH_FATHOM_LABEL = (
    '<input data-fathom="search" id ="searchbar" name="q" type="text" value=' "/>"
)
EMAIL_FATHOM_LABEL = (
    '<input data-fathom="email" id="id2" name="question_text" type="text" value=' "/>"
)
NO_LABEL = '<input id="id_question_text" name="question_text" type="text" value=' "/>"
WITH_FTA_ID = '<input data-fta_id="1234" id="id1" name="n" type="text" value=' "/>"
MULTIPLE_ELEMENTS_SAME_LABEL = (
    '<input data-fta_id="aaa" data-fathom="email"/>'
    '<input data-fta_id="bbb" data-fathom="email"/>'
)


def test_convert_fathom_sample_to_labeled_sample_1_labeled_element():
    page = PAGE_BEGIN + SEARCH_FATHOM_LABEL + NO_LABEL + WITH_FTA_ID + PAGE_END
    labeled_sample, fta_id_to_labels = convert_fathom_sample_to_labeled_sample(page)
    assert len(fta_id_to_labels) == 1
    assert "search" in fta_id_to_labels.values()

    # check that the html has 1 data-fta_id entry, not 2
    soup = BeautifulSoup(labeled_sample, features="html.parser")
    fta_labeled_elements = [
        item for item in soup.find_all() if "data-fta_id" in item.attrs
    ]
    assert len(fta_labeled_elements) == 1


def test_convert_fathom_sample_to_labeled_sample_2_labeled_elements():
    page = (
        PAGE_BEGIN + SEARCH_FATHOM_LABEL + EMAIL_FATHOM_LABEL + WITH_FTA_ID + PAGE_END
    )
    labeled_sample, fta_id_to_labels = convert_fathom_sample_to_labeled_sample(page)
    assert len(fta_id_to_labels) == 2
    assert "search" in fta_id_to_labels.values()
    assert "email" in fta_id_to_labels.values()

    # check that the html has 2 data-fta_id entries, not 3
    soup = BeautifulSoup(labeled_sample, features="html.parser")
    fta_labeled_elements = [
        item for item in soup.find_all() if "data-fta_id" in item.attrs
    ]
    assert len(fta_labeled_elements) == 2


def test_convert_fathom_sample_to_labeled_sample_multiple_elements_same_label():
    page = PAGE_BEGIN + MULTIPLE_ELEMENTS_SAME_LABEL + PAGE_END

    labeled_sample, fta_id_to_labels = convert_fathom_sample_to_labeled_sample(page)
    assert len(fta_id_to_labels) == 2

    # check that the value (label) is the same for both keys.
    assert "email" in fta_id_to_labels.values()
    values = fta_id_to_labels.values()
    assert list(values)[0] == list(values)[1]

    # check that the html has 2 data-fta_id entries
    soup = BeautifulSoup(labeled_sample, features="html.parser")
    fta_labeled_elements = [
        item for item in soup.find_all() if "data-fta_id" in item.attrs
    ]
    assert len(fta_labeled_elements) == 2
