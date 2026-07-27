#!/usr/bin/env bash
# Pick a 2A artefact preset from the press mix. This runs outside the model so
# a publish run receives one unambiguous, genuinely random selection.
set -euo pipefail

# /dev/urandom gives us an OS-supplied random value. Reject the small tail above
# the largest multiple of 100 so modulo mapping does not favour any bucket.
while :; do
  value="$(LC_ALL=C od -An -N2 -tu2 /dev/urandom | tr -d '[:space:]')"
  if [ "$value" -lt 65500 ]; then
    roll=$((value % 100))
    break
  fi
done

case "$roll" in
  0|1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31|32|33|34|35|36|37|38|39)
    echo research-poster ;;
  40|41|42|43|44|45|46|47|48|49|50|51|52|53|54|55|56|57|58|59|60|61|62|63|64|65|66|67|68|69|70|71|72|73|74|75|76|77|78|79)
    echo paper ;;
  80|81|82|83|84|85|86|87|88|89)
    echo marketing-poster ;;
  90|91|92|93|94|95|96|97)
    echo brochure ;;
  98)
    echo impact-report ;;
  99)
    echo strategy ;;
esac
