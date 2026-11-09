# Data source and attribution

Product data and images: **Amazon Berkeley Objects (ABO)**.
Credit for the data, including all images: **Amazon.com**.
License: Creative Commons Attribution 4.0 International (CC BY 4.0). Full text: `LICENSE-CC-BY-4.0.txt`.

Citation: Collins et al., "ABO: Dataset and Benchmarks for Real-World 3D Object Understanding", CVPR 2022.

## Changes made

- Selected 32 listings out of 147,702 (`../selection.csv`).
- `selected_listings.jsonl` holds the selected records as published, with one change: phone numbers in the text (a brand's customer-service line, in 13 bullet points across 5 coffee listings) are replaced with "[phone removed]". Where an item had more than one record, the record with the most English bullet points was kept.
- `images/<item_id>.jpg` holds each item's main image (original size), renamed to the item ID.
- The demo store ("Half Tempo Café", a fictional shop) shows each product under a new display name with the brand removed (`../selection.csv`), and the catalog loader removes brand names from the product text.
- Half Tempo Café is fictional. It is not affiliated with Amazon.com or with any brand in the data.
