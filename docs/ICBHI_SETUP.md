# ICBHI 2017 setup

RespLLM training uses the official respiratory-cycle annotations when they are on disk.
SwasthAI does not download this dataset. The challenge site requires registration, and
inventing cycles or scores is not part of the pipeline.

## Get the files

1. Open [https://bhichallenge.med.auth.gr/ICBHI_2017_Challenge](https://bhichallenge.med.auth.gr/ICBHI_2017_Challenge).
2. Register and download the respiratory sound database (wav files and the `.txt` cycle annotations).
3. If the site also offers the official train and test filename lists, download those too.
4. Extract everything into:

```
data/external/icbhi/
```

Either of these layouts works:

```
data/external/icbhi/101_1b1_Al_sc_Meditron.wav
data/external/icbhi/101_1b1_Al_sc_Meditron.txt
```

```
data/external/icbhi/ICBHI_final_database/101_1b1_Al_sc_Meditron.wav
data/external/icbhi/filename_train.txt
data/external/icbhi/filename_test.txt
```

Each annotation row is `start_sec end_sec crackle wheeze`. The patient id is the leading number in the filename. The loader refuses a split that puts one patient in both train and test.

## Train

From the repository root, with the project virtual environment active:

```powershell
python -m ml.respiratory.training.train
```

That command without code changes is the smoke test only if you call `train_respiratory_model(smoke_test=True)`. For the official corpus:

```powershell
python -c "from ml.respiratory.training.train import train_respiratory_model; print(train_respiratory_model(epochs=15, smoke_test=False))"
```

If the folder is empty, the command returns `DATASET_MISSING` and writes no accuracy.

Official filename lists are used when both `filename_train.txt` and `filename_test.txt` are present. Otherwise the run records `patient_shuffle_60_40_unofficial` in the checkpoint. That unofficial split is still patient-disjoint, and the report says it is unofficial.

## What is already runnable without the download

`python -c "from ml.respiratory.training.train import train_respiratory_model; train_respiratory_model(epochs=3, smoke_test=True)"`

The checkpoint is saved, and `dataset_source` is `synthetic_protocol_smoke`. Those metrics are not ICBHI results.
