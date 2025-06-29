from dotenv import load_dotenv

load_dotenv()

from vibetracer import analyze_my_code, dump_latest_run_llm_report


def main():
    report = dump_latest_run_llm_report()
    print(report)
    print('\n\n')
    res = analyze_my_code(report)
    print(res)


if __name__ == "__main__":
    main()
