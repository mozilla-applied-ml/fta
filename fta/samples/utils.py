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


def convert_labeled_sample_to_fathom_sample(labeled_sample):
    soup = BeautifulSoup(labeled_sample.modified_sample)
    labels = labeled_sample.labeled_elements.all()
    for label in labels:
        tagged_elements = soup.find_all(attrs={"data-fta_id": label.data_fta_id})
        for element in tagged_elements:
            element.attrs["data-fathom"] = label.label.slug
    return soup.encode("utf-8")
