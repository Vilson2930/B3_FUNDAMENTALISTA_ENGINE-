# ============================================================
# run_technical.py
# Executa apenas a análise técnica das TOP 20 Premium
# ============================================================

from engine.technical_engine import analisar_top20


def main():
    print("=" * 80)
    print("B3 TECHNICAL ENGINE")
    print("=" * 80)

    analisar_top20()

    print("=" * 80)
    print("ANÁLISE TÉCNICA FINALIZADA")
    print("=" * 80)


if __name__ == "__main__":
    main()
