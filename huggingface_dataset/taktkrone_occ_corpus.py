import json
import datasets

_DESCRIPTION = """The TAKTKRONE OCC Dialogue Corpus for metro operations control center assistance."""

_HOMEPAGE = "https://taktkrone.ai"
_LICENSE = "apache-2.0"

class TaktkroneOCCCorpus(datasets.GeneratorBasedBuilder):
    """TAKTKRONE OCC Dialogue Corpus dataset."""

    VERSION = datasets.Version("1.0.0")

    def _info(self):
        features = datasets.Features({
            "id": datasets.Value("string"),
            "timestamp": datasets.Value("string"),
            "operator": datasets.Value("string"),
            "source": datasets.Value("string"),
            "task_type": datasets.Value("string"),
            "difficulty": datasets.Value("string"),
            "messages": datasets.Sequence({
                "role": datasets.Value("string"),
                "content": datasets.Value("string"),
                "timestamp": datasets.Value("string"),
            }),
            "ground_truth": datasets.Value("string"),
            "metadata": datasets.Value("string"),
        })

        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=features,
            homepage=_HOMEPAGE,
            license=_LICENSE,
        )

    def _split_generators(self, dl_manager):
        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN,
                gen_kwargs={"filepath": "train.jsonl"},
            ),
            datasets.SplitGenerator(
                name=datasets.Split.TEST,
                gen_kwargs={"filepath": "test.jsonl"},
            ),
        ]

    def _generate_examples(self, filepath):
        with open(filepath, encoding="utf-8") as f:
            for idx, line in enumerate(f):
                data = json.loads(line)
                yield idx, {
                    "id": data["id"],
                    "timestamp": data["timestamp"],
                    "operator": data["operator"],
                    "source": data["source"],
                    "task_type": data["task_type"],
                    "difficulty": data["difficulty"],
                    "messages": data["messages"],
                    "ground_truth": json.dumps(data.get("ground_truth", {})),
                    "metadata": json.dumps(data.get("metadata", {})),
                }
