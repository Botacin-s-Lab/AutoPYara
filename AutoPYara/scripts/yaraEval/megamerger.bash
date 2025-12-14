# i=1; ls *.yar | sort | split -l 100 - group_ && for f in group_*; do cat $(cat "$f") >> "merged_group_$i.yar"; rm $(cat "$f") "$f"; ((i++)); done

python YayaReformat.py --csv-file /usr/src/app/YaraResults/clusterCSV/sdhash/Th50.csv --thv 50
mkdir -p Th50rules && i=1; ls *.yar | sort | split -l 100000 - group_ && for f in group_*; do cat $(cat "$f") >> "merged_group_$i.yar"; rm $(cat "$f") "$f"; ((i++)); done && mv merged_group_*.yar Th50rules/
python YayaReformat.py --csv-file /usr/src/app/YaraResults/clusterCSV/sdhash/Th60.csv --thv 60
mkdir -p Th60rules && i=1; ls *.yar | sort | split -l 100000 - group_ && for f in group_*; do cat $(cat "$f") >> "merged_group_$i.yar"; rm $(cat "$f") "$f"; ((i++)); done && mv merged_group_*.yar Th60rules/
python YayaReformat.py --csv-file /usr/src/app/YaraResults/clusterCSV/sdhash/Th70.csv --thv 70
mkdir -p Th70rules && i=1; ls *.yar | sort | split -l 100000 - group_ && for f in group_*; do cat $(cat "$f") >> "merged_group_$i.yar"; rm $(cat "$f") "$f"; ((i++)); done && mv merged_group_*.yar Th70rules/
python YayaReformat.py --csv-file /usr/src/app/YaraResults/clusterCSV/sdhash/Th80.csv --thv 80
mkdir -p Th80rules && i=1; ls *.yar | sort | split -l 100000 - group_ && for f in group_*; do cat $(cat "$f") >> "merged_group_$i.yar"; rm $(cat "$f") "$f"; ((i++)); done && mv merged_group_*.yar Th80rules/
python YayaReformat.py --csv-file /usr/src/app/YaraResults/clusterCSV/sdhash/Th90.csv --thv 90
mkdir -p Th90rules && i=1; ls *.yar | sort | split -l 100000 - group_ && for f in group_*; do cat $(cat "$f") >> "merged_group_$i.yar"; rm $(cat "$f") "$f"; ((i++)); done && mv merged_group_*.yar Th90rules/



# python YayaReformat.py --csv-file /usr/src/app/YaraResults/clusterCSV/ssdeep/th50.csv --thv 50
# mkdir -p Th50rules && i=1; ls *.yar | sort | split -l 100000 - group_ && for f in group_*; do cat $(cat "$f") >> "merged_group_$i.yar"; rm $(cat "$f") "$f"; ((i++)); done && mv merged_group_*.yar Th50rules/
# python YayaReformat.py --csv-file /usr/src/app/YaraResults/clusterCSV/ssdeep/th60.csv --thv 60
# mkdir -p Th60rules && i=1; ls *.yar | sort | split -l 100000 - group_ && for f in group_*; do cat $(cat "$f") >> "merged_group_$i.yar"; rm $(cat "$f") "$f"; ((i++)); done && mv merged_group_*.yar Th60rules/
# python YayaReformat.py --csv-file /usr/src/app/YaraResults/clusterCSV/ssdeep/th70.csv --thv 70
# mkdir -p Th70rules && i=1; ls *.yar | sort | split -l 100000 - group_ && for f in group_*; do cat $(cat "$f") >> "merged_group_$i.yar"; rm $(cat "$f") "$f"; ((i++)); done && mv merged_group_*.yar Th70rules/
# python YayaReformat.py --csv-file /usr/src/app/YaraResults/clusterCSV/ssdeep/th80.csv --thv 80
# mkdir -p Th80rules && i=1; ls *.yar | sort | split -l 100000 - group_ && for f in group_*; do cat $(cat "$f") >> "merged_group_$i.yar"; rm $(cat "$f") "$f"; ((i++)); done && mv merged_group_*.yar Th80rules/
# python YayaReformat.py --csv-file /usr/src/app/YaraResults/clusterCSV/ssdeep/th90.csv --thv 90
# mkdir -p Th90rules && i=1; ls *.yar | sort | split -l 100000 - group_ && for f in group_*; do cat $(cat "$f") >> "merged_group_$i.yar"; rm $(cat "$f") "$f"; ((i++)); done && mv merged_group_*.yar Th90rules/
