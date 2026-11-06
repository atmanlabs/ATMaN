#!/usr/bin/env bash
set -uo pipefail
W=/workspace/mg5-repro3/michaels-gate-v5-candidate-gen2; L=/workspace/mg5-repro3/logs; mkdir -p $L
export PYTHONDONTWRITEBYTECODE=1 PYTHONWARNINGS=ignore::ResourceWarning
step(){ n=$1; shift; echo "== $n start $(date '+%F %T %Z')" | tee -a $L/R3.log; ( "$@" ) > $L/$n.log 2>&1; rc=$?; echo "== $n exit $rc end $(date '+%F %T %Z')" | tee -a $L/R3.log; }
step v3_full bash -c "cd $W/inherited/v3/reference-model && ./verify.sh"
step v4_full bash -c "cd $W/inherited/v4/reference-model && ./verify.sh"
step tests bash -c "cd $W/reference-model && python3 -m unittest discover -s tests -t ."
step F1 bash -c "cd $W/reference-model && python3 q8F.py"
step F2 bash -c "cd $W/reference-model && python3 q8F2.py"
echo DONE >> $L/R3.log
