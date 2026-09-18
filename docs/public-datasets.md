# Public dataset assessment

Reviewed 2026-09-18. External records are separate from the synthetic investigation workflow.

## Acquired: ULB / Worldline credit-card transactions

The [publisher's Kaggle data card](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) describes anonymized real European card transactions from September 2013. We downloaded the CSV through the mirror explicitly used in the [official TensorFlow tutorial](https://www.tensorflow.org/tutorials/structured_data/imbalanced_data). No Kaggle credentials are needed.

The file has 284,807 rows and 31 columns: `Time`, `V1`–`V28`, `Amount`, and `Class`. There are 492 positive fraud labels. The acquisition script verifies every row for shape, missing values, finite numeric values, and permitted labels, and records a SHA-256 checksum. See [machine-readable acquisition report](../data/external/ulb-creditcard-profile.json) for measurements. Kaggle currently reports version 3; mirror byte identity with that version has not been established.

`Time` is elapsed seconds, not a calendar timestamp. PCA features have no disclosed business meanings. There are no usable account, login, device, or recipient identifiers. Do not invent those relationships or attribute a transaction to a synthetic account. Currency is not established by the inspected schema; do not assume USD.

**Use:** an optional, separate transaction-classification benchmark. It cannot establish account takeover, validate the investigation narrative, or measure RAG quality. No detector has been trained here. Future detection evaluation should freeze train/validation/test partitions, fit preprocessing on training data only, and report precision-recall metrics separately from retrieval/grounding metrics.

**License:** Kaggle reports “Database: Open Database, Contents: Database Contents,” corresponding to [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) and [DbCL 1.0](https://opendatacommons.org/licenses/dbcl/1-0/). Preserve attribution and these terms when using the data. This repository distributes acquisition code and aggregate metadata, not the CSV. Any later public redistribution or adapted database needs its own license review. Attribution: Machine Learning Group, Université Libre de Bruxelles, and Worldline; requested reference: Dal Pozzolo et al., *Calibrating Probability with Undersampling for Unbalanced Classification*, IEEE CIDM, 2015.

## Other candidates inspected

| Candidate | What the source actually offers | Decision |
| --- | --- | --- |
| [IEEE-CIS / Vesta](https://www.kaggle.com/competitions/ieee-fraud-detection/data) | Real e-commerce fraud data with transaction and partial identity tables joined by `TransactionID`; `DeviceType` / `DeviceInfo`; relative transaction time. License is subject to competition rules. | More relevant device context, but not a complete login/account audit trail. Not downloaded: readable competition terms and authorized download access have not been established. Do not acquire an unofficial mirror to bypass those conditions. |
| [Bank Account Fraud, NeurIPS 2022](https://www.kaggle.com/datasets/sgpjesus/bank-account-fraud-dataset-neurips-2022) | Six synthetic datasets generated from bank application data; CC BY-NC-SA 4.0. See the [publisher datasheet](https://raw.githubusercontent.com/feedzai/bank-account-fraud/main/documents/datasheet.pdf). | Account-opening fraud rather than established-account takeover. Not a source of real customer records. Not downloaded. |
| [Risk-Based Authentication research](https://riskbasedauthentication.org/publications/) | Researchers studied real service logins, but explicitly describe the released dataset as synthesized. | Potential future authentication benchmark, labeled synthetic. Not downloaded or joined to financial records. |

These candidate decisions are based on publisher schemas and documentation; only the ULB CSV has been acquired and row-profiled. No inspected source supplies all the linked records and investigation evidence needed for our ATO workflow. Keep the internally consistent synthetic case as the end-to-end demonstration.

## Reproduce the acquisition

From the project root, using Python 3.12+ (standard library only):

```sh
python scripts/download_public_data.py
```

On this Windows checkout:

```powershell
backend/.venv/Scripts/python.exe scripts/download_public_data.py
```

The CSV is approximately 151 MB, under `data/external/raw/ulb-creditcard/creditcard.csv`. Re-running validates an existing file instead of downloading again. The script enforces a 200 MB download limit, rejects unexpected schema/counts/license changes, and checks against the recorded checksum on subsequent runs. A failed partial download is removed.

The raw directory is ignored by Git. All `data/` is excluded from Vercel deployment. The application ingestion pipeline reads only its explicit document corpus; no endpoint imports this CSV. `Class` remains in the offline raw source for future evaluation, never in retrieved evidence. Before any future modeling integration, isolate labels from features and keep the evaluation process outside the runtime. No OpenAI key, model call, or hosted service is required for acquisition.
