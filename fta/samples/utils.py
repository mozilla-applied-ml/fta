import random

from bs4 import BeautifulSoup

suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]


def humansize(nbytes):
    # Sourced from stackoverflow - I forgot to grab the ref
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    f = ("%.2f" % nbytes).rstrip("0").rstrip(".")
    return "%s %s" % (f, suffixes[i])


def convert_labeled_sample_to_fathom_sample(labeled_sample, suffix=".html"):
    soup = BeautifulSoup(labeled_sample.modified_sample)
    labels = labeled_sample.labeled_elements.all()
    if len(labels) == 0:
        # Fathom looks for a `.n` suffix for negative examples
        suffix = f".n{suffix}"
    else:
        for label in labels:
            tagged_elements = soup.find_all(attrs={"data-fta_id": label.data_fta_id})
            for element in tagged_elements:
                element.attrs["data-fathom"] = label.label.slug
    return soup.encode("utf-8"), suffix


def get_splits_from_queryset(qs, train_pct, test_pct):
    # Returns train/test/validation splits from a queryset.
    # Validation set is the remaining once train and test are picked.
    # If train_pct and test_pct add to 100%, validation may still have 1
    # item in it.
    #
    # This isn't perfect, it'll do for now.
    #
    # If you have too few samples, this is going to get wierd
    if train_pct + test_pct > 1.0:
        raise RuntimeError(
            f"train_pct ({train_pct}) + test_pct ({test_pct}) must sum to less than 1.0."
        )
    n = qs.count()
    n_train = round(train_pct * n)
    n_test = round(test_pct * n)

    # Warning: this has the potential to get inefficient, but should be fine while we're
    # only doing modest samples.
    qs_set = set(qs)
    train_set = set(random.sample(qs_set, n_train))
    remaining = qs_set - train_set
    test_set = set(random.sample(remaining, n_test))
    validation_set = remaining - test_set

    return {
        "training": train_set,
        "testing": test_set,
        "validation": validation_set,
    }
