# Bazel Mini Benchmark Results
**Runs per Scenario:** 3


## 🖥️ Test Machine Specs

| Component      | Details              |
|----------------|----------------------|
| **CPU**        | i7-13850HX           |
| **RAM**        | 65GB                 |
| **Storage**    | 1TB  ssd             |
| **GPU**        | NVIDIA RTX A1000 6GB |
| **OS**         | WSL2 (on Windows 11) |
| **Bazel**      | 7.4.0                |

## Executed In Repo

Repository = [process description](https://github.com/eclipse-score/process_description) (Version 06b3c952b)

## Explanation of terms

* Ultra Cold Start = `bazel clean --expunge && rm -r _build`
* Cold Start = `bazel clean && rm -r _build`
* Small Change = `one line change in process/index.rst`
* Cached = `no change`

---

## Benchmark 1: `bazel run //:docs`

| Scenario         | Run 1         | Run 2         | Run 3         | Average   |
|------------------|---------------|---------------|---------------|-----------|
| Ultra Cold Start | 40.285s       | 40.226s       | 38.568s       | **39.693s** |
| Cold Start       | 10.760s       | 10.317s       | 10.573s       | **10.550s** |
| Small Change     | 6.250s        | 5.664s        | 5.820s        | **5.911s**  |
| Cached           | 5.403s        | 5.396s        | 5.348s        | **5.382s**  |

---

## Benchmark 2: `bazel build //:needs_json`

| Scenario         | Run 1         | Run 2         | Run 3         | Average   |
|------------------|---------------|---------------|---------------|-----------|
| Ultra Cold Start | 32.961s       | 33.461s       | 32.613s       | **33.012s** |
| Cold Start       | 13.704s       | 12.909s       | 12.902s       | **13.172s** |
| Small Change     | 3.732s        | 3.697s        | 3.742s        | **3.724s**  |
| Cached           | 4.916s        | 3.686s        | 3.678s        | **4.093s**  |

---

## Benchmark 3: `bazel run //:live_preview`

| Scenario         | Run 1         | Run 2         | Run 3         | Average   |
|------------------|---------------|---------------|---------------|-----------|
| Ultra Cold Start | 29.896s       | 31.930s       | 28.955s       | **30.260s** |
| Cold Start       | 8.634s        | 8.789s        | 8.251s        | **8.558s**  |
| Small Change     | 3.529s        | 3.519s        | 3.638s        | **3.562s**  |
| Cached           | 3.598s        | 3.434s        | 3.436s        | **3.489s**  |
