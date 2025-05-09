i=1; ls *.yar | sort | split -l 100 - group_ && for f in group_*; do cat $(cat "$f") >> "merged_group_$i.yar"; rm $(cat "$f") "$f"; ((i++)); done
mkdir -p Th50rules && i=1; ls *.yar | sort | split -l 10000 - group_ && for f in group_*; do cat $(cat "$f") >> "merged_group_$i.yar"; rm $(cat "$f") "$f"; ((i++)); done && mv merged_group_*.yar Th50rules/
