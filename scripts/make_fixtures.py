import random, csv, os
from datetime import date, timedelta


def make_fixture(path:str, employees=5, trips_per=20):
    with open(path, "w", newline="") as f:
        writer=csv.writer(f)
        writer.writerow(["Employee","Country","Entry","Exit"])
        for e in range(employees):
            name=f"Emp{e+1}"
            start=date(2025,1,1)
            for _ in range(trips_per):
                stay=random.randint(1,30)
                entry=start+timedelta(days=random.randint(0,300))
                exit=entry+timedelta(days=stay)
                writer.writerow([name,"FR",entry,exit])


if __name__=="__main__":
    os.makedirs("data/fixtures",exist_ok=True)
    for i in range(10):
        make_fixture(f"data/fixtures/fix_{i}.csv")
