# data/datasets/ — course data dictionary

Central store of **real** datasets used by homework and lectures.
Shapes measured directly from the files; regenerate this file with
`private/generators/build_datasets_readme.py`.

## Homework splits & supporting data
- `hotel_bookings.csv` — 119,390 rows x 32 cols
- `insurance.csv` — 1,338 rows x 7 cols
- `prices-split-adjusted.csv` — 851,264 rows x 7 cols
- `tsne.csv` — 300 rows x 3 cols

## L00-L06 · foundations (python, stats, probability, linear algebra)
- `Pond_water_Data.csv` — 200 rows x 8 cols
- `Social_Network_Ads.csv` — 400 rows x 5 cols
- `StudentsPerformance.csv` — 1,000 rows x 8 cols · exam scores - seeds Bazario satisfaction/ratings (real)
- `p4dataset2021.txt` — 995 rows x 10104 cols

## L07 · dimensionality reduction / PCA
- `WA_Fn-UseC_-Telco-Customer-Churn.csv` — 7,043 rows x 21 cols · Telco churn labels - also seeds MDX-Bazario customers (real)
- `iris.data` — 151 rows x 5 cols · Fisher's iris, no header (real)
- `london_merged.csv` — 17,414 rows x 10 cols · London bike-share hourly counts + weather (real)

## L08 · linear & multivariate regression, regularisation
- `50_Startups.csv` — 50 rows x 5 cols
- `advertising.csv` — 200 rows x 4 cols
- `boom_bikes.csv` — 730 rows x 16 cols
- `cardekho.csv` — 301 rows x 9 cols
- `concrete.csv` — 1,030 rows x 9 cols
- `kc_house_data.csv` — 21,613 rows x 21 cols

## L09-L15 · classification, metrics, kNN, recommenders, trees, boosting, naive bayes
- `NER dataset.csv` — 1,048,575 rows x 4 cols · POS/NER tags - real Markov structure for HMM lectures
- `bank-additional-full.csv` — 41,188 rows x 21 cols
- `cardio_train.csv` — 70,000 rows x 13 cols
- `credit_card_fraud.csv` — 284,807 rows x 9 cols
- `glass.csv` — 214 rows x 10 cols
- `healthcare-dataset-stroke-data.csv` — 5,110 rows x 12 cols
- `heart_disease_uci.csv` — 303 rows x 14 cols
- `heart_failure_clinical_records_dataset.csv` — 299 rows x 13 cols
- `jewelry.csv` — 113,302 rows x 13 cols
- `jewelry_mod.csv` — 113,302 rows x 21 cols
- `links_small.csv` — 150 rows x 3 cols
- `spam.csv` — 5,574 rows x 5 cols · SMS spam corpus for naive-Bayes text classification
- `stock-sentiment-data.csv` — 5,776 rows x 28 cols · financial headlines w/ sentiment labels
- `tmdb_5000_movies.csv` — 150 rows x 10 cols

## L16 · clustering
- `OnlineRetail.csv` — 541,909 rows x 8 cols · UK online-retail invoices 2010-11 (latin-1) - HW04 + Bazario orders
- `OnlineRetail_utf8.csv` — 541,909 rows x 8 cols · same, UTF-8 export

## L17-L23 · neural networks (NN, autoencoders, CNN, image processing, RNN, HMM)
- `5_class_images.zip`
- `AAPL_2006-01-01_to_2018-01-01.csv` — 3,019 rows x 7 cols
- `GOOGL_2006-01-01_to_2018-01-01.csv` — 3,019 rows x 7 cols
- `IBM_2006-01-01_to_2018-01-01.csv` — 3,020 rows x 7 cols · IBM OHLCV daily - HW05 Track B / RNN lectures
- `MSFT_2006-01-01_to_2018-01-01.csv` — 3,019 rows x 7 cols
- `brain_tumor_dataset.zip`
- `imdb.npz` — 4 arrays (x_test, x_train, y_train, y_test...) · keras-format IMDB reviews for embedding labs
- `mini_mnist.csv` — 12,500 rows x 786 cols · 12.5k x 784 grayscale digits (+label) for CNN lectures
- `opencv_examples.zip`

## Labs · official 2026 lab datasets (CST 4215)
- `MTDB2500.csv` — 2,500 rows x 14 cols · Makridakis time-series competition data - Lab 15 NeuralProphet
- `Real_estate.csv` — 201 rows x 7 cols · house prices w/ house-age & distance features - Labs 2/6/7 OLS
- `Wholesale_customers_data.csv` — 440 rows x 8 cols · wholesale spend by category - Lab 16 KMeans
- `decoder_data.csv` — 50 rows x 4 cols · number sequences - Lab 19 decoder-only LM
- `employment_records.csv` — 100 rows x 10 cols · small HR table - Lab 3 encoding + Lab 4 GaussianNB
- `loan_sample_data.csv` — 100 rows x 12 cols · loan outcomes - Lab 5 GaussianNB
- `student-mat.csv` — 395 rows x 33 cols · Portuguese maths grades, ';' separated (semicolon) - Labs 8/10-14
- `twitter_training.csv` — 74,642 rows x 4 cols · tweet sentiment corpus - Lab 20 LSTM (also HW05 alt)

## Other / utility
- `Fish.csv` — 159 rows x 7 cols · fish market measurements - seeds Bazario products/zones (real)
- `build_db.py`
- `credit_card_usage.csv` — 8,950 rows x 18 cols
- `datasets.db`

## Wide & big practice sets (p >> n, dirty big data)
- `gene_expression_100x1000.csv` — 100 rows x 1001 cols · synthetic gene-expression screen: 100 patients x 1000 probes, planted signal/blocks/batch-confound - curse of dimensionality, Lasso, multiple testing
- `gene_expression_100x1000_labels.csv` — 100 rows x 3 cols · patient response + batch for the wide screen (key: private/homework_keys/)
- `retail_large_noisy.csv` — 510,000 rows x 9 cols · OnlineRetail resampled to 510k rows + injected dirt (missing, mixed date formats, dupes, outliers) + is_suspicious label - big-data cleaning practice (key: private/)
