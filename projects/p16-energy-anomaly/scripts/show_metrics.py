import json

m = json.load(open("outputs/metrics.json"))
print("n:", m["injection_n"], "meter:", m["held_out_meter"], "seed:", m["seed"])
for method, types in m["injection_scores"].items():
    print("===", method)
    for t, s in types.items():
        print(
            f"  {t:9s} P={s['precision']:.3f} R={s['recall']:.3f} "
            f"F1={s['f1']:.3f} delay={s['mean_delay_periods']} n={s['n']}"
        )
