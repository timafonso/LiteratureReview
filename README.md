# LiteratureReviewAnalysis
Scripts for analysis of articles information obtained through the [Publish or Perish tool](https://harzing.com/resources/publish-or-perish).

Some of the functions assume that the name of the csv files are in the format:

`{Search Engine Used}_{keyword}(OP_keyword)*.csv`

Where `keyword` can be any keyword used for the search and `OP` are any boolean operators used to concatenate it ("AND", "OR", "ANDNOT")

The recommended way to use this script is to access the functions through the notebook. Otherwise, for more memory heavy operations, write your own scripts.