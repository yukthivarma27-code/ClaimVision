import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code import utils
from code.predictor import predict_csv


def main():
    parser = argparse.ArgumentParser(description="ClaimLens AI - Multi-Modal Evidence Review")
    parser.add_argument(
        "--input", type=str, default="dataset/claims.csv",
        help="Input claims CSV"
    )
    parser.add_argument(
        "--output", type=str, default="output.csv",
        help="Output predictions CSV"
    )
    parser.add_argument(
        "--sample", action="store_true",
        help="Run on sample_claims.csv instead"
    )
    parser.add_argument(
        "--api-key", type=str, default=None,
        help="OpenAI API key (or set OPENAI_API_KEY env var)"
    )
    args = parser.parse_args()

    import os
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key

    if args.sample:
        input_path = str(utils.DATASET_DIR / "sample_claims.csv")
    else:
        input_path = str(utils.DATASET_DIR / args.input)

    output_path = args.output

    utils.logger.info("=" * 60)
    utils.logger.info("ClaimLens AI - Multi-Modal Evidence Intelligence Platform")
    utils.logger.info("=" * 60)
    utils.logger.info(f"Input: {input_path}")
    utils.logger.info(f"Output: {output_path}")
    utils.logger.info(f"API Key present: {bool(os.getenv('OPENAI_API_KEY'))}")

    df = predict_csv(input_path, output_path)
    utils.logger.info(f"Done. Processed {len(df)} claims.")

    if args.sample:
        expected_path = utils.DATASET_DIR / "sample_claims.csv"
        expected = utils._pd_read_csv_expect(str(expected_path))
        actual = utils._pd_read_csv_expect(output_path)
        from sklearn.metrics import accuracy_score
        common = actual[actual["claim_status"].notna()]
        if len(common) > 0:
            acc = accuracy_score(expected.loc[common.index, "claim_status"], common["claim_status"])
            utils.logger.info(f"Sample accuracy (claim_status): {acc:.2%}")


if __name__ == "__main__":
    main()
