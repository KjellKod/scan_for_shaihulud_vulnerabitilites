#!/usr/bin/env bash

ROOT=${1:-"."}
BAD_LIST="bad-packages.txt"
OUTPUT="scan-results.txt"

if [ ! -f "$BAD_LIST" ]; then
  echo "Missing $BAD_LIST file"
  exit 1
fi

echo "" > "$OUTPUT"

BAD_ENTRIES=$(sed -E 's/\s*=\s*/|/' "$BAD_LIST")

scan_package_json() {
  local pkg="$1"
  local dir
  dir=$(dirname "$pkg")

  for sec in dependencies devDependencies peerDependencies optionalDependencies; do
    deps=$(jq -r "if .$sec then .$sec else {} end | to_entries[] | \"\(.key)|\(.value)\"" "$pkg" 2>/dev/null)
    for dep in $deps; do
      NAME="${dep%|*}"
      VERSION="${dep#*|}"
      CLEAN_VERSION=$(echo "$VERSION" | sed 's/^[~^]//')
      if echo "$BAD_ENTRIES" | grep -q "^$NAME|$CLEAN_VERSION$"; then
        echo "FOUND in package.json: $NAME@$VERSION  ($dir)" | tee -a "$OUTPUT"
      fi
    done
  done
}

scan_package_lock() {
  local lock="$1"
  local dir
  dir=$(dirname "$lock")

  # Detect lockfileVersion
  version=$(jq -r '.lockfileVersion // 1' "$lock" 2>/dev/null)

  if [ "$version" -ge 2 ]; then
    # npm v7+ lockfile format
    jq -r '.packages | to_entries[] | "\(.key)|\(.value.version // empty)"' "$lock" \
      | while read entry; do
          KEY="${entry%|*}"
          VERSION="${entry#*|}"
          [ -z "$VERSION" ] && continue
          NAME=$(basename "$KEY")
          if echo "$BAD_ENTRIES" | grep -q "^$NAME|$VERSION$"; then
            echo "FOUND in package-lock.json (v2): $NAME@$VERSION  ($dir)" | tee -a "$OUTPUT"
          fi
        done

  else
    # npm v6 lockfile format
    jq -r '.dependencies | to_entries[] | "\(.key)|\(.value.version)"' "$lock" \
      | while read entry; do
          NAME="${entry%|*}"
          VERSION="${entry#*|}"
          if echo "$BAD_ENTRIES" | grep -q "^$NAME|$VERSION$"; then
            echo "FOUND in package-lock.json (v1): $NAME@$VERSION  ($dir)" | tee -a "$OUTPUT"
          fi
        done
  fi
}

# Process package.json
while IFS= read -r pkg; do
  scan_package_json "$pkg"
done < <(find "$ROOT" -type f -name "package.json")

# Process package-lock.json
while IFS= read -r lock; do
  scan_package_lock "$lock"
done < <(find "$ROOT" -type f -name "package-lock.json")

echo "Done. Results saved to $OUTPUT"
