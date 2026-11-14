#!/bin/sh
# Ensambla la exposición. Uso: build.sh online|offline
#  online  -> fragmento para publicar como artifact (three desde cdnjs)
#  offline -> documento HTML autónomo (three incrustado), para usar sin internet
cd "$(dirname "$0")"
MODE=${1:-online}
{
  if [ "$MODE" = offline ]; then
    printf '<!doctype html>\n<html lang="es"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    cat head.html extra.css; printf '</head>\n<body>\n'; cat body.html
    printf '<script>\n'; cat node_modules/three/build/three.min.js; printf '\n</script>\n'
  else
    cat head.html extra.css body.html
    printf '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>\n'
  fi
  printf '<script>\n'; cat core.js; printf '\n</script>\n<script>\n'; cat trial.js; printf '\n</script>\n'
  [ -f h9data.js ] && { printf '<script>\n'; cat h9data.js; printf '\n</script>\n'; }
  printf '<script>\n'; cat deck.js; printf '\n</script>\n'
  [ "$MODE" = offline ] && printf '</body></html>\n'
} > expo-$MODE.html
wc -c expo-$MODE.html
